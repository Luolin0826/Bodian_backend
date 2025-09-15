#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精确匹配版本 - 使用姓名+手机号修正secondary_unit_id
"""

import pandas as pd
import mysql.connector
from mysql.connector import Error

# 数据库连接配置
DB_CONFIG = {
    'host': 'rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'database': 'bdprod',
    'user': 'dms_user_9332d9e',
    'password': 'AaBb19990826',
    'charset': 'utf8mb4'
}

def correct_secondary_unit_id_precise():
    """使用姓名+手机号进行精确匹配修正"""
    print("="*80)
    print("精确匹配修正secondary_unit_id (姓名+手机号)")
    print("="*80)
    
    try:
        # 1. 读取Excel文件
        print("1. 读取Excel文件...")
        excel_df = pd.read_excel('25国网南网录取_updated.xlsx', sheet_name='一批')
        print(f"读取第一批数据: {len(excel_df)} 条记录")
        
        # 2. 连接数据库
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        # 获取secondary_units映射
        cursor.execute("SELECT unit_id, unit_name FROM secondary_units")
        units = cursor.fetchall()
        unit_name_to_id = {unit['unit_name']: unit['unit_id'] for unit in units}
        
        print(f"数据库中共有 {len(units)} 个二级单位")
        
        # 3. 精确匹配并找出需要修正的记录
        print(f"\n2. 使用姓名+手机号进行精确匹配...")
        
        corrections_needed = []
        matched_count = 0
        not_found_count = 0
        unit_not_found = set()
        phone_issues = 0
        
        batch_size = 1000
        total_batches = (len(excel_df) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min((batch_num + 1) * batch_size, len(excel_df))
            batch_df = excel_df.iloc[start_idx:end_idx]
            
            print(f"  处理批次 {batch_num + 1}/{total_batches} (第 {start_idx+1}-{end_idx} 条记录)")
            
            for idx, row in batch_df.iterrows():
                name = str(row['姓名']).strip()
                excel_unit = str(row['上岸电网省份']).strip()
                excel_phone = str(row['手机号']).strip() if pd.notna(row['手机号']) else None
                
                # 获取Excel单位对应的unit_id
                excel_unit_id = unit_name_to_id.get(excel_unit)
                if not excel_unit_id:
                    unit_not_found.add(excel_unit)
                    continue
                
                # 使用姓名+手机号精确匹配
                if excel_phone and excel_phone != 'nan' and '*' not in excel_phone:
                    # 使用完整手机号匹配
                    cursor.execute("""
                        SELECT record_id, secondary_unit_id
                        FROM recruitment_records 
                        WHERE name = %s AND phone = %s AND company = '国网' AND batch = '第一批'
                    """, (name, excel_phone))
                elif excel_phone and '*' in excel_phone:
                    # 如果是脱敏手机号，使用LIKE匹配
                    phone_pattern = excel_phone.replace('*', '_')
                    cursor.execute("""
                        SELECT record_id, secondary_unit_id, phone
                        FROM recruitment_records 
                        WHERE name = %s AND phone LIKE %s AND company = '国网' AND batch = '第一批'
                    """, (name, phone_pattern))
                else:
                    # 没有手机号信息，跳过以避免错误匹配
                    phone_issues += 1
                    continue
                
                db_records = cursor.fetchall()
                
                if not db_records:
                    not_found_count += 1
                    continue
                
                # 处理匹配到的记录
                for db_record in db_records:
                    if db_record['secondary_unit_id'] != excel_unit_id:
                        corrections_needed.append({
                            'record_id': db_record['record_id'],
                            'name': name,
                            'phone': excel_phone,
                            'correct_unit_id': excel_unit_id,
                            'excel_unit': excel_unit,
                            'current_unit_id': db_record['secondary_unit_id']
                        })
                    else:
                        matched_count += 1
        
        print(f"\n匹配结果:")
        print(f"  匹配正确: {matched_count}")
        print(f"  需要修正: {len(corrections_needed)}")
        print(f"  未找到: {not_found_count}")
        print(f"  手机号问题: {phone_issues}")
        print(f"  Excel中未知单位: {len(unit_not_found)}")
        
        # 显示需要修正的示例
        if corrections_needed:
            print(f"\n需要修正的记录示例 (前10个):")
            for correction in corrections_needed[:10]:
                # 获取当前单位名称
                current_unit_name = "未知"
                for unit in units:
                    if unit['unit_id'] == correction['current_unit_id']:
                        current_unit_name = unit['unit_name']
                        break
                
                print(f"  {correction['name']} ({correction['phone']}): {current_unit_name} -> {correction['excel_unit']}")
        
        if unit_not_found:
            print(f"\nExcel中未找到的单位:")
            for unit in sorted(unit_not_found)[:5]:
                print(f"  - {unit}")
        
        # 4. 执行修正
        if corrections_needed:
            print(f"\n3. 执行修正...")
            
            print(f"准备修正 {len(corrections_needed)} 条记录")
            print("开始执行修正...")
            
            success_count = 0
            error_count = 0
            batch_size = 100
            
            for i in range(0, len(corrections_needed), batch_size):
                batch = corrections_needed[i:i + batch_size]
                
                try:
                    # 构建批量更新SQL
                    update_data = [(correction['correct_unit_id'], correction['record_id']) for correction in batch]
                    
                    cursor.executemany("""
                        UPDATE recruitment_records 
                        SET secondary_unit_id = %s, updated_at = NOW()
                        WHERE record_id = %s
                    """, update_data)
                    
                    connection.commit()
                    success_count += len(batch)
                    
                    if i % (batch_size * 10) == 0:  # 每1000条显示一次进度
                        print(f"  已修正: {success_count}/{len(corrections_needed)}")
                        
                except Exception as e:
                    print(f"  批量修正失败: {e}")
                    error_count += len(batch)
                    connection.rollback()
            
            print(f"\n修正完成:")
            print(f"  成功修正: {success_count}")
            print(f"  失败: {error_count}")
            
            # 5. 验证修正结果
            if success_count > 0:
                print(f"\n4. 验证修正结果...")
                
                # 随机验证一些记录
                import random
                sample_size = min(10, len(corrections_needed))
                sample_corrections = random.sample(corrections_needed, sample_size)
                verified_count = 0
                
                for correction in sample_corrections:
                    cursor.execute("""
                        SELECT s.unit_name
                        FROM recruitment_records r
                        JOIN secondary_units s ON r.secondary_unit_id = s.unit_id
                        WHERE r.record_id = %s
                    """, (correction['record_id'],))
                    
                    result = cursor.fetchone()
                    if result and result['unit_name'] == correction['excel_unit']:
                        verified_count += 1
                        print(f"  ✅ {correction['name']}: 已修正为 {result['unit_name']}")
                    else:
                        print(f"  ❌ {correction['name']}: 验证失败")
                
                print(f"\n验证结果: {verified_count}/{sample_size} 修正成功")
                
            # 6. 最终统计
            print(f"\n5. 最终统计...")
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN secondary_unit_id IS NOT NULL THEN 1 ELSE 0 END) as with_unit
                FROM recruitment_records 
                WHERE company = '国网' AND batch = '第一批'
            """)
            final_stats = cursor.fetchone()
            
            coverage_rate = (final_stats['with_unit'] / final_stats['total']) * 100
            print(f"  总记录数: {final_stats['total']}")
            print(f"  有单位分配: {final_stats['with_unit']}")
            print(f"  覆盖率: {coverage_rate:.1f}%")
            
        else:
            print("✅ 所有记录都已正确匹配！")
            
    except Exception as e:
        print(f"修正过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    correct_secondary_unit_id_precise()
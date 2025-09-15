#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化版本 - 根据25国网南网录取_updated表修正recruitment_records中的secondary_unit_id
"""

import pandas as pd
import mysql.connector
from mysql.connector import Error
import numpy as np

# 数据库连接配置
DB_CONFIG = {
    'host': 'rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'database': 'bdprod',
    'user': 'dms_user_9332d9e',
    'password': 'AaBb19990826',
    'charset': 'utf8mb4'
}

def correct_secondary_unit_id_optimized():
    """优化版本 - 批量处理修正secondary_unit_id"""
    print("="*80)
    print("优化版本 - 修正secondary_unit_id")
    print("="*80)
    
    try:
        # 1. 读取Excel文件
        print("1. 读取Excel文件...")
        excel_file = '25国网南网录取_updated.xlsx'
        excel_df = pd.read_excel(excel_file, sheet_name='一批')
        print(f"读取第一批数据: {len(excel_df)} 条记录")
        
        # 2. 连接数据库并获取所有相关数据
        print("2. 连接数据库并获取数据...")
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        # 获取secondary_units映射
        cursor.execute("SELECT unit_id, unit_name FROM secondary_units")
        units = cursor.fetchall()
        unit_name_to_id = {unit['unit_name']: unit['unit_id'] for unit in units}
        unit_id_to_name = {unit['unit_id']: unit['unit_name'] for unit in units}
        
        # 一次性获取所有国网第一批的记录
        cursor.execute("""
            SELECT r.record_id, r.name, r.secondary_unit_id, s.unit_name
            FROM recruitment_records r
            LEFT JOIN secondary_units s ON r.secondary_unit_id = s.unit_id
            WHERE r.company = '国网' AND r.batch = '第一批'
        """)
        
        db_records = cursor.fetchall()
        print(f"从数据库获取 {len(db_records)} 条记录")
        
        # 创建数据库记录的索引
        db_dict = {}
        for record in db_records:
            name = record['name']
            if name not in db_dict:
                db_dict[name] = []
            db_dict[name].append(record)
        
        # 3. 批量对比并找出需要修正的记录
        print("3. 批量对比数据...")
        
        corrections_needed = []
        matched_count = 0
        not_found_count = 0
        unit_not_found = set()
        
        for idx, row in excel_df.iterrows():
            name = str(row['姓名']).strip()
            excel_unit = str(row['上岸电网省份']).strip()
            
            # 获取Excel单位对应的unit_id
            excel_unit_id = unit_name_to_id.get(excel_unit)
            if not excel_unit_id:
                unit_not_found.add(excel_unit)
                continue
            
            # 查找数据库中的记录
            if name in db_dict:
                for db_record in db_dict[name]:
                    if db_record['secondary_unit_id'] != excel_unit_id:
                        corrections_needed.append({
                            'record_id': db_record['record_id'],
                            'name': name,
                            'correct_unit_id': excel_unit_id,
                            'excel_unit': excel_unit,
                            'current_unit': db_record['unit_name']
                        })
                    else:
                        matched_count += 1
            else:
                not_found_count += 1
        
        print(f"\n对比结果:")
        print(f"  匹配正确: {matched_count}")
        print(f"  需要修正: {len(corrections_needed)}")
        print(f"  在数据库中未找到: {not_found_count}")
        print(f"  Excel中未知单位: {len(unit_not_found)}")
        
        # 显示需要修正的示例
        if corrections_needed:
            print(f"\n需要修正的记录示例 (前10个):")
            for correction in corrections_needed[:10]:
                print(f"  {correction['name']}: {correction['current_unit']} -> {correction['excel_unit']}")
        
        if unit_not_found:
            print(f"\nExcel中未找到的单位:")
            for unit in sorted(unit_not_found):
                print(f"  - {unit}")
        
        # 4. 执行批量修正
        if corrections_needed:
            print(f"\n4. 执行批量修正...")
            
            confirm = input(f"发现 {len(corrections_needed)} 条需要修正的记录，是否继续? (y/N): ")
            
            if confirm.lower() == 'y':
                # 批量更新
                success_count = 0
                batch_size = 1000
                
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
                        print(f"  已修正: {success_count}/{len(corrections_needed)}")
                        
                    except Exception as e:
                        print(f"  批量修正失败: {e}")
                        connection.rollback()
                
                print(f"\n修正完成: {success_count} 条记录")
                
                # 5. 验证修正结果
                print(f"\n5. 验证修正结果...")
                
                # 随机验证10条记录
                import random
                sample_corrections = random.sample(corrections_needed, min(10, len(corrections_needed)))
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
                        print(f"  ✅ {correction['name']}: 修正为 {result['unit_name']}")
                    else:
                        print(f"  ❌ {correction['name']}: 验证失败")
                
                print(f"\n验证结果: {verified_count}/{len(sample_corrections)} 修正成功")
                
                # 6. 最终统计
                print(f"\n6. 最终统计...")
                cursor.execute("""
                    SELECT COUNT(*) as total,
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
                print("取消修正操作")
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
    correct_secondary_unit_id_optimized()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终版本 - 高效修正secondary_unit_id
"""

import pandas as pd
import mysql.connector
from mysql.connector import Error
import tempfile
import os

# 数据库连接配置
DB_CONFIG = {
    'host': 'rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'database': 'bdprod',
    'user': 'dms_user_9332d9e',
    'password': 'AaBb19990826',
    'charset': 'utf8mb4'
}

def final_correct_secondary_unit_id():
    """最终版本 - 高效修正"""
    print("="*80)
    print("最终版本 - 高效修正secondary_unit_id")
    print("="*80)
    
    try:
        # 1. 读取Excel文件
        print("1. 读取Excel数据...")
        excel_df = pd.read_excel('25国网南网录取_updated.xlsx', sheet_name='一批')
        print(f"Excel记录数: {len(excel_df)}")
        
        # 2. 连接数据库
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        # 获取单位映射
        cursor.execute("SELECT unit_id, unit_name FROM secondary_units")
        units = cursor.fetchall()
        unit_name_to_id = {unit['unit_name']: unit['unit_id'] for unit in units}
        
        print(f"单位映射表: {len(units)} 个单位")
        
        # 3. 一次性获取所有数据库记录
        print(f"2. 获取数据库记录...")
        cursor.execute("""
            SELECT record_id, name, phone, secondary_unit_id
            FROM recruitment_records 
            WHERE company = '国网' AND batch = '第一批'
        """)
        db_records = cursor.fetchall()
        
        print(f"数据库记录数: {len(db_records)}")
        
        # 创建数据库记录的字典索引 (name+phone -> record_info)
        db_index = {}
        for record in db_records:
            key = f"{record['name']}|{record['phone']}"
            db_index[key] = record
        
        print(f"创建索引完成: {len(db_index)} 个唯一键")
        
        # 4. 批量对比
        print(f"3. 批量对比数据...")
        corrections_needed = []
        stats = {
            'matched': 0,
            'need_correction': 0,
            'not_found': 0,
            'unit_not_found': 0,
            'phone_issue': 0
        }
        
        for idx, row in excel_df.iterrows():
            name = str(row['姓名']).strip()
            excel_unit = str(row['上岸电网省份']).strip()
            excel_phone = str(row['手机号']).strip() if pd.notna(row['手机号']) else ""
            
            # 检查单位映射
            excel_unit_id = unit_name_to_id.get(excel_unit)
            if not excel_unit_id:
                stats['unit_not_found'] += 1
                continue
            
            # 检查手机号
            if not excel_phone or excel_phone == 'nan':
                stats['phone_issue'] += 1
                continue
            
            # 查找数据库记录
            key = f"{name}|{excel_phone}"
            db_record = db_index.get(key)
            
            if not db_record:
                stats['not_found'] += 1
                continue
            
            # 比较单位ID
            if db_record['secondary_unit_id'] != excel_unit_id:
                corrections_needed.append({
                    'record_id': db_record['record_id'],
                    'name': name,
                    'phone': excel_phone,
                    'correct_unit_id': excel_unit_id,
                    'excel_unit': excel_unit,
                    'current_unit_id': db_record['secondary_unit_id']
                })
                stats['need_correction'] += 1
            else:
                stats['matched'] += 1
            
            # 进度显示
            if (idx + 1) % 5000 == 0:
                print(f"  已处理: {idx + 1}/{len(excel_df)}")
        
        print(f"\n对比结果:")
        print(f"  匹配正确: {stats['matched']}")
        print(f"  需要修正: {stats['need_correction']}")
        print(f"  未找到记录: {stats['not_found']}")
        print(f"  Excel单位未找到: {stats['unit_not_found']}")
        print(f"  手机号问题: {stats['phone_issue']}")
        
        # 显示修正示例
        if corrections_needed:
            print(f"\n需要修正的记录示例 (前10个):")
            unit_id_to_name = {unit['unit_id']: unit['unit_name'] for unit in units}
            
            for correction in corrections_needed[:10]:
                current_unit = unit_id_to_name.get(correction['current_unit_id'], '未知')
                print(f"  {correction['name']}: {current_unit} -> {correction['excel_unit']}")
        
        # 5. 执行修正
        if corrections_needed:
            print(f"\n4. 执行批量修正...")
            print(f"准备修正 {len(corrections_needed)} 条记录")
            
            # 分批执行更新
            batch_size = 1000
            success_count = 0
            
            for i in range(0, len(corrections_needed), batch_size):
                batch = corrections_needed[i:i + batch_size]
                
                try:
                    # 使用UPDATE语句批量更新
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
                    print(f"  批次修正失败: {e}")
                    connection.rollback()
            
            print(f"\n修正完成: {success_count} 条记录")
            
            # 6. 验证结果
            if success_count > 0:
                print(f"\n5. 验证修正结果...")
                
                # 抽样验证
                import random
                sample_size = min(20, len(corrections_needed))
                samples = random.sample(corrections_needed, sample_size)
                
                verified = 0
                for sample in samples:
                    cursor.execute("""
                        SELECT s.unit_name
                        FROM recruitment_records r
                        JOIN secondary_units s ON r.secondary_unit_id = s.unit_id
                        WHERE r.record_id = %s
                    """, (sample['record_id'],))
                    
                    result = cursor.fetchone()
                    if result and result['unit_name'] == sample['excel_unit']:
                        verified += 1
                
                print(f"验证结果: {verified}/{sample_size} 修正成功")
                
                # 最终统计
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN secondary_unit_id IS NOT NULL THEN 1 ELSE 0 END) as with_unit,
                        COUNT(DISTINCT secondary_unit_id) as distinct_units
                    FROM recruitment_records 
                    WHERE company = '国网' AND batch = '第一批'
                """)
                final_stats = cursor.fetchone()
                
                print(f"\n6. 最终统计:")
                print(f"  总记录数: {final_stats['total']}")
                print(f"  有单位分配: {final_stats['with_unit']}")
                print(f"  不同单位数: {final_stats['distinct_units']}")
                print(f"  分配覆盖率: {final_stats['with_unit']/final_stats['total']*100:.1f}%")
                
        else:
            print("✅ 所有记录都已正确匹配！")
            
        # 7. 生成报告
        print(f"\n7. 修正报告:")
        print(f"{'='*50}")
        print(f"Excel文件记录数: {len(excel_df)}")
        print(f"数据库记录数: {len(db_records)}")
        print(f"成功修正记录数: {success_count if corrections_needed else 0}")
        print(f"修正准确率: {verified/sample_size*100:.1f}%" if corrections_needed and success_count > 0 else "N/A")
        
        if stats['not_found'] > 0:
            print(f"\n⚠️ 有 {stats['not_found']} 条Excel记录在数据库中未找到")
        
        if stats['unit_not_found'] > 0:
            print(f"⚠️ 有 {stats['unit_not_found']} 条Excel记录的单位在数据库中未找到")
            
        print("✅ secondary_unit_id修正完成！")
        
    except Exception as e:
        print(f"修正过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    final_correct_secondary_unit_id()
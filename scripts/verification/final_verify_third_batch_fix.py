#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终验证第三批secondary_unit_id修正结果
"""
import pandas as pd
import mysql.connector
from mysql.connector import Error

def connect_to_database():
    """连接到数据库"""
    try:
        connection = mysql.connector.connect(
            host='rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
            port=3306,
            database='bdprod',
            user='dms_user_9332d9e',
            password='AaBb19990826',
            charset='utf8mb4'
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def final_verification():
    """最终验证修正结果"""
    print("="*80)
    print("最终验证第三批secondary_unit_id修正结果")
    print("="*80)
    
    connection = connect_to_database()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(buffered=True)
        
        # 1. 读取Excel数据
        print("1. 读取Excel第三批数据...")
        df = pd.read_excel("25国网南网录取_updated.xlsx", sheet_name="三批")
        excel_unit_stats = df['上岸电网省份'].value_counts()
        print(f"Excel记录数: {len(df)}")
        
        # 2. 查询数据库中修正后的分配情况
        print("2. 检查数据库中修正后的单位分配...")
        cursor.execute("""
            SELECT 
                su.unit_name,
                COUNT(rr.record_id) as db_count,
                su.unit_id
            FROM recruitment_records rr
            JOIN secondary_units su ON rr.secondary_unit_id = su.unit_id
            WHERE rr.batch = '第三批' AND rr.company = '国网'
            GROUP BY su.unit_name, su.unit_id
            ORDER BY db_count DESC
        """)
        
        db_unit_stats = cursor.fetchall()
        
        # 3. 对比Excel与数据库的单位分配
        print("3. 对比Excel与数据库单位分配...")
        print("-" * 80)
        print(f"{'单位名称':<30} {'Excel人数':<10} {'数据库人数':<12} {'匹配状态':<10}")
        print("-" * 80)
        
        # 创建数据库统计字典
        db_stats_dict = {unit_name: count for unit_name, count, unit_id in db_unit_stats}
        
        total_matches = 0
        total_mismatches = 0
        
        # 按Excel中的单位顺序显示对比
        for unit_name in excel_unit_stats.index:
            excel_count = excel_unit_stats[unit_name]
            db_count = db_stats_dict.get(unit_name, 0)
            
            if excel_count == db_count:
                status = "✅ 匹配"
                total_matches += excel_count
            else:
                status = "❌ 不匹配"
                total_mismatches += abs(excel_count - db_count)
            
            print(f"{unit_name:<30} {excel_count:<10} {db_count:<12} {status:<10}")
        
        print("-" * 80)
        print(f"总计匹配记录: {total_matches}")
        print(f"总计不匹配: {total_mismatches}")
        
        # 4. 检查是否有未分配的记录
        print("\n4. 检查未分配记录...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM recruitment_records 
            WHERE batch = '第三批' AND company = '国网' AND secondary_unit_id IS NULL
        """)
        unassigned_count = cursor.fetchone()[0]
        print(f"未分配secondary_unit_id的记录: {unassigned_count} 条")
        
        # 5. 最终统计
        print("\n5. 最终统计...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM recruitment_records 
            WHERE batch = '第三批' AND company = '国网'
        """)
        total_db_records = cursor.fetchone()[0]
        
        print(f"Excel记录总数: {len(df)}")
        print(f"数据库记录总数: {total_db_records}")
        print(f"分配成功率: {(total_db_records - unassigned_count) / total_db_records * 100:.1f}%")
        
        if total_mismatches == 0 and unassigned_count == 0:
            print("\n🎉 第三批secondary_unit_id修正完全成功！")
            print("✅ 所有记录都已正确分配到对应的二级单位")
        elif unassigned_count == 0:
            print(f"\n⚠️  虽然所有记录都已分配，但仍有 {total_mismatches} 条分配不匹配")
        else:
            print(f"\n❌ 仍有问题需要解决:")
            print(f"   - 未分配记录: {unassigned_count} 条")
            print(f"   - 分配不匹配: {total_mismatches} 条")
        
        print("\n" + "="*80)
        print("最终验证完成！")
        print("="*80)
        
    except Exception as e:
        print(f"验证过程中出现错误: {e}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    final_verification()
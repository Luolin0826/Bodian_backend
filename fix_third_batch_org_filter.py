#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复第三批数据的org_type筛选问题
"""
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

def analyze_third_batch_units():
    """分析第三批数据的单位类型分布"""
    print("="*80)
    print("分析第三批数据的单位类型问题")
    print("="*80)
    
    connection = connect_to_database()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(buffered=True)
        
        # 1. 查看第三批数据的单位分布
        print("1. 第三批数据的单位类型分布:")
        cursor.execute("""
            SELECT 
                su.org_type,
                su.unit_name,
                COUNT(rr.record_id) as record_count
            FROM recruitment_records rr
            JOIN secondary_units su ON rr.secondary_unit_id = su.unit_id
            WHERE rr.batch_code = '2025GW03'
            GROUP BY su.org_type, su.unit_name
            ORDER BY record_count DESC
        """)
        
        third_batch_units = cursor.fetchall()
        
        print(f"第三批共涉及 {len(third_batch_units)} 个单位:")
        org_type_stats = {}
        
        for org_type, unit_name, count in third_batch_units[:15]:  # 显示前15个
            print(f"  {org_type} - {unit_name}: {count} 人")
            org_type_stats[org_type] = org_type_stats.get(org_type, 0) + count
        
        print("\n第三批单位类型汇总:")
        for org_type, total in org_type_stats.items():
            print(f"  {org_type}: {total} 人")
        
        # 2. 检查第三批是否真的是国网数据
        print("\n2. 验证第三批是否为国网数据:")
        cursor.execute("""
            SELECT company, COUNT(*) as count
            FROM recruitment_records 
            WHERE batch_code = '2025GW03'
            GROUP BY company
        """)
        
        company_stats = cursor.fetchall()
        for company, count in company_stats:
            print(f"  {company}: {count} 人")
        
        # 3. 提供解决方案
        print("\n3. 解决方案选择:")
        print("由于第三批数据主要是'省属产业'单位，有以下解决方案:")
        print("")
        print("方案A: 修改API的guowang筛选逻辑，包含'省属产业'")
        print("  - 将'省属产业'也认为是国网相关单位")
        print("  - 优点: 简单快速")
        print("  - 缺点: 可能影响其他筛选逻辑")
        print("")
        print("方案B: 基于company字段筛选，而非org_type")
        print("  - guowang筛选改为company='国网'")
        print("  - 优点: 更准确反映数据本质")
        print("  - 缺点: 需要修改筛选逻辑")
        print("")
        print("方案C: 混合筛选策略")
        print("  - guowang = (company='国网' OR org_type IN ('国网省公司', '国网直属单位'))")
        print("  - 优点: 最全面")
        print("  - 缺点: 逻辑稍复杂")
        
        # 4. 测试方案B的效果
        print("\n4. 测试方案B (基于company筛选):")
        cursor.execute("""
            SELECT 
                u.standard_name,
                COUNT(*) as admission_count,
                su.unit_name,
                su.org_type
            FROM recruitment_records rr
            JOIN universities u ON rr.university_id = u.university_id
            JOIN secondary_units su ON rr.secondary_unit_id = su.unit_id
            WHERE rr.batch_code = '2025GW03' 
            AND rr.company = '国网'
            AND su.is_active = 1
            GROUP BY u.university_id, u.standard_name, su.unit_name, su.org_type
            ORDER BY admission_count DESC
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        print(f"使用company='国网'筛选结果: {len(results)} 所学校")
        
        if results:
            print("前10所学校:")
            for school, count, unit, org_type in results:
                print(f"  {school}: {count} 人 ({unit} - {org_type})")
        
        print("\n" + "="*80)
        print("分析完成！")
        print("="*80)
        
    except Exception as e:
        print(f"分析过程中出现错误: {e}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    analyze_third_batch_units()
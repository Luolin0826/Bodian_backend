#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版南网数据验证
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

def simple_verification():
    """简化验证"""
    print("="*80)
    print("南网数据简化验证")
    print("="*80)
    
    connection = connect_to_database()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(buffered=True)
        
        # 1. 基本统计
        print("1. 基本统计...")
        cursor.execute("""
            SELECT company, batch, COUNT(*) as count
            FROM recruitment_records 
            GROUP BY company, batch
            ORDER BY company, batch
        """)
        stats = cursor.fetchall()
        
        company_totals = {}
        print("详细统计:")
        for company, batch, count in stats:
            print(f"  {company} - {batch}: {count:,} 人")
            company_totals[company] = company_totals.get(company, 0) + count
        
        print("\n公司总计:")
        total_all = 0
        for company, total in company_totals.items():
            print(f"  {company}: {total:,} 人")
            total_all += total
        print(f"  总计: {total_all:,} 人")
        
        # 2. 院校总数
        print("\n2. 院校总数...")
        cursor.execute("SELECT COUNT(*) FROM universities")
        total_universities = cursor.fetchone()[0]
        print(f"院校总数: {total_universities} 个")
        
        # 3. 检查重叠人员数量
        print("\n3. 检查国网南网重叠人员数量...")
        cursor.execute("""
            SELECT COUNT(DISTINCT CONCAT(r1.name, '|', r1.phone)) as overlap_count
            FROM recruitment_records r1
            JOIN recruitment_records r2 ON r1.name = r2.name AND r1.phone = r2.phone
            WHERE r1.company != r2.company AND r1.record_id < r2.record_id
        """)
        overlap_count = cursor.fetchone()[0]
        print(f"国网南网重叠人员: {overlap_count} 个")
        
        # 4. 南网数据质量检查
        print("\n4. 南网数据质量检查...")
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(university_id) as has_university,
                   COUNT(secondary_unit_id) as has_unit
            FROM recruitment_records 
            WHERE company = '南网'
        """)
        result = cursor.fetchone()
        total, has_uni, has_unit = result
        
        print(f"南网记录总数: {total}")
        print(f"有院校信息: {has_uni} ({has_uni/total*100:.1f}%)")
        print(f"有单位信息: {has_unit} ({has_unit/total*100:.1f}%)")
        
        print("\n" + "="*80)
        print("简化验证完成！")
        print("="*80)
        
    except Exception as e:
        print(f"验证过程中出现错误: {e}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    simple_verification()
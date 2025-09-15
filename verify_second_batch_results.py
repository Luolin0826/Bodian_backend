#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证第二批数据处理结果
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

def verify_results():
    """验证第二批数据处理结果"""
    print("="*80)
    print("验证第二批数据处理结果")
    print("="*80)
    
    connection = connect_to_database()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(buffered=True)
        
        # 1. 读取Excel第二批数据
        print("1. 读取Excel数据...")
        df = pd.read_excel("25国网南网录取_updated.xlsx", sheet_name="二批")
        excel_records = len(df)
        print(f"Excel第二批记录数: {excel_records}")
        
        # 2. 检查数据库中第二批记录
        print("2. 检查数据库中第二批记录...")
        cursor.execute("""
            SELECT COUNT(*) FROM recruitment_records 
            WHERE batch = '第二批' AND company = '国网'
        """)
        db_second_batch = cursor.fetchone()[0]
        print(f"数据库中第二批记录数: {db_second_batch}")
        
        # 3. 检查Excel中重复的姓名+手机号组合
        print("3. 检查Excel中的重复记录...")
        df_clean = df.dropna(subset=['手机号'])
        df_clean['phone'] = df_clean['手机号'].astype(str)
        
        # 统计重复的姓名+手机号组合
        duplicates = df_clean.groupby(['姓名', 'phone']).size()
        duplicate_pairs = duplicates[duplicates > 1]
        
        print(f"Excel中唯一的姓名+手机号组合: {len(duplicates)}")
        print(f"Excel中重复的姓名+手机号组合: {len(duplicate_pairs)}")
        
        if len(duplicate_pairs) > 0:
            print("重复的组合样例:")
            for i, ((name, phone), count) in enumerate(duplicate_pairs.head().items(), 1):
                print(f"  {i}. {name} - {phone}: {count} 次")
        
        # 4. 使用临时表精确匹配
        print("4. 精确匹配验证...")
        
        # 创建临时表
        cursor.execute("DROP TEMPORARY TABLE IF EXISTS temp_verify")
        cursor.execute("""
            CREATE TEMPORARY TABLE temp_verify (
                name VARCHAR(50), 
                phone VARCHAR(20), 
                university VARCHAR(100),
                unit VARCHAR(50)
            )
        """)
        
        # 插入Excel数据
        temp_data = []
        for _, row in df_clean.iterrows():
            temp_data.append((
                row['姓名'], 
                row['phone'], 
                row['院校'],
                row['上岸电网省份']
            ))
        
        cursor.executemany("""
            INSERT INTO temp_verify (name, phone, university, unit) 
            VALUES (%s, %s, %s, %s)
        """, temp_data)
        
        # 查询匹配情况
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT CONCAT(tv.name, '|', tv.phone)) as excel_unique,
                COUNT(DISTINCT CONCAT(rr.name, '|', rr.phone)) as db_matched
            FROM temp_verify tv
            LEFT JOIN recruitment_records rr ON tv.name = rr.name AND tv.phone = rr.phone
        """)
        result = cursor.fetchone()
        excel_unique = result[0]
        db_matched = result[1]
        
        print(f"Excel中唯一人员: {excel_unique}")
        print(f"数据库中匹配人员: {db_matched}")
        
        # 5. 检查新添加的院校
        print("5. 检查新添加的院校...")
        cursor.execute("""
            SELECT university_id, standard_name 
            FROM universities 
            WHERE university_code LIKE 'B2U%'
            ORDER BY university_id
        """)
        new_unis = cursor.fetchall()
        print(f"新添加的院校数量: {len(new_unis)}")
        for uni in new_unis:
            print(f"  {uni[0]}. {uni[1]}")
        
        # 6. 检查批次分布
        print("6. 检查数据库中批次分布...")
        cursor.execute("""
            SELECT batch, COUNT(*) as count
            FROM recruitment_records 
            WHERE company = '国网'
            GROUP BY batch
            ORDER BY batch
        """)
        batch_stats = cursor.fetchall()
        print("批次统计:")
        for batch, count in batch_stats:
            print(f"  {batch}: {count} 人")
        
        print("\n" + "="*80)
        print("验证完成！")
        print("="*80)
        
    except Exception as e:
        print(f"验证过程中出现错误: {e}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    verify_results()
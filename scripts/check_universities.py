#!/usr/bin/env python3
"""查看universities表结构和数据"""

import mysql.connector

# 数据库配置
db_config = {
    'host': 'rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'database': 'bdprod',
    'user': 'dms_user_9332d9e',
    'password': 'AaBb19990826',
    'charset': 'utf8mb4',
    'autocommit': True,
    'use_unicode': True,
    'consume_results': True
}

try:
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)
    
    # 查看表结构
    print("=== Universities表结构 ===")
    cursor.execute("DESCRIBE universities")
    columns = cursor.fetchall()
    
    for col in columns:
        comment = col.get('Comment', '') or 'No comment'
        print(f"{col['Field']}: {col['Type']} - {comment}")
    
    # 查看数据总数
    cursor.execute("SELECT COUNT(*) as total FROM universities")
    total = cursor.fetchone()['total']
    print(f"\n总记录数: {total}")
    
    # 查看样本数据
    print(f"\n=== 前5条样本数据 ===")
    cursor.execute("""
        SELECT university_id, university_code, standard_name, level, type, 
               power_feature, location 
        FROM universities 
        ORDER BY university_id 
        LIMIT 5
    """)
    
    samples = cursor.fetchall()
    for sample in samples:
        print(f"ID: {sample['university_id']}, 代码: {sample['university_code']}, "
              f"名称: {sample['standard_name']}, 层次: {sample['level']}, "
              f"类型: {sample['type']}, 电力特色: {sample['power_feature']}, "
              f"属地: {sample['location']}")
    
    # 统计各个字段的数据分布
    print(f"\n=== 数据分布统计 ===")
    
    # 层次分布
    cursor.execute("SELECT level, COUNT(*) as count FROM universities GROUP BY level ORDER BY count DESC")
    levels = cursor.fetchall()
    print("院校层次分布:")
    for level in levels:
        print(f"  {level['level']}: {level['count']}所")
    
    # 类型分布
    cursor.execute("SELECT type, COUNT(*) as count FROM universities GROUP BY type ORDER BY count DESC")
    types = cursor.fetchall()
    print("\n院校类型分布:")
    for type_info in types:
        print(f"  {type_info['type']}: {type_info['count']}所")
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"错误: {e}")
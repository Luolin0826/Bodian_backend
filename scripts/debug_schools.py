#!/usr/bin/env python3
"""调试学校数据重复问题"""

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
    
    # 查询北京工商大学的具体数据
    query = """
    SELECT 
        u.university_id,
        u.standard_name,
        u.original_name,
        rr.batch,
        COUNT(*) as count_per_batch
    FROM recruitment_records rr
    JOIN universities u ON rr.university_id = u.university_id
    JOIN secondary_units su ON rr.secondary_unit_id = su.unit_id
    WHERE rr.secondary_unit_id = 29 AND u.standard_name LIKE '%工商%' AND su.is_active = 1
    GROUP BY u.university_id, u.standard_name, u.original_name, rr.batch
    ORDER BY u.standard_name, rr.batch
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print("=== 北京工商大学数据详情 ===")
    for row in results:
        print(f"ID: {row['university_id']}, 标准名称: {row['standard_name']}, 原始名称: {row['original_name']}, 批次: {row['batch']}, 数量: {row['count_per_batch']}")
    
    # 查询当前GROUP BY逻辑的结果
    print("\n=== 当前GROUP BY u.standard_name结果 ===")
    query2 = """
    SELECT 
        MIN(u.university_id) as university_id,
        u.standard_name as university_name,
        GROUP_CONCAT(DISTINCT rr.batch ORDER BY rr.batch SEPARATOR ', ') as batch,
        COUNT(*) as admission_count
    FROM recruitment_records rr
    JOIN universities u ON rr.university_id = u.university_id
    JOIN secondary_units su ON rr.secondary_unit_id = su.unit_id
    WHERE rr.secondary_unit_id = 29 AND u.standard_name LIKE '%工商%' AND su.is_active = 1
    GROUP BY u.standard_name
    ORDER BY admission_count DESC
    """
    
    cursor.execute(query2)
    results2 = cursor.fetchall()
    
    for row in results2:
        print(f"ID: {row['university_id']}, 学校: {row['university_name']}, 批次: {row['batch']}, 录取数: {row['admission_count']}")
        
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"错误: {e}")
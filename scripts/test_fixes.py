#!/usr/bin/env python3
"""测试修复后的查询逻辑"""

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
    
    print("=== 测试1: check-school-admission修复 - 未指定批次应合并 ===")
    
    # 模拟修复后的查询逻辑
    unit_id = 29
    batch_type = None
    school_name = "工商"
    
    # 构建查询条件
    conditions = ["rr.secondary_unit_id = %s", "su.is_active = 1"]
    params = [unit_id]
    
    if batch_type:
        conditions.append("rr.batch = %s")
        params.append(batch_type)
        
    conditions.append("(u.standard_name LIKE %s OR u.original_name LIKE %s)")
    school_pattern = f'%{school_name}%'
    params.extend([school_pattern, school_pattern])
    
    where_clause = " AND ".join(conditions)
    
    # 根据是否指定批次决定聚合方式
    if batch_type:
        group_field = "u.university_id, u.standard_name, u.level, rr.batch"
        batch_field = "rr.batch"
    else:
        group_field = "u.university_id, u.standard_name, u.level"
        batch_field = "GROUP_CONCAT(DISTINCT rr.batch ORDER BY rr.batch SEPARATOR ', ') as batch"
    
    query = f"""
        SELECT 
            u.university_id,
            u.standard_name as university_name,
            u.level as school_level,
            COUNT(*) as admission_count,
            COUNT(CASE WHEN rr.gender = '男' THEN 1 END) as male_count,
            COUNT(CASE WHEN rr.gender = '女' THEN 1 END) as female_count,
            MIN(su.unit_name) as unit_name,
            {batch_field}
        FROM recruitment_records rr
        JOIN universities u ON rr.university_id = u.university_id
        JOIN secondary_units su ON rr.secondary_unit_id = su.unit_id
        WHERE {where_clause}
        GROUP BY {group_field}
        ORDER BY admission_count DESC
    """
    
    cursor.execute(query, params)
    schools = cursor.fetchall()
    
    print(f"找到学校数量: {len(schools)}")
    for i, school in enumerate(schools, 1):
        print(f"第{i}条: {school['university_name']} - 批次: {school['batch']} - 录取数: {school['admission_count']}")
    
    print("\n=== 测试2: 学校层次排序测试 ===")
    
    # 测试学校层次正序排序
    school_level_order = """
        CASE u.level 
            WHEN '985工程' THEN 1
            WHEN '211工程' THEN 2
            WHEN '海外高校' THEN 3
            WHEN '双一流' THEN 4
            WHEN '普通本科' THEN 5
            WHEN '独立学院' THEN 6
            WHEN '专科院校' THEN 7
            WHEN '科研院所' THEN 8
            WHEN '民办本科' THEN 9
            ELSE 10 
        END
    """
    
    query_sort_test = f"""
        SELECT 
            MIN(u.university_id) as university_id,
            u.standard_name as university_name,
            MIN(u.level) as university_type,
            COUNT(*) as admission_count,
            MIN({school_level_order}) as level_priority
        FROM recruitment_records rr
        JOIN universities u ON rr.university_id = u.university_id
        JOIN secondary_units su ON rr.secondary_unit_id = su.unit_id
        WHERE rr.secondary_unit_id = %s AND su.is_active = 1
        GROUP BY u.standard_name
        ORDER BY level_priority DESC, university_name
        LIMIT 5
    """
    
    cursor.execute(query_sort_test, [unit_id])
    sorted_schools = cursor.fetchall()
    
    print("学校层次倒序排序结果 (前5所):")
    for i, school in enumerate(sorted_schools, 1):
        print(f"第{i}名: {school['university_name']} ({school['university_type']}) - 优先级: {school['level_priority']} - 录取数: {school['admission_count']}")
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"错误: {e}")
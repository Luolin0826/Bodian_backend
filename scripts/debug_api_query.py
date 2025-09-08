#!/usr/bin/env python3
"""调试API查询问题"""

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
    
    # 模拟API的完整查询
    unit_id = 29
    batch_type = None  # 未指定批次
    
    # 构建查询条件
    conditions = []
    params = []
    
    if unit_id:
        conditions.append("rr.secondary_unit_id = %s")
        params.append(unit_id)
        
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    # 学校层次排序优先级定义
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
    
    # 根据是否指定批次决定聚合方式
    if batch_type:
        # 指定批次时：按学校+批次聚合，保持批次区分
        group_field = "u.standard_name, rr.batch"
        select_name = "u.standard_name as university_name"
        batch_field = "rr.batch as batch"
    else:
        # 未指定批次时：按学校聚合，合并所有批次数据
        group_field = "u.standard_name"
        select_name = "u.standard_name as university_name"
        batch_field = "GROUP_CONCAT(DISTINCT rr.batch ORDER BY rr.batch SEPARATOR ', ') as batch"
    
    order_clause = "ORDER BY admission_count DESC, university_name"
    
    # 主查询 - 按选择的聚合方式统计学校录取
    main_query = f"""
        SELECT 
            MIN(u.university_id) as university_id,
            {select_name},
            MIN(u.level) as university_type,
            MIN(u.type) as university_category,
            {batch_field},
            COUNT(*) as admission_count,
            COUNT(CASE WHEN rr.gender = '男' THEN 1 END) as male_count,
            COUNT(CASE WHEN rr.gender = '女' THEN 1 END) as female_count,
            MIN(su.unit_name) as unit_name,
            MIN(su.org_type) as org_type,
            MIN({school_level_order}) as level_priority
        FROM recruitment_records rr
        JOIN universities u ON rr.university_id = u.university_id
        JOIN secondary_units su ON rr.secondary_unit_id = su.unit_id
        WHERE {where_clause} AND su.is_active = 1
        GROUP BY {group_field}
        {order_clause}
        LIMIT 50 OFFSET 0
    """
    
    print("=== 完整API查询 ===")
    print(main_query)
    print(f"参数: {params}")
    
    cursor.execute(main_query, params)
    results = cursor.fetchall()
    
    print(f"\n=== 查询结果总数: {len(results)} ===")
    for i, row in enumerate(results):
        if '工商' in row['university_name']:
            print(f"第{i+1}条: ID: {row['university_id']}, 学校: {row['university_name']}, 批次: {row['batch']}, 录取数: {row['admission_count']}")
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"错误: {e}")
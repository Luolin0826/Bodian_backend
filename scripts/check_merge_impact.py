#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查合并操作的影响
"""

import mysql.connector

def check_merge_impact():
    db_config = {
        'host': 'rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
        'port': 3306,
        'database': 'bdprod',
        'user': 'dms_user_9332d9e',
        'password': 'AaBb19990826',
        'charset': 'utf8mb4',
        'autocommit': False,
        'use_unicode': True
    }
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    # 检查第一次合并中华北电力大学的情况
    print("=== 检查华北电力大学合并情况 ===")
    
    # 主记录
    cursor.execute("SELECT university_id, standard_name FROM universities WHERE university_id = 14")
    main_record = cursor.fetchone()
    if main_record:
        print(f"主记录 (保留): ID {main_record[0]} - {main_record[1]}")
    else:
        print("主记录 ID 14 不存在")
    
    # 检查被合并的记录是否还存在 (应该已被删除)
    merged_ids = [2, 291, 853, 157, 248, 251, 505, 281]
    print("\n被合并的记录 (应该已被删除):")
    for uid in merged_ids:
        cursor.execute("SELECT university_id, standard_name FROM universities WHERE university_id = %s", (uid,))
        record = cursor.fetchone()
        if record:
            print(f"  错误: ID {record[0]} - {record[1]} 仍然存在!")
        else:
            print(f"  ✓ ID {uid} 已被删除")
    
    # 检查是否误删了分校区
    print("\n=== 检查可能被误删的分校区 ===")
    
    # 检查华北电力大学保定校区等是否还存在
    cursor.execute("""
        SELECT u.university_id, u.standard_name, 
               COUNT(rr.record_id) as recruitment_count
        FROM universities u
        LEFT JOIN recruitment_records rr ON u.university_id = rr.university_id
        WHERE u.standard_name LIKE '%华北电力%'
        GROUP BY u.university_id, u.standard_name
        ORDER BY recruitment_count DESC
    """)
    
    remaining_records = cursor.fetchall()
    print(f"当前华北电力大学相关记录:")
    for uid, name, count in remaining_records:
        print(f"  ID {uid}: {name} - {count} 条招聘记录")
    
    # 检查其他可能的分校区问题
    print("\n=== 检查其他分校区情况 ===")
    
    # 中国矿业大学
    cursor.execute("""
        SELECT u.university_id, u.standard_name, 
               COUNT(rr.record_id) as recruitment_count
        FROM universities u
        LEFT JOIN recruitment_records rr ON u.university_id = rr.university_id
        WHERE u.standard_name LIKE '%中国矿业大学%'
        GROUP BY u.university_id, u.standard_name
        ORDER BY recruitment_count DESC
    """)
    
    mining_records = cursor.fetchall()
    print("中国矿业大学:")
    for uid, name, count in mining_records:
        print(f"  ID {uid}: {name} - {count} 条招聘记录")
    
    # 中国地质大学
    cursor.execute("""
        SELECT u.university_id, u.standard_name, 
               COUNT(rr.record_id) as recruitment_count
        FROM universities u
        LEFT JOIN recruitment_records rr ON u.university_id = rr.university_id
        WHERE u.standard_name LIKE '%中国地质大学%'
        GROUP BY u.university_id, u.standard_name
        ORDER BY recruitment_count DESC
    """)
    
    geology_records = cursor.fetchall()
    print("中国地质大学:")
    for uid, name, count in geology_records:
        print(f"  ID {uid}: {name} - {count} 条招聘记录")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_merge_impact()
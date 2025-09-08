#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速检查合并影响和格式问题
"""

import mysql.connector
import pandas as pd

def quick_check():
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
    
    print("=== 检查第一次合并造成的问题 ===")
    
    # 第一次合并的具体操作
    merges = [
        {'name': '华北电力', 'kept': 14, 'deleted': [2, 291, 853, 157, 248, 251, 505, 281]},
        {'name': '中国矿业(徐州)', 'kept': 10, 'deleted': [854, 353]},
        {'name': '中国矿业(北京)', 'kept': 104, 'deleted': [352]},
        {'name': '中国地质(武汉)', 'kept': 325, 'deleted': [842, 955]},
        {'name': '中国石油(华东)', 'kept': 90, 'deleted': [378]},
        {'name': '中国石油(北京)', 'kept': 284, 'deleted': [759]},
        {'name': '南京大学', 'kept': 41, 'deleted': [86]},
        {'name': '浙江科技', 'kept': 506, 'deleted': [920]},
        {'name': '宁夏师范', 'kept': 720, 'deleted': [101]}
    ]
    
    # 检查被删除的ID是否有分校区信息损失
    problem_merges = []
    
    for merge in merges:
        cursor.execute("""
            SELECT university_id, standard_name, recruitment_count
            FROM universities 
            WHERE university_id = %s
        """, (merge['kept'],))
        
        kept_record = cursor.fetchone()
        if kept_record:
            uid, name, count = kept_record
            print(f"{merge['name']}: 保留 ID {uid} - {name} ({count} 条)")
            
            # 检查删除的记录数量，如果数量很大可能有问题
            if count > 500 and merge['name'] != '华北电力':  # 华北电力已修复
                print(f"  ⚠️  记录数较大，可能包含分校区合并")
                problem_merges.append(merge)
    
    print(f"\n=== 检查格式问题 ===")
    
    # 查找括号格式差异
    cursor.execute("""
        SELECT u1.university_id, u1.standard_name, u1.recruitment_count,
               u2.university_id, u2.standard_name, u2.recruitment_count
        FROM universities u1, universities u2
        WHERE u1.university_id < u2.university_id
        AND (
            -- 括号格式差异 (英文vs中文)
            REPLACE(REPLACE(u1.standard_name, '(', '（'), ')', '）') = u2.standard_name OR
            REPLACE(REPLACE(u2.standard_name, '(', '（'), ')', '）') = u1.standard_name
        )
        AND u1.standard_name != u2.standard_name
        LIMIT 10
    """)
    
    format_issues = cursor.fetchall()
    print(f"发现 {len(format_issues)} 对括号格式问题:")
    for id1, name1, count1, id2, name2, count2 in format_issues:
        print(f"  {name1} (ID:{id1}, {count1}条) <-> {name2} (ID:{id2}, {count2}条)")
    
    # 检查特定的已知问题学校
    print(f"\n=== 检查已知问题学校 ===")
    
    problem_schools = ['中国矿业大学', '中国地质大学', '中国石油大学', '哈尔滨工业大学']
    
    for school in problem_schools:
        cursor.execute("""
            SELECT university_id, standard_name, recruitment_count
            FROM universities 
            WHERE standard_name LIKE %s
            ORDER BY recruitment_count DESC
        """, (f'%{school}%',))
        
        records = cursor.fetchall()
        if len(records) > 1:
            print(f"\n{school}相关记录:")
            for uid, name, count in records:
                print(f"  ID {uid}: {name} - {count} 条")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    quick_check()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接执行大学名称合并
"""

import mysql.connector

def execute_university_merge():
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
    
    # 经过分析的合并计划
    merge_operations = [
        # 华北电力大学合并
        {'primary': 14, 'duplicates': [2, 291, 853, 157, 248, 251, 505, 281]},
        
        # 中国矿业大学徐州
        {'primary': 10, 'duplicates': [854, 353]},
        
        # 中国矿业大学北京
        {'primary': 104, 'duplicates': [352]},
        
        # 中国地质大学武汉
        {'primary': 325, 'duplicates': [842, 955]},
        
        # 中国石油大学华东
        {'primary': 90, 'duplicates': [378]},
        
        # 中国石油大学北京
        {'primary': 284, 'duplicates': [759]},
        
        # 南京大学
        {'primary': 41, 'duplicates': [86]},
        
        # 浙江科技学院
        {'primary': 506, 'duplicates': [920]},
        
        # 宁夏师范大学
        {'primary': 720, 'duplicates': [101]}
    ]
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    try:
        total_records_updated = 0
        total_universities_removed = 0
        
        print("开始执行大学名称合并...")
        
        for i, operation in enumerate(merge_operations, 1):
            primary_id = operation['primary']
            duplicate_ids = operation['duplicates']
            
            # 获取主记录信息
            cursor.execute(
                "SELECT standard_name FROM universities WHERE university_id = %s",
                (primary_id,)
            )
            primary_record = cursor.fetchone()
            
            if not primary_record:
                print(f"跳过操作 {i}: 主记录 {primary_id} 不存在")
                continue
                
            print(f"\n{i}. 合并到: {primary_record[0]} (ID: {primary_id})")
            
            for dup_id in duplicate_ids:
                # 获取重复记录信息
                cursor.execute(
                    "SELECT standard_name FROM universities WHERE university_id = %s",
                    (dup_id,)
                )
                dup_record = cursor.fetchone()
                
                if not dup_record:
                    print(f"   跳过: ID {dup_id} 不存在")
                    continue
                
                # 统计影响的招聘记录
                cursor.execute(
                    "SELECT COUNT(*) FROM recruitment_records WHERE university_id = %s",
                    (dup_id,)
                )
                record_count = cursor.fetchone()[0]
                
                print(f"   合并: {dup_record[0]} (ID: {dup_id}) - {record_count} 条记录")
                
                # 更新recruitment_records表
                cursor.execute(
                    "UPDATE recruitment_records SET university_id = %s WHERE university_id = %s",
                    (primary_id, dup_id)
                )
                
                # 删除重复的大学记录
                cursor.execute(
                    "DELETE FROM universities WHERE university_id = %s",
                    (dup_id,)
                )
                
                total_records_updated += record_count
                total_universities_removed += 1
        
        # 提交事务
        conn.commit()
        
        print(f"\n=== 合并完成 ===")
        print(f"总计更新招聘记录: {total_records_updated} 条")
        print(f"总计删除重复大学: {total_universities_removed} 个")
        
        # 验证结果
        cursor.execute("SELECT COUNT(*) FROM universities")
        total_unis = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT u.university_id)
            FROM universities u
            JOIN recruitment_records rr ON u.university_id = rr.university_id
        """)
        unis_with_records = cursor.fetchone()[0]
        
        print(f"\n=== 验证结果 ===")
        print(f"当前大学总数: {total_unis}")
        print(f"有招聘记录的大学数: {unis_with_records}")
        
    except Exception as e:
        conn.rollback()
        print(f"执行失败，已回滚: {str(e)}")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("即将执行大学名称标准化合并...")
    confirm = input("确认继续? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        execute_university_merge()
    else:
        print("操作已取消")
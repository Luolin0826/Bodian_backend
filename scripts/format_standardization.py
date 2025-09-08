#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大学名称格式标准化 - 统一括号格式
解决中英文括号混用问题
"""

import mysql.connector
import pandas as pd

class FormatStandardizer:
    def __init__(self):
        self.db_config = {
            'host': 'rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
            'port': 3306,
            'database': 'bdprod',
            'user': 'dms_user_9332d9e',
            'password': 'AaBb19990826',
            'charset': 'utf8mb4',
            'autocommit': False,
            'use_unicode': True
        }
    
    def get_connection(self):
        return mysql.connector.connect(**self.db_config)
    
    def find_format_issues(self):
        """找出所有格式不统一的学校对"""
        print("=== 查找格式问题 ===")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 找出括号格式不一致的学校
        cursor.execute("""
            SELECT u1.university_id as id1, u1.standard_name as name1, u1.recruitment_count as count1,
                   u2.university_id as id2, u2.standard_name as name2, u2.recruitment_count as count2
            FROM universities u1, universities u2
            WHERE u1.university_id < u2.university_id
            AND (
                -- 中英文括号互换后相等
                REPLACE(REPLACE(u1.standard_name, '(', '（'), ')', '）') = u2.standard_name OR
                REPLACE(REPLACE(u2.standard_name, '(', '（'), ')', '）') = u1.standard_name
            )
            AND u1.standard_name != u2.standard_name
            ORDER BY u1.standard_name
        """)
        
        format_pairs = cursor.fetchall()
        
        print(f"发现 {len(format_pairs)} 对格式问题:")
        
        standardization_plan = []
        
        for id1, name1, count1, id2, name2, count2 in format_pairs:
            print(f"  {name1} (ID:{id1}, {count1}条) <-> {name2} (ID:{id2}, {count2}条)")
            
            # 决定保留哪个格式：优先保留记录多的，或者统一使用英文括号
            if count1 >= count2:
                keep_id, keep_name = id1, name1
                merge_id, merge_name = id2, name2
                merge_count = count2
            else:
                keep_id, keep_name = id2, name2
                merge_id, merge_name = id1, name1
                merge_count = count1
            
            # 统一使用英文括号格式
            standard_name = keep_name.replace('（', '(').replace('）', ')')
            
            standardization_plan.append({
                'keep_id': keep_id,
                'keep_name': keep_name, 
                'merge_id': merge_id,
                'merge_name': merge_name,
                'merge_count': merge_count,
                'standard_name': standard_name
            })
        
        cursor.close()
        conn.close()
        
        return standardization_plan
    
    def execute_standardization(self, plan, dry_run=True):
        """执行格式标准化"""
        if dry_run:
            print("\n=== 干运行模式 - 格式标准化预览 ===")
        else:
            print("\n=== 执行格式标准化 ===")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            total_merged_records = 0
            total_merged_universities = 0
            
            for item in plan:
                keep_id = item['keep_id']
                merge_id = item['merge_id']
                merge_count = item['merge_count']
                standard_name = item['standard_name']
                
                print(f"\n合并: {item['merge_name']} -> {item['keep_name']}")
                print(f"  标准化为: {standard_name}")
                
                if not dry_run:
                    # 1. 更新招聘记录
                    cursor.execute("""
                        UPDATE recruitment_records 
                        SET university_id = %s 
                        WHERE university_id = %s
                    """, (keep_id, merge_id))
                    
                    print(f"  ✓ 转移了 {merge_count} 条招聘记录")
                    
                    # 2. 删除重复的大学记录
                    cursor.execute("""
                        DELETE FROM universities 
                        WHERE university_id = %s
                    """, (merge_id,))
                    
                    print(f"  ✓ 删除重复大学记录")
                    
                    # 3. 更新主记录名称为标准格式
                    cursor.execute("""
                        UPDATE universities 
                        SET standard_name = %s
                        WHERE university_id = %s
                    """, (standard_name, keep_id))
                    
                    print(f"  ✓ 标准化名称格式")
                    
                    # 4. 更新招聘计数
                    cursor.execute("""
                        UPDATE universities 
                        SET recruitment_count = (
                            SELECT COUNT(*) FROM recruitment_records WHERE university_id = %s
                        )
                        WHERE university_id = %s
                    """, (keep_id, keep_id))
                    
                else:
                    print(f"  [干运行] 将转移 {merge_count} 条招聘记录")
                    print(f"  [干运行] 将删除重复记录")
                    print(f"  [干运行] 将标准化为: {standard_name}")
                
                total_merged_records += merge_count
                total_merged_universities += 1
            
            if not dry_run:
                conn.commit()
                print(f"\n=== 格式标准化完成 ===")
            else:
                print(f"\n=== 干运行完成 ===")
            
            print(f"总计合并记录: {total_merged_records} 条")
            print(f"总计删除大学: {total_merged_universities} 个")
            
        except Exception as e:
            conn.rollback()
            print(f"标准化失败: {str(e)}")
            
        finally:
            cursor.close()
            conn.close()
    
    def verify_results(self):
        """验证标准化结果"""
        print("\n=== 验证标准化结果 ===")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 检查是否还有括号不一致的问题
        cursor.execute("""
            SELECT university_id, standard_name, recruitment_count
            FROM universities 
            WHERE standard_name LIKE '%（%' OR standard_name LIKE '%）%'
            ORDER BY recruitment_count DESC
        """)
        
        remaining_issues = cursor.fetchall()
        
        if remaining_issues:
            print(f"仍有 {len(remaining_issues)} 个使用中文括号的记录:")
            for uid, name, count in remaining_issues:
                print(f"  ID {uid}: {name} ({count} 条)")
        else:
            print("✓ 所有括号已标准化为英文格式")
        
        # 检查关键学校的最终状态
        print(f"\n关键学校最终状态:")
        key_schools = ['中国矿业大学', '中国地质大学', '中国石油大学', '哈尔滨工业大学']
        
        for school in key_schools:
            cursor.execute("""
                SELECT university_id, standard_name, recruitment_count
                FROM universities 
                WHERE standard_name LIKE %s
                ORDER BY recruitment_count DESC
            """, (f'%{school}%',))
            
            records = cursor.fetchall()
            if records:
                print(f"\n{school}:")
                for uid, name, count in records:
                    print(f"  ID {uid}: {name} - {count} 条")
        
        cursor.close()
        conn.close()

def main():
    import sys
    
    standardizer = FormatStandardizer()
    
    print("大学名称格式标准化工具")
    print("=" * 40)
    
    # 查找格式问题
    plan = standardizer.find_format_issues()
    
    if not plan:
        print("没有发现格式问题，所有名称已标准化")
        return
    
    # 执行标准化
    if len(sys.argv) > 1 and sys.argv[1] == 'execute':
        standardizer.execute_standardization(plan, dry_run=False)
        standardizer.verify_results()
    else:
        standardizer.execute_standardization(plan, dry_run=True)

if __name__ == "__main__":
    main()
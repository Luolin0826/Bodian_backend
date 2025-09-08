#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复括号格式问题 - 合并相同学校的不同括号格式记录
"""

import mysql.connector

class BracketFormatFixer:
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
    
    def create_merge_plan(self):
        """创建括号格式合并计划"""
        # 基于实际发现的问题创建精确的合并计划
        merge_plan = [
            {
                'school': '中国矿业大学 (北京)',
                'keep_id': 104,     # 记录多的保留
                'merge_id': 262,    # 记录少的合并
                'reason': '中英文括号格式统一'
            },
            {
                'school': '中国地质大学 (武汉)', 
                'keep_id': 325,
                'merge_id': 256,
                'reason': '中英文括号格式统一'
            },
            {
                'school': '中国石油大学 (华东)',
                'keep_id': 90,
                'merge_id': 922,
                'reason': '中英文括号格式统一'
            },
            {
                'school': '中国石油大学 (北京)',
                'keep_id': 284,
                'merge_id': 923,
                'reason': '中英文括号格式统一'
            },
            {
                'school': '哈尔滨工业大学 (深圳)',
                'keep_id': 72,
                'merge_id': 247,
                'reason': '中英文括号格式统一'
            },
            {
                'school': '哈尔滨工业大学 (威海)',
                'keep_id': 53,
                'merge_id': 784,
                'reason': '英文括号格式统一'
            }
        ]
        
        return merge_plan
    
    def execute_merge(self, merge_plan, dry_run=True):
        """执行格式修复合并"""
        if dry_run:
            print("=== 干运行模式 - 括号格式修复预览 ===")
        else:
            print("=== 执行括号格式修复 ===")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            total_merged_records = 0
            total_merged_universities = 0
            
            for item in merge_plan:
                keep_id = item['keep_id']
                merge_id = item['merge_id']
                school = item['school']
                reason = item['reason']
                
                print(f"\n修复: {school}")
                print(f"原因: {reason}")
                
                # 获取两个记录的详细信息
                cursor.execute("SELECT university_id, standard_name, recruitment_count FROM universities WHERE university_id IN (%s, %s)", (keep_id, merge_id))
                records = cursor.fetchall()
                
                keep_record = None
                merge_record = None
                
                for uid, name, count in records:
                    if uid == keep_id:
                        keep_record = (uid, name, count)
                    elif uid == merge_id:
                        merge_record = (uid, name, count)
                
                if not keep_record:
                    print(f"  错误: 保留记录 ID {keep_id} 不存在")
                    continue
                    
                if not merge_record:
                    print(f"  错误: 合并记录 ID {merge_id} 不存在") 
                    continue
                
                print(f"  保留: {keep_record[1]} (ID:{keep_record[0]}, {keep_record[2]}条)")
                print(f"  合并: {merge_record[1]} (ID:{merge_record[0]}, {merge_record[2]}条)")
                
                if not dry_run:
                    # 1. 转移招聘记录
                    cursor.execute("""
                        UPDATE recruitment_records 
                        SET university_id = %s 
                        WHERE university_id = %s
                    """, (keep_id, merge_id))
                    
                    print(f"  ✓ 转移了 {merge_record[2]} 条招聘记录")
                    
                    # 2. 删除重复记录
                    cursor.execute("DELETE FROM universities WHERE university_id = %s", (merge_id,))
                    print(f"  ✓ 删除重复大学记录")
                    
                    # 3. 更新招聘计数
                    cursor.execute("""
                        UPDATE universities 
                        SET recruitment_count = (
                            SELECT COUNT(*) FROM recruitment_records WHERE university_id = %s
                        )
                        WHERE university_id = %s
                    """, (keep_id, keep_id))
                    
                    new_count = keep_record[2] + merge_record[2]
                    print(f"  ✓ 更新计数为 {new_count} 条")
                else:
                    print(f"  [干运行] 将转移 {merge_record[2]} 条记录")
                    print(f"  [干运行] 将删除重复记录")
                    print(f"  [干运行] 新计数: {keep_record[2] + merge_record[2]} 条")
                
                total_merged_records += merge_record[2]
                total_merged_universities += 1
            
            if not dry_run:
                conn.commit()
                print(f"\n=== 括号格式修复完成 ===")
            else:
                print(f"\n=== 干运行完成 ===")
            
            print(f"总计合并记录: {total_merged_records} 条")
            print(f"总计删除重复大学: {total_merged_universities} 个")
            
        except Exception as e:
            conn.rollback()
            print(f"修复失败: {str(e)}")
            
        finally:
            cursor.close()
            conn.close()
    
    def verify_results(self):
        """验证修复结果"""
        print("\n=== 验证修复结果 ===")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 检查关键学校的状态
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
                    # 检查是否还有格式问题
                    has_issue = '（' in name or '）' in name
                    status = " ⚠️" if has_issue else " ✓"
                    print(f"  ID {uid}: {name} - {count} 条{status}")
        
        # 统计剩余的中文括号记录
        cursor.execute("SELECT COUNT(*) FROM universities WHERE standard_name LIKE '%（%' OR standard_name LIKE '%）%'")
        remaining_count = cursor.fetchone()[0]
        
        print(f"\n剩余中文括号记录: {remaining_count} 个")
        
        cursor.close()
        conn.close()

def main():
    import sys
    
    fixer = BracketFormatFixer()
    
    print("括号格式修复工具")
    print("=" * 30)
    
    # 创建合并计划
    merge_plan = fixer.create_merge_plan()
    
    # 执行修复
    if len(sys.argv) > 1 and sys.argv[1] == 'execute':
        fixer.execute_merge(merge_plan, dry_run=False)
        fixer.verify_results()
    else:
        fixer.execute_merge(merge_plan, dry_run=True)

if __name__ == "__main__":
    main()
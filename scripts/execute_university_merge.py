#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
University Name Consolidation Execution Script
执行大学名称合并和数据库更新操作
"""

import mysql.connector
import re
from collections import defaultdict

class UniversityMergeExecutor:
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
        """创建详细的合并计划，用户可以手动调整"""
        merge_plan = [
            # 华北电力大学合并 - 保留招聘记录最多的北京校区作为主记录
            {
                'primary_id': 14,
                'primary_name': '华北电力大学 (北京)',
                'duplicate_ids': [2, 291, 853, 157, 248, 251, 505, 281],
                'final_name': '华北电力大学 (北京)',
                'reason': '合并华北电力大学的所有变体，保留北京校区'
            },
            
            # 中国矿业大学合并 - 保留徐州校区
            {
                'primary_id': 10,
                'primary_name': '中国矿业大学 (徐州)',
                'duplicate_ids': [854, 353],  # 只合并没有明确校区的记录
                'final_name': '中国矿业大学 (徐州)',
                'reason': '合并中国矿业大学的重复记录，保留明确的校区区分'
            },
            
            # 中国矿业大学北京 - 单独保留
            {
                'primary_id': 104,
                'primary_name': '中国矿业大学 (北京)',
                'duplicate_ids': [352],
                'final_name': '中国矿业大学 (北京)',
                'reason': '合并中国矿业大学北京校区的重复记录'
            },
            
            # 中国地质大学合并 - 保留武汉校区
            {
                'primary_id': 325,
                'primary_name': '中国地质大学 (武汉)',
                'duplicate_ids': [842, 955],  # 只合并没有明确校区的记录
                'final_name': '中国地质大学 (武汉)',
                'reason': '合并中国地质大学的重复记录，保留明确的校区区分'
            },
            
            # 中国石油大学合并 - 保留华东校区
            {
                'primary_id': 90,
                'primary_name': '中国石油大学 (华东)',
                'duplicate_ids': [378],  # 只合并华东的重复
                'final_name': '中国石油大学 (华东)',
                'reason': '合并中国石油大学华东校区的重复记录'
            },
            
            # 中国石油大学北京 - 单独处理
            {
                'primary_id': 284,
                'primary_name': '中国石油大学 (北京)',
                'duplicate_ids': [759],
                'final_name': '中国石油大学 (北京)',
                'reason': '合并中国石油大学北京校区的重复记录'
            },
            
            # 山东大学合并 - 保留主校区
            {
                'primary_id': 27,
                'primary_name': '山东大学',
                'duplicate_ids': [],  # 威海分校应该保持独立
                'final_name': '山东大学',
                'reason': '山东大学主校区，威海分校保持独立'
            },
            
            # 哈工大分校区暂不合并，保持独立
            # 因为分校区在招聘中确实需要区分
            
            # 其他明确的重复项合并
            {
                'primary_id': 144,
                'primary_name': '河南科技大学',
                'duplicate_ids': [],  # 河南科技学院是不同学校，不合并
                'final_name': '河南科技大学',
                'reason': '河南科技大学和河南科技学院是不同学校，不合并'
            },
            
            # 明确的错误记录合并
            {
                'primary_id': 41,
                'primary_name': '南京大学',
                'duplicate_ids': [86],  # "南京"明显是错误记录
                'final_name': '南京大学',
                'reason': '修正错误的南京大学记录'
            },
            
            # 学院升级为大学的情况
            {
                'primary_id': 506,
                'primary_name': '浙江科技学院',
                'duplicate_ids': [920],  # 可能是升级后的名称
                'final_name': '浙江科技学院',
                'reason': '合并浙江科技学院升级记录'
            },
            
            {
                'primary_id': 720,
                'primary_name': '宁夏师范大学',
                'duplicate_ids': [101],
                'final_name': '宁夏师范大学',
                'reason': '合并宁夏师范升级记录'
            }
        ]
        
        return merge_plan
    
    def execute_merge(self, merge_plan, dry_run=True):
        """执行合并操作"""
        if dry_run:
            print("=== 干运行模式 - 不会实际修改数据库 ===")
        else:
            print("=== 执行模式 - 将实际修改数据库 ===")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            total_records_updated = 0
            total_universities_removed = 0
            
            for i, merge in enumerate(merge_plan, 1):
                if not merge['duplicate_ids']:  # 跳过没有重复项的
                    continue
                
                print(f"\n{i}. 处理: {merge['primary_name']}")
                print(f"   原因: {merge['reason']}")
                
                # 检查主记录是否存在
                cursor.execute(
                    "SELECT university_id, standard_name FROM universities WHERE university_id = %s",
                    (merge['primary_id'],)
                )
                primary_record = cursor.fetchone()
                
                if not primary_record:
                    print(f"   错误: 主记录 ID {merge['primary_id']} 不存在")
                    continue
                
                print(f"   主记录: {primary_record[1]} (ID: {primary_record[0]})")
                
                # 处理每个重复记录
                for dup_id in merge['duplicate_ids']:
                    # 检查重复记录
                    cursor.execute(
                        "SELECT university_id, standard_name FROM universities WHERE university_id = %s",
                        (dup_id,)
                    )
                    dup_record = cursor.fetchone()
                    
                    if not dup_record:
                        print(f"   警告: 重复记录 ID {dup_id} 不存在，跳过")
                        continue
                    
                    print(f"   处理重复: {dup_record[1]} (ID: {dup_record[0]})")
                    
                    # 统计受影响的招聘记录数
                    cursor.execute(
                        "SELECT COUNT(*) FROM recruitment_records WHERE university_id = %s",
                        (dup_id,)
                    )
                    record_count = cursor.fetchone()[0]
                    print(f"     将更新 {record_count} 条招聘记录")
                    
                    if not dry_run:
                        # 更新招聘记录的university_id
                        cursor.execute(
                            "UPDATE recruitment_records SET university_id = %s WHERE university_id = %s",
                            (merge['primary_id'], dup_id)
                        )
                        
                        # 删除重复的大学记录
                        cursor.execute(
                            "DELETE FROM universities WHERE university_id = %s",
                            (dup_id,)
                        )
                        
                        print(f"     ✓ 已更新 {record_count} 条招聘记录")
                        print(f"     ✓ 已删除重复大学记录")
                    else:
                        print(f"     [干运行] 将更新 {record_count} 条招聘记录")
                        print(f"     [干运行] 将删除重复大学记录")
                    
                    total_records_updated += record_count
                    total_universities_removed += 1
                
                # 更新主记录的名称（如果需要）
                if merge['final_name'] != primary_record[1]:
                    if not dry_run:
                        cursor.execute(
                            "UPDATE universities SET standard_name = %s WHERE university_id = %s",
                            (merge['final_name'], merge['primary_id'])
                        )
                        print(f"   ✓ 已更新主记录名称为: {merge['final_name']}")
                    else:
                        print(f"   [干运行] 将更新主记录名称为: {merge['final_name']}")
            
            if not dry_run:
                conn.commit()
                print(f"\n=== 合并完成 ===")
            else:
                print(f"\n=== 干运行完成 ===")
            
            print(f"总计更新招聘记录: {total_records_updated} 条")
            print(f"总计删除重复大学: {total_universities_removed} 个")
            
        except Exception as e:
            conn.rollback()
            print(f"执行失败: {str(e)}")
            
        finally:
            cursor.close()
            conn.close()
    
    def verify_merge_results(self):
        """验证合并结果"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        print("\n=== 验证合并结果 ===")
        
        # 检查是否还有明显的重复
        cursor.execute("""
            SELECT standard_name, COUNT(*) as count
            FROM universities u
            WHERE EXISTS (
                SELECT 1 FROM recruitment_records rr WHERE rr.university_id = u.university_id
            )
            GROUP BY standard_name
            HAVING count > 1
            ORDER BY count DESC
        """)
        
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"仍有 {len(duplicates)} 个可能重复的大学名称:")
            for name, count in duplicates[:10]:
                print(f"  - {name}: {count} 个记录")
        else:
            print("✓ 没有发现明显的重复大学名称")
        
        # 统计总体情况
        cursor.execute("SELECT COUNT(*) FROM universities")
        total_unis = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT u.university_id)
            FROM universities u
            JOIN recruitment_records rr ON u.university_id = rr.university_id
        """)
        unis_with_records = cursor.fetchone()[0]
        
        print(f"\n总计大学数量: {total_unis}")
        print(f"有招聘记录的大学: {unis_with_records}")
        
        cursor.close()
        conn.close()

def main():
    import sys
    
    executor = UniversityMergeExecutor()
    
    print("大学名称标准化合并工具")
    print("=" * 40)
    
    # 创建合并计划
    merge_plan = executor.create_merge_plan()
    
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == 'preview':
            executor.execute_merge(merge_plan, dry_run=True)
            return
        elif sys.argv[1] == 'execute':
            executor.execute_merge(merge_plan, dry_run=False)
            return
        elif sys.argv[1] == 'verify':
            executor.verify_merge_results()
            return
    
    while True:
        print("\n请选择操作:")
        print("1. 预览合并计划 (干运行)")
        print("2. 执行合并 (实际修改数据库)")
        print("3. 验证当前状态")
        print("4. 退出")
        
        try:
            choice = input("\n请输入选择 (1-4): ").strip()
        except EOFError:
            print("\n检测到非交互环境，默认执行预览...")
            choice = '1'
        
        if choice == '1':
            executor.execute_merge(merge_plan, dry_run=True)
            
        elif choice == '2':
            try:
                confirm = input("确认要执行实际合并操作吗? (yes/no): ").strip().lower()
            except EOFError:
                print("非交互环境，取消执行")
                return
            if confirm == 'yes':
                executor.execute_merge(merge_plan, dry_run=False)
            else:
                print("操作已取消")
                
        elif choice == '3':
            executor.verify_merge_results()
            
        elif choice == '4':
            break
            
        else:
            print("无效选择，请重新输入")
        
        # 在非交互环境中执行一次后退出
        if len(sys.argv) == 1:
            try:
                input()  # 测试是否在交互环境
            except EOFError:
                break

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析所有被合并的学校，检查是否有分校区被误合并
同时检查格式问题需要修复的学校
"""

import pandas as pd
import mysql.connector
from collections import defaultdict

class ComprehensiveMergeAnalyzer:
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
    
    def load_excel_data(self):
        """加载Excel中所有学校数据用于验证"""
        print("=== 加载Excel原始数据 ===")
        
        excel_file = '/workspace/25国网南网录取信息.xlsx'
        all_data = []
        
        sheet_names = ['一批', '二批', '三批', '南网']
        
        for sheet in sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet)
            df['批次'] = sheet
            all_data.append(df)
        
        combined_data = pd.concat(all_data, ignore_index=True)
        print(f"Excel数据总计: {len(combined_data)} 条记录")
        
        # 统计所有学校
        university_counts = combined_data['院校'].value_counts()
        print(f"Excel中不同学校: {len(university_counts)} 个")
        
        return combined_data, university_counts
    
    def analyze_merged_schools(self):
        """分析第一次合并中涉及的所有学校"""
        print("\n=== 分析第一次合并涉及的学校 ===")
        
        # 第一次合并的操作列表
        merge_operations = [
            {'name': '华北电力大学', 'primary': 14, 'duplicates': [2, 291, 853, 157, 248, 251, 505, 281]},
            {'name': '中国矿业大学徐州', 'primary': 10, 'duplicates': [854, 353]},
            {'name': '中国矿业大学北京', 'primary': 104, 'duplicates': [352]},
            {'name': '中国地质大学武汉', 'primary': 325, 'duplicates': [842, 955]},
            {'name': '中国石油大学华东', 'primary': 90, 'duplicates': [378]},
            {'name': '中国石油大学北京', 'primary': 284, 'duplicates': [759]},
            {'name': '南京大学', 'primary': 41, 'duplicates': [86]},
            {'name': '浙江科技学院', 'primary': 506, 'duplicates': [920]},
            {'name': '宁夏师范大学', 'primary': 720, 'duplicates': [101]}
        ]
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        problem_schools = []
        
        for operation in merge_operations:
            print(f"\n--- 分析: {operation['name']} ---")
            
            # 检查主记录
            cursor.execute("""
                SELECT university_id, standard_name, recruitment_count
                FROM universities 
                WHERE university_id = %s
            """, (operation['primary'],))
            
            primary_record = cursor.fetchone()
            if primary_record:
                print(f"主记录: ID {primary_record[0]} - {primary_record[1]} ({primary_record[2]} 条)")
            
            # 检查被删除的记录是否包含分校区
            all_ids = [operation['primary']] + operation['duplicates']
            id_placeholders = ','.join(['%s'] * len(all_ids))
            
            # 这些ID可能已被删除，我们需要从Excel数据中验证
            self.check_campus_separation_needed(operation, cursor)
        
        cursor.close()
        conn.close()
        
        return problem_schools
    
    def check_campus_separation_needed(self, operation, cursor):
        """检查特定学校是否需要分校区分离"""
        school_name = operation['name']
        
        # 检查Excel数据中是否有明确的分校区信息
        excel_data, _ = self.load_excel_data()
        
        # 根据学校名称模糊匹配
        keywords = {
            '华北电力大学': '华北电力',
            '中国矿业大学徐州': '中国矿业',
            '中国矿业大学北京': '中国矿业',
            '中国地质大学武汉': '中国地质',
            '中国石油大学华东': '中国石油',
            '中国石油大学北京': '中国石油',
            '南京大学': '南京大学',
            '浙江科技学院': '浙江科技',
            '宁夏师范大学': '宁夏师范'
        }
        
        keyword = keywords.get(school_name, school_name)
        
        # 在Excel中查找相关记录
        related_mask = excel_data['院校'].astype(str).str.contains(keyword, na=False)
        related_records = excel_data[related_mask]
        
        if len(related_records) > 0:
            print(f"Excel中找到 {len(related_records)} 条相关记录")
            
            # 分析变体
            variants = related_records['院校'].value_counts()
            print("院校名称变体:")
            
            has_campus_info = False
            for variant, count in variants.items():
                print(f"  {variant}: {count} 条")
                
                # 检查是否包含校区信息
                if any(campus in str(variant) for campus in ['北京', '保定', '徐州', '华东', '武汉', '深圳', '威海']):
                    has_campus_info = True
            
            if has_campus_info and school_name != '华北电力大学':  # 华北电力已处理
                print(f"⚠️  {school_name} 可能需要分校区恢复!")
                return True
            
        return False
    
    def find_format_issues(self):
        """查找格式问题（如括号差异）"""
        print("\n=== 查找格式标准化问题 ===")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 查找括号格式不一致的学校
        cursor.execute("""
            SELECT u1.university_id as id1, u1.standard_name as name1, u1.recruitment_count as count1,
                   u2.university_id as id2, u2.standard_name as name2, u2.recruitment_count as count2
            FROM universities u1
            JOIN universities u2 ON u1.university_id < u2.university_id
            WHERE (
                -- 中英文括号差异
                (REPLACE(REPLACE(u1.standard_name, '(', '（'), ')', '）') = u2.standard_name) OR
                (REPLACE(REPLACE(u2.standard_name, '(', '（'), ')', '）') = u1.standard_name) OR
                
                -- 去除括号后相同
                (REPLACE(REPLACE(REPLACE(REPLACE(u1.standard_name, '(', ''), ')', ''), '（', ''), '）', '') = 
                 REPLACE(REPLACE(REPLACE(REPLACE(u2.standard_name, '(', ''), ')', ''), '（', ''), '）', '')) OR
                 
                -- 去除空格后相同
                (REPLACE(u1.standard_name, ' ', '') = REPLACE(u2.standard_name, ' ', ''))
            )
            AND u1.standard_name != u2.standard_name
            ORDER BY u1.standard_name
        """)
        
        format_issues = cursor.fetchall()
        
        print(f"发现 {len(format_issues)} 对格式问题:")
        
        format_groups = []
        for id1, name1, count1, id2, name2, count2 in format_issues:
            print(f"  {name1} (ID:{id1}, {count1}条) <-> {name2} (ID:{id2}, {count2}条)")
            
            format_groups.append({
                'school1': {'id': id1, 'name': name1, 'count': count1},
                'school2': {'id': id2, 'name': name2, 'count': count2}
            })
        
        cursor.close()
        conn.close()
        
        return format_groups
    
    def create_comprehensive_fix_plan(self):
        """创建全面的修复计划"""
        print("\n=== 创建全面修复计划 ===")
        
        # 1. 检查需要分校区恢复的学校
        problem_schools = self.analyze_merged_schools()
        
        # 2. 检查格式问题
        format_issues = self.find_format_issues()
        
        fix_plan = {
            'campus_recovery_needed': [],  # 需要分校区恢复的
            'format_standardization': []   # 需要格式标准化的
        }
        
        # 分析哪些学校需要分校区恢复（除了已处理的华北电力）
        excel_data, _ = self.load_excel_data()
        
        # 检查其他可能的分校区问题
        campus_schools = ['中国矿业', '中国地质', '中国石油', '哈尔滨工业', '山东大学']
        
        for school_key in campus_schools:
            related_mask = excel_data['院校'].astype(str).str.contains(school_key, na=False)
            related_records = excel_data[related_mask]
            
            if len(related_records) > 0:
                variants = related_records['院校'].value_counts()
                
                campus_variants = []
                for variant, count in variants.items():
                    if any(campus in str(variant) for campus in ['北京', '保定', '徐州', '华东', '武汉', '深圳', '威海']):
                        campus_variants.append((variant, count))
                
                if len(campus_variants) > 1:
                    fix_plan['campus_recovery_needed'].append({
                        'school': school_key,
                        'variants': campus_variants,
                        'total_records': len(related_records)
                    })
        
        # 格式标准化问题
        for issue in format_issues:
            fix_plan['format_standardization'].append(issue)
        
        return fix_plan

def main():
    analyzer = ComprehensiveMergeAnalyzer()
    
    print("全面合并影响分析工具")
    print("=" * 50)
    
    # 创建修复计划
    fix_plan = analyzer.create_comprehensive_fix_plan()
    
    print(f"\n=== 修复计划总结 ===")
    print(f"需要分校区恢复: {len(fix_plan['campus_recovery_needed'])} 个学校")
    print(f"需要格式标准化: {len(fix_plan['format_standardization'])} 对学校")
    
    if fix_plan['campus_recovery_needed']:
        print("\n需要分校区恢复的学校:")
        for item in fix_plan['campus_recovery_needed']:
            print(f"  {item['school']}: {item['total_records']} 条记录")
            for variant, count in item['variants']:
                print(f"    - {variant}: {count} 条")
    
    if fix_plan['format_standardization']:
        print("\n需要格式标准化的学校:")
        for item in fix_plan['format_standardization']:
            school1 = item['school1']
            school2 = item['school2']
            print(f"  {school1['name']} ({school1['count']}条) <-> {school2['name']} ({school2['count']}条)")

if __name__ == "__main__":
    main()
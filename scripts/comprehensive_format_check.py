#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面检查大学名称格式问题
包括：空格问题、括号格式、标点符号等
"""

import mysql.connector
import re
from collections import defaultdict

class ComprehensiveFormatChecker:
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
    
    def find_all_format_issues(self):
        """查找所有格式问题"""
        print("=== 全面格式问题检查 ===")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 获取所有大学记录
        cursor.execute("""
            SELECT university_id, standard_name, recruitment_count
            FROM universities
            ORDER BY standard_name
        """)
        
        all_universities = cursor.fetchall()
        
        # 按基础名称分组，查找格式差异
        base_name_groups = defaultdict(list)
        
        for uid, name, count in all_universities:
            # 标准化处理：移除空格、统一括号，获取基础名称
            base_name = self.get_base_name(name)
            base_name_groups[base_name].append((uid, name, count))
        
        format_issues = []
        
        print(f"检查 {len(base_name_groups)} 个基础学校名称...")
        
        for base_name, variants in base_name_groups.items():
            if len(variants) > 1:
                # 检查是否是真正的格式问题（不是分校区差异）
                issues = self.analyze_variants(base_name, variants)
                if issues:
                    format_issues.extend(issues)
        
        cursor.close()
        conn.close()
        
        return format_issues
    
    def get_base_name(self, name):
        """获取基础名称，用于分组"""
        # 移除各种括号内容，统一格式
        base = re.sub(r'[（(][^）)]*[）)]', '', name)  # 移除括号内容
        base = re.sub(r'\s+', '', base)  # 移除所有空格
        return base.strip()
    
    def analyze_variants(self, base_name, variants):
        """分析变体，找出格式问题"""
        issues = []
        
        # 按相似度分组
        similar_groups = defaultdict(list)
        
        for uid, name, count in variants:
            # 检查是否是分校区差异
            campus_info = self.extract_campus_info(name)
            if campus_info:
                # 有分校区信息，按分校区分组
                group_key = campus_info
            else:
                # 无分校区信息，按去空格后的名称分组
                group_key = re.sub(r'\s+', '', name)
            
            similar_groups[group_key].append((uid, name, count))
        
        # 检查每个相似组内的格式问题
        for group_key, group_variants in similar_groups.items():
            if len(group_variants) > 1:
                # 找出最标准的格式作为目标
                standard_variant = self.choose_standard_format(group_variants)
                
                for uid, name, count in group_variants:
                    if name != standard_variant[1]:  # 不是标准格式
                        issues.append({
                            'base_name': base_name,
                            'campus': group_key,
                            'merge_id': uid,
                            'merge_name': name,
                            'merge_count': count,
                            'keep_id': standard_variant[0],
                            'keep_name': standard_variant[1],
                            'keep_count': standard_variant[2],
                            'issue_type': self.identify_issue_type(name, standard_variant[1])
                        })
        
        return issues
    
    def extract_campus_info(self, name):
        """提取校区信息"""
        # 查找括号内的校区信息
        campus_match = re.search(r'[（(]([^）)]*)[）)]', name)
        if campus_match:
            campus = campus_match.group(1).strip()
            # 过滤掉非校区信息
            if any(keyword in campus for keyword in ['北京', '上海', '深圳', '威海', '保定', '徐州', '武汉', '华东', '西安', '大连']):
                return campus
        return None
    
    def choose_standard_format(self, variants):
        """选择标准格式 - 优先选择记录多的，然后选择格式最规范的"""
        # 按记录数排序
        sorted_variants = sorted(variants, key=lambda x: x[2], reverse=True)
        
        # 在记录数最多的几个中选择格式最规范的
        top_variants = [v for v in sorted_variants if v[2] >= sorted_variants[0][2] * 0.5]
        
        # 格式规范性评分
        def format_score(name):
            score = 0
            # 有空格的格式更规范
            if ' (' in name and ')' in name:
                score += 10
            # 英文括号更标准
            if '(' in name and ')' in name:
                score += 5
            # 避免中文括号
            if '（' in name or '）' in name:
                score -= 5
            return score
        
        best_variant = max(top_variants, key=lambda x: format_score(x[1]))
        return best_variant
    
    def identify_issue_type(self, name1, name2):
        """识别问题类型"""
        if '（' in name1 or '）' in name1:
            return '中文括号'
        elif ' (' not in name1 and '(' in name1:
            return '缺少空格'
        elif name1.replace(' ', '') == name2.replace(' ', ''):
            return '空格问题'
        else:
            return '其他格式问题'
    
    def execute_comprehensive_fix(self, issues, dry_run=True):
        """执行全面格式修复"""
        if dry_run:
            print("\n=== 干运行模式 - 全面格式修复预览 ===")
        else:
            print("\n=== 执行全面格式修复 ===")
        
        # 按问题类型分组显示
        issue_types = defaultdict(list)
        for issue in issues:
            issue_types[issue['issue_type']].append(issue)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            total_merged_records = 0
            total_merged_universities = 0
            
            for issue_type, type_issues in issue_types.items():
                print(f"\n--- {issue_type} 问题 ---")
                
                for issue in type_issues:
                    print(f"\n{issue['base_name']} ({issue['campus']}):")
                    print(f"  保留: {issue['keep_name']} (ID:{issue['keep_id']}, {issue['keep_count']}条)")
                    print(f"  合并: {issue['merge_name']} (ID:{issue['merge_id']}, {issue['merge_count']}条)")
                    
                    if not dry_run:
                        # 1. 转移招聘记录
                        cursor.execute("""
                            UPDATE recruitment_records 
                            SET university_id = %s 
                            WHERE university_id = %s
                        """, (issue['keep_id'], issue['merge_id']))
                        
                        print(f"  ✓ 转移了 {issue['merge_count']} 条招聘记录")
                        
                        # 2. 删除重复记录
                        cursor.execute("DELETE FROM universities WHERE university_id = %s", (issue['merge_id'],))
                        print(f"  ✓ 删除重复大学记录")
                        
                        # 3. 更新招聘计数
                        cursor.execute("""
                            UPDATE universities 
                            SET recruitment_count = (
                                SELECT COUNT(*) FROM recruitment_records WHERE university_id = %s
                            )
                            WHERE university_id = %s
                        """, (issue['keep_id'], issue['keep_id']))
                        
                        new_count = issue['keep_count'] + issue['merge_count']
                        print(f"  ✓ 更新计数为 {new_count} 条")
                    else:
                        print(f"  [干运行] 将转移 {issue['merge_count']} 条记录")
                        print(f"  [干运行] 将删除重复记录")
                        print(f"  [干运行] 新计数: {issue['keep_count'] + issue['merge_count']} 条")
                    
                    total_merged_records += issue['merge_count']
                    total_merged_universities += 1
            
            if not dry_run:
                conn.commit()
                print(f"\n=== 全面格式修复完成 ===")
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

def main():
    import sys
    
    checker = ComprehensiveFormatChecker()
    
    print("全面大学名称格式检查工具")
    print("=" * 40)
    
    # 查找所有格式问题
    issues = checker.find_all_format_issues()
    
    if not issues:
        print("没有发现格式问题，所有名称已标准化")
        return
    
    print(f"\n发现 {len(issues)} 个格式问题")
    
    # 执行修复
    if len(sys.argv) > 1 and sys.argv[1] == 'execute':
        checker.execute_comprehensive_fix(issues, dry_run=False)
    else:
        checker.execute_comprehensive_fix(issues, dry_run=True)

if __name__ == "__main__":
    main()
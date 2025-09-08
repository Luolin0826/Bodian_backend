#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
University Name Standardization and Consolidation Script
合并重复和非标准化的大学名称，并更新相关引用
"""

import mysql.connector
import re
from collections import defaultdict

class UniversityConsolidator:
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
    
    def analyze_universities(self):
        """分析大学表中的重复和非标准化情况"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 获取所有大学及其招聘记录数量
            query = """
                SELECT u.university_id, u.standard_name, u.type, u.level, 
                       COUNT(rr.record_id) as recruitment_count
                FROM universities u
                LEFT JOIN recruitment_records rr ON u.university_id = rr.university_id
                GROUP BY u.university_id, u.standard_name, u.type, u.level
                ORDER BY u.standard_name, recruitment_count DESC
            """
            cursor.execute(query)
            results = cursor.fetchall()
            
            print(f"=== 大学数据分析 ===")
            print(f"总计大学数量: {len(results)}")
            print("\n=== 前20个大学及其招聘记录数 ===")
            
            for i, (uid, name, type_, level, count) in enumerate(results[:20]):
                print(f"{i+1:2d}. ID:{uid:3d} | {name:25s} | {type_ or '未知':8s} | {level or '未知':10s} | 招聘:{count:4d}")
            
            # 分析可能的重复名称
            name_groups = defaultdict(list)
            for uid, name, type_, level, count in results:
                # 移除常见的变体后缀和前缀进行分组
                clean_name = self.clean_university_name(name)
                name_groups[clean_name].append((uid, name, type_, level, count))
            
            print(f"\n=== 可能重复的大学名称 ===")
            duplicates_found = 0
            potential_merges = []
            
            for clean_name, variants in name_groups.items():
                if len(variants) > 1:
                    duplicates_found += 1
                    total_records = sum(count for _, _, _, _, count in variants)
                    print(f"\n{duplicates_found}. 基础名称: {clean_name}")
                    print(f"   总招聘记录数: {total_records}")
                    
                    # 按招聘记录数排序，选择最高的作为主记录
                    variants.sort(key=lambda x: x[4], reverse=True)
                    primary = variants[0]
                    duplicates = variants[1:]
                    
                    print(f"   主记录: ID:{primary[0]} | {primary[1]} | 招聘:{primary[4]}")
                    for dup in duplicates:
                        print(f"   重复:   ID:{dup[0]} | {dup[1]} | 招聘:{dup[4]}")
                    
                    if total_records > 0:  # 只处理有招聘记录的
                        potential_merges.append({
                            'primary_id': primary[0],
                            'primary_name': primary[1],
                            'duplicate_ids': [d[0] for d in duplicates],
                            'duplicate_names': [d[1] for d in duplicates],
                            'total_records': total_records
                        })
            
            print(f"\n=== 合并建议 ===")
            print(f"发现 {len(potential_merges)} 组可合并的大学")
            
            cursor.close()
            conn.close()
            
            return potential_merges
            
        except Exception as e:
            print(f"分析失败: {str(e)}")
            return []
    
    def clean_university_name(self, name):
        """清理大学名称，移除常见变体以便分组"""
        if not name:
            return ""
        
        # 移除常见的后缀变体
        suffixes_to_remove = [
            r'\s*\([^)]+\)',  # 括号内容
            r'\s*分校$',
            r'\s*校区$', 
            r'\s*学院$',
            r'\s*大学$'
        ]
        
        clean = name
        for suffix in suffixes_to_remove:
            clean = re.sub(suffix, '', clean)
        
        # 标准化常见的大学名称变体
        replacements = {
            '华北电力': '华北电力大学',
            '北京理工': '北京理工大学',
            '清华': '清华大学',
            '北大': '北京大学',
        }
        
        for old, new in replacements.items():
            if old in clean:
                clean = new.replace('大学', '')  # 移除后缀以便分组
                break
        
        return clean.strip()
    
    def preview_consolidation(self, merges):
        """预览合并操作，但不实际执行"""
        print(f"\n=== 合并预览（不会实际执行）===")
        
        total_duplicates_to_remove = 0
        total_records_to_update = 0
        
        for i, merge in enumerate(merges[:10], 1):  # 只显示前10个
            print(f"\n{i}. 主大学: {merge['primary_name']} (ID: {merge['primary_id']})")
            print(f"   将合并的重复项:")
            
            for dup_id, dup_name in zip(merge['duplicate_ids'], merge['duplicate_names']):
                print(f"   - {dup_name} (ID: {dup_id})")
                total_duplicates_to_remove += 1
            
            print(f"   受影响的招聘记录数: {merge['total_records']}")
            total_records_to_update += merge['total_records']
        
        print(f"\n=== 预览总结 ===")
        print(f"将删除重复大学记录: {total_duplicates_to_remove} 个")
        print(f"将更新招聘记录: {total_records_to_update} 条")
        print(f"共有 {len(merges)} 组合并操作")
        
        return total_duplicates_to_remove, total_records_to_update

if __name__ == "__main__":
    consolidator = UniversityConsolidator()
    print("开始分析大学名称标准化需求...")
    
    merges = consolidator.analyze_universities()
    
    if merges:
        consolidator.preview_consolidation(merges)
        print(f"\n注意: 这只是分析和预览，没有实际修改数据库。")
        print(f"如需执行合并，需要确认后运行实际的合并脚本。")
    else:
        print("没有发现需要合并的重复大学名称。")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于Excel数据的精确分校区恢复脚本
通过姓名+手机号匹配，恢复华北电力大学分校区信息
"""

import pandas as pd
import mysql.connector
from collections import defaultdict

class PreciseRecovery:
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
        """加载Excel中的所有华北电力数据"""
        print("=== 加载Excel恢复数据 ===")
        
        excel_file = '/workspace/25国网南网录取信息.xlsx'
        all_huabei_data = []
        
        # 读取所有工作表
        sheet_names = ['一批', '二批', '三批', '南网']
        
        for sheet in sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet)
            
            # 筛选华北电力记录
            huabei_mask = df['院校'].astype(str).str.contains('华北电力', na=False)
            huabei_records = df[huabei_mask].copy()
            
            # 标准化分校区信息
            huabei_records['校区'] = huabei_records['院校'].apply(self.determine_campus)
            huabei_records['批次'] = sheet
            
            all_huabei_data.append(huabei_records)
            
            print(f"工作表 '{sheet}': {len(huabei_records)} 条华北电力记录")
        
        # 合并所有数据
        combined_data = pd.concat(all_huabei_data, ignore_index=True)
        
        print(f"\n总计加载: {len(combined_data)} 条华北电力记录")
        print("分校区分布:")
        campus_counts = combined_data['校区'].value_counts()
        for campus, count in campus_counts.items():
            print(f"  {campus}: {count} 条")
        
        return combined_data
    
    def determine_campus(self, university_name):
        """根据大学名称确定校区"""
        name_str = str(university_name).strip()
        
        if '北京' in name_str:
            return '北京'
        elif '保定' in name_str:
            return '保定'
        else:
            return '未知'  # 南网中的"华北电力大学"
    
    def load_database_records(self):
        """加载数据库中当前的华北电力记录"""
        print("\n=== 加载数据库当前记录 ===")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT record_id, name, gender, phone, company, batch, secondary_unit_id
            FROM recruitment_records
            WHERE university_id = 14
            ORDER BY record_id
        """)
        
        db_records = cursor.fetchall()
        print(f"数据库中华北电力记录: {len(db_records)} 条")
        
        cursor.close()
        conn.close()
        
        return db_records
    
    def create_matching_plan(self, excel_data, db_records):
        """创建匹配计划"""
        print("\n=== 创建匹配计划 ===")
        
        # 创建Excel数据的查找索引 (姓名 + 手机号)
        excel_index = {}
        for _, row in excel_data.iterrows():
            name = str(row['姓名']).strip()
            phone = str(row['手机号']).strip()
            key = f"{name}|{phone}"
            excel_index[key] = {
                'campus': row['校区'],
                'original_uni': row['院校'],
                'batch_sheet': row['批次']
            }
        
        print(f"Excel索引创建完成: {len(excel_index)} 个唯一记录")
        
        # 匹配数据库记录
        matches = {
            'beijing': [],      # 北京校区
            'baoding': [],      # 保定校区  
            'unknown': [],      # 未知校区
            'unmatched': []     # 无法匹配
        }
        
        for record in db_records:
            record_id, name, gender, phone, company, batch, secondary_unit_id = record
            
            # 尝试匹配
            key = f"{name}|{phone}"
            
            if key in excel_index:
                excel_info = excel_index[key]
                campus = excel_info['campus']
                
                match_info = {
                    'record_id': record_id,
                    'name': name,
                    'phone': phone,
                    'campus': campus,
                    'excel_uni': excel_info['original_uni'],
                    'batch_sheet': excel_info['batch_sheet']
                }
                
                if campus == '北京':
                    matches['beijing'].append(match_info)
                elif campus == '保定':
                    matches['baoding'].append(match_info)
                else:
                    matches['unknown'].append(match_info)
            else:
                matches['unmatched'].append({
                    'record_id': record_id,
                    'name': name,
                    'phone': phone
                })
        
        # 统计匹配结果
        print("\n匹配结果统计:")
        print(f"  北京校区: {len(matches['beijing'])} 条")
        print(f"  保定校区: {len(matches['baoding'])} 条") 
        print(f"  未知校区: {len(matches['unknown'])} 条")
        print(f"  无法匹配: {len(matches['unmatched'])} 条")
        
        total_matched = len(matches['beijing']) + len(matches['baoding']) + len(matches['unknown'])
        match_rate = total_matched / len(db_records) * 100
        print(f"  匹配成功率: {match_rate:.1f}%")
        
        return matches
    
    def execute_recovery(self, matches, dry_run=True):
        """执行恢复操作"""
        if dry_run:
            print("\n=== 干运行模式 - 模拟恢复 ===")
        else:
            print("\n=== 执行恢复操作 ===")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. 重建华北电力大学保定校区记录
            if not dry_run:
                # 检查ID 2是否已存在
                cursor.execute("SELECT university_id FROM universities WHERE university_id = 2")
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO universities (university_id, university_code, original_name, standard_name, level, type, location)
                        VALUES (2, 'HUABEI_BD', '华北电力大学 (保定)', '华北电力大学 (保定)', '211工程', '理工类', '保定')
                    """)
                    print("✓ 重建华北电力大学 (保定) 记录")
                else:
                    print("华北电力大学 (保定) 记录已存在")
            else:
                print("[干运行] 将重建华北电力大学 (保定) 记录")
            
            # 2. 更新保定校区的记录
            baoding_count = len(matches['baoding'])
            if baoding_count > 0:
                if not dry_run:
                    baoding_ids = [match['record_id'] for match in matches['baoding']]
                    id_placeholders = ','.join(['%s'] * len(baoding_ids))
                    
                    cursor.execute(f"""
                        UPDATE recruitment_records 
                        SET university_id = 2 
                        WHERE record_id IN ({id_placeholders})
                    """, baoding_ids)
                    
                    print(f"✓ 已将 {baoding_count} 条记录迁移到保定校区")
                else:
                    print(f"[干运行] 将迁移 {baoding_count} 条记录到保定校区")
            
            # 3. 处理未知校区记录（南网中的华北电力大学）
            unknown_count = len(matches['unknown'])
            if unknown_count > 0:
                print(f"发现 {unknown_count} 条未明确校区的记录，保持在北京校区")
            
            # 4. 更新recruitment_count
            if not dry_run:
                # 更新北京校区计数
                cursor.execute("""
                    UPDATE universities 
                    SET recruitment_count = (
                        SELECT COUNT(*) FROM recruitment_records WHERE university_id = 14
                    )
                    WHERE university_id = 14
                """)
                
                # 更新保定校区计数
                cursor.execute("""
                    UPDATE universities 
                    SET recruitment_count = (
                        SELECT COUNT(*) FROM recruitment_records WHERE university_id = 2
                    )
                    WHERE university_id = 2
                """)
                
                print("✓ 已更新招聘记录计数")
            
            if not dry_run:
                conn.commit()
                print("\n=== 恢复操作完成 ===")
            else:
                print("\n=== 干运行完成 ===")
                
            # 显示预期结果
            beijing_final = len(matches['beijing']) + len(matches['unknown'])
            baoding_final = len(matches['baoding'])
            
            print(f"恢复后分布:")
            print(f"  华北电力大学 (北京): {beijing_final} 条记录")
            print(f"  华北电力大学 (保定): {baoding_final} 条记录")
            print(f"  无法匹配: {len(matches['unmatched'])} 条记录")
                
        except Exception as e:
            conn.rollback()
            print(f"恢复失败: {str(e)}")
            
        finally:
            cursor.close()
            conn.close()

def main():
    import sys
    
    recovery = PreciseRecovery()
    
    print("华北电力大学分校区精确恢复工具")
    print("=" * 50)
    
    # 加载数据
    excel_data = recovery.load_excel_data()
    db_records = recovery.load_database_records()
    
    # 创建匹配计划
    matches = recovery.create_matching_plan(excel_data, db_records)
    
    # 执行恢复
    if len(sys.argv) > 1 and sys.argv[1] == 'execute':
        recovery.execute_recovery(matches, dry_run=False)
    else:
        recovery.execute_recovery(matches, dry_run=True)

if __name__ == "__main__":
    main()
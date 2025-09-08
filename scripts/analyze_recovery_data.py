#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析恢复数据源 - 25国网南网录取信息.xlsx
用于恢复被错误合并的大学分校区信息
"""

import pandas as pd
import mysql.connector
from collections import defaultdict, Counter

class RecoveryDataAnalyzer:
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
    
    def analyze_excel_structure(self):
        """分析Excel文件结构"""
        print("=== 分析25国网南网录取信息.xlsx文件结构 ===")
        
        # 读取所有工作表名称
        excel_file = '/workspace/25国网南网录取信息.xlsx'
        
        try:
            # 获取所有工作表名称
            xl = pd.ExcelFile(excel_file)
            sheet_names = xl.sheet_names
            
            print(f"发现 {len(sheet_names)} 个工作表:")
            for i, name in enumerate(sheet_names, 1):
                print(f"  {i}. {name}")
            
            # 分析每个工作表的结构
            sheets_data = {}
            for sheet_name in sheet_names:
                print(f"\n--- 分析工作表: {sheet_name} ---")
                
                # 读取前几行查看结构
                df = pd.read_excel(excel_file, sheet_name=sheet_name, nrows=5)
                print(f"列数: {len(df.columns)}")
                print(f"列名: {list(df.columns)}")
                print(f"前5行数据:")
                print(df.head())
                
                # 读取完整数据统计
                df_full = pd.read_excel(excel_file, sheet_name=sheet_name)
                print(f"总行数: {len(df_full)}")
                
                # 查找大学相关列
                uni_columns = []
                for col in df_full.columns:
                    col_str = str(col).lower()
                    if any(keyword in col_str for keyword in ['学校', '大学', '院校', '高校', 'university', 'college']):
                        uni_columns.append(col)
                
                if uni_columns:
                    print(f"发现大学相关列: {uni_columns}")
                    for col in uni_columns:
                        unique_unis = df_full[col].dropna().unique()
                        print(f"  {col}: {len(unique_unis)} 个不同值")
                        # 显示华北电力相关的条目
                        huabei_entries = [u for u in unique_unis if '华北电力' in str(u)]
                        if huabei_entries:
                            print(f"    华北电力相关条目: {huabei_entries}")
                
                sheets_data[sheet_name] = {
                    'dataframe': df_full,
                    'uni_columns': uni_columns,
                    'total_rows': len(df_full)
                }
            
            return sheets_data
            
        except Exception as e:
            print(f"分析Excel文件失败: {str(e)}")
            return None
    
    def find_university_recovery_info(self, sheets_data):
        """寻找可用于恢复大学信息的数据"""
        print("\n=== 寻找华北电力大学分校区恢复信息 ===")
        
        all_huabei_records = []
        
        for sheet_name, data in sheets_data.items():
            df = data['dataframe']
            uni_columns = data['uni_columns']
            
            print(f"\n--- 工作表 {sheet_name} 中的华北电力数据 ---")
            
            for col in uni_columns:
                # 查找华北电力相关记录
                huabei_mask = df[col].astype(str).str.contains('华北电力', na=False)
                huabei_records = df[huabei_mask]
                
                if len(huabei_records) > 0:
                    print(f"在列 '{col}' 中发现 {len(huabei_records)} 条华北电力记录")
                    
                    # 统计不同的华北电力变体
                    huabei_variants = huabei_records[col].value_counts()
                    print("华北电力变体分布:")
                    for variant, count in huabei_variants.items():
                        print(f"  {variant}: {count} 条")
                        
                        # 收集记录以备恢复使用
                        variant_records = huabei_records[huabei_records[col] == variant]
                        all_huabei_records.append({
                            'sheet': sheet_name,
                            'column': col,
                            'university_name': variant,
                            'count': count,
                            'records': variant_records
                        })
        
        return all_huabei_records
    
    def analyze_current_database_state(self):
        """分析当前数据库状态"""
        print("\n=== 分析当前数据库状态 ===")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 检查当前华北电力的数据
        cursor.execute("""
            SELECT rr.name, rr.gender, rr.phone, rr.company, rr.batch
            FROM recruitment_records rr
            WHERE rr.university_id = 14
            LIMIT 10
        """)
        
        current_records = cursor.fetchall()
        print(f"当前数据库中华北电力大学(ID 14)的记录样本:")
        for record in current_records:
            print(f"  {record[0]} | {record[1]} | {record[2]} | {record[3]} | {record[4]}")
        
        cursor.close()
        conn.close()
        
        return current_records
    
    def create_recovery_mapping(self, excel_data, db_data):
        """创建恢复映射关系"""
        print("\n=== 创建恢复映射关系 ===")
        
        # 这里需要通过姓名、电话等信息来匹配Excel和数据库中的记录
        # 从而确定每条记录应该属于哪个分校区
        
        recovery_plan = {
            'huabei_beijing': [],  # 北京校区
            'huabei_baoding': [],  # 保定校区
            'uncertain': []        # 无法确定的记录
        }
        
        print("恢复计划已创建，需要根据Excel数据进行详细匹配")
        
        return recovery_plan

def main():
    analyzer = RecoveryDataAnalyzer()
    
    print("大学分校区信息恢复分析工具")
    print("=" * 50)
    
    # 分析Excel文件结构
    sheets_data = analyzer.analyze_excel_structure()
    
    if sheets_data:
        # 寻找华北电力恢复信息
        huabei_info = analyzer.find_university_recovery_info(sheets_data)
        
        # 分析当前数据库状态
        db_info = analyzer.analyze_current_database_state()
        
        # 创建恢复计划
        recovery_plan = analyzer.create_recovery_mapping(huabei_info, db_info)
        
        print(f"\n=== 总结 ===")
        print(f"Excel文件包含 {sum(info['count'] for info in huabei_info)} 条华北电力相关记录")
        print(f"数据库当前有华北电力记录，需要通过姓名/电话等信息进行匹配")
        print(f"如果匹配成功，可以恢复分校区信息")

if __name__ == "__main__":
    main()
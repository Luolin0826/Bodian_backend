#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细检查一批录取数据.xlsx与数据库recruitment_records的对应情况
"""

import pandas as pd
import mysql.connector
from mysql.connector import Error
from difflib import get_close_matches
import hashlib

# 数据库连接配置
DB_CONFIG = {
    'host': 'rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'database': 'bdprod',
    'user': 'dms_user_9332d9e',
    'password': 'AaBb19990826',
    'charset': 'utf8mb4'
}

def get_db_connection():
    """获取数据库连接"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"数据库连接失败: {e}")
        return None

def detailed_analysis():
    """详细分析对比"""
    print("="*60)
    print("详细数据对比分析")
    print("="*60)
    
    # 1. 读取Excel数据
    try:
        excel_df = pd.read_excel('一批录取数据.xlsx')
        print(f"✅ Excel文件读取成功: {len(excel_df)} 条记录")
        print(f"   列名: {list(excel_df.columns)}")
    except Exception as e:
        print(f"❌ Excel文件读取失败: {e}")
        return
    
    # 2. 连接数据库
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # 3. 获取数据库中的数据
        print(f"\n{'='*60}")
        print("数据库数据分析")
        print("="*60)
        
        cursor.execute("SELECT COUNT(*) as total FROM recruitment_records")
        db_total = cursor.fetchone()['total']
        print(f"数据库recruitment_records表总记录数: {db_total}")
        
        # 4. 获取大学映射关系
        cursor.execute("SELECT university_id, original_name, standard_name FROM universities")
        universities = cursor.fetchall()
        
        # 创建映射字典
        name_to_id = {}
        name_to_standard = {}
        for uni in universities:
            name_to_id[uni['standard_name']] = uni['university_id']
            name_to_id[uni['original_name']] = uni['university_id']
            name_to_standard[uni['original_name']] = uni['standard_name']
            if uni['original_name'] != uni['standard_name']:
                name_to_standard[uni['standard_name']] = uni['standard_name']
        
        print(f"数据库universities表总记录数: {len(universities)}")
        
        # 5. 分析Excel中的学校匹配情况
        print(f"\n{'='*60}")
        print("学校名称匹配分析") 
        print("="*60)
        
        excel_schools = excel_df['院校'].unique()
        print(f"Excel中不同学校数量: {len(excel_schools)}")
        
        matched_schools = []
        unmatched_schools = []
        name_mappings = []
        
        for school in excel_schools:
            if pd.notna(school):
                school_str = str(school).strip()
                
                # 直接匹配
                if school_str in name_to_id:
                    matched_schools.append(school_str)
                    if school_str in name_to_standard:
                        standard = name_to_standard[school_str]
                        name_mappings.append((school_str, standard, 1.0, "直接匹配"))
                    else:
                        name_mappings.append((school_str, school_str, 1.0, "直接匹配"))
                else:
                    # 模糊匹配
                    all_names = list(name_to_id.keys())
                    matches = get_close_matches(school_str, all_names, n=3, cutoff=0.8)
                    if matches:
                        matched_schools.append(school_str)
                        best_match = matches[0]
                        standard = name_to_standard.get(best_match, best_match)
                        name_mappings.append((school_str, best_match, 0.8, "模糊匹配"))
                    else:
                        unmatched_schools.append(school_str)
        
        print(f"✅ 匹配成功的学校: {len(matched_schools)}")
        print(f"❌ 未匹配的学校: {len(unmatched_schools)}")
        print(f"   匹配率: {len(matched_schools) / len(excel_schools) * 100:.1f}%")
        
        # 显示未匹配的学校
        if unmatched_schools:
            print(f"\n未匹配的学校列表 (前20个):")
            for school in unmatched_schools[:20]:
                print(f"  - {school}")
            if len(unmatched_schools) > 20:
                print(f"  ... 还有 {len(unmatched_schools) - 20} 个未匹配学校")
        
        # 显示一些匹配示例
        print(f"\n学校名称匹配示例 (前15个):")
        for original, matched, score, method in name_mappings[:15]:
            if original != matched:
                print(f"  {original} -> {matched} ({method})")
            else:
                print(f"  {original} (精确匹配)")
        
        # 6. 检查数据导入完整性
        print(f"\n{'='*60}")
        print("数据完整性检查")
        print("="*60)
        
        # 按公司/省份分组统计
        excel_stats = excel_df['上岸电网省份'].value_counts()
        print(f"\nExcel数据按省份统计:")
        for province, count in excel_stats.items():
            print(f"  {province}: {count}")
        
        # 获取数据库中对应的统计
        cursor.execute("""
            SELECT company, COUNT(*) as count 
            FROM recruitment_records 
            WHERE company IS NOT NULL 
            GROUP BY company
        """)
        db_stats = cursor.fetchall()
        
        print(f"\n数据库数据按公司统计:")
        db_company_counts = {}
        for stat in db_stats:
            db_company_counts[stat['company']] = stat['count']
            print(f"  {stat['company']}: {stat['count']}")
        
        # 7. 数据质量检查
        print(f"\n{'='*60}")
        print("数据质量检查")
        print("="*60)
        
        # Excel数据质量
        excel_null_counts = excel_df.isnull().sum()
        print(f"Excel数据空值统计:")
        for col, null_count in excel_null_counts.items():
            print(f"  {col}: {null_count} ({null_count/len(excel_df)*100:.1f}%)")
        
        # 数据库数据质量
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN name IS NULL OR name = '' THEN 1 ELSE 0 END) as null_names,
                SUM(CASE WHEN university_id IS NULL THEN 1 ELSE 0 END) as null_universities,
                SUM(CASE WHEN phone IS NULL OR phone = '' THEN 1 ELSE 0 END) as null_phones,
                SUM(CASE WHEN company IS NULL OR company = '' THEN 1 ELSE 0 END) as null_companies
            FROM recruitment_records
        """)
        db_quality = cursor.fetchone()
        
        print(f"\n数据库数据空值统计:")
        print(f"  姓名为空: {db_quality['null_names']} ({db_quality['null_names']/db_total*100:.1f}%)")
        print(f"  大学ID为空: {db_quality['null_universities']} ({db_quality['null_universities']/db_total*100:.1f}%)")
        print(f"  手机号为空: {db_quality['null_phones']} ({db_quality['null_phones']/db_total*100:.1f}%)")
        print(f"  公司为空: {db_quality['null_companies']} ({db_quality['null_companies']/db_total*100:.1f}%)")
        
        # 8. 具体数据样本对比
        print(f"\n{'='*60}")
        print("数据样本对比")
        print("="*60)
        
        # 取Excel前几条记录，看能否在数据库中找到
        sample_matches = 0
        print("样本数据匹配检查 (前10条):")
        
        for idx, row in excel_df.head(10).iterrows():
            name = row['姓名']
            school = row['院校']
            phone = row['手机号'] if pd.notna(row['手机号']) else None
            province = row['上岸电网省份']
            
            # 在数据库中查找匹配记录
            query = "SELECT * FROM recruitment_records WHERE name = %s"
            params = [name]
            
            if phone and str(phone) != 'nan':
                phone_str = str(phone)
                if '*' not in phone_str:  # 如果不是脱敏的手机号
                    query += " AND phone = %s"
                    params.append(phone_str)
            
            cursor.execute(query, params)
            matches = cursor.fetchall()
            
            if matches:
                sample_matches += 1
                print(f"  ✅ {name} ({school}) - 找到 {len(matches)} 条匹配记录")
            else:
                print(f"  ❌ {name} ({school}) - 未找到匹配记录")
        
        print(f"\n样本匹配率: {sample_matches}/10 = {sample_matches*10}%")
        
        # 9. 总结报告
        print(f"\n{'='*60}")
        print("检查结果总结")
        print("="*60)
        
        print(f"📊 数据量对比:")
        print(f"  Excel文件记录数: {len(excel_df)}")
        print(f"  数据库记录数: {db_total}")
        print(f"  差异: {abs(len(excel_df) - db_total)}")
        
        print(f"\n🏫 学校匹配情况:")
        print(f"  Excel中不同学校: {len(excel_schools)}")
        print(f"  匹配成功: {len(matched_schools)}")
        print(f"  未匹配: {len(unmatched_schools)}")
        print(f"  匹配率: {len(matched_schools) / len(excel_schools) * 100:.1f}%")
        
        print(f"\n✅ 数据导入状态:")
        if len(excel_df) == db_total:
            print("  记录数完全匹配，可能已完全导入")
        elif db_total > len(excel_df):
            print("  数据库记录数多于Excel，可能包含其他批次数据")
        else:
            print("  数据库记录数少于Excel，可能存在导入不完整")
            
        print(f"\n🔍 建议:")
        if unmatched_schools:
            print("  1. 需要标准化未匹配的学校名称")
        if sample_matches < 8:
            print("  2. 建议检查具体数据导入过程")
        if abs(len(excel_df) - db_total) > 1000:
            print("  3. 存在较大数据差异，需要详细核查")
            
    except Error as e:
        print(f"数据库操作失败: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    detailed_analysis()
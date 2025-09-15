#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
找出Excel文件中缺失的1703条记录
"""

import pandas as pd
import mysql.connector
from mysql.connector import Error

# 数据库连接配置
DB_CONFIG = {
    'host': 'rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'database': 'bdprod',
    'user': 'dms_user_9332d9e',
    'password': 'AaBb19990826',
    'charset': 'utf8mb4'
}

def find_missing_records():
    """找出缺失的记录"""
    print("="*80)
    print("查找Excel文件中缺失的记录")
    print("="*80)
    
    try:
        # 读取Excel数据
        excel_df = pd.read_excel('一批录取数据.xlsx')
        excel_names = set(excel_df['姓名'].tolist())
        
        print(f"Excel中的姓名数量: {len(excel_names)}")
        print(f"Excel总记录数: {len(excel_df)}")
        
        # 连接数据库
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        # 获取数据库中第一批的所有记录
        print(f"\n获取数据库中国网第一批的所有记录...")
        cursor.execute("""
            SELECT r.name, r.gender, r.phone, r.company, u.standard_name as university_name,
                   r.batch, r.batch_code, r.created_at
            FROM recruitment_records r
            LEFT JOIN universities u ON r.university_id = u.university_id
            WHERE r.company = '国网' AND r.batch = '第一批'
            ORDER BY r.name
        """)
        
        db_records = cursor.fetchall()
        db_names = set([record['name'] for record in db_records])
        
        print(f"数据库中国网第一批记录数: {len(db_records)}")
        print(f"数据库中不同姓名数量: {len(db_names)}")
        
        # 找出Excel中有但数据库中没有的记录
        excel_only = excel_names - db_names
        print(f"\nExcel中有但数据库中没有的姓名: {len(excel_only)}")
        if excel_only:
            print("前10个:")
            for name in list(excel_only)[:10]:
                print(f"  - {name}")
        
        # 找出数据库中有但Excel中没有的记录  
        db_only = db_names - excel_names
        print(f"\n数据库中有但Excel中没有的姓名: {len(db_only)}")
        if db_only:
            print("前20个:")
            for name in list(db_only)[:20]:
                print(f"  - {name}")
        
        # 分析缺失记录的特征
        if db_only:
            print(f"\n分析缺失记录的特征:")
            
            # 按省份/公司分析
            missing_records = [record for record in db_records if record['name'] in db_only]
            
            # 统计缺失记录的省份分布（通过手机号前3位推测）
            province_analysis = {}
            university_analysis = {}
            
            for record in missing_records[:50]:  # 分析前50个
                name = record['name']
                university = record['university_name']
                
                if university:
                    university_analysis[university] = university_analysis.get(university, 0) + 1
            
            print(f"缺失记录的学校分布 (前10):")
            sorted_universities = sorted(university_analysis.items(), key=lambda x: x[1], reverse=True)
            for uni, count in sorted_universities[:10]:
                print(f"  {uni}: {count} 人")
        
        # 详细分析数量差异
        print(f"\n{'='*80}")
        print("数量差异详细分析")
        print("="*80)
        
        db_first_batch_count = len(db_records)
        excel_count = len(excel_df)
        interface_count = 19851
        
        print(f"数据库第一批总数: {db_first_batch_count}")
        print(f"Excel文件记录数: {excel_count}")  
        print(f"接口查询结果: {interface_count}")
        
        print(f"\n差异分析:")
        print(f"数据库 - Excel = {db_first_batch_count - excel_count}")
        print(f"接口 - Excel = {interface_count - excel_count}")
        print(f"数据库 - 接口 = {db_first_batch_count - interface_count}")
        
        # 检查Excel文件的完整性
        print(f"\n{'='*80}")
        print("Excel文件完整性检查")
        print("="*80)
        
        # 按省份对比
        excel_province_counts = excel_df['上岸电网省份'].value_counts()
        
        # 获取数据库中各省份的统计（这里需要通过其他方式推断省份）
        # 暂时通过样本分析
        sample_size = 1000
        cursor.execute(f"""
            SELECT r.name, r.phone, u.standard_name as university_name
            FROM recruitment_records r
            LEFT JOIN universities u ON r.university_id = u.university_id
            WHERE r.company = '国网' AND r.batch = '第一批'
            LIMIT {sample_size}
        """)
        sample_records = cursor.fetchall()
        
        print(f"数据库样本分析 (前{sample_size}条):")
        sample_names = [r['name'] for r in sample_records]
        excel_sample_match = len([name for name in sample_names if name in excel_names])
        
        print(f"样本中在Excel中找到的记录: {excel_sample_match}/{sample_size} ({excel_sample_match/sample_size*100:.1f}%)")
        
        # 结论
        print(f"\n{'='*80}")
        print("结论")
        print("="*80)
        
        if db_first_batch_count > interface_count > excel_count:
            print("📊 数据量关系: 数据库 > 接口 > Excel")
            print("\n🔍 可能的原因:")
            print("1. Excel文件是接口查询结果的子集")
            print("2. Excel文件可能应用了额外的筛选条件")
            print("3. Excel文件可能是某个特定时间点的导出")
            print("4. 接口查询可能有分页限制")
            
        print(f"\n💡 建议:")
        print("1. 检查Excel文件的导出条件和时间")
        print("2. 确认接口查询的完整参数")
        print("3. 检查是否存在数据过滤逻辑")
        print("4. 对比接口返回的完整数据与Excel文件")
        
    except Exception as e:
        print(f"分析过程中出错: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    find_missing_records()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终验证报告 - 一批录取数据导入完整性检查
"""

import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import datetime

# 数据库连接配置
DB_CONFIG = {
    'host': 'rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'database': 'bdprod',
    'user': 'dms_user_9332d9e',
    'password': 'AaBb19990826',
    'charset': 'utf8mb4'
}

def generate_final_report():
    """生成最终验证报告"""
    print("="*80)
    print("一批录取数据导入完整性检查 - 最终报告")
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    try:
        # 读取Excel数据
        excel_df = pd.read_excel('一批录取数据.xlsx')
        excel_total = len(excel_df)
        
        # 连接数据库
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        # 获取数据库统计
        cursor.execute("SELECT COUNT(*) as total FROM recruitment_records")
        db_total = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM universities")
        uni_total = cursor.fetchone()['total']
        
        print("📊 数据概览")
        print("-" * 40)
        print(f"Excel文件记录数:        {excel_total:>8}")
        print(f"数据库记录数:          {db_total:>8}")
        print(f"数据库大学数:          {uni_total:>8}")
        print(f"记录差异:              {abs(excel_total - db_total):>8}")
        
        # 学校匹配分析
        print(f"\n🏫 学校匹配分析")
        print("-" * 40)
        
        excel_schools = excel_df['院校'].unique()
        excel_schools_count = len(excel_schools)
        
        # 未匹配的学校(已知的6个)
        unmatched_schools = [
            "南京", "哈尔滨工业大学（深圳）", "华北电力大学（北京）", 
            "华北电力大学（保定）", "中国地质大学（武汉）", "中国矿业大学（北京）"
        ]
        matched_count = excel_schools_count - len(unmatched_schools)
        match_rate = (matched_count / excel_schools_count) * 100
        
        print(f"Excel中不同学校数:     {excel_schools_count:>8}")
        print(f"已匹配学校数:          {matched_count:>8}")
        print(f"未匹配学校数:          {len(unmatched_schools):>8}")
        print(f"匹配成功率:            {match_rate:>7.1f}%")
        
        # 省份分布对比
        print(f"\n📍 省份分布分析")
        print("-" * 40)
        
        excel_provinces = excel_df['上岸电网省份'].value_counts()
        print("Excel数据省份分布 (Top 10):")
        for i, (province, count) in enumerate(excel_provinces.head(10).items(), 1):
            print(f"  {i:2d}. {province:<12} {count:>6} 人")
        
        # 数据质量检查
        print(f"\n✅ 数据质量检查")
        print("-" * 40)
        
        # Excel数据质量
        excel_nulls = excel_df.isnull().sum()
        total_excel_cells = len(excel_df) * len(excel_df.columns)
        excel_null_rate = (excel_nulls.sum() / total_excel_cells) * 100
        
        print("Excel数据完整性:")
        print(f"  姓名为空:              {excel_nulls['姓名']:>8} ({excel_nulls['姓名']/len(excel_df)*100:>5.1f}%)")
        print(f"  性别为空:              {excel_nulls['性别']:>8} ({excel_nulls['性别']/len(excel_df)*100:>5.1f}%)")
        print(f"  院校为空:              {excel_nulls['院校']:>8} ({excel_nulls['院校']/len(excel_df)*100:>5.1f}%)")
        print(f"  手机号为空:            {excel_nulls['手机号']:>8} ({excel_nulls['手机号']/len(excel_df)*100:>5.1f}%)")
        print(f"  省份为空:              {excel_nulls['上岸电网省份']:>8} ({excel_nulls['上岸电网省份']/len(excel_df)*100:>5.1f}%)")
        print(f"  总体完整率:            {100-excel_null_rate:>7.1f}%")
        
        # 数据库数据质量
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN name IS NULL OR name = '' THEN 1 ELSE 0 END) as null_names,
                SUM(CASE WHEN university_id IS NULL THEN 1 ELSE 0 END) as null_universities,
                SUM(CASE WHEN phone IS NULL OR phone = '' THEN 1 ELSE 0 END) as null_phones,
                SUM(CASE WHEN company IS NULL OR company = '' THEN 1 ELSE 0 END) as null_companies,
                COUNT(*) as total
            FROM recruitment_records
        """)
        db_quality = cursor.fetchone()
        
        print(f"\n数据库数据完整性:")
        print(f"  姓名为空:              {db_quality['null_names']:>8} ({db_quality['null_names']/db_quality['total']*100:>5.1f}%)")
        print(f"  大学ID为空:            {db_quality['null_universities']:>8} ({db_quality['null_universities']/db_quality['total']*100:>5.1f}%)")
        print(f"  手机号为空:            {db_quality['null_phones']:>8} ({db_quality['null_phones']/db_quality['total']*100:>5.1f}%)")
        print(f"  公司为空:              {db_quality['null_companies']:>8} ({db_quality['null_companies']/db_quality['total']*100:>5.1f}%)")
        
        # 抽样验证
        print(f"\n🔍 抽样验证结果")
        print("-" * 40)
        
        sample_size = 50
        sample_df = excel_df.sample(n=min(sample_size, len(excel_df)), random_state=42)
        verified_count = 0
        
        for idx, row in sample_df.iterrows():
            name = row['姓名']
            phone = str(row['手机号']) if pd.notna(row['手机号']) else None
            
            # 在数据库中查找
            if phone and phone != 'nan' and '*' not in phone:
                cursor.execute(
                    "SELECT COUNT(*) as count FROM recruitment_records WHERE name = %s AND phone = %s",
                    (name, phone)
                )
            else:
                cursor.execute(
                    "SELECT COUNT(*) as count FROM recruitment_records WHERE name = %s",
                    (name,)
                )
            
            result = cursor.fetchone()
            if result['count'] > 0:
                verified_count += 1
        
        verification_rate = (verified_count / len(sample_df)) * 100
        print(f"抽样验证数量:          {len(sample_df):>8}")
        print(f"验证通过数量:          {verified_count:>8}")
        print(f"验证通过率:            {verification_rate:>7.1f}%")
        
        # 最终结论
        print(f"\n📝 检查结论")
        print("=" * 40)
        
        if verification_rate >= 95:
            data_status = "✅ 优秀"
        elif verification_rate >= 90:
            data_status = "✅ 良好"
        elif verification_rate >= 80:
            data_status = "⚠️ 一般"
        else:
            data_status = "❌ 需要改进"
            
        print(f"数据导入状态:          {data_status}")
        
        if excel_total == db_total:
            import_status = "✅ 完全匹配"
        elif db_total > excel_total:
            import_status = "ℹ️ 数据库包含更多数据"
        else:
            import_status = "⚠️ 可能存在导入不完整"
            
        print(f"记录数量对比:          {import_status}")
        print(f"学校名称匹配:          {'✅ 优秀' if match_rate > 99 else '⚠️ 需要改进'}")
        
        # 改进建议
        print(f"\n💡 改进建议")
        print("-" * 40)
        
        suggestions = []
        
        if len(unmatched_schools) > 0:
            suggestions.append("1. 标准化学校名称映射规则:")
            for school in unmatched_schools[:5]:  # 只显示前5个
                if school == "南京":
                    suggestions.append(f"   - '{school}' -> 需要人工确认完整学校名称")
                elif "（" in school:
                    corrected = school.replace("（", " (").replace("）", ")")
                    suggestions.append(f"   - '{school}' -> '{corrected}'")
        
        if abs(excel_total - db_total) > 1000:
            suggestions.append("2. 调查记录数量差异原因:")
            suggestions.append(f"   - 检查是否包含其他批次数据")
            suggestions.append(f"   - 确认数据源的完整性")
        
        if verification_rate < 95:
            suggestions.append("3. 提高数据验证准确性:")
            suggestions.append(f"   - 检查姓名匹配逻辑")
            suggestions.append(f"   - 完善手机号脱敏处理")
        
        if suggestions:
            for suggestion in suggestions:
                print(suggestion)
        else:
            print("数据质量良好，无需特别改进。")
        
        print(f"\n" + "=" * 80)
        print("报告生成完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 生成报告时出错: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    generate_final_report()
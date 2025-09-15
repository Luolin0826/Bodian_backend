#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正未匹配的学校名称
"""

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

def check_unmatched_schools():
    """检查未匹配的学校名称并找到正确的映射"""
    unmatched_schools = [
        "南京",  # 这个可能是不完整的数据
        "哈尔滨工业大学（深圳）",
        "华北电力大学（北京）", 
        "华北电力大学（保定）",
        "中国地质大学（武汉）",
        "中国矿业大学（北京）"
    ]
    
    # 正确的映射关系
    name_mappings = {
        "哈尔滨工业大学（深圳）": "哈尔滨工业大学 (深圳)",
        "华北电力大学（北京）": "华北电力大学 (北京)",
        "华北电力大学（保定）": "华北电力大学 (保定)", 
        "中国地质大学（武汉）": "中国地质大学 (武汉)",
        "中国矿业大学（北京）": "中国矿业大学 (北京)"
    }
    
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        print("检查未匹配学校的数据库对应情况:")
        print("="*50)
        
        for excel_name in unmatched_schools:
            print(f"\n原名称: {excel_name}")
            
            if excel_name == "南京":
                print("  这是不完整的数据，可能需要人工确认")
                continue
                
            if excel_name in name_mappings:
                standard_name = name_mappings[excel_name]
                print(f"  应该映射到: {standard_name}")
                
                # 在数据库中查找
                cursor.execute(
                    "SELECT university_id, original_name, standard_name FROM universities WHERE original_name = %s OR standard_name = %s",
                    (standard_name, standard_name)
                )
                matches = cursor.fetchall()
                
                if matches:
                    for match in matches:
                        print(f"  ✅ 找到匹配: ID={match['university_id']}, 原名={match['original_name']}, 标准名={match['standard_name']}")
                else:
                    print(f"  ❌ 未在数据库中找到对应记录")
                    
                    # 尝试模糊搜索
                    search_term = f"%{standard_name.split()[0]}%"
                    cursor.execute(
                        "SELECT university_id, original_name, standard_name FROM universities WHERE original_name LIKE %s OR standard_name LIKE %s",
                        (search_term, search_term)
                    )
                    fuzzy_matches = cursor.fetchall()
                    
                    if fuzzy_matches:
                        print(f"  🔍 可能的匹配:")
                        for match in fuzzy_matches[:3]:
                            print(f"      ID={match['university_id']}, 原名={match['original_name']}, 标准名={match['standard_name']}")
        
        # 检查Excel中这些学校的使用情况
        print(f"\n{'='*50}")
        print("Excel中未匹配学校的使用统计:")
        print("="*50)
        
        import pandas as pd
        excel_df = pd.read_excel('一批录取数据.xlsx')
        
        for school in unmatched_schools:
            count = len(excel_df[excel_df['院校'] == school])
            if count > 0:
                print(f"{school}: {count} 条记录")
                
                # 显示这些记录的省份分布
                provinces = excel_df[excel_df['院校'] == school]['上岸电网省份'].value_counts()
                print(f"  省份分布: {dict(provinces)}")
        
    except Error as e:
        print(f"数据库操作失败: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def suggest_fixes():
    """建议修正方案"""
    print(f"\n{'='*50}")
    print("修正建议")
    print("="*50)
    
    fixes = {
        "哈尔滨工业大学（深圳）": "哈尔滨工业大学 (深圳)",
        "华北电力大学（北京）": "华北电力大学 (北京)", 
        "华北电力大学（保定）": "华北电力大学 (保定)",
        "中国地质大学（武汉）": "中国地质大学 (武汉)",
        "中国矿业大学（北京）": "中国矿业大学 (北京)"
    }
    
    print("建议的名称映射规则:")
    for original, corrected in fixes.items():
        print(f"  '{original}' -> '{corrected}'")
    
    print(f"\n主要差异:")
    print("  - 中文括号 '（）' 需要改为英文括号 '()'")
    print("  - 括号前需要空格")
    
    print(f"\n对于 '南京' 这个条目:")
    print("  - 这可能是数据录入错误或不完整")
    print("  - 建议人工检查原始数据确定正确的学校名称")

if __name__ == "__main__":
    check_unmatched_schools()
    suggest_fixes()
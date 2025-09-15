#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步Excel数据到数据库的脚本
根据Excel文件中的快捷查询表数据更新数据库中不一致的记录
"""

import mysql.connector
import pandas as pd
from mysql.connector import Error
import json

def normalize_value(value, max_length=None):
    """标准化数据值"""
    if pd.isna(value) or value == 'nan' or value == 'None' or value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value in ['无', '无数据', '—', '', 'None']:
            return None
    
    result = str(value) if value is not None else None
    
    # 如果指定了最大长度，进行截断
    if result and max_length and len(result) > max_length:
        result = result[:max_length-3] + '...'  # 保留省略号
        
    return result

def connect_database():
    """连接数据库"""
    return mysql.connector.connect(
        host='rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
        port=3306,
        database='bdprod',
        user='dms_user_9332d9e',
        password='AaBb19990826'
    )

def get_unit_id_by_province(cursor, province_name):
    """根据省份名称获取unit_id"""
    query = "SELECT unit_id FROM secondary_units WHERE unit_name = %s AND is_active = 1"
    cursor.execute(query, (province_name,))
    result = cursor.fetchone()
    return result[0] if result else None

def update_quick_query_info(cursor, unit_id, field_name, new_value):
    """更新quick_query_info表中的字段"""
    query = f"UPDATE quick_query_info SET {field_name} = %s WHERE unit_id = %s"
    cursor.execute(query, (new_value, unit_id))
    return cursor.rowcount > 0

def main():
    """主函数"""
    print("开始同步Excel数据到数据库...")
    
    # 读取Excel数据
    excel_file_path = '/workspace/各省份要求，快捷查询表.xlsx'
    df_excel = pd.read_excel(excel_file_path, sheet_name='Sheet1')
    
    # 读取比较结果
    with open('/workspace/comparison_results.json', 'r', encoding='utf-8') as f:
        comparison_results = json.load(f)
    
    # 字段映射关系
    field_mappings = {
        '本科英语': 'undergraduate_english',
        '本科计算机': 'undergraduate_computer',
        '资格审查': 'undergraduate_qualification',
        '本科年龄': 'undergraduate_age',
        '25年一批本科录取分数': 'undergrad_2025_batch1_score',
        '25年二批本科录取分数': 'undergrad_2025_batch2_score',
        '24年一批本科录取分数线': 'undergrad_2024_batch1_score',
        '24年二批本科录取分数': 'undergrad_2024_batch2_score',
        '23年一批本科分数线': 'undergrad_2023_batch1_score',
        '23年二批本科分数线': 'undergrad_2023_batch2_score',
        '硕士英语': 'graduate_english',
        '硕士计算机': 'graduate_computer',
        '资格审查.1': 'graduate_qualification',
        '硕士年龄': 'graduate_age',
        '25年一批硕士录取分数': 'graduate_2025_batch1_score',
        '25年二批硕士录取分数': 'graduate_2025_batch2_score',
        '24年一批硕士录取分数线': 'graduate_2024_batch1_score',
        '24年二批硕士录取分数': 'graduate_2024_batch2_score',
        '23年一批硕士分数线': 'graduate_2023_batch1_score',
        '23年二批硕士分数线': 'graduate_2023_batch2_score',
    }
    
    try:
        connection = connect_database()
        cursor = connection.cursor()
        
        updated_count = 0
        total_updates = 0
        
        print(f"\n处理 {len(comparison_results)} 个省份的数据...")
        
        for result in comparison_results:
            province = result['province']
            differences = result['differences']
            
            if result['status'] != '存在差异':
                continue
                
            print(f"\n🔄 处理省份: {province}")
            
            # 获取unit_id
            unit_id = get_unit_id_by_province(cursor, province)
            if not unit_id:
                print(f"   ❌ 无法找到省份 {province} 对应的unit_id")
                continue
                
            # 获取Excel中该省份的数据
            excel_row = df_excel[df_excel['省份'] == province]
            if len(excel_row) == 0:
                print(f"   ❌ Excel中未找到省份 {province}")
                continue
                
            excel_row = excel_row.iloc[0]
            province_updated = 0
            
            for diff in differences:
                field_name = diff['field']
                excel_value = diff['excel_value']
                
                if field_name not in field_mappings:
                    continue
                    
                db_field = field_mappings[field_name]
                
                # 标准化Excel值（现在字段已扩容到200字符，不需要长度限制）
                normalized_value = normalize_value(excel_value)
                
                # 更新数据库
                if update_quick_query_info(cursor, unit_id, db_field, normalized_value):
                    print(f"   ✅ 更新 {field_name}: '{diff['db_value']}' -> '{normalized_value}'")
                    province_updated += 1
                    total_updates += 1
                else:
                    print(f"   ❌ 更新失败 {field_name}")
            
            if province_updated > 0:
                updated_count += 1
                print(f"   📊 {province} 共更新 {province_updated} 个字段")
        
        # 提交事务
        connection.commit()
        
        print(f"\n✅ 同步完成!")
        print(f"📊 统计信息:")
        print(f"   - 处理省份数: {len([r for r in comparison_results if r['status'] == '存在差异'])}")
        print(f"   - 更新省份数: {updated_count}")
        print(f"   - 总更新字段数: {total_updates}")
        
    except Error as e:
        print(f"❌ 数据库错误: {e}")
        if connection:
            connection.rollback()
    except Exception as e:
        print(f"❌ 程序错误: {e}")
        if connection:
            connection.rollback()
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("数据库连接已关闭")

if __name__ == "__main__":
    main()
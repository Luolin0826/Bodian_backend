#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将学校Excel文件数据同步到数据库universities表
"""

import pandas as pd
import pymysql
from datetime import datetime
import sys

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host='rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
        port=3306,
        user='dms_user_9332d9e',
        password='AaBb19990826',
        database='bdprod',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def analyze_table_structure():
    """分析数据库universities表结构"""
    print("正在连接数据库并分析表结构...")
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 检查universities表是否存在
            cursor.execute("SHOW TABLES LIKE 'universities'")
            result = cursor.fetchone()
            
            if not result:
                print("❌ 数据库中不存在universities表")
                return None
            
            # 获取表结构
            cursor.execute("DESCRIBE universities")
            columns = cursor.fetchall()
            
            print("✓ Universities表结构:")
            for col in columns:
                nullable = "是" if col['Null'] == 'YES' else "否"
                default = col['Default'] if col['Default'] is not None else "无"
                print(f"  {col['Field']}: {col['Type']} (可空: {nullable}, 默认: {default})")
            
            # 获取数据样本
            cursor.execute("SELECT COUNT(*) as total FROM universities")
            total = cursor.fetchone()['total']
            print(f"\n当前记录数: {total}")
            
            if total > 0:
                cursor.execute("SELECT * FROM universities LIMIT 3")
                samples = cursor.fetchall()
                print("\n前3条记录示例:")
                for i, row in enumerate(samples, 1):
                    print(f"{i}. ID: {row.get('id')}, 名称: {row.get('name', row.get('university_name'))}, Level: {row.get('level')}")
            
            return [col['Field'] for col in columns]
    
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

def load_excel_data(file_path):
    """加载Excel数据"""
    try:
        df = pd.read_excel(file_path)
        print(f"✓ 成功加载Excel数据，共 {len(df)} 条记录")
        print(f"Excel列名: {list(df.columns)}")
        return df
    except Exception as e:
        print(f"❌ 加载Excel文件失败: {e}")
        return None

def sync_data_to_database(excel_file, dry_run=True):
    """同步数据到数据库"""
    print(f"\n{'=' * 50}")
    print("开始数据同步处理")
    print(f"{'=' * 50}")
    
    # 分析表结构
    db_columns = analyze_table_structure()
    if not db_columns:
        return False
    
    # 加载Excel数据
    df = load_excel_data(excel_file)
    if df is None:
        return False
    
    # 建立字段映射
    field_mapping = {}
    
    # Excel字段到数据库字段的映射
    excel_to_db_mapping = {
        'standard_name': ['standard_name', 'name', 'university_name'],
        'university_code': ['university_code', 'code', 'school_code'],
        'level': ['level', 'school_level'],
        'type': ['type', 'school_type', 'category'],
        'power_feature': ['power_feature', 'feature', 'characteristics'],
        'location': ['location', 'province', 'area', 'region'],
        'university_id': ['university_id', 'id', 'school_id']
    }
    
    print(f"\n建立字段映射:")
    for excel_col in df.columns:
        for db_field, possible_names in excel_to_db_mapping.items():
            if excel_col in possible_names and db_field in db_columns:
                field_mapping[excel_col] = db_field
                print(f"  {excel_col} -> {db_field}")
                break
    
    if not field_mapping:
        print("❌ 无法建立有效的字段映射")
        return False
    
    # 开始数据同步
    try:
        conn = get_db_connection()
        updated_count = 0
        matched_count = 0
        not_found_count = 0
        
        print(f"\n开始数据同步 (模式: {'试运行' if dry_run else '实际更新'})...")
        
        for index, row in df.iterrows():
            school_name = str(row.get('standard_name', ''))
            if pd.isna(school_name) or school_name == 'nan':
                continue
            
            # 构建查询条件 - 优先使用名称匹配
            with conn.cursor() as cursor:
                # 尝试通过名称查找
                query = """
                SELECT university_id, standard_name, level FROM universities 
                WHERE standard_name = %s 
                   OR standard_name LIKE %s 
                   OR %s LIKE CONCAT('%%', standard_name, '%%')
                LIMIT 1
                """
                cursor.execute(query, (school_name, f'%{school_name}%', school_name))
                db_record = cursor.fetchone()
                
                if db_record:
                    matched_count += 1
                    old_level = db_record.get('level', '')
                    new_level = str(row.get('level', ''))
                    
                    if old_level != new_level:
                        if not dry_run:
                            # 构建更新SQL
                            update_fields = []
                            update_values = []
                            
                            for excel_col, db_col in field_mapping.items():
                                if excel_col in row and not pd.isna(row[excel_col]):
                                    update_fields.append(f"{db_col} = %s")
                                    update_values.append(str(row[excel_col]))
                            
                            if update_fields:
                                update_sql = f"UPDATE universities SET {', '.join(update_fields)} WHERE university_id = %s"
                                update_values.append(db_record['university_id'])
                                cursor.execute(update_sql, update_values)
                                updated_count += 1
                        else:
                            updated_count += 1
                        
                        print(f"{'✓' if not dry_run else '→'} {school_name}: {old_level} -> {new_level}")
                else:
                    not_found_count += 1
                    if index < 10:  # 只显示前10个未找到的
                        print(f"? 未找到: {school_name}")
        
        if not dry_run:
            conn.commit()
        
        print(f"\n{'=' * 50}")
        print("数据同步完成统计:")
        print(f"{'=' * 50}")
        print(f"Excel记录总数: {len(df)}")
        print(f"匹配到数据库: {matched_count} 条")
        print(f"需要更新: {updated_count} 条")
        print(f"未找到匹配: {not_found_count} 条")
        
        return True
    
    except Exception as e:
        print(f"❌ 数据同步失败: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    excel_file = '/workspace/学校_更新后_20250911_140522.xlsx'
    
    print("学校数据同步到数据库工具")
    print("=" * 50)
    
    # 首先进行试运行
    print("\n第一步: 试运行模式 - 分析数据但不实际更新")
    success = sync_data_to_database(excel_file, dry_run=True)
    
    if success:
        print("\n" + "=" * 50)
        response = input("试运行完成，是否执行实际更新？(y/N): ")
        
        if response.lower() in ['y', 'yes']:
            print("\n第二步: 实际更新模式")
            sync_data_to_database(excel_file, dry_run=False)
            print("✅ 数据更新完成！")
        else:
            print("🔄 已取消实际更新")
    else:
        print("❌ 试运行失败，请检查配置")

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接执行数据库同步，不需要交互式输入
"""

import pandas as pd
import pymysql
from datetime import datetime

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

def execute_sync():
    """执行数据同步"""
    excel_file = '/workspace/学校_更新后_20250911_140522.xlsx'
    
    print("开始执行数据库同步...")
    print("=" * 50)
    
    # 加载Excel数据
    df = pd.read_excel(excel_file)
    print(f"✓ 成功加载Excel数据，共 {len(df)} 条记录")
    
    # 建立字段映射
    field_mapping = {
        'university_id': 'university_id',
        'university_code': 'university_code',
        'standard_name': 'standard_name',
        'level': 'level',
        'type': 'type',
        'power_feature': 'power_feature',
        'location': 'location'
    }
    
    try:
        conn = get_db_connection()
        updated_count = 0
        matched_count = 0
        error_count = 0
        
        print(f"\n开始实际更新数据库...")
        
        for index, row in df.iterrows():
            school_name = str(row.get('standard_name', ''))
            if pd.isna(school_name) or school_name == 'nan':
                continue
            
            try:
                with conn.cursor() as cursor:
                    # 通过名称查找记录
                    query = """
                    SELECT university_id, standard_name, level FROM universities 
                    WHERE standard_name = %s 
                    LIMIT 1
                    """
                    cursor.execute(query, (school_name,))
                    db_record = cursor.fetchone()
                    
                    if db_record:
                        matched_count += 1
                        old_level = db_record.get('level', '')
                        new_level = str(row.get('level', ''))
                        
                        if old_level != new_level:
                            # 构建更新SQL
                            update_fields = []
                            update_values = []
                            
                            for excel_col, db_col in field_mapping.items():
                                if excel_col in row and not pd.isna(row[excel_col]):
                                    value = str(row[excel_col])
                                    if excel_col == 'university_id':
                                        continue  # 跳过主键字段
                                    update_fields.append(f"{db_col} = %s")
                                    update_values.append(value)
                            
                            if update_fields:
                                update_sql = f"UPDATE universities SET {', '.join(update_fields)} WHERE university_id = %s"
                                update_values.append(db_record['university_id'])
                                cursor.execute(update_sql, update_values)
                                updated_count += 1
                                
                                print(f"✓ 更新: {school_name} - {old_level} -> {new_level}")
                
            except Exception as e:
                error_count += 1
                print(f"❌ 更新失败: {school_name} - {e}")
        
        # 提交事务
        conn.commit()
        
        print(f"\n{'=' * 50}")
        print("数据同步完成!")
        print(f"{'=' * 50}")
        print(f"Excel记录总数: {len(df)}")
        print(f"匹配到数据库: {matched_count} 条")
        print(f"成功更新: {updated_count} 条")
        print(f"更新失败: {error_count} 条")
        
        # 生成更新报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f'/workspace/数据库同步报告_{timestamp}.txt'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"数据库同步报告\n")
            f.write(f"=" * 50 + "\n")
            f.write(f"同步时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Excel文件: {excel_file}\n")
            f.write(f"Excel记录总数: {len(df)}\n")
            f.write(f"匹配到数据库: {matched_count} 条\n")
            f.write(f"成功更新: {updated_count} 条\n")
            f.write(f"更新失败: {error_count} 条\n")
        
        print(f"\n📊 详细报告已保存到: {report_file}")
        return True
        
    except Exception as e:
        print(f"❌ 数据库同步失败: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    execute_sync()
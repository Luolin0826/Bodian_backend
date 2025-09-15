#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清理secondary_units表：去重、删除指定记录、删除不需要的列
"""
import pymysql
import re
from app.config.config import Config

def clean_secondary_units():
    """清理secondary_units表"""
    config = Config()
    
    # 解析数据库连接信息
    db_url = config.SQLALCHEMY_DATABASE_URI
    pattern = r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)'
    match = re.match(pattern, db_url)
    
    if not match:
        print("无法解析数据库连接字符串")
        return
    
    db_user, db_password, db_host, db_port, db_name = match.groups()
    db_port = int(db_port)
    
    try:
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            print("=" * 80)
            print("开始清理secondary_units表")
            print("=" * 80)
            
            # 1. 检查外键约束和相关数据
            print("\n1. 检查要删除记录的外键引用...")
            
            # 检查UNIT0065的引用
            print("检查UNIT0065的引用情况...")
            tables_to_check = [
                'advance_batch_provinces',
                'data_query_content', 
                'early_batch_policies_extended',
                'policy_rules_extended',
                'quick_query_info',
                'recruitment_records',
                'rural_grid_policies_extended'
            ]
            
            references_found = False
            for table in tables_to_check:
                try:
                    if table == 'advance_batch_provinces' or table == 'recruitment_records':
                        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE secondary_unit_id = 65")
                    else:
                        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE unit_id = 65")
                    count = cursor.fetchone()[0]
                    if count > 0:
                        print(f"  ✗ {table}: {count} 条引用")
                        references_found = True
                    else:
                        print(f"  ✓ {table}: 无引用")
                except Exception as e:
                    print(f"  ? {table}: 检查失败 - {e}")
            
            # 检查重复记录的引用
            print("\n检查重复记录的引用情况...")
            duplicate_ids = [36, 39]  # 不活跃的重复记录
            
            for dup_id in duplicate_ids:
                print(f"\n检查ID {dup_id} 的引用:")
                has_references = False
                for table in tables_to_check:
                    try:
                        if table == 'advance_batch_provinces' or table == 'recruitment_records':
                            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE secondary_unit_id = %s", (dup_id,))
                        else:
                            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE unit_id = %s", (dup_id,))
                        count = cursor.fetchone()[0]
                        if count > 0:
                            print(f"  ✗ {table}: {count} 条引用")
                            has_references = True
                        else:
                            print(f"  ✓ {table}: 无引用")
                    except Exception as e:
                        print(f"  ? {table}: 检查失败 - {e}")
                
                if not has_references:
                    print(f"  ✓ ID {dup_id} 可以安全删除")
            
            # 2. 删除UNIT0065记录
            print(f"\n2. 删除UNIT0065记录...")
            if not references_found:
                cursor.execute("DELETE FROM secondary_units WHERE unit_id = 65")
                print("✓ 已删除UNIT0065记录")
            else:
                print("✗ UNIT0065有外键引用，跳过删除")
            
            # 3. 删除重复的不活跃记录
            print(f"\n3. 删除重复的不活跃记录...")
            
            # 删除冀北电网的不活跃记录 (ID: 39)
            cursor.execute("""
                SELECT COUNT(*) FROM quick_query_info WHERE unit_id = 39
            """)
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.execute("DELETE FROM secondary_units WHERE unit_id = 39")
                print("✓ 已删除冀北电网重复记录 (ID: 39)")
            else:
                print("✗ 冀北电网重复记录有引用，跳过删除")
            
            # 删除蒙东电网的不活跃记录 (ID: 36)
            cursor.execute("""
                SELECT COUNT(*) FROM quick_query_info WHERE unit_id = 36
            """)
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.execute("DELETE FROM secondary_units WHERE unit_id = 36")
                print("✓ 已删除蒙东电网重复记录 (ID: 36)")
            else:
                print("✗ 蒙东电网重复记录有引用，跳过删除")
            
            # 4. 删除不需要的列（分步骤进行）
            print(f"\n4. 删除不需要的列...")
            
            columns_to_drop = [
                'economic_level',
                'is_key_city', 
                'version',
                'custom_data',
                'salary_range',
                'estimated_score_range',
                'apply_status'
            ]
            
            # 先检查列是否存在
            cursor.execute("DESCRIBE secondary_units")
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            for column in columns_to_drop:
                if column in existing_columns:
                    try:
                        cursor.execute(f"ALTER TABLE secondary_units DROP COLUMN {column}")
                        print(f"✓ 已删除列: {column}")
                    except Exception as e:
                        print(f"✗ 删除列 {column} 失败: {e}")
                else:
                    print(f"- 列 {column} 不存在，跳过")
            
            # 提交更改
            connection.commit()
            
            # 5. 验证清理结果
            print(f"\n5. 验证清理结果...")
            
            # 检查总记录数
            cursor.execute("SELECT COUNT(*) FROM secondary_units")
            total_count = cursor.fetchone()[0]
            print(f"清理后总记录数: {total_count}")
            
            # 检查重复数据
            cursor.execute("""
                SELECT unit_name, COUNT(*) as count
                FROM secondary_units
                GROUP BY unit_name
                HAVING COUNT(*) > 1
            """)
            duplicates = cursor.fetchall()
            if duplicates:
                print(f"仍存在重复数据: {len(duplicates)} 个")
                for dup in duplicates:
                    print(f"  {dup[0]}: {dup[1]} 条")
            else:
                print("✓ 无重复数据")
            
            # 检查表结构
            cursor.execute("DESCRIBE secondary_units")
            columns = cursor.fetchall()
            print(f"清理后列数: {len(columns)}")
            
            print("\n清理完成！")
        
        connection.close()
        
    except Exception as e:
        print(f"清理过程中出现错误: {e}")
        try:
            connection.rollback()
        except:
            pass

def backup_before_clean():
    """清理前备份重要数据"""
    config = Config()
    
    # 解析数据库连接信息
    db_url = config.SQLALCHEMY_DATABASE_URI
    pattern = r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)'
    match = re.match(pattern, db_url)
    
    if not match:
        print("无法解析数据库连接字符串")
        return
    
    db_user, db_password, db_host, db_port, db_name = match.groups()
    db_port = int(db_port)
    
    try:
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            charset='utf8mb4'
        )
        
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            print("创建备份...")
            
            # 备份要删除的记录
            cursor.execute("""
                SELECT * FROM secondary_units 
                WHERE unit_id IN (65, 36, 39)
            """)
            backup_records = cursor.fetchall()
            
            print("备份的记录:")
            for record in backup_records:
                print(f"  ID: {record['unit_id']}, Name: {record['unit_name']}, Code: {record['unit_code']}")
        
        connection.close()
        
    except Exception as e:
        print(f"备份失败: {e}")

if __name__ == '__main__':
    print("开始secondary_units表清理...")
    
    # 先备份
    backup_before_clean()
    
    # 执行清理
    clean_secondary_units()
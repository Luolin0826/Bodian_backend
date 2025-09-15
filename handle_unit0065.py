#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
处理UNIT0065记录的外键引用
"""
import pymysql
import re
from app.config.config import Config

def handle_unit0065():
    """处理UNIT0065的外键引用"""
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
            print("=" * 80)
            print("分析UNIT0065的外键引用详情")
            print("=" * 80)
            
            # 查看UNIT0065的详细信息
            cursor.execute("SELECT * FROM secondary_units WHERE unit_id = 65")
            unit_info = cursor.fetchone()
            if unit_info:
                print("UNIT0065详细信息:")
                print(f"  ID: {unit_info['unit_id']}")
                print(f"  Code: {unit_info['unit_code']}")
                print(f"  Name: {unit_info['unit_name']}")
                print(f"  Type: {unit_info['unit_type']}")
                print(f"  Org: {unit_info['org_type']}")
                print(f"  Active: {unit_info['is_active']}")
            
            # 查看各表中的引用详情
            print("\n外键引用详情:")
            
            # early_batch_policies_extended
            cursor.execute("SELECT * FROM early_batch_policies_extended WHERE unit_id = 65")
            records = cursor.fetchall()
            print(f"\nearly_batch_policies_extended: {len(records)} 条引用")
            for record in records:
                print(f"  ID: {record.get('id', 'N/A')}, Policy: {record.get('policy_name', 'N/A')}")
            
            # policy_rules_extended
            cursor.execute("SELECT * FROM policy_rules_extended WHERE unit_id = 65")
            records = cursor.fetchall()
            print(f"\npolicy_rules_extended: {len(records)} 条引用")
            for record in records:
                print(f"  ID: {record.get('id', 'N/A')}, Rule: {record.get('rule_description', 'N/A')}")
            
            # recruitment_records
            cursor.execute("SELECT * FROM recruitment_records WHERE secondary_unit_id = 65")
            records = cursor.fetchall()
            print(f"\nrecruitment_records: {len(records)} 条引用")
            for record in records:
                print(f"  ID: {record.get('id', 'N/A')}, Position: {record.get('position_name', 'N/A')}")
            
            # rural_grid_policies_extended
            cursor.execute("SELECT * FROM rural_grid_policies_extended WHERE unit_id = 65")
            records = cursor.fetchall()
            print(f"\nrural_grid_policies_extended: {len(records)} 条引用")
            for record in records:
                print(f"  ID: {record.get('id', 'N/A')}, Policy: {record.get('policy_name', 'N/A')}")
        
        connection.close()
        
    except Exception as e:
        print(f"分析过程中出现错误: {e}")

def delete_unit0065_references():
    """删除UNIT0065的相关引用（如果这些数据不重要的话）"""
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
            print("删除UNIT0065的外键引用")
            print("=" * 80)
            
            # 删除相关记录
            tables_to_clean = [
                ('early_batch_policies_extended', 'unit_id'),
                ('policy_rules_extended', 'unit_id'),
                ('recruitment_records', 'secondary_unit_id'),
                ('rural_grid_policies_extended', 'unit_id')
            ]
            
            for table_name, column_name in tables_to_clean:
                cursor.execute(f"DELETE FROM {table_name} WHERE {column_name} = 65")
                affected_rows = cursor.rowcount
                if affected_rows > 0:
                    print(f"✓ {table_name}: 删除了 {affected_rows} 条引用记录")
                else:
                    print(f"- {table_name}: 无需删除")
            
            # 现在可以安全删除UNIT0065
            cursor.execute("DELETE FROM secondary_units WHERE unit_id = 65")
            print("✓ 已删除UNIT0065记录")
            
            # 提交更改
            connection.commit()
            print("\n✓ 所有更改已提交")
            
            # 验证
            cursor.execute("SELECT COUNT(*) FROM secondary_units")
            total_count = cursor.fetchone()[0]
            print(f"最终记录数: {total_count}")
        
        connection.close()
        
    except Exception as e:
        print(f"删除过程中出现错误: {e}")
        try:
            connection.rollback()
            print("已回滚更改")
        except:
            pass

if __name__ == '__main__':
    print("分析UNIT0065引用情况...")
    handle_unit0065()
    
    print("\n" + "=" * 80)
    response = input("是否要删除UNIT0065及其所有引用？(y/N): ")
    if response.lower() == 'y':
        delete_unit0065_references()
    else:
        print("跳过删除操作")
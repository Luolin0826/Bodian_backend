#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接删除UNIT0065及其外键引用
"""
import pymysql
import re
from app.config.config import Config

def delete_unit0065_and_references():
    """删除UNIT0065及其所有外键引用"""
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
            print("删除UNIT0065及其外键引用")
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
            
            # 验证最终结果
            print("\n验证最终结果:")
            cursor.execute("SELECT COUNT(*) FROM secondary_units")
            total_count = cursor.fetchone()[0]
            print(f"最终记录数: {total_count}")
            
            cursor.execute("SELECT COUNT(*) FROM secondary_units WHERE is_active = 1")
            active_count = cursor.fetchone()[0]
            print(f"活跃记录数: {active_count}")
            
            # 检查是否还有重复数据
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
            
            print("\n清理完成！")
        
        connection.close()
        
    except Exception as e:
        print(f"删除过程中出现错误: {e}")
        try:
            connection.rollback()
            print("已回滚更改")
        except:
            pass

if __name__ == '__main__':
    delete_unit0065_and_references()
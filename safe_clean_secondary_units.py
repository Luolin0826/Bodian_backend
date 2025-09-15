#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安全清理secondary_units表：先处理外键引用，再去重，最后删除不需要的列
"""
import pymysql
import re
from app.config.config import Config

def safe_clean_secondary_units():
    """安全清理secondary_units表"""
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
            print("开始安全清理secondary_units表")
            print("=" * 80)
            
            # 第一步：处理重复数据的外键引用，将引用迁移到活跃记录
            print("\n1. 处理重复数据的外键引用...")
            
            # 处理蒙东电网：将ID 36的引用迁移到ID 26
            print("处理蒙东电网重复数据...")
            print("将ID 36的引用迁移到ID 26...")
            
            # 迁移recruitment_records
            cursor.execute("""
                UPDATE recruitment_records 
                SET secondary_unit_id = 26 
                WHERE secondary_unit_id = 36
            """)
            affected_rows = cursor.rowcount
            print(f"  ✓ recruitment_records: 迁移了 {affected_rows} 条记录")
            
            # 迁移其他相关表
            tables_to_migrate = [
                ('early_batch_policies_extended', 'unit_id'),
                ('policy_rules_extended', 'unit_id'),
                ('rural_grid_policies_extended', 'unit_id')
            ]
            
            for table_name, column_name in tables_to_migrate:
                cursor.execute(f"""
                    UPDATE {table_name} 
                    SET {column_name} = 26 
                    WHERE {column_name} = 36
                """)
                affected_rows = cursor.rowcount
                if affected_rows > 0:
                    print(f"  ✓ {table_name}: 迁移了 {affected_rows} 条记录")
            
            # 处理冀北电网：将ID 39的引用迁移到ID 28
            print("\n处理冀北电网重复数据...")
            print("将ID 39的引用迁移到ID 28...")
            
            # 迁移recruitment_records
            cursor.execute("""
                UPDATE recruitment_records 
                SET secondary_unit_id = 28 
                WHERE secondary_unit_id = 39
            """)
            affected_rows = cursor.rowcount
            print(f"  ✓ recruitment_records: 迁移了 {affected_rows} 条记录")
            
            # 迁移其他相关表
            for table_name, column_name in tables_to_migrate:
                cursor.execute(f"""
                    UPDATE {table_name} 
                    SET {column_name} = 28 
                    WHERE {column_name} = 39
                """)
                affected_rows = cursor.rowcount
                if affected_rows > 0:
                    print(f"  ✓ {table_name}: 迁移了 {affected_rows} 条记录")
            
            # 处理UNIT0065的引用（如果有替代方案的话，这里先保持原状）
            print("\n处理UNIT0065的引用...")
            print("UNIT0065 '目标省份电网' 是一个特殊记录，暂时保留其引用")
            
            # 第二步：删除重复的不活跃记录
            print("\n2. 删除重复的不活跃记录...")
            
            # 删除蒙东电网的重复记录 (ID: 36)
            cursor.execute("DELETE FROM secondary_units WHERE unit_id = 36")
            print("✓ 已删除蒙东电网重复记录 (ID: 36)")
            
            # 删除冀北电网的重复记录 (ID: 39) 
            cursor.execute("DELETE FROM secondary_units WHERE unit_id = 39")
            print("✓ 已删除冀北电网重复记录 (ID: 39)")
            
            # 第三步：暂时不删除UNIT0065，因为它有外键引用
            print("\n3. 处理UNIT0065记录...")
            print("UNIT0065有外键引用，建议手动处理后再删除")
            
            # 第四步：删除不需要的列
            print("\n4. 删除不需要的列...")
            
            columns_to_drop = [
                'economic_level',
                'is_key_city', 
                'version',
                'custom_data',
                'salary_range',
                'estimated_score_range',
                'apply_status'
            ]
            
            # 检查哪些列存在
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
            print("\n✓ 所有更改已提交")
            
            # 第五步：验证清理结果
            print(f"\n5. 验证清理结果...")
            
            # 检查总记录数
            cursor.execute("SELECT COUNT(*) FROM secondary_units")
            total_count = cursor.fetchone()[0]
            print(f"清理后总记录数: {total_count}")
            
            # 检查活跃记录数
            cursor.execute("SELECT COUNT(*) FROM secondary_units WHERE is_active = 1")
            active_count = cursor.fetchone()[0]
            print(f"活跃记录数: {active_count}")
            
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
            remaining_columns = [col[0] for col in columns]
            print("保留的列:", remaining_columns)
            
            print("\n安全清理完成！")
            print("注意：UNIT0065 '目标省份电网' 由于有外键引用未删除，请根据业务需要手动处理。")
        
        connection.close()
        
    except Exception as e:
        print(f"清理过程中出现错误: {e}")
        try:
            connection.rollback()
            print("已回滚更改")
        except:
            pass

if __name__ == '__main__':
    print("开始secondary_units表安全清理...")
    safe_clean_secondary_units()
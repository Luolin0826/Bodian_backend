#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
更新secondary_units表的org_type枚举，添加'省属产业'选项
"""
import pymysql
import re
from app.config.config import Config

def update_org_type_enum():
    """更新org_type枚举类型"""
    config = Config()
    
    # 解析数据库连接信息
    db_url = config.SQLALCHEMY_DATABASE_URI
    pattern = r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)'
    match = re.match(pattern, db_url)
    
    if not match:
        print("无法解析数据库连接字符串")
        return False
    
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
            print("更新org_type枚举类型")
            print("=" * 80)
            
            # 检查当前的枚举定义
            cursor.execute("""
                SELECT COLUMN_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
                AND TABLE_NAME = 'secondary_units'
                AND COLUMN_NAME = 'org_type'
            """, (db_name,))
            
            current_enum = cursor.fetchone()[0]
            print(f"当前枚举定义: {current_enum}")
            
            # 更新枚举类型，添加'省属产业'
            alter_sql = """
                ALTER TABLE secondary_units 
                MODIFY COLUMN org_type ENUM(
                    '国网省公司',
                    '国网直属单位', 
                    '南网省公司',
                    '南网直属单位',
                    '省属产业'
                ) COMMENT '组织类型'
            """
            
            cursor.execute(alter_sql)
            print("✓ 已添加'省属产业'到org_type枚举")
            
            # 验证更新
            cursor.execute("""
                SELECT COLUMN_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
                AND TABLE_NAME = 'secondary_units'
                AND COLUMN_NAME = 'org_type'
            """, (db_name,))
            
            new_enum = cursor.fetchone()[0]
            print(f"新的枚举定义: {new_enum}")
            
            connection.commit()
            print("✓ 更改已提交")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"更新枚举过程中出现错误: {e}")
        try:
            connection.rollback()
            print("已回滚更改")
        except:
            pass
        return False

if __name__ == '__main__':
    update_org_type_enum()
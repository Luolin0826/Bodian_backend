#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
添加display_order和requirement_type字段到quick_query_info表
"""
import pymysql
from app.config.config import Config

def add_columns():
    """添加新字段到quick_query_info表"""
    
    config = Config()
    
    # 解析数据库连接字符串
    db_url = config.SQLALCHEMY_DATABASE_URI.replace('mysql+pymysql://', '')
    user_pass, host_db = db_url.split('@')
    user, password = user_pass.split(':')
    host_port, database = host_db.split('/')
    host, port = host_port.split(':')
    # 移除查询参数
    if '?' in database:
        database = database.split('?')[0]
    
    # 连接数据库
    connection = pymysql.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=database,
        charset='utf8mb4'
    )
    
    try:
        with connection.cursor() as cursor:
            # 检查display_order列是否存在
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'quick_query_info' 
                AND COLUMN_NAME = 'display_order'
            """, (database,))
            
            if not cursor.fetchone():
                print("Adding display_order column...")
                cursor.execute("""
                    ALTER TABLE quick_query_info 
                    ADD COLUMN display_order INT DEFAULT NULL COMMENT '展示顺序'
                    AFTER unit_id
                """)
                print("✓ display_order column added")
            else:
                print("display_order column already exists")
            
            # 检查requirement_type列是否存在
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'quick_query_info' 
                AND COLUMN_NAME = 'requirement_type'
            """, (database,))
            
            if not cursor.fetchone():
                print("Adding requirement_type column...")
                cursor.execute("""
                    ALTER TABLE quick_query_info 
                    ADD COLUMN requirement_type VARCHAR(20) DEFAULT NULL COMMENT '要求类型：明确要求/有限条件/无条件'
                    AFTER display_order
                """)
                print("✓ requirement_type column added")
            else:
                print("requirement_type column already exists")
            
            # 添加索引
            cursor.execute("""
                SELECT COUNT(1) 
                FROM INFORMATION_SCHEMA.STATISTICS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'quick_query_info' 
                AND INDEX_NAME = 'idx_display_order'
            """, (database,))
            
            if cursor.fetchone()[0] == 0:
                print("Adding index on display_order...")
                cursor.execute("""
                    CREATE INDEX idx_display_order ON quick_query_info(display_order)
                """)
                print("✓ Index added on display_order")
            else:
                print("Index on display_order already exists")
            
            connection.commit()
            print("\n✓ All columns added successfully!")
            
    except Exception as e:
        print(f"Error: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == '__main__':
    add_columns()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建话术分类相关的数据库表结构
"""

import sys
import os

# 添加项目路径到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db
from sqlalchemy import text

def create_category_tables():
    """创建分类相关的表结构"""
    app = create_app()
    
    with app.app_context():
        try:
            print("开始创建话术分类相关表结构...")
            
            # 创建所有表（包括新的ScriptCategory表）
            print("1. 创建数据库表...")
            db.create_all()
            
            # 检查是否需要添加category_id字段到scripts表
            print("2. 检查并添加category_id字段...")
            
            # 使用原生SQL检查字段是否存在
            result = db.session.execute(text(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'scripts' "
                "AND COLUMN_NAME = 'category_id'"
            ))
            
            if not result.fetchone():
                print("   添加category_id字段到scripts表...")
                db.session.execute(text(
                    "ALTER TABLE scripts ADD COLUMN category_id INTEGER, "
                    "ADD CONSTRAINT fk_scripts_category_id "
                    "FOREIGN KEY (category_id) REFERENCES script_categories(id)"
                ))
                db.session.commit()
                print("   ✅ category_id字段添加成功")
            else:
                print("   ✅ category_id字段已存在")
            
            print("\n✅ 表结构创建完成!")
            
            # 显示创建的表信息
            print("\n创建的表:")
            print("- script_categories: 话术分类表")
            print("- scripts: 话术表（已添加category_id外键）")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 创建表结构时发生错误: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False

def check_tables():
    """检查表结构是否存在"""
    app = create_app()
    
    with app.app_context():
        try:
            print("检查数据库表结构...")
            
            # 检查script_categories表
            result = db.session.execute(text(
                "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'script_categories'"
            ))
            
            if result.fetchone():
                print("✅ script_categories 表存在")
                
                # 获取表字段信息
                columns = db.session.execute(text(
                    "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE "
                    "FROM INFORMATION_SCHEMA.COLUMNS "
                    "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'script_categories' "
                    "ORDER BY ORDINAL_POSITION"
                )).fetchall()
                
                print("   字段列表:")
                for col in columns:
                    nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                    print(f"   - {col[0]}: {col[1]} {nullable}")
            else:
                print("❌ script_categories 表不存在")
            
            # 检查scripts表的category_id字段
            result = db.session.execute(text(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'scripts' "
                "AND COLUMN_NAME = 'category_id'"
            ))
            
            if result.fetchone():
                print("✅ scripts.category_id 字段存在")
            else:
                print("❌ scripts.category_id 字段不存在")
            
            # 检查外键约束
            constraints = db.session.execute(text(
                "SELECT CONSTRAINT_NAME, TABLE_NAME, COLUMN_NAME, "
                "REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME "
                "FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE "
                "WHERE TABLE_SCHEMA = DATABASE() "
                "AND CONSTRAINT_NAME LIKE 'fk_%category%'"
            )).fetchall()
            
            if constraints:
                print("✅ 外键约束存在:")
                for constraint in constraints:
                    print(f"   - {constraint[0]}: {constraint[1]}.{constraint[2]} -> {constraint[3]}.{constraint[4]}")
            else:
                print("❌ 没有找到相关外键约束")
            
        except Exception as e:
            print(f"❌ 检查表结构时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == 'create':
            create_category_tables()
        elif command == 'check':
            check_tables()
        else:
            print("未知命令。使用方法:")
            print("  python create_category_tables.py create  # 创建表结构")
            print("  python create_category_tables.py check   # 检查表结构")
    else:
        print("使用方法:")
        print("  python create_category_tables.py create  # 创建表结构")
        print("  python create_category_tables.py check   # 检查表结构")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化话术库性能 - 添加数据库索引和查询优化
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db
from sqlalchemy import text

def optimize_database():
    """优化数据库性能"""
    app = create_app()
    
    with app.app_context():
        try:
            print("开始优化数据库性能...")
            
            # 1. 检查现有索引
            print("1. 检查现有索引...")
            indexes = db.session.execute(text("""
                SELECT TABLE_NAME, INDEX_NAME, COLUMN_NAME 
                FROM INFORMATION_SCHEMA.STATISTICS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME IN ('scripts', 'script_categories')
                ORDER BY TABLE_NAME, INDEX_NAME
            """)).fetchall()
            
            print("现有索引:")
            for idx in indexes:
                print(f"  {idx[0]}.{idx[2]} -> {idx[1]}")
            
            # 2. 添加性能索引
            print("\n2. 添加性能优化索引...")
            
            # 检查 category_id 索引是否存在
            category_id_idx = db.session.execute(text("""
                SELECT INDEX_NAME FROM INFORMATION_SCHEMA.STATISTICS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'scripts' 
                AND COLUMN_NAME = 'category_id'
                AND INDEX_NAME != 'PRIMARY'
            """)).fetchall()
            
            if not category_id_idx:
                print("   添加 scripts.category_id 索引...")
                db.session.execute(text("CREATE INDEX idx_scripts_category_id ON scripts(category_id)"))
                print("   ✅ scripts.category_id 索引创建成功")
            else:
                print("   ✅ scripts.category_id 索引已存在")
            
            # 检查复合索引
            composite_idx = db.session.execute(text("""
                SELECT INDEX_NAME FROM INFORMATION_SCHEMA.STATISTICS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'scripts' 
                AND INDEX_NAME = 'idx_scripts_active_pinned_usage'
            """)).fetchall()
            
            if not composite_idx:
                print("   添加复合查询索引...")
                db.session.execute(text("""
                    CREATE INDEX idx_scripts_active_pinned_usage 
                    ON scripts(is_active, is_pinned DESC, usage_count DESC)
                """))
                print("   ✅ 复合查询索引创建成功")
            else:
                print("   ✅ 复合查询索引已存在")
            
            # 优化分类表索引
            cat_idx = db.session.execute(text("""
                SELECT INDEX_NAME FROM INFORMATION_SCHEMA.STATISTICS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'script_categories' 
                AND INDEX_NAME = 'idx_categories_active_parent'
            """)).fetchall()
            
            if not cat_idx:
                print("   添加分类表索引...")
                db.session.execute(text("""
                    CREATE INDEX idx_categories_active_parent 
                    ON script_categories(is_active, parent_id, sort_order)
                """))
                print("   ✅ 分类表索引创建成功")
            else:
                print("   ✅ 分类表索引已存在")
            
            # 3. 提交更改
            print("\n3. 提交数据库更改...")
            db.session.commit()
            
            # 4. 分析表统计信息
            print("4. 更新表统计信息...")
            db.session.execute(text("ANALYZE TABLE scripts"))
            db.session.execute(text("ANALYZE TABLE script_categories"))
            
            # 5. 检查查询性能
            print("\n5. 性能测试...")
            import time
            
            # 测试话术查询性能
            start_time = time.time()
            result = db.session.execute(text("""
                SELECT COUNT(*) FROM scripts 
                WHERE is_active = 1 
                ORDER BY is_pinned DESC, usage_count DESC 
                LIMIT 20
            """)).fetchone()
            query_time = (time.time() - start_time) * 1000
            
            print(f"   话术查询性能: {query_time:.2f}ms ({result[0]} 条记录)")
            
            # 测试分类查询性能
            start_time = time.time()
            cat_result = db.session.execute(text("""
                SELECT COUNT(*) FROM script_categories 
                WHERE is_active = 1 
                ORDER BY parent_id ASC, sort_order ASC
            """)).fetchone()
            cat_query_time = (time.time() - start_time) * 1000
            
            print(f"   分类查询性能: {cat_query_time:.2f}ms ({cat_result[0]} 条记录)")
            
            print("\n✅ 数据库性能优化完成!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 优化过程中发生错误: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False

def check_slow_queries():
    """检查慢查询"""
    app = create_app()
    
    with app.app_context():
        try:
            print("检查数据库配置和慢查询...")
            
            # 检查慢查询日志状态
            slow_log = db.session.execute(text("SHOW VARIABLES LIKE 'slow_query_log'")).fetchone()
            slow_time = db.session.execute(text("SHOW VARIABLES LIKE 'long_query_time'")).fetchone()
            
            print(f"慢查询日志: {slow_log[1] if slow_log else 'Unknown'}")
            print(f"慢查询时间阈值: {slow_time[1]}s" if slow_time else 'Unknown')
            
            # 检查表大小
            table_sizes = db.session.execute(text("""
                SELECT TABLE_NAME, 
                       ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) AS size_mb,
                       TABLE_ROWS
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME IN ('scripts', 'script_categories')
            """)).fetchall()
            
            print("\n表大小统计:")
            for table in table_sizes:
                print(f"  {table[0]}: {table[1]}MB, {table[2]} 行")
                
        except Exception as e:
            print(f"❌ 检查时发生错误: {str(e)}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == 'optimize':
            optimize_database()
        elif command == 'check':
            check_slow_queries()
        else:
            print("使用方法:")
            print("  python optimize_script_performance.py check     # 检查性能状态")
            print("  python optimize_script_performance.py optimize  # 执行性能优化")
    else:
        print("使用方法:")
        print("  python optimize_script_performance.py check     # 检查性能状态")
        print("  python optimize_script_performance.py optimize  # 执行性能优化")
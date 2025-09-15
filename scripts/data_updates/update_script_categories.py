#!/usr/bin/env python3
"""
Update script categories to new project-based system
将现有话术的category字段更新为'电网'
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Script

def update_script_categories():
    """将所有现有话术的category设置为'电网'"""
    app = create_app()
    
    with app.app_context():
        try:
            # 先查看现有的category值
            from sqlalchemy import text
            result = db.session.execute(text("SELECT DISTINCT category, COUNT(*) as count FROM scripts WHERE is_active = 1 GROUP BY category"))
            categories = result.fetchall()
            
            print("现有分类统计:")
            for category, count in categories:
                print(f"  {category}: {count} 条")
            
            # 使用原生SQL更新所有记录
            print("\n开始更新所有话术分类为'电网'...")
            result = db.session.execute(text("UPDATE scripts SET category = '电网' WHERE is_active = 1"))
            
            # 提交更改
            db.session.commit()
            print(f"成功更新 {result.rowcount} 条话术记录")
            
        except Exception as e:
            db.session.rollback()
            print(f"更新失败: {str(e)}")
            return False
    
    return True

if __name__ == '__main__':
    print("开始更新话术分类...")
    success = update_script_categories()
    if success:
        print("话术分类更新完成!")
    else:
        print("话术分类更新失败!")
        sys.exit(1)
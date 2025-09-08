#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
话术分类数据迁移脚本
将现有Script表中的category数据迁移到新的ScriptCategory表中
"""

import sys
import os
from datetime import datetime

# 添加项目路径到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Script, ScriptCategory

def migrate_script_categories():
    """迁移话术分类数据"""
    app = create_app()
    
    with app.app_context():
        try:
            print("开始迁移话术分类数据...")
            
            # 1. 先创建默认系统分类
            print("1. 创建默认系统分类...")
            default_categories = ScriptCategory.create_default_categories()
            print(f"   创建了 {len(default_categories)} 个默认分类")
            
            # 2. 获取现有的所有不重复分类名称
            print("2. 分析现有话术分类数据...")
            existing_categories = db.session.query(Script.category).distinct().filter(
                Script.category.isnot(None),
                Script.category != '',
                Script.is_active == True
            ).all()
            
            existing_category_names = [cat[0] for cat in existing_categories if cat[0]]
            print(f"   发现 {len(existing_category_names)} 个现有分类: {existing_category_names}")
            
            # 3. 创建不存在的分类
            print("3. 创建新发现的分类...")
            created_count = 0
            category_mapping = {}  # 用于记录分类名称到ID的映射
            
            # 先获取已存在的分类映射
            existing_script_categories = ScriptCategory.query.filter_by(is_active=True).all()
            for cat in existing_script_categories:
                category_mapping[cat.name] = cat.id
            
            for category_name in existing_category_names:
                if category_name not in category_mapping:
                    # 创建新分类
                    new_category = ScriptCategory(
                        name=category_name,
                        description=f'从旧系统迁移的分类: {category_name}',
                        is_system=False,  # 用户自定义分类
                        created_by=None  # 系统迁移
                    )
                    db.session.add(new_category)
                    db.session.flush()  # 获取ID
                    
                    category_mapping[category_name] = new_category.id
                    created_count += 1
                    print(f"   创建分类: {category_name} (ID: {new_category.id})")
            
            print(f"   新创建了 {created_count} 个分类")
            
            # 4. 更新Script表中的category_id字段
            print("4. 更新话术的分类关联...")
            updated_count = 0
            
            scripts_to_update = Script.query.filter(
                Script.category.isnot(None),
                Script.category != '',
                Script.category_id.is_(None),  # 只更新还没有category_id的记录
                Script.is_active == True
            ).all()
            
            print(f"   找到 {len(scripts_to_update)} 个需要更新的话术")
            
            for script in scripts_to_update:
                if script.category in category_mapping:
                    script.category_id = category_mapping[script.category]
                    updated_count += 1
                    
                    if updated_count % 100 == 0:  # 每100条记录显示进度
                        print(f"   已更新 {updated_count} 个话术...")
            
            print(f"   总共更新了 {updated_count} 个话术的分类关联")
            
            # 5. 提交所有更改
            print("5. 提交数据库更改...")
            db.session.commit()
            
            # 6. 验证迁移结果
            print("6. 验证迁移结果...")
            total_categories = ScriptCategory.query.filter_by(is_active=True).count()
            total_scripts_with_category = Script.query.filter(
                Script.category_id.isnot(None),
                Script.is_active == True
            ).count()
            
            print(f"   总分类数: {total_categories}")
            print(f"   已关联分类的话术数: {total_scripts_with_category}")
            
            # 7. 显示分类统计
            print("7. 分类统计:")
            for category in ScriptCategory.query.filter_by(is_active=True).order_by(ScriptCategory.name).all():
                script_count = category.get_script_count(include_children=False)
                category_type = "系统" if category.is_system else "用户"
                print(f"   {category.name} ({category_type}): {script_count} 个话术")
            
            print("\n✅ 话术分类数据迁移完成!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 迁移过程中发生错误: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False

def rollback_migration():
    """回滚迁移（清空category_id字段）"""
    app = create_app()
    
    with app.app_context():
        try:
            print("开始回滚话术分类迁移...")
            
            # 清空所有话术的category_id字段
            updated_count = Script.query.filter(
                Script.category_id.isnot(None)
            ).update({Script.category_id: None})
            
            print(f"清空了 {updated_count} 个话术的category_id字段")
            
            # 删除所有非系统分类
            deleted_count = ScriptCategory.query.filter_by(is_system=False).delete()
            print(f"删除了 {deleted_count} 个用户创建的分类")
            
            db.session.commit()
            print("✅ 回滚完成!")
            
        except Exception as e:
            print(f"❌ 回滚过程中发生错误: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()

def check_migration_status():
    """检查迁移状态"""
    app = create_app()
    
    with app.app_context():
        try:
            print("检查话术分类迁移状态...")
            
            # 统计信息
            total_scripts = Script.query.filter_by(is_active=True).count()
            scripts_with_old_category = Script.query.filter(
                Script.category.isnot(None),
                Script.category != '',
                Script.is_active == True
            ).count()
            scripts_with_new_category = Script.query.filter(
                Script.category_id.isnot(None),
                Script.is_active == True
            ).count()
            total_categories = ScriptCategory.query.filter_by(is_active=True).count()
            
            print(f"总话术数: {total_scripts}")
            print(f"有旧分类的话术数: {scripts_with_old_category}")
            print(f"有新分类的话术数: {scripts_with_new_category}")
            print(f"总分类数: {total_categories}")
            
            # 检查是否需要迁移
            need_migration = scripts_with_old_category > scripts_with_new_category
            print(f"\n{'需要迁移' if need_migration else '无需迁移'}")
            
            if total_categories > 0:
                print("\n现有分类:")
                for category in ScriptCategory.query.filter_by(is_active=True).order_by(ScriptCategory.name).all():
                    script_count = category.get_script_count(include_children=False)
                    category_type = "系统" if category.is_system else "用户"
                    print(f"  {category.name} ({category_type}): {script_count} 个话术")
            
        except Exception as e:
            print(f"❌ 检查状态时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == 'migrate':
            migrate_script_categories()
        elif command == 'rollback':
            rollback_migration()
        elif command == 'status':
            check_migration_status()
        else:
            print("未知命令。使用方法:")
            print("  python migrate_script_categories.py migrate   # 执行迁移")
            print("  python migrate_script_categories.py rollback  # 回滚迁移") 
            print("  python migrate_script_categories.py status    # 检查状态")
    else:
        print("使用方法:")
        print("  python migrate_script_categories.py migrate   # 执行迁移")
        print("  python migrate_script_categories.py rollback  # 回滚迁移")
        print("  python migrate_script_categories.py status    # 检查状态")
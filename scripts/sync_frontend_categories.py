#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步前端分类体系到新分类系统
将前端使用的 primary_category 和 secondary_category 同步到 ScriptCategory 表中
"""

import sys
import os
from datetime import datetime

# 添加项目路径到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Script, ScriptCategory
from sqlalchemy import func

def sync_frontend_categories():
    """同步前端分类体系"""
    app = create_app()
    
    with app.app_context():
        try:
            print("开始同步前端分类体系...")
            
            # 1. 定义前端分类体系
            frontend_categories = {
                'project_category': {
                    'label': '项目分类',
                    'children': {
                        'power_grid': '电网',
                        'electrical_exam': '电气考研'
                    }
                },
                'product_intro': {
                    'label': '产品介绍', 
                    'children': {}
                },
                'marketing': {
                    'label': '营销话术',
                    'children': {}
                },
                'faq': {
                    'label': '常见问题',
                    'children': {}
                },
                'learning_guidance': {
                    'label': '学习指导',
                    'children': {
                        'application_guide': '网申',
                        'review_planning': '复习规划',
                        'consultation': '报考咨询'
                    }
                },
                'study_planning': {
                    'label': '学习规划',
                    'children': {}
                }
            }
            
            # 2. 创建或更新主分类
            print("2. 创建主分类...")
            primary_categories = {}
            
            for primary_key, primary_info in frontend_categories.items():
                # 检查是否已存在
                existing = ScriptCategory.query.filter_by(
                    name=primary_info['label'],
                    parent_id=None,
                    is_active=True
                ).first()
                
                if existing:
                    print(f"   主分类已存在: {primary_info['label']} (ID: {existing.id})")
                    primary_categories[primary_key] = existing
                else:
                    # 创建新的主分类
                    new_category = ScriptCategory(
                        name=primary_info['label'],
                        description=f'前端分类体系: {primary_info["label"]}',
                        is_system=True,  # 标记为系统分类
                        parent_id=None,
                        sort_order=len(primary_categories)
                    )
                    db.session.add(new_category)
                    db.session.flush()
                    
                    primary_categories[primary_key] = new_category
                    print(f"   创建主分类: {primary_info['label']} (ID: {new_category.id})")
            
            # 3. 创建子分类
            print("3. 创建子分类...")
            secondary_categories = {}
            
            for primary_key, primary_info in frontend_categories.items():
                if not primary_info['children']:
                    continue
                    
                parent_category = primary_categories[primary_key]
                
                for secondary_key, secondary_label in primary_info['children'].items():
                    # 检查是否已存在
                    existing = ScriptCategory.query.filter_by(
                        name=secondary_label,
                        parent_id=parent_category.id,
                        is_active=True
                    ).first()
                    
                    if existing:
                        print(f"   子分类已存在: {secondary_label} (父: {parent_category.name}, ID: {existing.id})")
                        secondary_categories[f"{primary_key}.{secondary_key}"] = existing
                    else:
                        # 创建新的子分类
                        new_category = ScriptCategory(
                            name=secondary_label,
                            description=f'前端子分类: {secondary_label}',
                            is_system=True,
                            parent_id=parent_category.id,
                            sort_order=len([k for k in secondary_categories.keys() if k.startswith(primary_key)])
                        )
                        db.session.add(new_category)
                        db.session.flush()
                        
                        secondary_categories[f"{primary_key}.{secondary_key}"] = new_category
                        print(f"   创建子分类: {secondary_label} (父: {parent_category.name}, ID: {new_category.id})")
            
            # 4. 将现有话术按照 primary_category 和 secondary_category 字段映射到新分类
            print("4. 更新话术分类关联...")
            updated_count = 0
            
            # 获取有分类字段的话术
            scripts_with_categories = Script.query.filter(
                Script.is_active == True,
                db.or_(
                    Script.primary_category.isnot(None),
                    Script.secondary_category.isnot(None)
                )
            ).all()
            
            print(f"   找到 {len(scripts_with_categories)} 个有前端分类字段的话术")
            
            for script in scripts_with_categories:
                target_category = None
                
                # 优先使用子分类
                if script.primary_category and script.secondary_category:
                    category_key = f"{script.primary_category}.{script.secondary_category}"
                    if category_key in secondary_categories:
                        target_category = secondary_categories[category_key]
                
                # 如果没有匹配的子分类，使用主分类
                if not target_category and script.primary_category:
                    if script.primary_category in primary_categories:
                        target_category = primary_categories[script.primary_category]
                
                # 更新分类关联
                if target_category and script.category_id != target_category.id:
                    old_category = script.category_id
                    script.category_id = target_category.id
                    updated_count += 1
                    
                    if updated_count % 50 == 0:
                        print(f"   已更新 {updated_count} 个话术...")
            
            print(f"   总共更新了 {updated_count} 个话术的分类关联")
            
            # 5. 提交所有更改
            print("5. 提交数据库更改...")
            db.session.commit()
            
            # 6. 显示最终统计
            print("6. 同步完成，分类统计:")
            all_categories = ScriptCategory.query.filter_by(is_active=True).order_by(
                ScriptCategory.parent_id.asc(), 
                ScriptCategory.sort_order.asc(),
                ScriptCategory.name.asc()
            ).all()
            
            for category in all_categories:
                level = "主分类" if category.parent_id is None else "└─ 子分类"
                script_count = category.get_script_count(include_children=False)
                print(f"   {level}: {category.name} ({script_count} 个话术)")
            
            print("\n✅ 前端分类体系同步完成!")
            return True
            
        except Exception as e:
            print(f"\n❌ 同步过程中发生错误: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False

def check_frontend_mapping():
    """检查前端分类字段的使用情况"""
    app = create_app()
    
    with app.app_context():
        try:
            print("检查前端分类字段使用情况...")
            
            # 统计 primary_category 使用情况
            primary_stats = db.session.query(
                Script.primary_category,
                func.count(Script.id).label('count')
            ).filter(
                Script.is_active == True,
                Script.primary_category.isnot(None)
            ).group_by(Script.primary_category).all()
            
            print("\nprimary_category 使用情况:")
            for stat in primary_stats:
                print(f"  {stat[0]}: {stat[1]} 个话术")
            
            # 统计 secondary_category 使用情况
            secondary_stats = db.session.query(
                Script.secondary_category,
                func.count(Script.id).label('count')
            ).filter(
                Script.is_active == True,
                Script.secondary_category.isnot(None)
            ).group_by(Script.secondary_category).all()
            
            print("\nsecondary_category 使用情况:")
            for stat in secondary_stats:
                print(f"  {stat[0]}: {stat[1]} 个话术")
            
            # 统计组合使用情况
            combined_stats = db.session.query(
                Script.primary_category,
                Script.secondary_category,
                func.count(Script.id).label('count')
            ).filter(
                Script.is_active == True,
                Script.primary_category.isnot(None)
            ).group_by(
                Script.primary_category, 
                Script.secondary_category
            ).all()
            
            print("\n组合分类使用情况:")
            for stat in combined_stats:
                secondary = stat[1] or '(无子分类)'
                print(f"  {stat[0]} -> {secondary}: {stat[2]} 个话术")
                
        except Exception as e:
            print(f"❌ 检查过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == 'sync':
            sync_frontend_categories()
        elif command == 'check':
            check_frontend_mapping()
        else:
            print("未知命令。使用方法:")
            print("  python sync_frontend_categories.py check  # 检查前端分类使用情况")
            print("  python sync_frontend_categories.py sync   # 同步前端分类到新系统")
    else:
        print("使用方法:")
        print("  python sync_frontend_categories.py check  # 检查前端分类使用情况")
        print("  python sync_frontend_categories.py sync   # 同步前端分类到新系统")
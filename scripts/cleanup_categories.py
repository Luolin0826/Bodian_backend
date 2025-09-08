#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理多余分类，只保留前端实际使用的分类
"""

import sys
import os
from datetime import datetime

# 添加项目路径到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Script, ScriptCategory
from sqlalchemy import func

def cleanup_categories():
    """清理多余分类，只保留前端使用的分类"""
    app = create_app()
    
    with app.app_context():
        try:
            print("开始清理多余分类...")
            
            # 定义需要保留的分类结构
            keep_categories = {
                # 主分类
                'project_category': '项目分类',
                'product_intro': '产品介绍', 
                'marketing': '营销话术',
                'faq': '常见问题',
                'learning_guidance': '学习指导',
                'study_planning': '学习规划',
                
                # 子分类
                'power_grid': '电网',
                'electrical_exam': '电气考研',
                'application_guide': '网申',
                'review_planning': '复习规划',
                'consultation': '报考咨询'
            }
            
            # 1. 获取当前所有分类
            all_categories = ScriptCategory.query.filter_by(is_active=True).all()
            print(f"当前总分类数: {len(all_categories)}")
            
            # 2. 识别需要保留的分类
            categories_to_keep = []
            categories_to_remove = []
            
            for category in all_categories:
                if category.name in keep_categories.values():
                    categories_to_keep.append(category)
                    print(f"保留分类: {category.name} (ID: {category.id})")
                else:
                    categories_to_remove.append(category)
                    print(f"待删除分类: {category.name} (ID: {category.id})")
            
            print(f"\n保留 {len(categories_to_keep)} 个分类，删除 {len(categories_to_remove)} 个分类")
            
            # 3. 处理要删除分类下的话术
            print("\n3. 处理待删除分类下的话术...")
            
            # 找到一个通用的分类作为默认分类（比如"常见问题"）
            default_category = None
            for cat in categories_to_keep:
                if cat.name == '常见问题':
                    default_category = cat
                    break
            
            if not default_category:
                print("未找到默认分类，创建一个...")
                default_category = ScriptCategory(
                    name='常见问题',
                    description='默认分类',
                    is_system=True,
                    parent_id=None,
                    sort_order=0
                )
                db.session.add(default_category)
                db.session.flush()
                print(f"创建默认分类: {default_category.name} (ID: {default_category.id})")
            
            # 迁移话术到默认分类
            moved_scripts = 0
            for category in categories_to_remove:
                # 获取该分类下的话术数量
                script_count = Script.query.filter_by(category_id=category.id, is_active=True).count()
                
                if script_count > 0:
                    print(f"   迁移 {category.name} 下的 {script_count} 个话术到 {default_category.name}")
                    
                    # 更新话术分类
                    Script.query.filter_by(category_id=category.id, is_active=True).update({
                        'category_id': default_category.id
                    })
                    moved_scripts += script_count
            
            print(f"总共迁移了 {moved_scripts} 个话术")
            
            # 4. 软删除多余分类
            print("\n4. 删除多余分类...")
            deleted_count = 0
            for category in categories_to_remove:
                category.is_active = False
                deleted_count += 1
                print(f"   删除分类: {category.name}")
            
            # 5. 重新整理保留分类的层级关系
            print("\n5. 整理分类层级关系...")
            
            # 建立正确的父子关系
            main_categories = {
                '项目分类': None,
                '产品介绍': None, 
                '营销话术': None,
                '常见问题': None,
                '学习指导': None,
                '学习规划': None
            }
            
            sub_categories = {
                '电网': '项目分类',
                '电气考研': '项目分类',
                '网申': '学习指导',
                '复习规划': '学习指导',
                '报考咨询': '学习指导'
            }
            
            # 更新主分类
            for i, (cat_name, _) in enumerate(main_categories.items()):
                category = next((c for c in categories_to_keep if c.name == cat_name), None)
                if category:
                    category.parent_id = None
                    category.sort_order = i
                    category.is_system = True
                    main_categories[cat_name] = category.id
            
            # 更新子分类
            for sub_name, parent_name in sub_categories.items():
                sub_category = next((c for c in categories_to_keep if c.name == sub_name), None)
                parent_id = main_categories.get(parent_name)
                
                if sub_category and parent_id:
                    sub_category.parent_id = parent_id
                    sub_category.is_system = True
                    # 计算同级排序
                    same_level_count = sum(1 for k, v in sub_categories.items() if v == parent_name and k <= sub_name)
                    sub_category.sort_order = same_level_count - 1
            
            # 6. 提交更改
            print("\n6. 提交数据库更改...")
            db.session.commit()
            
            # 7. 显示最终结果
            print("\n7. 清理完成，最终分类结构:")
            final_categories = ScriptCategory.query.filter_by(is_active=True).order_by(
                ScriptCategory.parent_id.asc(), 
                ScriptCategory.sort_order.asc()
            ).all()
            
            for category in final_categories:
                if category.parent_id is None:
                    script_count = category.get_script_count(include_children=False)
                    print(f"📁 {category.name} - {script_count} 个话术")
                    
                    # 显示子分类
                    children = [c for c in final_categories if c.parent_id == category.id]
                    for child in children:
                        child_count = child.get_script_count(include_children=False)
                        print(f"   └─ {child.name} - {child_count} 个话术")
            
            total_scripts = Script.query.filter_by(is_active=True).count()
            total_categories = len(final_categories)
            print(f"\n✅ 清理完成! 保留 {total_categories} 个分类，{total_scripts} 个话术")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 清理过程中发生错误: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False

def preview_cleanup():
    """预览将要进行的清理操作"""
    app = create_app()
    
    with app.app_context():
        try:
            print("预览清理操作...")
            
            # 定义需要保留的分类
            keep_category_names = {
                '项目分类', '产品介绍', '营销话术', '常见问题', '学习指导', '学习规划',
                '电网', '电气考研', '网申', '复习规划', '报考咨询'
            }
            
            # 获取所有分类
            all_categories = ScriptCategory.query.filter_by(is_active=True).all()
            
            print(f"\n当前分类 ({len(all_categories)} 个):")
            keep_count = 0
            remove_count = 0
            
            for category in all_categories:
                script_count = category.get_script_count(include_children=False)
                
                if category.name in keep_category_names:
                    print(f"✅ 保留: {category.name} ({script_count} 个话术)")
                    keep_count += 1
                else:
                    print(f"❌ 删除: {category.name} ({script_count} 个话术)")
                    remove_count += 1
            
            print(f"\n预览结果:")
            print(f"- 保留 {keep_count} 个分类")
            print(f"- 删除 {remove_count} 个分类")
            
            if remove_count > 0:
                print(f"\n注意: 被删除分类下的话术将迁移到'常见问题'分类中")
            
        except Exception as e:
            print(f"❌ 预览时发生错误: {str(e)}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == 'cleanup':
            cleanup_categories()
        elif command == 'preview':
            preview_cleanup()
        else:
            print("未知命令。使用方法:")
            print("  python cleanup_categories.py preview  # 预览清理操作")
            print("  python cleanup_categories.py cleanup  # 执行清理")
    else:
        print("使用方法:")
        print("  python cleanup_categories.py preview  # 预览清理操作")
        print("  python cleanup_categories.py cleanup  # 执行清理")
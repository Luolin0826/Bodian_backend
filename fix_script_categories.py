#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复话术分类问题
检查并修复话术的分类ID更新
"""

import pandas as pd
import sys
sys.path.append('/workspace')

from app import create_app
from app.models.script import Script
from app.models import db

def fix_script_categories():
    """修复话术分类"""
    print("=== 修复话术分类 ===")
    
    app = create_app()
    with app.app_context():
        try:
            # 读取Excel文件建立映射
            df = pd.read_excel('/workspace/话术库.xlsx')
            
            category_mapping = {
                '产品和服务': 27,
                '复习规划': 28, 
                '竞品分析': 29,
                '线上课': 30,
                '线下班': 31,
                '小程序': 32,
                '其他': 33
            }
            
            updated_count = 0
            error_count = 0
            
            # 处理每个Excel记录
            for _, row in df.iterrows():
                script_id = row['ID']
                category_name = str(row['分类名称']).strip()
                new_category_id = category_mapping.get(category_name, 33)
                
                # 获取数据库中的话术
                script = Script.query.get(script_id)
                if script and script.is_active:
                    if script.category_id != new_category_id:
                        old_category_id = script.category_id
                        script.category_id = new_category_id
                        print(f"话术 {script_id}: 分类 {old_category_id} -> {new_category_id} ({category_name})")
                        updated_count += 1
                    # else:
                    #     print(f"话术 {script_id}: 分类已正确 ({new_category_id})")
                elif script:
                    print(f"话术 {script_id}: 已被删除，跳过")
                else:
                    print(f"话术 {script_id}: 不存在于数据库")
                    error_count += 1
            
            # 提交更改
            db.session.commit()
            print(f"\n=== 分类修复完成 ===")
            print(f"更新了 {updated_count} 条话术的分类")
            print(f"错误数量: {error_count}")
            
            # 验证结果
            print(f"\n=== 验证修复结果 ===")
            for category_name, category_id in category_mapping.items():
                count = Script.query.filter_by(category_id=category_id, is_active=True).count()
                print(f"分类 {category_id} ({category_name}): {count} 条")
            
            # 计算预期数量
            expected_counts = df['分类名称'].value_counts()
            print(f"\nExcel中的分类分布:")
            for category_name, expected_count in expected_counts.items():
                actual_count = Script.query.filter_by(
                    category_id=category_mapping.get(category_name, 33), 
                    is_active=True
                ).count()
                status = "✅" if expected_count == actual_count else "❌"
                print(f"  {category_name}: 预期 {expected_count}, 实际 {actual_count} {status}")
            
            return True
            
        except Exception as e:
            print(f"修复分类失败: {e}")
            db.session.rollback()
            import traceback
            print(traceback.format_exc())
            return False

def cleanup_deleted_scripts():
    """清理应该被删除的话术"""
    print("\n=== 清理删除的话术 ===")
    
    app = create_app()
    with app.app_context():
        try:
            # 读取Excel文件获取应该存在的ID
            df = pd.read_excel('/workspace/话术库.xlsx')
            excel_ids = set(df['ID'].tolist())
            
            # 获取数据库中所有活跃话术
            all_active_scripts = Script.query.filter_by(is_active=True).all()
            
            deleted_count = 0
            
            for script in all_active_scripts:
                if script.id not in excel_ids:
                    script.is_active = False
                    print(f"标记删除话术 {script.id}: {script.title}")
                    deleted_count += 1
            
            db.session.commit()
            print(f"标记删除 {deleted_count} 条话术")
            
            # 验证最终结果
            active_count = Script.query.filter_by(is_active=True).count()
            inactive_count = Script.query.filter_by(is_active=False).count()
            
            print(f"\n=== 最终统计 ===")
            print(f"活跃话术: {active_count} 条")
            print(f"已删除话术: {inactive_count} 条")
            print(f"Excel话术: {len(excel_ids)} 条")
            
            if active_count == len(excel_ids):
                print("✅ 数据完全同步")
            else:
                print("❌ 数据仍有差异")
                
            return True
            
        except Exception as e:
            print(f"清理失败: {e}")
            db.session.rollback()
            import traceback
            print(traceback.format_exc())
            return False

if __name__ == "__main__":
    print("=== 话术分类修复工具 ===")
    
    # 1. 修复分类
    if fix_script_categories():
        print("✅ 分类修复成功")
    else:
        print("❌ 分类修复失败")
        exit(1)
    
    # 2. 清理删除的话术
    if cleanup_deleted_scripts():
        print("✅ 清理完成")
    else:
        print("❌ 清理失败")
        exit(1)
    
    print("\n🎉 话术库更新完全成功！")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
话术库数据更新脚本
根据Excel文件更新数据库中的话术内容，调整分类体系，清理无效数据
"""

import pandas as pd
import sys
import os
sys.path.append('/workspace')

from app import create_app
from app.models.script import Script
from app.models.script_category import ScriptCategory
from app.models import db

def analyze_differences():
    """分析Excel文件与数据库的差异"""
    print("=== 话术库数据差异分析 ===")
    
    app = create_app()
    with app.app_context():
        try:
            # 1. 读取Excel文件
            df = pd.read_excel('/workspace/话术库.xlsx')
            print(f"Excel文件: 共 {len(df)} 条话术")
            
            # 建立Excel话术ID索引
            excel_scripts = {}
            category_mapping = {
                '产品和服务': 27,
                '复习规划': 28, 
                '竞品分析': 29,
                '线上课': 30,
                '线下班': 31,
                '小程序': 32,
                '其他': 33
            }
            
            for _, row in df.iterrows():
                excel_scripts[row['ID']] = {
                    'question': str(row['问题']).strip(),
                    'answer': str(row['答案']).strip(),
                    'category_name': str(row['分类名称']).strip(),
                    'category_id': category_mapping.get(str(row['分类名称']).strip(), 33)  # 默认为"其他"
                }
            
            print(f"Excel分类统计:")
            category_stats = df['分类名称'].value_counts()
            for cat, count in category_stats.items():
                print(f"  {cat}: {count} 条")
            
            # 2. 获取数据库现有话术
            db_scripts = Script.query.filter_by(is_active=True).all()
            print(f"\n数据库: 共 {len(db_scripts)} 条活跃话术")
            
            db_script_dict = {}
            for script in db_scripts:
                db_script_dict[script.id] = {
                    'question': script.question or '',
                    'answer': script.answer or '',
                    'category_id': script.category_id,
                    'title': script.title
                }
            
            # 3. 分析差异
            excel_ids = set(excel_scripts.keys())
            db_ids = set(db_script_dict.keys())
            
            # 需要更新的话术(Excel中存在)
            existing_ids = excel_ids & db_ids
            # 需要新增的话术(Excel中有但数据库中没有)
            new_ids = excel_ids - db_ids
            # 需要删除的话术(数据库中有但Excel中没有)
            delete_ids = db_ids - excel_ids
            
            print(f"\n=== 差异统计 ===")
            print(f"Excel中存在的话术: {len(excel_ids)} 条")
            print(f"数据库中存在的话术: {len(db_ids)} 条")
            print(f"需要检查更新的话术: {len(existing_ids)} 条")
            print(f"需要新增的话术: {len(new_ids)} 条")
            print(f"需要标记删除的话术: {len(delete_ids)} 条")
            
            # 4. 检查内容变化
            content_changes = []
            category_changes = []
            
            for script_id in existing_ids:
                excel_data = excel_scripts[script_id]
                db_data = db_script_dict[script_id]
                
                # 检查问题和答案是否有变化
                question_changed = excel_data['question'] != db_data['question']
                answer_changed = excel_data['answer'] != db_data['answer']
                
                if question_changed or answer_changed:
                    content_changes.append({
                        'id': script_id,
                        'question_changed': question_changed,
                        'answer_changed': answer_changed,
                        'old_question': db_data['question'][:50] + '...',
                        'new_question': excel_data['question'][:50] + '...',
                        'old_answer': db_data['answer'][:50] + '...',
                        'new_answer': excel_data['answer'][:50] + '...'
                    })
                
                # 检查分类是否需要变化
                if excel_data['category_id'] != db_data['category_id']:
                    category_changes.append({
                        'id': script_id,
                        'old_category_id': db_data['category_id'],
                        'new_category_id': excel_data['category_id'],
                        'new_category_name': excel_data['category_name']
                    })
            
            print(f"\n=== 内容变化统计 ===")
            print(f"需要更新内容的话术: {len(content_changes)} 条")
            print(f"需要更新分类的话术: {len(category_changes)} 条")
            
            # 显示部分变化示例
            if content_changes:
                print("\n内容变化示例(前5条):")
                for change in content_changes[:5]:
                    print(f"  ID {change['id']}:")
                    if change['question_changed']:
                        print(f"    问题: {change['old_question']} -> {change['new_question']}")
                    if change['answer_changed']:
                        print(f"    答案: {change['old_answer']} -> {change['new_answer']}")
            
            if category_changes:
                print(f"\n分类变化示例(前5条):")
                for change in category_changes[:5]:
                    print(f"  ID {change['id']}: 分类ID {change['old_category_id']} -> {change['new_category_id']} ({change['new_category_name']})")
            
            if new_ids:
                print(f"\n需要新增的话术ID: {list(new_ids)[:10]}{'...' if len(new_ids) > 10 else ''}")
            
            if delete_ids:
                print(f"\n需要删除的话术ID: {list(delete_ids)[:10]}{'...' if len(delete_ids) > 10 else ''}")
            
            return {
                'excel_scripts': excel_scripts,
                'db_scripts': db_script_dict,
                'existing_ids': existing_ids,
                'new_ids': new_ids,
                'delete_ids': delete_ids,
                'content_changes': content_changes,
                'category_changes': category_changes,
                'category_mapping': category_mapping
            }
            
        except Exception as e:
            print(f"分析失败: {e}")
            import traceback
            print(traceback.format_exc())
            return None

def update_script_contents(analysis_result):
    """更新话术内容"""
    print("\n=== 更新话术内容 ===")
    
    app = create_app()
    with app.app_context():
        try:
            excel_scripts = analysis_result['excel_scripts']
            content_changes = analysis_result['content_changes']
            existing_ids = analysis_result['existing_ids']
            
            updated_count = 0
            
            # 更新有变化的话术内容
            for change in content_changes:
                script_id = change['id']
                script = Script.query.get(script_id)
                
                if script:
                    excel_data = excel_scripts[script_id]
                    
                    if change['question_changed']:
                        script.question = excel_data['question']
                        print(f"更新话术 {script_id} 的问题")
                    
                    if change['answer_changed']:
                        script.answer = excel_data['answer']
                        print(f"更新话术 {script_id} 的答案")
                    
                    updated_count += 1
            
            # 为没有内容变化但存在于Excel中的话术也确保内容一致
            for script_id in existing_ids:
                if script_id not in [c['id'] for c in content_changes]:
                    script = Script.query.get(script_id)
                    if script:
                        excel_data = excel_scripts[script_id]
                        # 确保内容完全一致
                        if script.question != excel_data['question'] or script.answer != excel_data['answer']:
                            script.question = excel_data['question']
                            script.answer = excel_data['answer']
                            print(f"同步话术 {script_id} 内容")
            
            db.session.commit()
            print(f"成功更新 {updated_count} 条话术的内容")
            
            return True
            
        except Exception as e:
            print(f"更新话术内容失败: {e}")
            db.session.rollback()
            import traceback
            print(traceback.format_exc())
            return False

def update_script_categories(analysis_result):
    """重整话术分类体系"""
    print("\n=== 重整话术分类体系 ===")
    
    app = create_app()
    with app.app_context():
        try:
            excel_scripts = analysis_result['excel_scripts']
            existing_ids = analysis_result['existing_ids']
            category_mapping = analysis_result['category_mapping']
            
            updated_count = 0
            
            # 更新所有存在于Excel中的话术分类
            for script_id in existing_ids:
                script = Script.query.get(script_id)
                if script:
                    excel_data = excel_scripts[script_id]
                    new_category_id = excel_data['category_id']
                    
                    if script.category_id != new_category_id:
                        old_category_id = script.category_id
                        script.category_id = new_category_id
                        print(f"话术 {script_id}: 分类 {old_category_id} -> {new_category_id} ({excel_data['category_name']})")
                        updated_count += 1
            
            db.session.commit()
            print(f"成功更新 {updated_count} 条话术的分类")
            
            # 统计新分类体系下的话术分布
            print(f"\n=== 新分类体系话术分布 ===")
            for category_name, category_id in category_mapping.items():
                count = Script.query.filter_by(category_id=category_id, is_active=True).count()
                print(f"分类 {category_id} ({category_name}): {count} 条")
            
            return True
            
        except Exception as e:
            print(f"更新分类失败: {e}")
            db.session.rollback()
            import traceback
            print(traceback.format_exc())
            return False

def handle_new_scripts(analysis_result):
    """处理需要新增的话术"""
    print("\n=== 处理新增话术 ===")
    
    app = create_app()
    with app.app_context():
        try:
            excel_scripts = analysis_result['excel_scripts']
            new_ids = analysis_result['new_ids']
            
            if not new_ids:
                print("没有需要新增的话术")
                return True
            
            created_count = 0
            
            for script_id in new_ids:
                excel_data = excel_scripts[script_id]
                
                # 创建新话术
                new_script = Script(
                    id=script_id,  # 使用Excel中的ID
                    question=excel_data['question'],
                    answer=excel_data['answer'],
                    category_id=excel_data['category_id'],
                    title=excel_data['question'][:50] + '...' if len(excel_data['question']) > 50 else excel_data['question'],
                    is_active=True,
                    usage_count=0,
                    effectiveness=0.0
                )
                
                db.session.add(new_script)
                print(f"新增话术 {script_id}: {excel_data['category_name']}")
                created_count += 1
            
            db.session.commit()
            print(f"成功新增 {created_count} 条话术")
            
            return True
            
        except Exception as e:
            print(f"新增话术失败: {e}")
            db.session.rollback()
            import traceback
            print(traceback.format_exc())
            return False

def mark_deleted_scripts(analysis_result):
    """标记需要删除的话术"""
    print("\n=== 标记删除话术 ===")
    
    app = create_app()
    with app.app_context():
        try:
            delete_ids = analysis_result['delete_ids']
            
            if not delete_ids:
                print("没有需要删除的话术")
                return True
            
            deleted_count = 0
            
            for script_id in delete_ids:
                script = Script.query.get(script_id)
                if script and script.is_active:
                    script.is_active = False
                    print(f"标记删除话术 {script_id}: {script.title}")
                    deleted_count += 1
            
            db.session.commit()
            print(f"成功标记删除 {deleted_count} 条话术")
            
            return True
            
        except Exception as e:
            print(f"标记删除失败: {e}")
            db.session.rollback()
            import traceback
            print(traceback.format_exc())
            return False

def validate_and_report(analysis_result):
    """验证更新结果并生成报告"""
    print("\n=== 验证更新结果 ===")
    
    app = create_app()
    with app.app_context():
        try:
            category_mapping = analysis_result['category_mapping']
            
            # 统计最终结果
            total_active = Script.query.filter_by(is_active=True).count()
            total_inactive = Script.query.filter_by(is_active=False).count()
            
            print(f"活跃话术总数: {total_active}")
            print(f"已删除话术总数: {total_inactive}")
            
            # 分类分布验证
            print(f"\n=== 最终分类分布 ===")
            category_distribution = {}
            
            for category_name, category_id in category_mapping.items():
                count = Script.query.filter_by(category_id=category_id, is_active=True).count()
                category_distribution[category_name] = count
                print(f"分类 {category_id} ({category_name}): {count} 条")
            
            # 验证Excel数据是否完全同步
            df = pd.read_excel('/workspace/话术库.xlsx')
            excel_count = len(df)
            
            print(f"\n=== 同步验证 ===")
            print(f"Excel文件话术数: {excel_count}")
            print(f"数据库活跃话术数: {total_active}")
            
            if excel_count == total_active:
                print("✅ 数据同步成功，数量完全匹配")
            else:
                print("⚠️  数据同步存在差异，需要进一步检查")
            
            # 生成更新报告
            report = {
                'excel_count': excel_count,
                'db_active_count': total_active,
                'db_inactive_count': total_inactive,
                'category_distribution': category_distribution,
                'sync_status': 'success' if excel_count == total_active else 'warning'
            }
            
            return report
            
        except Exception as e:
            print(f"验证失败: {e}")
            import traceback
            print(traceback.format_exc())
            return None

def main():
    """主函数"""
    print("=== 话术库数据更新工具 ===")
    
    # 1. 分析差异
    print("\n步骤1: 分析数据差异")
    analysis_result = analyze_differences()
    if not analysis_result:
        print("❌ 差异分析失败，退出")
        return
    
    # 2. 更新话术内容
    print("\n步骤2: 更新话术内容")
    if not update_script_contents(analysis_result):
        print("❌ 更新话术内容失败，退出")
        return
    
    # 3. 处理新增话术
    print("\n步骤3: 处理新增话术")
    if not handle_new_scripts(analysis_result):
        print("❌ 新增话术失败，退出")
        return
    
    # 4. 重整分类体系
    print("\n步骤4: 重整分类体系")
    if not update_script_categories(analysis_result):
        print("❌ 更新分类失败，退出")
        return
    
    # 5. 标记删除话术
    print("\n步骤5: 标记删除话术")
    if not mark_deleted_scripts(analysis_result):
        print("❌ 标记删除失败，退出")
        return
    
    # 6. 验证和报告
    print("\n步骤6: 验证结果")
    report = validate_and_report(analysis_result)
    if report:
        print(f"\n=== 更新完成 ===")
        print(f"✅ 话术库更新成功")
        print(f"📊 最终统计: {report['db_active_count']} 条活跃话术, {report['db_inactive_count']} 条已删除")
        
        if report['sync_status'] == 'success':
            print("🎉 Excel与数据库完全同步")
        else:
            print("⚠️  建议进一步检查同步状态")
    else:
        print("❌ 验证失败")

if __name__ == "__main__":
    main()
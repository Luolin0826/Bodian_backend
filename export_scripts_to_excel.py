#!/usr/bin/env python3
"""
导出scripts表数据到Excel文件
包含ID、问题、答案和对应的分类信息，便于批量调整分类
"""
import os
import sys
import pandas as pd
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db
from app.models.script import Script
from app.models.script_category import ScriptCategory

def export_scripts_with_categories():
    """导出scripts表数据到Excel"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 开始导出scripts表数据...")
            
            # 查询所有scripts和对应的分类信息
            query = db.session.query(
                Script.id,
                Script.title,
                Script.question,
                Script.answer,
                Script.category_id,
                ScriptCategory.name.label('category_name'),
                Script.keywords,
                Script.is_active,
                Script.created_at,
                Script.updated_at
            ).outerjoin(
                ScriptCategory, Script.category_id == ScriptCategory.id
            ).filter(
                Script.is_active == True
            ).order_by(Script.id)
            
            results = query.all()
            
            if not results:
                print("❌ 没有找到任何scripts数据")
                return False
            
            # 转换为DataFrame
            data = []
            for row in results:
                data.append({
                    'ID': row.id,
                    '标题': row.title or '',
                    '问题': row.question or '',
                    '答案': row.answer or '',
                    '分类ID': row.category_id,
                    '分类名称': row.category_name or '未分类',
                    '关键词': row.keywords or '',
                    '是否启用': '是' if row.is_active else '否',
                    '创建时间': row.created_at.strftime('%Y-%m-%d %H:%M:%S') if row.created_at else '',
                    '更新时间': row.updated_at.strftime('%Y-%m-%d %H:%M:%S') if row.updated_at else ''
                })
            
            df = pd.DataFrame(data)
            
            # 生成文件名（包含时间戳）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'/workspace/scripts_export_{timestamp}.xlsx'
            
            # 创建Excel写入器
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # 主数据表
                df.to_excel(writer, sheet_name='Scripts数据', index=False)
                
                # 分类映射表
                categories_query = db.session.query(
                    ScriptCategory.id,
                    ScriptCategory.name,
                    ScriptCategory.parent_id,
                    ScriptCategory.description,
                    ScriptCategory.is_active
                ).filter(
                    ScriptCategory.is_active == True
                ).order_by(ScriptCategory.id)
                
                categories = categories_query.all()
                category_data = []
                for cat in categories:
                    category_data.append({
                        '分类ID': cat.id,
                        '分类名称': cat.name,
                        '父分类ID': cat.parent_id,
                        '描述': cat.description or '',
                        '是否启用': '是' if cat.is_active else '否'
                    })
                
                category_df = pd.DataFrame(category_data)
                category_df.to_excel(writer, sheet_name='分类对照表', index=False)
                
                # 统计信息表
                stats_data = []
                
                # 按分类统计数量
                category_stats = db.session.query(
                    ScriptCategory.name,
                    db.func.count(Script.id).label('count')
                ).outerjoin(
                    Script, ScriptCategory.id == Script.category_id
                ).filter(
                    Script.is_active == True
                ).group_by(
                    ScriptCategory.id, ScriptCategory.name
                ).order_by(
                    db.func.count(Script.id).desc()
                ).all()
                
                for stat in category_stats:
                    stats_data.append({
                        '分类名称': stat.name,
                        '脚本数量': stat.count
                    })
                
                # 未分类统计
                uncategorized_count = db.session.query(Script).filter(
                    Script.is_active == True,
                    Script.category_id.is_(None)
                ).count()
                
                if uncategorized_count > 0:
                    stats_data.append({
                        '分类名称': '未分类',
                        '脚本数量': uncategorized_count
                    })
                
                stats_df = pd.DataFrame(stats_data)
                stats_df.to_excel(writer, sheet_name='分类统计', index=False)
            
            print(f"✅ 导出完成！")
            print(f"📁 文件路径: {filename}")
            print(f"📊 导出数据统计:")
            print(f"   - 脚本总数: {len(data)}")
            print(f"   - 分类总数: {len(category_data)}")
            print(f"   - 未分类脚本: {uncategorized_count}")
            
            # 显示分类统计
            print(f"\n📈 各分类脚本数量:")
            for stat in stats_data[:10]:  # 显示前10个
                print(f"   - {stat['分类名称']}: {stat['脚本数量']}个")
            
            return True
            
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    # 检查pandas和openpyxl是否可用
    try:
        import pandas as pd
        import openpyxl
        print("📚 依赖库检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖库: {e}")
        print("请安装: pip install pandas openpyxl")
        sys.exit(1)
    
    success = export_scripts_with_categories()
    sys.exit(0 if success else 1)
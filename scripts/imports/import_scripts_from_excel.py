#!/usr/bin/env python3
"""
从Excel文件导入scripts表数据（用于批量更新分类）
支持批量更新scripts的category_id
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

def import_scripts_from_excel(excel_file):
    """从Excel文件导入并更新scripts数据"""
    app = create_app()
    
    with app.app_context():
        try:
            print(f"🔄 开始从Excel文件导入数据: {excel_file}")
            
            if not os.path.exists(excel_file):
                print(f"❌ 文件不存在: {excel_file}")
                return False
            
            # 读取Excel文件
            df = pd.read_excel(excel_file, sheet_name='Scripts数据')
            
            # 检查必需的列
            required_columns = ['ID', '分类ID']
            for col in required_columns:
                if col not in df.columns:
                    print(f"❌ Excel文件缺少必需列: {col}")
                    return False
            
            print(f"📊 准备更新 {len(df)} 条记录...")
            
            # 验证分类ID是否存在
            valid_categories = set()
            categories = ScriptCategory.query.filter(ScriptCategory.is_active == True).all()
            for cat in categories:
                valid_categories.add(cat.id)
            
            print(f"📋 可用分类ID: {sorted(valid_categories)}")
            
            updated_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                try:
                    script_id = row['ID']
                    new_category_id = row['分类ID']
                    
                    # 跳过空值
                    if pd.isna(new_category_id):
                        continue
                    
                    new_category_id = int(new_category_id)
                    
                    # 验证分类ID
                    if new_category_id not in valid_categories:
                        print(f"⚠️  跳过无效分类ID {new_category_id} (Script ID: {script_id})")
                        error_count += 1
                        continue
                    
                    # 查找并更新script
                    script = Script.query.get(script_id)
                    if not script:
                        print(f"⚠️  未找到Script ID: {script_id}")
                        error_count += 1
                        continue
                    
                    # 只在需要时更新
                    if script.category_id != new_category_id:
                        old_category_id = script.category_id
                        script.category_id = new_category_id
                        script.updated_at = datetime.utcnow()
                        
                        print(f"✅ 更新Script ID {script_id}: 分类 {old_category_id} → {new_category_id}")
                        updated_count += 1
                
                except Exception as e:
                    print(f"❌ 处理行 {index + 2} 时出错: {e}")
                    error_count += 1
                    continue
            
            # 提交更改
            if updated_count > 0:
                try:
                    db.session.commit()
                    print(f"\n🎉 更新完成！")
                    print(f"   - 成功更新: {updated_count} 条记录")
                    print(f"   - 错误/跳过: {error_count} 条记录")
                    
                    # 显示更新后的统计
                    show_category_stats()
                    
                except Exception as e:
                    db.session.rollback()
                    print(f"❌ 提交更改时出错: {e}")
                    return False
            else:
                print("ℹ️  没有需要更新的数据")
            
            return True
            
        except Exception as e:
            print(f"❌ 导入失败: {e}")
            import traceback
            traceback.print_exc()
            return False

def show_category_stats():
    """显示分类统计信息"""
    try:
        print(f"\n📈 更新后的分类统计:")
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
            print(f"   - {stat.name}: {stat.count}个")
            
        # 未分类统计
        uncategorized_count = db.session.query(Script).filter(
            Script.is_active == True,
            Script.category_id.is_(None)
        ).count()
        
        if uncategorized_count > 0:
            print(f"   - 未分类: {uncategorized_count}个")
    
    except Exception as e:
        print(f"❌ 获取统计信息失败: {e}")

def list_available_categories():
    """显示所有可用的分类"""
    app = create_app()
    
    with app.app_context():
        try:
            print("📋 所有可用分类:")
            categories = ScriptCategory.query.filter(
                ScriptCategory.is_active == True
            ).order_by(ScriptCategory.id).all()
            
            for cat in categories:
                parent_info = ""
                if cat.parent_id:
                    parent = ScriptCategory.query.get(cat.parent_id)
                    if parent:
                        parent_info = f" (父分类: {parent.name})"
                
                print(f"   - ID: {cat.id:2d} | {cat.name}{parent_info}")
        
        except Exception as e:
            print(f"❌ 获取分类信息失败: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法:")
        print(f"  {sys.argv[0]} <Excel文件路径>     # 导入Excel数据更新分类")
        print(f"  {sys.argv[0]} --categories       # 查看所有可用分类")
        print()
        print("示例:")
        print(f"  {sys.argv[0]} scripts_export_20250909_125330.xlsx")
        sys.exit(1)
    
    if sys.argv[1] == "--categories":
        list_available_categories()
        sys.exit(0)
    
    excel_file = sys.argv[1]
    
    # 检查pandas和openpyxl是否可用
    try:
        import pandas as pd
        import openpyxl
    except ImportError as e:
        print(f"❌ 缺少依赖库: {e}")
        print("请安装: pip install pandas openpyxl")
        sys.exit(1)
    
    success = import_scripts_from_excel(excel_file)
    sys.exit(0 if success else 1)
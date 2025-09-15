#!/usr/bin/env python3
"""
自动删除二级单位表中多余的"电网"单位记录
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, SecondaryUnit, QuickQueryInfo
from sqlalchemy.exc import SQLAlchemyError

def delete_redundant_grid_units():
    """删除多余的电网单位记录"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 查找需要删除的电网单位...")
            
            # 查找包含"电网"的单位，排除已有快捷查询数据的
            grid_units = SecondaryUnit.query.filter(
                SecondaryUnit.unit_name.like('%电网'),
                SecondaryUnit.is_active == True
            ).all()
            
            print(f"找到 {len(grid_units)} 个电网单位:")
            for unit in grid_units:
                # 检查是否有快捷查询数据
                has_quick_query = QuickQueryInfo.query.filter_by(unit_id=unit.unit_id).first() is not None
                print(f"  - {unit.unit_name} (ID: {unit.unit_id}, type: {unit.unit_type}, has_data: {has_quick_query})")
            
            # 找到没有快捷查询数据的电网单位进行删除
            units_to_delete = []
            for unit in grid_units:
                has_quick_query = QuickQueryInfo.query.filter_by(unit_id=unit.unit_id).first() is not None
                if not has_quick_query:
                    units_to_delete.append(unit)
            
            if not units_to_delete:
                print("✅ 没有找到需要删除的电网单位")
                return
            
            print(f"\n🗑️  自动删除 {len(units_to_delete)} 个没有数据的电网单位:")
            for unit in units_to_delete:
                print(f"  - {unit.unit_name} (ID: {unit.unit_id})")
            
            # 执行删除
            deleted_count = 0
            for unit in units_to_delete:
                try:
                    print(f"删除: {unit.unit_name} (ID: {unit.unit_id})")
                    db.session.delete(unit)
                    deleted_count += 1
                except Exception as e:
                    print(f"❌ 删除 {unit.unit_name} 失败: {e}")
                    db.session.rollback()
                    continue
            
            # 提交更改
            db.session.commit()
            print(f"\n✅ 成功删除 {deleted_count} 个电网单位记录")
            
            # 验证删除结果
            print("\n🔍 验证删除后的结果:")
            remaining_grid_units = SecondaryUnit.query.filter(
                SecondaryUnit.unit_name.like('%电网'),
                SecondaryUnit.is_active == True
            ).all()
            
            if remaining_grid_units:
                print("剩余的电网单位:")
                for unit in remaining_grid_units:
                    has_quick_query = QuickQueryInfo.query.filter_by(unit_id=unit.unit_id).first() is not None
                    print(f"  - {unit.unit_name} (ID: {unit.unit_id}, has_data: {has_quick_query})")
            else:
                print("✅ 所有多余的电网单位已清理完毕")
                
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"❌ 数据库操作失败: {e}")
        except Exception as e:
            print(f"❌ 操作失败: {e}")

if __name__ == '__main__':
    delete_redundant_grid_units()
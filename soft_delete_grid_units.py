#!/usr/bin/env python3
"""
软删除二级单位表中多余的"电网"单位记录 (设置is_active=False)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, SecondaryUnit, QuickQueryInfo
from sqlalchemy.exc import SQLAlchemyError

def soft_delete_redundant_grid_units():
    """软删除多余的电网单位记录"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 查找需要软删除的电网单位...")
            
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
            
            # 找到没有快捷查询数据的电网单位进行软删除
            units_to_soft_delete = []
            for unit in grid_units:
                has_quick_query = QuickQueryInfo.query.filter_by(unit_id=unit.unit_id).first() is not None
                if not has_quick_query:
                    units_to_soft_delete.append(unit)
            
            if not units_to_soft_delete:
                print("✅ 没有找到需要软删除的电网单位")
                return
            
            print(f"\n🗑️  软删除 {len(units_to_soft_delete)} 个没有数据的电网单位 (设置is_active=False):")
            for unit in units_to_soft_delete:
                print(f"  - {unit.unit_name} (ID: {unit.unit_id})")
            
            # 执行软删除
            soft_deleted_count = 0
            for unit in units_to_soft_delete:
                try:
                    print(f"软删除: {unit.unit_name} (ID: {unit.unit_id})")
                    unit.is_active = False
                    soft_deleted_count += 1
                except Exception as e:
                    print(f"❌ 软删除 {unit.unit_name} 失败: {e}")
                    db.session.rollback()
                    continue
            
            # 提交更改
            db.session.commit()
            print(f"\n✅ 成功软删除 {soft_deleted_count} 个电网单位记录")
            
            # 验证软删除结果
            print("\n🔍 验证软删除后的结果:")
            remaining_active_grid_units = SecondaryUnit.query.filter(
                SecondaryUnit.unit_name.like('%电网'),
                SecondaryUnit.is_active == True
            ).all()
            
            if remaining_active_grid_units:
                print("剩余的活跃电网单位:")
                for unit in remaining_active_grid_units:
                    has_quick_query = QuickQueryInfo.query.filter_by(unit_id=unit.unit_id).first() is not None
                    print(f"  - {unit.unit_name} (ID: {unit.unit_id}, has_data: {has_quick_query})")
            else:
                print("✅ 所有多余的电网单位已被软删除")
                
            # 显示被软删除的单位
            soft_deleted_units = SecondaryUnit.query.filter(
                SecondaryUnit.unit_name.like('%电网'),
                SecondaryUnit.is_active == False
            ).all()
            
            if soft_deleted_units:
                print(f"\n已软删除的电网单位 ({len(soft_deleted_units)} 个):")
                for unit in soft_deleted_units:
                    print(f"  - {unit.unit_name} (ID: {unit.unit_id}, is_active: {unit.is_active})")
                
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"❌ 数据库操作失败: {e}")
        except Exception as e:
            print(f"❌ 操作失败: {e}")

if __name__ == '__main__':
    soft_delete_redundant_grid_units()
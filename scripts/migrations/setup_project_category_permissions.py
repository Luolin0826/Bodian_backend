#!/usr/bin/env python3
"""
项目分类权限配置脚本
为现有角色设置默认的项目分类权限
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Role, ScriptCategory

def setup_project_category_permissions():
    """为现有角色设置默认的项目分类权限"""
    
    print("开始配置项目分类权限...")
    
    # 获取所有项目分类
    project_categories = ScriptCategory.query.filter_by(
        is_active=True,
        parent_id=None
    ).all()
    
    if not project_categories:
        print("警告: 未找到项目分类数据，请先确保项目分类已正确配置")
        return
    
    category_map = {cat.name: str(cat.id) for cat in project_categories}
    print(f"找到 {len(category_map)} 个项目分类: {list(category_map.keys())}")
    
    # 定义角色与项目分类的映射关系
    role_category_mapping = {
        'super_admin': ['all'],  # 超级管理员拥有所有权限
        'admin': ['all'],        # 管理员拥有所有权限
        'manager': ['all'],      # 管理者拥有所有权限
        'sales': [],             # 销售人员权限待定
        'teacher': [],           # 教师权限待定
        'viewer': [],            # 查看者权限待定
        'student': []            # 学生权限待定
    }
    
    # 根据角色名称推断权限
    def infer_permissions_by_role_name(role_name, display_name):
        """根据角色名称和显示名称推断项目分类权限"""
        name_lower = (role_name + ' ' + (display_name or '')).lower()
        permissions = []
        
        # 电网相关
        if any(keyword in name_lower for keyword in ['电网', '南网', '国网', 'grid', 'power']):
            permissions.extend([
                category_map.get('南网'),
                category_map.get('国网'),
                category_map.get('电气考研')
            ])
        
        # 考研相关
        if any(keyword in name_lower for keyword in ['考研', '408', 'graduate', 'exam']):
            if '408' in name_lower or '计算机' in name_lower:
                permissions.append(category_map.get('408'))
            elif '医学' in name_lower or '306' in name_lower:
                permissions.append(category_map.get('医学306'))
            else:
                # 通用考研权限
                permissions.extend([
                    category_map.get('408'),
                    category_map.get('医学306'),
                    category_map.get('电气考研')
                ])
        
        # 建筑考证相关
        if any(keyword in name_lower for keyword in ['建筑', '一建', '二建', 'construction']):
            permissions.append(category_map.get('一建二建考证'))
        
        # 移除None值并去重
        permissions = list(set(filter(None, permissions)))
        return permissions if permissions else ['all']  # 如果无法推断，给予全部权限
    
    # 获取所有角色
    roles = Role.query.all()
    updated_count = 0
    
    for role in roles:
        print(f"\n处理角色: {role.name} ({role.display_name})")
        
        # 初始化权限配置
        if not role.permissions:
            role.permissions = {}
        
        if 'data' not in role.permissions:
            role.permissions['data'] = {}
        
        # 检查是否已有项目分类权限配置
        existing_permissions = role.permissions['data'].get('project_category_permissions', [])
        if existing_permissions:
            print(f"  角色 {role.name} 已有项目分类权限: {existing_permissions}")
            continue
        
        # 获取权限配置
        if role.name in role_category_mapping:
            # 使用预定义映射
            permissions = role_category_mapping[role.name]
        else:
            # 根据角色名称推断
            permissions = infer_permissions_by_role_name(role.name, role.display_name)
        
        # 设置权限
        role.permissions['data']['project_category_permissions'] = permissions
        
        # 标记JSON字段为已修改（重要：SQLAlchemy需要知道JSON字段已被修改）
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(role, 'permissions')
        
        # 标记为已修改
        db.session.add(role)
        updated_count += 1
        
        if 'all' in permissions:
            print(f"  ✓ 已设置全部项目权限")
        else:
            category_names = []
            for perm in permissions:
                for name, cat_id in category_map.items():
                    if cat_id == perm:
                        category_names.append(name)
                        break
            print(f"  ✓ 已设置项目权限: {category_names}")
    
    # 保存更改
    if updated_count > 0:
        try:
            db.session.commit()
            print(f"\n成功更新了 {updated_count} 个角色的项目分类权限配置")
        except Exception as e:
            db.session.rollback()
            print(f"\n保存失败: {str(e)}")
            return False
    else:
        print("\n所有角色都已有项目分类权限配置，无需更新")
    
    return True

def verify_permissions():
    """验证权限配置是否正确"""
    print("\n验证权限配置...")
    
    roles = Role.query.all()
    for role in roles:
        if role.permissions and 'data' in role.permissions:
            project_perms = role.permissions['data'].get('project_category_permissions', [])
            if project_perms:
                print(f"角色 {role.name}: {project_perms}")
            else:
                print(f"角色 {role.name}: 无项目分类权限")
        else:
            print(f"角色 {role.name}: 权限配置为空")

def main():
    """主函数"""
    app = create_app()
    
    with app.app_context():
        print("项目分类权限配置脚本")
        print("=" * 50)
        
        # 设置权限
        success = setup_project_category_permissions()
        
        if success:
            # 验证权限
            verify_permissions()
            print("\n项目分类权限配置完成！")
        else:
            print("\n项目分类权限配置失败！")

if __name__ == '__main__':
    main()
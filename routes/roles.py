# app/routes/roles.py
from flask import Blueprint, request, jsonify
from app.models import db, Role, PermissionTemplate, User
from app.utils.auth_decorators import require_permission, log_operation
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

roles_bp = Blueprint('roles', __name__)

# ==================== 权限树结构 ====================

@roles_bp.route('/permissions/tree', methods=['GET'])
@jwt_required()
@require_permission('menu', 'system.role')
def get_permission_tree():
    """获取权限树结构"""
    try:
        # 菜单权限树
        menu_tree = [
            {
                "key": "dashboard",
                "title": "工作台",
                "description": "系统主页和概览信息",
                "icon": "DashboardOutlined",
                "level": "low",
                "risk": "safe"
            },
            {
                "key": "customer",
                "title": "客户管理",
                "description": "客户信息管理和维护",
                "icon": "UserOutlined",
                "level": "medium",
                "risk": "safe",
                "children": [
                    {
                        "key": "customer.list",
                        "title": "客户列表",
                        "description": "查看和管理客户信息",
                        "level": "medium",
                        "risk": "safe"
                    },
                    {
                        "key": "customer.follow",
                        "title": "跟进管理", 
                        "description": "客户跟进记录管理",
                        "level": "medium",
                        "risk": "safe"
                    }
                ]
            },
            {
                "key": "sales",
                "title": "销售管理",
                "description": "销售数据和统计管理",
                "icon": "ShoppingOutlined", 
                "level": "medium",
                "risk": "warning",
                "children": [
                    {
                        "key": "sales.record",
                        "title": "销售记录",
                        "description": "销售订单和记录",
                        "level": "medium",
                        "risk": "safe"
                    },
                    {
                        "key": "sales.stats",
                        "title": "销售统计",
                        "description": "销售数据分析和报表",
                        "level": "high",
                        "risk": "warning"
                    }
                ]
            },
            {
                "key": "system",
                "title": "系统设置",
                "description": "系统配置和管理",
                "icon": "SettingOutlined",
                "level": "high",
                "risk": "danger",
                "children": [
                    {
                        "key": "system.user",
                        "title": "用户管理",
                        "description": "用户账号管理",
                        "level": "high",
                        "risk": "warning"
                    },
                    {
                        "key": "system.department",
                        "title": "部门管理",
                        "description": "组织架构管理",
                        "level": "high",
                        "risk": "warning"
                    },
                    {
                        "key": "system.role",
                        "title": "角色权限",
                        "description": "角色和权限配置",
                        "level": "high",
                        "risk": "danger"
                    },
                    {
                        "key": "system.log",
                        "title": "操作日志",
                        "description": "系统操作记录",
                        "level": "medium",
                        "risk": "safe"
                    }
                ]
            }
        ]
        
        return jsonify({
            "menu": menu_tree,
            "operation_modules": get_operation_modules(),
            "data_scopes": get_data_scopes(),
            "sensitive_data": get_sensitive_data()
        })
    
    except Exception as e:
        return jsonify({'error': f'获取权限树失败: {str(e)}'}), 500

def get_operation_modules():
    """获取操作权限模块"""
    return [
        {
            "key": "user",
            "title": "用户操作",
            "icon": "UserOutlined",
            "permissions": [
                {"key": "create", "name": "新增用户", "description": "创建新用户账号", "risk": "warning"},
                {"key": "edit", "name": "编辑用户", "description": "修改用户信息", "risk": "warning"},
                {"key": "delete", "name": "删除用户", "description": "删除用户账号", "risk": "danger"},
                {"key": "reset_password", "name": "重置密码", "description": "重置用户登录密码", "risk": "danger"},
                {"key": "change_status", "name": "状态管理", "description": "启用或禁用用户", "risk": "warning"},
                {"key": "view_sensitive", "name": "查看敏感信息", "description": "查看手机号等敏感信息", "risk": "warning"}
            ]
        },
        {
            "key": "department",
            "title": "部门操作",
            "icon": "ApartmentOutlined",
            "permissions": [
                {"key": "create", "name": "新增部门", "description": "创建新部门", "risk": "warning"},
                {"key": "edit", "name": "编辑部门", "description": "修改部门信息", "risk": "warning"},
                {"key": "delete", "name": "删除部门", "description": "删除部门", "risk": "danger"},
                {"key": "transfer", "name": "转移部门", "description": "调整部门归属", "risk": "danger"}
            ]
        },
        {
            "key": "customer",
            "title": "客户操作", 
            "icon": "TeamOutlined",
            "permissions": [
                {"key": "create", "name": "新增客户", "description": "添加新客户", "risk": "safe"},
                {"key": "edit", "name": "编辑客户", "description": "修改客户信息", "risk": "safe"},
                {"key": "delete", "name": "删除客户", "description": "删除客户记录", "risk": "warning"},
                {"key": "assign", "name": "分配客户", "description": "将客户分配给其他人", "risk": "warning"},
                {"key": "export", "name": "导出客户", "description": "导出客户数据", "risk": "warning"}
            ]
        },
        {
            "key": "system",
            "title": "系统操作",
            "icon": "SettingOutlined",
            "permissions": [
                {"key": "backup", "name": "数据备份", "description": "执行系统数据备份", "risk": "danger"},
                {"key": "restore", "name": "数据恢复", "description": "恢复系统数据", "risk": "danger"},
                {"key": "config", "name": "系统配置", "description": "修改系统配置参数", "risk": "danger"},
                {"key": "clear_log", "name": "清理日志", "description": "清理系统操作日志", "risk": "danger"}
            ]
        }
    ]

def get_data_scopes():
    """获取数据范围选项"""
    return [
        {"key": "student_data", "name": "学生数据", "description": "学生信息和学习记录"},
        {"key": "sales_data", "name": "销售数据", "description": "销售订单和业绩统计"},
        {"key": "financial_data", "name": "财务数据", "description": "财务报表和收支记录"},
        {"key": "system_data", "name": "系统数据", "description": "系统配置和用户信息"},
        {"key": "log_data", "name": "日志数据", "description": "操作日志和审计记录"},
        {"key": "report_data", "name": "报表数据", "description": "各类统计报表数据"}
    ]

def get_sensitive_data():
    """获取敏感数据选项"""
    return [
        {"key": "phone", "name": "手机号码", "description": "用户和客户的手机号码"},
        {"key": "id_card", "name": "身份证号", "description": "身份证号码信息"},
        {"key": "bank_info", "name": "银行信息", "description": "银行卡号和账户信息"},
        {"key": "salary", "name": "薪资信息", "description": "员工薪资和绩效数据"},
        {"key": "commission", "name": "提成信息", "description": "销售提成和奖金数据"}
    ]

# ==================== 角色管理 ====================

@roles_bp.route('/', methods=['GET'])
@jwt_required()
@require_permission('menu', 'system.role')
def get_roles():
    """获取角色列表"""
    try:
        roles = Role.query.all()
        result = [role.to_dict() for role in roles]
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': f'获取角色列表失败: {str(e)}'}), 500

@roles_bp.route('/', methods=['POST'])
@jwt_required()
@require_permission('operation', 'role.create')
@log_operation('create', 'role', '创建角色')
def create_role():
    """创建角色"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['name', 'display_name', 'description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'缺少必需字段: {field}'}), 400
        
        # 检查角色名是否已存在
        existing_role = Role.query.filter_by(name=data['name']).first()
        if existing_role:
            return jsonify({'error': '角色名称已存在'}), 400
        
        # 创建角色
        role = Role(
            name=data['name'],
            display_name=data['display_name'],
            level=data.get('level', 1),
            description=data['description'],
            permissions=data.get('permissions', {}),
            is_system=data.get('is_system', False)
        )
        
        db.session.add(role)
        db.session.commit()
        
        return jsonify({
            'message': '角色创建成功',
            'data': role.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建角色失败: {str(e)}'}), 500

@roles_bp.route('/<role_name>/permissions', methods=['GET'])
@jwt_required()
@require_permission('menu', 'system.role')
def get_role_permissions(role_name):
    """获取特定角色的权限配置"""
    try:
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            return jsonify({'error': '角色不存在'}), 404
        
        return jsonify(role.permissions or {})
    
    except Exception as e:
        return jsonify({'error': f'获取角色权限失败: {str(e)}'}), 500

@roles_bp.route('/<role_name>/permissions', methods=['PUT'])
@jwt_required()
@require_permission('operation', 'role.edit_permissions')
@log_operation('update', 'role.permissions', '更新角色权限', sensitive=True)
def update_role_permissions(role_name):
    """更新角色权限配置"""
    try:
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            return jsonify({'error': '角色不存在'}), 404
        
        data = request.get_json()
        # 兼容两种数据格式：直接发送权限数据 或 包含在permissions字段中
        if 'permissions' in data:
            permissions = data.get('permissions', {})
        else:
            # 直接使用请求数据作为权限数据
            permissions = data
        
        # 权限验证 - 获取当前用户权限等级
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        current_user_level = get_user_role_level(current_user.role) if current_user else 1
        current_user_role = current_user.role if current_user else 'unknown'
        
        # 系统角色修改权限检查 - 只有超级管理员和系统管理员可以修改系统角色
        if role.is_system:
            if current_user_role not in ['super_admin', 'admin']:
                return jsonify({'error': '只有系统管理员及以上级别可以修改系统角色'}), 403
            
            # 特殊保护：只有超级管理员可以修改超级管理员角色
            if role_name == 'super_admin' and current_user_role != 'super_admin':
                return jsonify({'error': '只有超级管理员可以修改超级管理员角色'}), 403
        
        # 等级检查 - 但允许管理员修改系统角色（已经在上面检查过）
        if not role.is_system and role.level >= current_user_level:
            return jsonify({'error': '不能修改同级或更高级别的角色权限'}), 403
        
        # 高风险权限检查
        validate_high_risk_permissions(permissions, current_user_level)
        
        # 权限子集检查 - 防止权限提升
        if current_user_role != 'super_admin':
            current_user_role_obj = Role.query.filter_by(name=current_user_role).first()
            if current_user_role_obj and current_user_role_obj.permissions:
                validation_error = validate_permission_subset(permissions, current_user_role_obj.permissions, current_user_role)
                if validation_error:
                    return jsonify({'error': validation_error}), 403
        
        # 更新权限
        print(f"DEBUG: Updating permissions for role {role_name}")
        print(f"DEBUG: Original permissions: {role.permissions}")
        print(f"DEBUG: New permissions: {permissions}")
        
        role.permissions = permissions
        role.updated_at = datetime.utcnow()
        
        print(f"DEBUG: Role permissions after assignment: {role.permissions}")
        
        db.session.commit()
        
        # 验证保存是否成功
        updated_role = Role.query.filter_by(name=role_name).first()
        print(f"DEBUG: Permissions after commit: {updated_role.permissions}")
        
        return jsonify({'message': '权限配置更新成功'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新角色权限失败: {str(e)}'}), 500

@roles_bp.route('/<role_name>/users', methods=['GET']) 
@jwt_required()
@require_permission('menu', 'system.role')
def get_role_users(role_name):
    """获取角色下的用户列表"""
    try:
        # 检查角色是否存在
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            return jsonify({'error': '角色不存在'}), 404
        
        users = User.query.filter_by(role=role_name, is_active=True).all()
        
        result = []
        for user in users:
            user_data = {
                'id': user.id,
                'username': user.username,
                'real_name': user.real_name,
                'department_name': user.department.name if user.department else None,
                'email': user.email,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'is_active': user.is_active
            }
            result.append(user_data)
        
        return jsonify({
            'users': result,
            'total': len(result),
            'role_info': {
                'name': role_name,
                'display_name': role.display_name
            }
        })
    
    except Exception as e:
        return jsonify({'error': f'获取角色用户列表失败: {str(e)}'}), 500

# ==================== 辅助函数 ====================

def get_user_role_level(role_name):
    """获取用户角色等级"""
    role_levels = {
        'super_admin': 10,
        'admin': 8,
        'manager': 6,
        'sales': 3,
        'teacher': 3,
        'viewer': 1
    }
    return role_levels.get(role_name, 1)

# ==================== 权限模板 ====================

@roles_bp.route('/templates', methods=['GET'])
@jwt_required()
@require_permission('menu', 'system.role')
def get_permission_templates():
    """获取权限模板"""
    try:
        # 内置模板
        builtin_templates = [
            {
                "id": 1,
                "name": "销售员模板",
                "description": "适用于销售人员的基础权限配置",
                "role_type": "sales",
                "is_builtin": True,
                "permissions": get_sales_template_permissions()
            },
            {
                "id": 2,
                "name": "部门经理模板", 
                "description": "适用于部门管理人员的权限配置",
                "role_type": "manager",
                "is_builtin": True,
                "permissions": get_manager_template_permissions()
            },
            {
                "id": 3,
                "name": "系统管理员模板",
                "description": "适用于系统管理人员的权限配置", 
                "role_type": "admin",
                "is_builtin": True,
                "permissions": get_admin_template_permissions()
            }
        ]
        
        # 数据库中的自定义模板
        custom_templates = PermissionTemplate.query.all()
        custom_template_list = [template.to_dict() for template in custom_templates]
        
        return jsonify({
            "builtin": builtin_templates,
            "custom": custom_template_list
        })
    
    except Exception as e:
        return jsonify({'error': f'获取权限模板失败: {str(e)}'}), 500

@roles_bp.route('/<role_name>/permissions/import', methods=['POST'])
@jwt_required()
@require_permission('operation', 'role.edit_permissions')
@log_operation('update', 'role.permissions', '从模板导入权限')
def import_permissions_from_template(role_name):
    """从模板导入权限配置"""
    try:
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            return jsonify({'error': '角色不存在'}), 404
        
        data = request.get_json()
        template_name = data.get('template_name')
        
        template_permissions = get_template_permissions(template_name)
        if not template_permissions:
            return jsonify({'error': '模板不存在'}), 404
        
        role.permissions = template_permissions
        role.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': '权限模板导入成功'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'导入权限模板失败: {str(e)}'}), 500

@roles_bp.route('/validate-permissions', methods=['POST'])
@jwt_required()
@require_permission('menu', 'system.role')
def validate_permissions():
    """验证权限配置的合法性"""
    try:
        data = request.get_json()
        permissions = data.get('permissions', {})
        
        errors = []
        warnings = []
        
        # 检查权限冲突
        conflicts = check_permission_conflicts(permissions)
        if conflicts:
            errors.extend(conflicts)
        
        # 检查高风险权限
        high_risk = check_high_risk_permissions(permissions)
        if high_risk:
            warnings.extend(high_risk)
        
        # 检查必要权限
        missing_required = check_required_permissions(permissions)
        if missing_required:
            warnings.extend(missing_required)
        
        return jsonify({
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        })
    
    except Exception as e:
        return jsonify({'error': f'验证权限配置失败: {str(e)}'}), 500

# ==================== 辅助函数 ====================

def validate_high_risk_permissions(permissions, user_level):
    """验证高风险权限"""
    high_risk_ops = [
        "user.delete", "user.reset_password",
        "department.delete", "department.transfer", 
        "system.backup", "system.restore", "system.config"
    ]
    
    operation = permissions.get('operation', {})
    for module, perms in operation.items():
        if isinstance(perms, list):
            for perm in perms:
                perm_key = f"{module}.{perm}"
                if perm_key in high_risk_ops and user_level < 8:
                    raise ValueError(f"权限不足，无法分配高风险权限: {perm_key}")

def get_sales_template_permissions():
    """销售员权限模板"""
    return {
        "menu": ["dashboard", "customer", "customer.list", "customer.follow", "sales.record"],
        "operation": {
            "customer": ["create", "edit"],
            "sales": ["create", "edit"]
        },
        "data": {
            "scope": "self",
            "custom_scopes": [],
            "sensitive": []
        },
        "time": {
            "enable_login_time": True,
            "login_time_range": ["08:00", "20:00"],
            "login_weekdays": ["1", "2", "3", "4", "5", "6"],
            "session_timeout": 120,
            "max_sessions": 2
        }
    }

def get_manager_template_permissions():
    """部门经理权限模板"""
    return {
        "menu": [
            "dashboard", "customer", "customer.list", "customer.follow", 
            "sales", "sales.record", "sales.stats"
        ],
        "operation": {
            "customer": ["create", "edit", "delete", "assign"],
            "sales": ["create", "edit", "delete", "export"],
            "user": ["edit"]
        },
        "data": {
            "scope": "department",
            "custom_scopes": ["student_data", "sales_data"],
            "sensitive": ["phone"]
        },
        "time": {
            "enable_login_time": False,
            "session_timeout": 480,
            "max_sessions": 3
        }
    }

def get_admin_template_permissions():
    """系统管理员权限模板"""
    return {
        "menu": [
            "dashboard", "customer", "customer.list", "customer.follow",
            "sales", "sales.record", "sales.stats",
            "system", "system.user", "system.department", "system.log"
        ],
        "operation": {
            "user": ["create", "edit", "delete", "reset_password", "change_status", "view_sensitive"],
            "department": ["create", "edit", "delete", "transfer"],
            "customer": ["create", "edit", "delete", "assign", "export"],
            "sales": ["create", "edit", "delete", "export"],
            "system": ["backup", "config", "clear_log"]
        },
        "data": {
            "scope": "all",
            "custom_scopes": ["student_data", "sales_data", "financial_data", "system_data", "log_data"],
            "sensitive": ["phone", "id_card", "salary"]
        },
        "time": {
            "enable_login_time": False,
            "session_timeout": 480,
            "max_sessions": 5
        }
    }

def get_template_permissions(template_name):
    """根据模板名获取权限配置"""
    templates = {
        "销售员模板": get_sales_template_permissions(),
        "部门经理模板": get_manager_template_permissions(),
        "系统管理员模板": get_admin_template_permissions()
    }
    return templates.get(template_name)

def check_permission_conflicts(permissions):
    """检查权限冲突"""
    conflicts = []
    
    # 检查菜单权限和操作权限的一致性
    menu_perms = set(permissions.get('menu', []))
    operation = permissions.get('operation', {})
    
    # 如果有系统操作权限，必须有系统菜单权限
    if operation.get('system') and 'system' not in menu_perms:
        conflicts.append("拥有系统操作权限但缺少系统菜单权限")
    
    return conflicts

def check_high_risk_permissions(permissions):
    """检查高风险权限"""
    warnings = []
    
    high_risk_ops = ["delete", "reset_password", "backup", "restore", "config"]
    operation = permissions.get('operation', {})
    
    for module, perms in operation.items():
        if isinstance(perms, list):
            for perm in perms:
                if perm in high_risk_ops:
                    warnings.append(f"包含高风险操作权限: {module}.{perm}")
    
    return warnings

def check_required_permissions(permissions):
    """检查必要权限"""
    warnings = []
    
    # 检查是否有基础菜单权限
    menu_perms = permissions.get('menu', [])
    if not menu_perms:
        warnings.append("未配置任何菜单权限，用户可能无法访问系统功能")
    elif 'dashboard' not in menu_perms:
        warnings.append("建议添加工作台菜单权限作为用户主页")
    
    return warnings

def validate_permission_subset(target_permissions, current_user_permissions, current_user_role):
    """
    验证目标权限是否为当前用户权限的子集
    防止权限提升攻击 - 用户只能授予自己拥有的权限
    """
    
    # 1. 验证菜单权限
    target_menu = set(target_permissions.get('menu', []))
    current_menu = set(current_user_permissions.get('menu', []))
    
    unauthorized_menu = target_menu - current_menu
    if unauthorized_menu:
        return f"尝试授予超出权限范围的菜单权限: {', '.join(unauthorized_menu)}"
    
    # 2. 验证操作权限
    target_operations = target_permissions.get('operation', {})
    current_operations = current_user_permissions.get('operation', {})
    
    for module, target_ops in target_operations.items():
        if not isinstance(target_ops, list):
            continue
            
        current_ops = set(current_operations.get(module, []))
        target_ops_set = set(target_ops)
        
        unauthorized_ops = target_ops_set - current_ops
        if unauthorized_ops:
            return f"尝试授予超出权限范围的操作权限: {module}.{', '.join(unauthorized_ops)}"
    
    # 3. 验证数据权限
    target_data = target_permissions.get('data', {})
    current_data = current_user_permissions.get('data', {})
    
    # 验证数据范围权限
    target_scope = target_data.get('scope', 'none')
    current_scope = current_data.get('scope', 'none')
    
    # 定义权限范围等级: none < self < department < all
    scope_levels = {'none': 0, 'self': 1, 'department': 2, 'all': 3}
    
    target_scope_level = scope_levels.get(target_scope, 0)
    current_scope_level = scope_levels.get(current_scope, 0)
    
    if target_scope_level > current_scope_level:
        return f"尝试授予超出权限范围的数据访问权限: {target_scope} (当前最高: {current_scope})"
    
    # 验证自定义数据范围
    target_custom_scopes = set(target_data.get('custom_scopes', []))
    current_custom_scopes = set(current_data.get('custom_scopes', []))
    
    unauthorized_scopes = target_custom_scopes - current_custom_scopes
    if unauthorized_scopes:
        return f"尝试授予超出权限范围的自定义数据范围: {', '.join(unauthorized_scopes)}"
    
    # 验证敏感数据权限
    target_sensitive = set(target_data.get('sensitive', []))
    current_sensitive = set(current_data.get('sensitive', []))
    
    unauthorized_sensitive = target_sensitive - current_sensitive
    if unauthorized_sensitive:
        return f"尝试授予超出权限范围的敏感数据权限: {', '.join(unauthorized_sensitive)}"
    
    # 4. 验证时间限制权限（防止绕过时间限制）
    target_time = target_permissions.get('time', {})
    current_time = current_user_permissions.get('time', {})
    
    # 检查会话超时时间（不能超过当前用户的设置）
    target_timeout = target_time.get('session_timeout', 60)
    current_timeout = current_time.get('session_timeout', 60)
    
    if target_timeout > current_timeout:
        return f"尝试设置超出权限范围的会话超时时间: {target_timeout}分钟 (当前最高: {current_timeout}分钟)"
    
    # 检查最大会话数（不能超过当前用户的设置）
    target_sessions = target_time.get('max_sessions', 1)
    current_sessions = current_time.get('max_sessions', 1)
    
    if target_sessions > current_sessions:
        return f"尝试设置超出权限范围的最大会话数: {target_sessions} (当前最高: {current_sessions})"
    
    # 检查登录时间限制（如果当前用户有时间限制，被修改的角色不能取消时间限制）
    current_time_restriction = current_time.get('enable_login_time', True)
    target_time_restriction = target_time.get('enable_login_time', True)
    
    if current_time_restriction and not target_time_restriction:
        return "不能为角色取消登录时间限制，因为当前用户受时间限制约束"
    
    return None  # 验证通过
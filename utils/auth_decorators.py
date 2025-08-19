# app/utils/auth_decorators.py
from functools import wraps
from flask import jsonify, request, g
from flask_jwt_extended import get_current_user, verify_jwt_in_request
from app.models import Role, OperationLog

def require_permission(permission_type, permission_name):
    """
    权限控制装饰器
    permission_type: 'menu', 'operation', 'data'
    permission_name: 具体权限名称
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # 验证JWT token
                verify_jwt_in_request()
                current_user = get_current_user()
                
                if not current_user or not current_user.is_active:
                    return jsonify({'code': 401, 'message': '用户未登录或已被禁用'}), 401
                
                # 超级管理员拥有所有权限
                if current_user.role == 'super_admin':
                    g.current_user = current_user
                    return f(*args, **kwargs)
                
                # 获取用户角色权限
                role = Role.query.filter_by(name=current_user.role, is_active=True).first()
                if not role:
                    return jsonify({'code': 403, 'message': '用户角色不存在或已被禁用'}), 403
                
                # 检查权限
                if not role.has_permission(permission_type, permission_name):
                    return jsonify({'code': 403, 'message': '权限不足'}), 403
                
                g.current_user = current_user
                return f(*args, **kwargs)
                
            except Exception as e:
                return jsonify({'code': 500, 'message': f'权限验证失败: {str(e)}'}), 500
        
        return decorated_function
    return decorator

def require_role(required_roles):
    """
    角色控制装饰器
    required_roles: 允许的角色列表
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
                current_user = get_current_user()
                
                if not current_user or not current_user.is_active:
                    return jsonify({'code': 401, 'message': '用户未登录或已被禁用'}), 401
                
                if isinstance(required_roles, str):
                    roles = [required_roles]
                else:
                    roles = required_roles
                
                if current_user.role not in roles:
                    return jsonify({'code': 403, 'message': '角色权限不足'}), 403
                
                g.current_user = current_user
                return f(*args, **kwargs)
                
            except Exception as e:
                return jsonify({'code': 500, 'message': f'角色验证失败: {str(e)}'}), 500
        
        return decorated_function
    return decorator

def log_operation(action, resource, description=None, sensitive=False):
    """
    操作日志装饰器
    action: 操作类型
    resource: 操作对象
    description: 操作描述
    sensitive: 是否敏感操作
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
                current_user = get_current_user()
                
                # 执行原函数
                result = f(*args, **kwargs)
                
                # 记录操作日志
                if current_user:
                    # 构建操作描述
                    if description:
                        log_description = description
                    else:
                        log_description = f"{action} {resource}"
                    
                    # 如果是敏感操作，自动判断
                    is_sensitive = sensitive or OperationLog.is_sensitive_action(action, resource)
                    
                    OperationLog.create_log(
                        user=current_user,
                        action=action,
                        resource=resource,
                        description=log_description,
                        request=request,
                        sensitive=is_sensitive
                    )
                
                return result
                
            except Exception as e:
                # 如果日志记录失败，不影响主业务
                print(f"记录操作日志失败: {str(e)}")
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def data_scope_filter(query, model, user_field='user_id', department_field='department_id'):
    """
    数据权限过滤器
    query: SQLAlchemy查询对象
    model: 数据模型
    user_field: 用户字段名
    department_field: 部门字段名
    """
    try:
        current_user = g.get('current_user')
        if not current_user:
            return query.filter(False)  # 返回空结果
        
        # 超级管理员可以查看所有数据
        if current_user.role == 'super_admin':
            return query
        
        # 获取用户角色权限
        role = Role.query.filter_by(name=current_user.role, is_active=True).first()
        if not role or not role.permissions:
            return query.filter(False)
        
        data_permissions = role.permissions.get('data', {})
        scope = data_permissions.get('scope', 'none')
        
        if scope == 'all':
            # 可以查看所有数据
            return query
        elif scope == 'department':
            # 只能查看本部门数据
            if hasattr(model, department_field) and current_user.department_id:
                return query.filter(getattr(model, department_field) == current_user.department_id)
        elif scope == 'self':
            # 只能查看自己的数据
            if hasattr(model, user_field):
                return query.filter(getattr(model, user_field) == current_user.id)
        
        # 默认不返回任何数据
        return query.filter(False)
        
    except Exception as e:
        print(f"数据权限过滤失败: {str(e)}")
        return query.filter(False)

def mask_sensitive_fields(data, user=None):
    """
    敏感字段脱敏处理
    data: 要处理的数据（字典或字典列表）
    user: 当前用户
    """
    if not user:
        user = g.get('current_user')
    
    if not user:
        return data
    
    # 超级管理员不脱敏
    if user.role == 'super_admin':
        return data
    
    # 获取用户角色权限
    role = Role.query.filter_by(name=user.role, is_active=True).first()
    if not role or not role.permissions:
        return data
    
    data_permissions = role.permissions.get('data', {})
    sensitive_fields = data_permissions.get('sensitive', [])
    
    if '*' in sensitive_fields:
        # 脱敏所有敏感字段
        sensitive_fields = ['phone', 'email', 'address', 'id_card']
    
    def mask_field(value, field_name):
        """脱敏具体字段"""
        if field_name == 'phone' and value:
            return value[:3] + '****' + value[-4:] if len(value) >= 7 else '****'
        elif field_name == 'email' and value:
            parts = value.split('@')
            if len(parts) == 2:
                return parts[0][:2] + '****@' + parts[1]
            return '****'
        elif field_name in ['address', 'id_card'] and value:
            return value[:4] + '****' if len(value) > 4 else '****'
        return value
    
    def process_item(item):
        """处理单个数据项"""
        if not isinstance(item, dict):
            return item
        
        result = item.copy()
        for field in sensitive_fields:
            if field in result:
                result[field] = mask_field(result[field], field)
        
        return result
    
    if isinstance(data, list):
        return [process_item(item) for item in data]
    else:
        return process_item(data)
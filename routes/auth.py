# app/routes/auth.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from datetime import datetime
from app.models import db, User, Role, UserLoginLog
from app.services.auth_service import AuthService
from app.utils.timezone import now
from app.utils.ip_location import get_ip_location_text
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """用户登录"""
    # 处理预检请求
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # 获取请求信息
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    
    if not username or not password:
        return jsonify({'message': '用户名和密码不能为空'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    # 记录登录失败 - 用户不存在
    if not user:
        # 创建一个临时用户记录用于日志（可选）
        UserLoginLog.create_login_log(
            user_id=0,  # 用0表示用户不存在
            ip_address=ip_address,
            user_agent=user_agent,
            status='failed',
            failure_reason='用户不存在',
            location=get_ip_location_text(ip_address)
        )
        return jsonify({'message': '用户名或密码错误'}), 401
    
    # 记录登录失败 - 密码错误
    if not user.check_password(password):
        UserLoginLog.create_login_log(
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            status='failed',
            failure_reason='密码错误',
            location=get_ip_location_text(ip_address)
        )
        return jsonify({'message': '用户名或密码错误'}), 401
    
    # 记录登录失败 - 账号被禁用
    if not user.is_active:
        UserLoginLog.create_login_log(
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            status='failed',
            failure_reason='账号已被禁用',
            location=get_ip_location_text(ip_address)
        )
        return jsonify({'message': '账号已被禁用'}), 403
    
    # 生成会话ID
    session_id = str(uuid.uuid4())
    
    # 记录登录成功
    UserLoginLog.create_login_log(
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        status='success',
        session_id=session_id,
        location=get_ip_location_text(ip_address)
    )
    
    # 更新最后登录时间
    user.last_login = now()
    db.session.commit()
    
    # 创建访问令牌 - 使用字符串格式的user_id，并在payload中包含session_id
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={'session_id': session_id}
    )
    
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict(),
        'session_id': session_id
    }), 200

@auth_bp.route('/logout', methods=['POST', 'OPTIONS'])
@jwt_required()
def logout():
    """用户登出"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        # 从JWT token中获取session_id
        from flask_jwt_extended import get_jwt
        claims = get_jwt()
        session_id = claims.get('session_id')
        
        if session_id:
            # 更新登出时间
            UserLoginLog.update_logout_time(session_id)
    except Exception as e:
        # 登出时记录日志失败不应该影响登出过程
        current_app.logger.warning(f"更新登出时间失败: {str(e)}")
    
    return jsonify({'message': '登出成功'}), 200

@auth_bp.route('/refresh', methods=['POST', 'OPTIONS'])
@jwt_required(refresh=True)
def refresh():
    """刷新访问令牌"""
    if request.method == 'OPTIONS':
        return '', 200
    current_user_id = int(get_jwt_identity())
    access_token = create_access_token(identity=str(current_user_id))
    return jsonify({'access_token': access_token}), 200

@auth_bp.route('/me', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_current_user():
    """获取当前用户信息和权限"""
    if request.method == 'OPTIONS':
        return '', 200
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    # 获取用户角色权限
    permissions = get_user_permissions(user.role)
    
    # 构建返回数据
    user_data = user.to_dict()
    user_data['permissions'] = permissions
    
    return jsonify(user_data), 200

def get_user_permissions(role_name):
    """获取用户角色权限"""
    # 超级管理员和管理员的默认全部权限
    if role_name in ['super_admin', 'admin']:
        return {
            'menu': [
                '/dashboard',
                '/customer', '/customer/list', '/customer/follow', '/customer/reminders', '/customer/analytics',
                '/sales', '/sales/record', '/sales/stats',
                '/script',
                '/knowledge', 
                '/user-center', '/user-center/profile', '/user-center/preferences', '/user-center/security',
                '/system', '/system/user', '/system/department', '/system/role', '/system/log', '/system/test-api'
            ],
            'operation': {
                'dashboard': ['view', 'export'],
                'customer': ['create', 'read', 'update', 'delete', 'view_sensitive', 'import', 'export', 'assign', 'follow_up', 'reminder', 'analytics'],
                'sales': ['create', 'read', 'update', 'delete', 'approve', 'stats', 'commission'],
                'script': ['create', 'read', 'update', 'delete', 'copy', 'category_manage', 'export'],
                'knowledge': ['create', 'read', 'update', 'delete', 'copy', 'publish', 'category_manage', 'approve', 'export'],
                'system': ['user_manage', 'dept_manage', 'role_manage', 'permission_config', 'log_manage', 'system_config', 'backup']
            },
            'data': {
                'scope': 'all',
                'custom_scopes': [],
                'sensitive': ['all']
            }
        }
    
    # 从数据库获取角色权限
    role = Role.query.filter_by(name=role_name).first()
    if role and role.permissions:
        return role.permissions
    
    # 默认权限（基础权限）
    return {
        'menu': ['/dashboard', '/user-center/profile'],
        'operation': {},
        'data': {
            'scope': 'self',
            'custom_scopes': [],
            'sensitive': []
        }
    }

@auth_bp.route('/permissions', methods=['GET'])
@jwt_required()
def get_user_permissions_api():
    """获取当前用户权限（独立接口）"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    permissions = get_user_permissions(user.role)
    return jsonify({'permissions': permissions}), 200

@auth_bp.route('/login-logs', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_login_logs():
    """获取登录日志"""
    if request.method == 'OPTIONS':
        return '', 200
    
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    status = request.args.get('status')  # success/failed
    days = request.args.get('days', 30, type=int)  # 最近多少天
    
    # 构建查询
    query = UserLoginLog.query.filter_by(user_id=current_user_id)
    
    # 时间范围过滤
    if days > 0:
        from datetime import timedelta
        start_date = now() - timedelta(days=days)
        query = query.filter(UserLoginLog.login_time >= start_date)
    
    # 状态过滤
    if status:
        query = query.filter(UserLoginLog.status == status)
    
    # 排序和分页
    query = query.order_by(UserLoginLog.login_time.desc())
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)
    
    # 构建返回数据
    login_logs = []
    for log in pagination.items:
        log_data = log.to_dict()
        # 添加用户信息（当前用户的日志，所以可以直接添加）
        log_data['username'] = user.username
        log_data['real_name'] = user.real_name
        login_logs.append(log_data)
    
    return jsonify({
        'login_logs': login_logs,
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next
        }
    }), 200

@auth_bp.route('/login-stats', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_login_stats():
    """获取登录统计"""
    if request.method == 'OPTIONS':
        return '', 200
    
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    # 获取查询参数
    days = request.args.get('days', 30, type=int)
    
    # 获取统计数据
    stats = UserLoginLog.get_user_login_stats(current_user_id, days)
    
    return jsonify({
        'stats': stats,
        'period_days': days
    }), 200

# 管理员接口 - 查看所有用户登录日志
@auth_bp.route('/admin/login-logs', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_all_login_logs():
    """管理员获取所有用户登录日志"""
    if request.method == 'OPTIONS':
        return '', 200
    
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user or user.role not in ['super_admin', 'admin']:
        return jsonify({'message': '权限不足'}), 403
    
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    status = request.args.get('status')  # success/failed
    days = request.args.get('days', 30, type=int)  # 最近多少天
    user_id = request.args.get('user_id', type=int)  # 特定用户
    keyword = request.args.get('keyword')  # 用户名关键字搜索
    
    # 构建查询
    query = UserLoginLog.query
    
    # 用户过滤
    if user_id:
        query = query.filter(UserLoginLog.user_id == user_id)
    
    # 时间范围过滤
    if days > 0:
        from datetime import timedelta
        start_date = now() - timedelta(days=days)
        query = query.filter(UserLoginLog.login_time >= start_date)
    
    # 状态过滤
    if status:
        query = query.filter(UserLoginLog.status == status)
    
    # 关键字搜索（通过用户名）
    if keyword:
        users = User.query.filter(
            (User.username.like(f'%{keyword}%')) |
            (User.real_name.like(f'%{keyword}%'))
        ).all()
        user_ids = [u.id for u in users]
        if user_ids:
            query = query.filter(UserLoginLog.user_id.in_(user_ids))
        else:
            # 没有匹配的用户，返回空结果
            return jsonify({
                'login_logs': [],
                'pagination': {
                    'page': page,
                    'pages': 0,
                    'per_page': page_size,
                    'total': 0,
                    'has_prev': False,
                    'has_next': False
                }
            }), 200
    
    # 排序和分页
    query = query.order_by(UserLoginLog.login_time.desc())
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)
    
    # 构建返回数据，包含用户信息
    login_logs = []
    for log in pagination.items:
        log_data = log.to_dict()
        # 添加用户信息
        if log.user_id > 0:  # 排除用户不存在的情况
            log_user = User.query.get(log.user_id)
            if log_user:
                log_data['username'] = log_user.username
                log_data['real_name'] = log_user.real_name
                log_data['department_name'] = log_user.department.name if log_user.department else None
        login_logs.append(log_data)
    
    return jsonify({
        'login_logs': login_logs,
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next
        }
    }), 200
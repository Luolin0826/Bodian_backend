# app/routes/auth.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from datetime import datetime
from app.models import db, User
from app.services.auth_service import AuthService
from app.utils.timezone import now

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
    
    if not username or not password:
        return jsonify({'message': '用户名和密码不能为空'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return jsonify({'message': '用户名或密码错误'}), 401
    
    if not user.check_password(password):
        return jsonify({'message': '用户名或密码错误'}), 401
    
    if not user.is_active:
        return jsonify({'message': '账号已被禁用'}), 403
    
    # 更新最后登录时间
    user.last_login = now()
    db.session.commit()
    
    # 创建访问令牌 - 使用字符串格式的user_id
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/logout', methods=['POST', 'OPTIONS'])
def logout():
    """用户登出"""
    if request.method == 'OPTIONS':
        return '', 200
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
    """获取当前用户信息"""
    if request.method == 'OPTIONS':
        return '', 200
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if user:
        return jsonify(user.to_dict()), 200
    
    return jsonify({'message': '用户不存在'}), 404
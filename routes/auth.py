# app/routes/auth.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from datetime import datetime
from app.models import db, User
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': '用户名和密码不能为空'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        if not user.is_active:
            return jsonify({'message': '账号已被禁用'}), 403
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # 创建访问令牌和刷新令牌
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200
    
    return jsonify({'message': '用户名或密码错误'}), 401

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新访问令牌"""
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    return jsonify({'access_token': access_token}), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """获取当前用户信息"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user:
        return jsonify(user.to_dict()), 200
    
    return jsonify({'message': '用户不存在'}), 404
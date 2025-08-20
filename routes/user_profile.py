# app/routes/user_profile.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, User, UserLoginLog
from app.utils.timezone import now
import bcrypt

user_profile_bp = Blueprint('user_profile', __name__)

@user_profile_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取用户个人信息"""
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    
    # 获取登录统计
    login_stats = UserLoginLog.get_user_login_stats(user_id)
    
    # 角色显示名映射
    role_display_names = {
        'super_admin': '超级管理员',
        'admin': '系统管理员',
        'manager': '管理员',
        'sales': '销售',
        'teacher': '教师',
        'viewer': '查看者'
    }
    
    # 获取部门信息
    department_name = None
    if user.department_id:
        from app.models.department import Department
        department = Department.query.get(user.department_id)
        if department:
            department_name = department.name
    
    data = {
        'id': user.id,
        'username': user.username,
        'real_name': user.real_name,
        'email': user.email,
        'phone': user.phone,
        'avatar': user.avatar,
        'role': user.role,
        'role_display_name': role_display_names.get(user.role, user.role),
        'department_id': user.department_id,
        'department_name': department_name,
        'employee_no': user.employee_no,
        'hire_date': user.hire_date.isoformat() if user.hire_date else None,
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'login_count': login_stats.get('total_logins', 0),
        'is_active': user.is_active,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'updated_at': user.updated_at.isoformat() if user.updated_at else None
    }
    
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': data
    })

@user_profile_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新用户个人信息"""
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    # 允许更新的字段
    allowed_fields = ['real_name', 'email', 'phone', 'avatar']
    
    try:
        # 验证数据
        if 'email' in data and data['email']:
            # 简单的邮箱格式验证
            import re
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data['email']):
                return jsonify({
                    'code': 400,
                    'message': '邮箱格式不正确'
                }), 400
            
            # 检查邮箱是否已被其他用户使用
            existing_user = User.query.filter(
                User.email == data['email'],
                User.id != user_id
            ).first()
            if existing_user:
                return jsonify({
                    'code': 400,
                    'message': '邮箱已被其他用户使用'
                }), 400
        
        if 'phone' in data and data['phone']:
            # 手机号格式验证
            import re
            if not re.match(r'^1[3-9]\d{9}$', data['phone']):
                return jsonify({
                    'code': 400,
                    'message': '手机号格式不正确'
                }), 400
        
        # 更新字段
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        user.updated_at = now()
        db.session.commit()
        
        # 记录操作日志
        from app.models.operation_log import OperationLog
        OperationLog.create_log(
            user=user,
            action='update_profile',
            resource='user_profile',
            description='更新个人信息',
            request=request,
            resource_id=user_id
        )
        
        return jsonify({
            'code': 0,
            'message': '个人信息更新成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'更新失败: {str(e)}'
        }), 500

@user_profile_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """修改密码"""
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    # 验证请求数据
    required_fields = ['old_password', 'new_password', 'confirm_password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                'code': 400,
                'message': f'{field} 不能为空'
            }), 400
    
    # 验证旧密码
    if not user.check_password(data['old_password']):
        return jsonify({
            'code': 400,
            'message': '旧密码错误'
        }), 400
    
    # 验证新密码和确认密码
    if data['new_password'] != data['confirm_password']:
        return jsonify({
            'code': 400,
            'message': '新密码和确认密码不一致'
        }), 400
    
    # 密码强度验证
    if len(data['new_password']) < 6:
        return jsonify({
            'code': 400,
            'message': '密码长度不能少于6位'
        }), 400
    
    # 新密码不能和旧密码相同
    if data['new_password'] == data['old_password']:
        return jsonify({
            'code': 400,
            'message': '新密码不能与旧密码相同'
        }), 400
    
    try:
        # 更新密码
        user.set_password(data['new_password'])
        user.updated_at = now()
        db.session.commit()
        
        # 记录操作日志
        from app.models.operation_log import OperationLog
        OperationLog.create_log(
            user=user,
            action='change_password',
            resource='user_profile',
            description='修改密码',
            request=request,
            resource_id=user_id,
            sensitive=True
        )
        
        return jsonify({
            'code': 0,
            'message': '密码修改成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'密码修改失败: {str(e)}'
        }), 500
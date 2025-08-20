# app/routes/user_preferences.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, UserPreferences
from app.models.operation_log import OperationLog

user_preferences_bp = Blueprint('user_preferences', __name__)

@user_preferences_bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_preferences():
    """获取用户偏好设置"""
    user_id = int(get_jwt_identity())
    
    # 获取或创建用户偏好设置
    preferences = UserPreferences.query.filter_by(user_id=user_id).first()
    if not preferences:
        preferences = UserPreferences.create_default(user_id)
    
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': preferences.to_dict()
    })

@user_preferences_bp.route('/preferences', methods=['PUT'])
@jwt_required()
def update_preferences():
    """更新用户偏好设置"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data:
        return jsonify({
            'code': 400,
            'message': '请求数据不能为空'
        }), 400
    
    try:
        # 获取或创建用户偏好设置
        preferences = UserPreferences.query.filter_by(user_id=user_id).first()
        if not preferences:
            preferences = UserPreferences.create_default(user_id)
        
        # 验证数据格式
        valid_categories = ['appearance', 'notification', 'security', 'workspace']
        
        # 验证每个类别的字段
        validation_rules = {
            'appearance': {
                'theme_mode': ['light', 'dark', 'auto'],
                'sidebar_collapsed': bool,
                'show_breadcrumb': bool,
                'language': str,
                'font_size': ['small', 'medium', 'large']
            },
            'notification': {
                'system_notification': bool,
                'email_notification': bool,
                'sound_notification': bool,
                'browser_notification': bool
            },
            'security': {
                'auto_logout_time': int,  # 分钟，0表示永不
                'session_timeout': int,
                'enable_two_factor': bool
            },
            'workspace': {
                'default_page': str,
                'items_per_page': int,
                'date_format': str,
                'time_format': ['12h', '24h']
            }
        }
        
        # 验证数据
        for category, settings in data.items():
            if category not in valid_categories:
                return jsonify({
                    'code': 400,
                    'message': f'无效的设置类别: {category}'
                }), 400
            
            if not isinstance(settings, dict):
                return jsonify({
                    'code': 400,
                    'message': f'设置类别 {category} 的值必须是对象'
                }), 400
            
            # 验证每个字段
            for key, value in settings.items():
                if key not in validation_rules[category]:
                    return jsonify({
                        'code': 400,
                        'message': f'无效的设置项: {category}.{key}'
                    }), 400
                
                expected_type = validation_rules[category][key]
                
                # 类型验证
                if isinstance(expected_type, list):
                    # 枚举值验证
                    if value not in expected_type:
                        return jsonify({
                            'code': 400,
                            'message': f'{category}.{key} 的值必须是 {expected_type} 中的一个'
                        }), 400
                elif isinstance(expected_type, type):
                    # 类型验证
                    if not isinstance(value, expected_type):
                        return jsonify({
                            'code': 400,
                            'message': f'{category}.{key} 的值类型不正确'
                        }), 400
        
        # 特殊验证
        if 'security' in data:
            security_settings = data['security']
            
            # 自动登出时间验证
            if 'auto_logout_time' in security_settings:
                auto_logout_time = security_settings['auto_logout_time']
                if auto_logout_time < 0 or auto_logout_time > 1440:  # 最大24小时
                    return jsonify({
                        'code': 400,
                        'message': '自动登出时间必须在0-1440分钟之间'
                    }), 400
            
            # 会话超时时间验证
            if 'session_timeout' in security_settings:
                session_timeout = security_settings['session_timeout']
                if session_timeout < 5 or session_timeout > 480:  # 5分钟到8小时
                    return jsonify({
                        'code': 400,
                        'message': '会话超时时间必须在5-480分钟之间'
                    }), 400
        
        if 'workspace' in data:
            workspace_settings = data['workspace']
            
            # 每页条数验证
            if 'items_per_page' in workspace_settings:
                items_per_page = workspace_settings['items_per_page']
                if items_per_page < 10 or items_per_page > 100:
                    return jsonify({
                        'code': 400,
                        'message': '每页条数必须在10-100之间'
                    }), 400
        
        # 记录旧值用于日志
        old_preferences = preferences.to_dict()
        
        # 更新偏好设置
        preferences.update_from_dict(data)
        db.session.commit()
        
        # 记录操作日志
        changes = {}
        for category, settings in data.items():
            for key, value in settings.items():
                old_value = old_preferences[category].get(key)
                if old_value != value:
                    changes[f'{category}.{key}'] = {
                        'old': old_value,
                        'new': value
                    }
        
        if changes:
            from app.models.user import User
            user = User.query.get(user_id)
            if user:
                OperationLog.create_log(
                    user=user,
                    action='update_preferences',
                    resource='user_preferences',
                    description='更新用户偏好设置',
                    request=request,
                    resource_id=preferences.id
                )
        
        return jsonify({
            'code': 0,
            'message': '偏好设置更新成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'偏好设置更新失败: {str(e)}'
        }), 500

@user_preferences_bp.route('/preferences/reset', methods=['POST'])
@jwt_required()
def reset_preferences():
    """重置用户偏好设置为默认值"""
    user_id = int(get_jwt_identity())
    
    try:
        # 删除现有偏好设置
        preferences = UserPreferences.query.filter_by(user_id=user_id).first()
        if preferences:
            db.session.delete(preferences)
        
        # 创建新的默认偏好设置
        new_preferences = UserPreferences.create_default(user_id)
        
        # 记录操作日志
        from app.models.user import User
        user = User.query.get(user_id)
        if user:
            OperationLog.create_log(
                user=user,
                action='reset_preferences',
                resource='user_preferences',
                description='重置用户偏好设置为默认值',
                request=request,
                resource_id=new_preferences.id
            )
        
        return jsonify({
            'code': 0,
            'message': '偏好设置已重置为默认值',
            'data': new_preferences.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'重置偏好设置失败: {str(e)}'
        }), 500
# app/routes/security.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models import db, User, UserLoginLog, UserSession
from app.models.operation_log import OperationLog
from datetime import datetime, timedelta
import secrets

security_bp = Blueprint('security', __name__)

@security_bp.route('/login-logs', methods=['GET'])
@jwt_required()
def get_login_logs():
    """获取用户登录日志"""
    user_id = int(get_jwt_identity())
    
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 限制每页条数
    per_page = min(per_page, 100)
    
    # 构建查询
    query = UserLoginLog.query.filter_by(user_id=user_id)
    
    # 时间范围过滤
    try:
        if start_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(UserLoginLog.login_time >= start_dt)
        
        if end_date:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            # 设置为当天结束时间
            from datetime import time
            end_dt = datetime.combine(end_dt.date(), time.max)
            query = query.filter(UserLoginLog.login_time <= end_dt)
    except ValueError:
        return jsonify({
            'code': 400,
            'message': '日期格式错误，请使用YYYY-MM-DD格式'
        }), 400
    
    # 排序和分页
    query = query.order_by(UserLoginLog.login_time.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # 获取当前会话信息（如果有）
    current_session = None
    try:
        jwt_data = get_jwt()
        session_id = jwt_data.get('session_id')  # 如果JWT中包含session_id
        if session_id:
            current_session_obj = UserSession.query.filter_by(
                session_id=session_id,
                user_id=user_id
            ).first()
            if current_session_obj:
                current_session = {
                    'session_id': current_session_obj.session_id,
                    'login_time': current_session_obj.created_at.isoformat(),
                    'ip_address': current_session_obj.ip_address,
                    'expires_at': current_session_obj.expires_at.isoformat()
                }
    except:
        pass  # JWT中可能没有session_id，这是正常的
    
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': {
            'logs': [log.to_dict() for log in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
            'current_session': current_session
        }
    })

@security_bp.route('/logout-other-sessions', methods=['POST'])
@jwt_required()
def logout_other_sessions():
    """登出其他会话"""
    user_id = int(get_jwt_identity())
    
    try:
        # 获取当前会话ID（如果有）
        current_session_id = None
        try:
            jwt_data = get_jwt()
            current_session_id = jwt_data.get('session_id')
        except:
            pass
        
        # 登出其他会话
        logged_out_count = UserSession.logout_other_sessions(user_id, current_session_id)
        
        # 记录操作日志
        from app.models.user import User
        user = User.query.get(user_id)
        if user:
            OperationLog.create_log(
                user=user,
                action='logout_other_sessions',
                resource='user_session',
                description=f'登出其他会话，共{logged_out_count}个',
                request=request,
                sensitive=True
            )
        
        return jsonify({
            'code': 0,
            'message': '其他会话已登出',
            'data': {
                'logged_out_sessions': logged_out_count
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'操作失败: {str(e)}'
        }), 500

@security_bp.route('/security-settings', methods=['GET'])
@jwt_required()
def get_security_settings():
    """获取安全设置"""
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    
    # 获取登录统计
    login_stats = UserLoginLog.get_user_login_stats(user_id, days=30)
    
    # 计算密码强度（简单评估）
    password_strength = 'medium'  # 默认中等，实际应该基于密码复杂度计算
    
    # 获取最后一次密码修改时间（假设updated_at反映密码修改）
    last_password_change = user.updated_at
    
    # 计算密码过期天数（这里假设密码90天过期，实际应该可配置）
    password_expires_in = 90
    if last_password_change:
        days_since_change = (datetime.now() - last_password_change).days
        password_expires_in = max(0, 90 - days_since_change)
    
    # 检查双因素认证状态
    from app.models.user_preferences import UserPreferences
    preferences = UserPreferences.query.filter_by(user_id=user_id).first()
    two_factor_enabled = preferences.enable_two_factor if preferences else False
    
    # 获取失败登录次数（最近24小时）
    failed_attempts_24h = UserLoginLog.query.filter(
        UserLoginLog.user_id == user_id,
        UserLoginLog.status == 'failed',
        UserLoginLog.login_time >= datetime.now() - timedelta(hours=24)
    ).count()
    
    # 检查账户锁定状态（这里是示例，实际需要根据业务逻辑实现）
    account_locked_until = None
    
    # 获取受信任设备数量
    trusted_devices = UserSession.query.filter_by(user_id=user_id).count()
    
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': {
            'password_strength': password_strength,
            'last_password_change': last_password_change.isoformat() if last_password_change else None,
            'password_expires_in': password_expires_in,
            'two_factor_enabled': two_factor_enabled,
            'security_questions_set': False,  # 假设未实现安全问题功能
            'failed_login_attempts': failed_attempts_24h,
            'account_locked_until': account_locked_until,
            'trusted_devices': trusted_devices,
            'login_stats': login_stats
        }
    })

@security_bp.route('/enable-two-factor', methods=['POST'])
@jwt_required()
def enable_two_factor():
    """启用双因素认证"""
    user_id = int(get_jwt_identity())
    
    try:
        # 检查是否已经启用
        from app.models.user_preferences import UserPreferences
        preferences = UserPreferences.query.filter_by(user_id=user_id).first()
        if not preferences:
            preferences = UserPreferences.create_default(user_id)
        
        if preferences.enable_two_factor:
            return jsonify({
                'code': 400,
                'message': '双因素认证已经启用'
            }), 400
        
        # 生成密钥和二维码（这里是示例，实际需要使用专门的库）
        secret_key = secrets.token_hex(16)
        
        # 生成备份码
        backup_codes = [secrets.token_hex(4) for _ in range(8)]
        
        # 这里应该生成实际的二维码，示例中返回占位符
        qr_code = "data:image/png;base64,iVBORw0KGgoAAAANS..."  # 占位符
        
        # 启用双因素认证
        preferences.enable_two_factor = True
        db.session.commit()
        
        # 记录操作日志
        from app.models.user import User
        user = User.query.get(user_id)
        if user:
            OperationLog.create_log(
                user=user,
                action='enable_two_factor',
                resource='user_security',
                description='启用双因素认证',
                request=request,
                sensitive=True
            )
        
        return jsonify({
            'code': 0,
            'message': '双因素认证已启用',
            'data': {
                'qr_code': qr_code,
                'secret_key': secret_key,
                'backup_codes': backup_codes
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'启用失败: {str(e)}'
        }), 500

@security_bp.route('/disable-two-factor', methods=['POST'])
@jwt_required()
def disable_two_factor():
    """禁用双因素认证"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    # 验证当前密码
    if not data or not data.get('password'):
        return jsonify({
            'code': 400,
            'message': '请提供当前密码以确认操作'
        }), 400
    
    user = User.query.get_or_404(user_id)
    if not user.check_password(data['password']):
        return jsonify({
            'code': 400,
            'message': '密码错误'
        }), 400
    
    try:
        # 禁用双因素认证
        from app.models.user_preferences import UserPreferences
        preferences = UserPreferences.query.filter_by(user_id=user_id).first()
        if preferences:
            preferences.enable_two_factor = False
            db.session.commit()
        
        # 记录操作日志
        OperationLog.create_log(
            user=user,
            action='disable_two_factor',
            resource='user_security',
            description='禁用双因素认证',
            request=request,
            sensitive=True
        )
        
        return jsonify({
            'code': 0,
            'message': '双因素认证已禁用'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'操作失败: {str(e)}'
        }), 500

@security_bp.route('/active-sessions', methods=['GET'])
@jwt_required()
def get_active_sessions():
    """获取活跃会话列表"""
    user_id = int(get_jwt_identity())
    
    # 清理过期会话
    UserSession.cleanup_expired_sessions()
    
    # 获取活跃会话
    active_sessions = UserSession.query.filter(
        UserSession.user_id == user_id,
        UserSession.expires_at > datetime.now()
    ).order_by(UserSession.last_activity.desc()).all()
    
    # 获取当前会话ID
    current_session_id = None
    try:
        jwt_data = get_jwt()
        current_session_id = jwt_data.get('session_id')
    except:
        pass
    
    sessions_data = []
    for session in active_sessions:
        session_info = session.to_dict()
        session_info['is_current'] = (session.session_id == current_session_id)
        sessions_data.append(session_info)
    
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': {
            'sessions': sessions_data,
            'total': len(sessions_data)
        }
    })

@security_bp.route('/sessions/<session_id>', methods=['DELETE'])
@jwt_required()
def terminate_session(session_id):
    """终止指定会话"""
    user_id = int(get_jwt_identity())
    
    # 获取当前会话ID
    current_session_id = None
    try:
        jwt_data = get_jwt()
        current_session_id = jwt_data.get('session_id')
    except:
        pass
    
    # 不能终止当前会话
    if session_id == current_session_id:
        return jsonify({
            'code': 400,
            'message': '不能终止当前会话，请使用登出功能'
        }), 400
    
    # 查找会话
    session = UserSession.query.filter_by(
        session_id=session_id,
        user_id=user_id
    ).first()
    
    if not session:
        return jsonify({
            'code': 404,
            'message': '会话不存在'
        }), 404
    
    try:
        db.session.delete(session)
        db.session.commit()
        
        # 记录操作日志
        from app.models.user import User
        user = User.query.get(user_id)
        if user:
            OperationLog.create_log(
                user=user,
                action='terminate_session',
                resource='user_session',
                description=f'终止会话: {session_id}',
                request=request,
                resource_id=session.id,
                sensitive=True
            )
        
        return jsonify({
            'code': 0,
            'message': '会话已终止'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'操作失败: {str(e)}'
        }), 500
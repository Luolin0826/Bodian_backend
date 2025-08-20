# app/routes/notifications.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Notification
from app.models.operation_log import OperationLog
from datetime import datetime
from sqlalchemy import func, and_, or_

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('', methods=['GET'])
@jwt_required()
def get_notifications():
    """获取用户通知列表"""
    user_id = int(get_jwt_identity())
    
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    notification_type = request.args.get('type', 'all')
    status = request.args.get('status', 'all')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 限制每页条数
    per_page = min(per_page, 100)
    
    # 构建查询
    query = Notification.query.filter_by(user_id=user_id)
    
    # 类型过滤
    if notification_type != 'all':
        if notification_type not in ['system', 'email', 'push']:
            return jsonify({
                'code': 400,
                'message': '无效的通知类型'
            }), 400
        query = query.filter(Notification.type == notification_type)
    
    # 状态过滤
    if status == 'unread':
        query = query.filter(Notification.is_read == False)
    elif status == 'read':
        query = query.filter(Notification.is_read == True)
    elif status != 'all':
        return jsonify({
            'code': 400,
            'message': '无效的状态值'
        }), 400
    
    # 时间范围过滤
    try:
        if start_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Notification.created_at >= start_dt)
        
        if end_date:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            # 设置为当天结束时间
            from datetime import time
            end_dt = datetime.combine(end_dt.date(), time.max)
            query = query.filter(Notification.created_at <= end_dt)
    except ValueError:
        return jsonify({
            'code': 400,
            'message': '日期格式错误，请使用YYYY-MM-DD格式'
        }), 400
    
    # 过滤已过期的通知
    current_time = datetime.now()
    query = query.filter(
        or_(
            Notification.expires_at.is_(None),
            Notification.expires_at > current_time
        )
    )
    
    # 排序和分页
    query = query.order_by(Notification.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # 获取未读数量统计
    unread_counts = Notification.get_unread_count(user_id)
    
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': {
            'notifications': [notification.to_dict() for notification in pagination.items],
            'total': pagination.total,
            'unread_count': unread_counts['total_unread'],
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })

@notifications_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """获取未读通知数量"""
    user_id = int(get_jwt_identity())
    
    unread_counts = Notification.get_unread_count(user_id)
    
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': unread_counts
    })

@notifications_bp.route('/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_notification_read(notification_id):
    """标记通知为已读"""
    user_id = int(get_jwt_identity())
    
    # 验证通知是否存在且属于当前用户
    notification = Notification.query.filter_by(
        id=notification_id, 
        user_id=user_id
    ).first()
    
    if not notification:
        return jsonify({
            'code': 404,
            'message': '通知不存在'
        }), 404
    
    if notification.is_read:
        return jsonify({
            'code': 0,
            'message': '通知已经是已读状态'
        })
    
    try:
        success = Notification.mark_as_read(user_id, notification_id)
        
        if success:
            # 记录操作日志
            from app.models.user import User
            user = User.query.get(user_id)
            if user:
                OperationLog.create_log(
                    user=user,
                    action='mark_notification_read',
                    resource='notification',
                    description=f'标记通知为已读: {notification.title}',
                    request=request,
                    resource_id=notification_id
                )
            
            return jsonify({
                'code': 0,
                'message': '通知已标记为已读'
            })
        else:
            return jsonify({
                'code': 500,
                'message': '标记失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'操作失败: {str(e)}'
        }), 500

@notifications_bp.route('/read-all', methods=['PUT'])
@jwt_required()
def mark_all_read():
    """标记所有通知为已读"""
    user_id = int(get_jwt_identity())
    
    try:
        # 获取未读通知数量
        unread_count = Notification.query.filter_by(
            user_id=user_id, 
            is_read=False
        ).count()
        
        if unread_count == 0:
            return jsonify({
                'code': 0,
                'message': '没有未读通知'
            })
        
        success = Notification.mark_as_read(user_id)
        
        if success:
            # 记录操作日志
            from app.models.user import User
            user = User.query.get(user_id)
            if user:
                OperationLog.create_log(
                    user=user,
                    action='mark_all_notifications_read',
                    resource='notification',
                    description=f'标记所有通知为已读，共{unread_count}条',
                    request=request
                )
            
            return jsonify({
                'code': 0,
                'message': f'所有通知已标记为已读，共{unread_count}条'
            })
        else:
            return jsonify({
                'code': 500,
                'message': '标记失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'操作失败: {str(e)}'
        }), 500

@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """删除通知"""
    user_id = int(get_jwt_identity())
    
    # 验证通知是否存在且属于当前用户
    notification = Notification.query.filter_by(
        id=notification_id, 
        user_id=user_id
    ).first()
    
    if not notification:
        return jsonify({
            'code': 404,
            'message': '通知不存在'
        }), 404
    
    try:
        notification_title = notification.title
        db.session.delete(notification)
        db.session.commit()
        
        # 记录操作日志
        from app.models.user import User
        user = User.query.get(user_id)
        if user:
            OperationLog.create_log(
                user=user,
                action='delete_notification',
                resource='notification',
                description=f'删除通知: {notification_title}',
                request=request,
                resource_id=notification_id
            )
        
        return jsonify({
            'code': 0,
            'message': '通知已删除'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'删除失败: {str(e)}'
        }), 500

@notifications_bp.route('/cleanup-expired', methods=['POST'])
@jwt_required()
def cleanup_expired_notifications():
    """清理过期通知（系统管理员功能）"""
    user_id = int(get_jwt_identity())
    
    # 检查用户权限（仅超级管理员和管理员可以执行）
    from app.models.user import User
    user = User.query.get(user_id)
    if not user or user.role not in ['super_admin', 'admin']:
        return jsonify({
            'code': 403,
            'message': '权限不足'
        }), 403
    
    try:
        current_time = datetime.now()
        
        # 查找过期通知
        expired_notifications = Notification.query.filter(
            Notification.expires_at < current_time
        ).all()
        
        count = len(expired_notifications)
        
        if count == 0:
            return jsonify({
                'code': 0,
                'message': '没有过期通知需要清理'
            })
        
        # 删除过期通知
        for notification in expired_notifications:
            db.session.delete(notification)
        
        db.session.commit()
        
        # 记录操作日志
        from app.models.user import User
        user = User.query.get(user_id)
        if user:
            OperationLog.create_log(
                user=user,
                action='cleanup_expired_notifications',
                resource='notification',
                description=f'清理过期通知，共{count}条',
                request=request
            )
        
        return jsonify({
            'code': 0,
            'message': f'已清理{count}条过期通知'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'清理失败: {str(e)}'
        }), 500
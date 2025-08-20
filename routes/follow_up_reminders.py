# app/routes/follow_up_reminders.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date
from sqlalchemy import and_, func, desc, asc
from app.models import db, FollowUpReminder, Customer, FollowUpRecord
from app.utils.timezone import now

follow_up_reminders_bp = Blueprint('follow_up_reminders', __name__)

@follow_up_reminders_bp.route('/follow-up-reminders', methods=['GET'])
@jwt_required()
def get_follow_up_reminders():
    """获取跟进提醒列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    remind_date = request.args.get('date')
    is_completed = request.args.get('is_completed')
    customer_id = request.args.get('customer_id', type=int)
    priority = request.args.get('priority')
    customer_name = request.args.get('customer_name')
    current_user_id = int(get_jwt_identity())
    
    query = FollowUpReminder.query.filter_by(created_by=current_user_id)
    
    # 筛选条件
    if remind_date:
        query = query.filter_by(remind_date=datetime.strptime(remind_date, '%Y-%m-%d').date())
    if is_completed is not None:
        is_completed_bool = is_completed.lower() in ['true', '1', 'yes']
        query = query.filter_by(is_completed=is_completed_bool)
    if customer_id:
        query = query.filter_by(customer_id=customer_id)
    if priority:
        query = query.filter_by(priority=priority)
    if customer_name:
        query = query.join(Customer).filter(Customer.wechat_name.like(f'%{customer_name}%'))
    
    # 排序：未完成的提醒按日期正序，已完成的按完成时间倒序
    query = query.order_by(
        FollowUpReminder.is_completed.asc(),
        FollowUpReminder.remind_date.asc(),
        FollowUpReminder.priority.desc()
    )
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # 获取详细信息
    reminders = [reminder.to_detail_dict() for reminder in pagination.items]
    
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': {
            'reminders': reminders,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })

@follow_up_reminders_bp.route('/follow-up-reminders', methods=['POST'])
@jwt_required()
def create_follow_up_reminder():
    """创建跟进提醒"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    # 验证必填字段
    if not data.get('customer_id'):
        return jsonify({
            'code': 400,
            'message': '客户ID不能为空'
        }), 400
    
    if not data.get('remind_content'):
        return jsonify({
            'code': 400,
            'message': '提醒内容不能为空'
        }), 400
    
    if not data.get('remind_date'):
        return jsonify({
            'code': 400,
            'message': '提醒日期不能为空'
        }), 400
    
    # 验证客户是否存在
    customer = Customer.query.get_or_404(data['customer_id'])
    
    # 创建提醒
    reminder = FollowUpReminder(
        customer_id=data['customer_id'],
        remind_date=datetime.strptime(data['remind_date'], '%Y-%m-%d').date(),
        remind_content=data['remind_content'],
        priority=data.get('priority', 'medium'),
        follow_up_record_id=data.get('follow_up_record_id'),
        created_by=current_user_id
    )
    
    db.session.add(reminder)
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'message': '跟进提醒创建成功',
        'data': reminder.to_detail_dict()
    }), 201

@follow_up_reminders_bp.route('/follow-up-reminders/<int:id>', methods=['PUT'])
@jwt_required()
def update_follow_up_reminder(id):
    """更新跟进提醒"""
    current_user_id = int(get_jwt_identity())
    reminder = FollowUpReminder.query.get_or_404(id)
    data = request.get_json()
    
    # 只有创建者可以修改
    if reminder.created_by != current_user_id:
        return jsonify({
            'code': 403,
            'message': '只能修改自己创建的提醒'
        }), 403
    
    # 更新字段
    updatable_fields = ['remind_content', 'priority']
    for field in updatable_fields:
        if field in data:
            setattr(reminder, field, data[field])
    
    # 更新提醒日期
    if 'remind_date' in data:
        reminder.remind_date = datetime.strptime(data['remind_date'], '%Y-%m-%d').date()
    
    # 更新关联跟进记录
    if 'follow_up_record_id' in data:
        reminder.follow_up_record_id = data['follow_up_record_id']
    
    reminder.updated_at = now()
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'message': '跟进提醒更新成功',
        'data': reminder.to_detail_dict()
    })

@follow_up_reminders_bp.route('/follow-up-reminders/<int:id>/complete', methods=['PUT'])
@jwt_required()
def complete_follow_up_reminder(id):
    """标记提醒为已完成"""
    current_user_id = int(get_jwt_identity())
    reminder = FollowUpReminder.query.get_or_404(id)
    
    # 只有创建者可以标记完成
    if reminder.created_by != current_user_id:
        return jsonify({
            'code': 403,
            'message': '只能标记自己创建的提醒为完成'
        }), 403
    
    if reminder.is_completed:
        return jsonify({
            'code': 400,
            'message': '该提醒已经完成'
        }), 400
    
    reminder.mark_completed(current_user_id)
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'message': '提醒已标记为完成',
        'data': reminder.to_detail_dict()
    })

@follow_up_reminders_bp.route('/follow-up-reminders/<int:id>/reopen', methods=['PUT'])
@jwt_required()
def reopen_follow_up_reminder(id):
    """重新打开已完成的提醒"""
    current_user_id = int(get_jwt_identity())
    reminder = FollowUpReminder.query.get_or_404(id)
    
    # 只有创建者可以重新打开
    if reminder.created_by != current_user_id:
        return jsonify({
            'code': 403,
            'message': '只能重新打开自己创建的提醒'
        }), 403
    
    if not reminder.is_completed:
        return jsonify({
            'code': 400,
            'message': '该提醒尚未完成'
        }), 400
    
    reminder.is_completed = False
    reminder.completed_at = None
    reminder.completed_by = None
    reminder.updated_at = now()
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'message': '提醒已重新打开',
        'data': reminder.to_detail_dict()
    })

@follow_up_reminders_bp.route('/follow-up-reminders/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_follow_up_reminder(id):
    """删除跟进提醒"""
    current_user_id = int(get_jwt_identity())
    reminder = FollowUpReminder.query.get_or_404(id)
    
    # 只有创建者可以删除
    if reminder.created_by != current_user_id:
        return jsonify({
            'code': 403,
            'message': '只能删除自己创建的提醒'
        }), 403
    
    db.session.delete(reminder)
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'message': '跟进提醒删除成功'
    })

@follow_up_reminders_bp.route('/follow-up-reminders/today', methods=['GET'])
@jwt_required()
def get_today_reminders():
    """获取今日提醒"""
    current_user_id = int(get_jwt_identity())
    today = date.today()
    
    reminders = FollowUpReminder.query.filter(
        and_(
            FollowUpReminder.created_by == current_user_id,
            FollowUpReminder.remind_date <= today,
            FollowUpReminder.is_completed == False
        )
    ).order_by(
        FollowUpReminder.priority.desc(),
        FollowUpReminder.remind_date.asc()
    ).all()
    
    # 分类提醒：今日、逾期
    today_reminders = []
    overdue_reminders = []
    
    for reminder in reminders:
        reminder_dict = reminder.to_detail_dict()
        if reminder.remind_date == today:
            today_reminders.append(reminder_dict)
        else:
            overdue_reminders.append(reminder_dict)
    
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': {
            'today_reminders': today_reminders,
            'overdue_reminders': overdue_reminders,
            'total_count': len(today_reminders) + len(overdue_reminders)
        }
    })

@follow_up_reminders_bp.route('/follow-up-reminders/statistics', methods=['GET'])
@jwt_required()
def get_reminder_statistics():
    """获取提醒统计数据"""
    current_user_id = int(get_jwt_identity())
    today = date.today()
    
    # 今日提醒数
    today_count = FollowUpReminder.query.filter(
        and_(
            FollowUpReminder.created_by == current_user_id,
            FollowUpReminder.remind_date == today,
            FollowUpReminder.is_completed == False
        )
    ).count()
    
    # 逾期提醒数
    overdue_count = FollowUpReminder.query.filter(
        and_(
            FollowUpReminder.created_by == current_user_id,
            FollowUpReminder.remind_date < today,
            FollowUpReminder.is_completed == False
        )
    ).count()
    
    # 总提醒数（未完成）
    total_pending = FollowUpReminder.query.filter(
        and_(
            FollowUpReminder.created_by == current_user_id,
            FollowUpReminder.is_completed == False
        )
    ).count()
    
    # 本月完成的提醒数
    month_start = today.replace(day=1)
    completed_this_month = FollowUpReminder.query.filter(
        and_(
            FollowUpReminder.created_by == current_user_id,
            FollowUpReminder.is_completed == True,
            FollowUpReminder.completed_at >= datetime.combine(month_start, datetime.min.time())
        )
    ).count()
    
    # 按优先级统计
    priority_stats = db.session.query(
        FollowUpReminder.priority,
        func.count(FollowUpReminder.id).label('count')
    ).filter(
        and_(
            FollowUpReminder.created_by == current_user_id,
            FollowUpReminder.is_completed == False
        )
    ).group_by(FollowUpReminder.priority).all()
    
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': {
            'today_count': today_count,
            'overdue_count': overdue_count,
            'total_pending': total_pending,
            'completed_this_month': completed_this_month,
            'priority_statistics': [{'priority': item[0], 'count': item[1]} for item in priority_stats]
        }
    })
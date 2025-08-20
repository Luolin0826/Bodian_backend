# app/routes/follow_up_records.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date
from sqlalchemy import and_, func, desc
from app.models import db, FollowUpRecord, Customer, User
from app.utils.timezone import now

follow_up_records_bp = Blueprint('follow_up_records', __name__)

@follow_up_records_bp.route('/customers/<int:customer_id>/follow-ups', methods=['GET'])
@jwt_required()
def get_customer_follow_ups(customer_id):
    """获取客户跟进记录列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    follow_up_type = request.args.get('follow_up_type')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    result = request.args.get('result')
    
    # 验证客户是否存在
    customer = Customer.query.get_or_404(customer_id)
    
    query = FollowUpRecord.query.filter_by(customer_id=customer_id)
    
    # 筛选条件
    if follow_up_type:
        query = query.filter_by(follow_up_type=follow_up_type)
    if result:
        query = query.filter_by(result=result)
    if date_from:
        query = query.filter(FollowUpRecord.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(FollowUpRecord.created_at <= datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
    
    # 按创建时间倒序
    query = query.order_by(desc(FollowUpRecord.created_at))
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # 获取详细信息，包含创建者姓名
    records = []
    for record in pagination.items:
        record_dict = record.to_detail_dict()
        records.append(record_dict)
    
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': {
            'records': records,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
            'customer': customer.to_dict()
        }
    })

@follow_up_records_bp.route('/customers/<int:customer_id>/follow-ups', methods=['POST'])
@jwt_required()
def create_follow_up_record(customer_id):
    """创建跟进记录"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    # 验证客户是否存在
    customer = Customer.query.get_or_404(customer_id)
    
    # 验证必填字段
    if not data.get('follow_up_content'):
        return jsonify({
            'code': 400,
            'message': '跟进内容不能为空'
        }), 400
    
    # 记录状态变化前的状态
    status_before = customer.status
    
    # 创建跟进记录
    follow_up_record = FollowUpRecord(
        customer_id=customer_id,
        follow_up_type=data.get('follow_up_type', 'phone'),
        follow_up_content=data['follow_up_content'],
        result=data.get('result'),
        status_before=status_before,
        created_by=current_user_id
    )
    
    # 处理下次跟进日期
    if data.get('next_follow_date'):
        follow_up_record.next_follow_date = datetime.strptime(data['next_follow_date'], '%Y-%m-%d').date()
    
    # 如果有状态变化，更新客户状态
    if data.get('status_after') and data['status_after'] != status_before:
        customer.status = data['status_after']
        customer.updated_at = now()
        follow_up_record.status_after = data['status_after']
        
        # 如果状态变为已成交，记录成交日期
        if data['status_after'] == '已成交':
            customer.deal_date = date.today()
    
    db.session.add(follow_up_record)
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'message': '跟进记录创建成功',
        'data': follow_up_record.to_detail_dict()
    }), 201

@follow_up_records_bp.route('/follow-ups/<int:id>', methods=['PUT'])
@jwt_required()
def update_follow_up_record(id):
    """更新跟进记录"""
    current_user_id = int(get_jwt_identity())
    follow_up_record = FollowUpRecord.query.get_or_404(id)
    data = request.get_json()
    
    # 只有创建者可以修改
    if follow_up_record.created_by != current_user_id:
        return jsonify({
            'code': 403,
            'message': '只能修改自己创建的跟进记录'
        }), 403
    
    # 更新基本字段
    updatable_fields = ['follow_up_type', 'follow_up_content', 'result']
    for field in updatable_fields:
        if field in data:
            setattr(follow_up_record, field, data[field])
    
    # 处理下次跟进日期
    if 'next_follow_date' in data:
        if data['next_follow_date']:
            follow_up_record.next_follow_date = datetime.strptime(data['next_follow_date'], '%Y-%m-%d').date()
        else:
            follow_up_record.next_follow_date = None
    
    follow_up_record.updated_at = now()
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'message': '跟进记录更新成功',
        'data': follow_up_record.to_detail_dict()
    })

@follow_up_records_bp.route('/follow-ups/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_follow_up_record(id):
    """删除跟进记录"""
    current_user_id = int(get_jwt_identity())
    follow_up_record = FollowUpRecord.query.get_or_404(id)
    
    # 只有创建者可以删除
    if follow_up_record.created_by != current_user_id:
        return jsonify({
            'code': 403,
            'message': '只能删除自己创建的跟进记录'
        }), 403
    
    db.session.delete(follow_up_record)
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'message': '跟进记录删除成功'
    })

@follow_up_records_bp.route('/follow-ups/statistics', methods=['GET'])
@jwt_required()
def get_follow_up_statistics():
    """获取跟进统计数据"""
    current_user_id = int(get_jwt_identity())
    today = date.today()
    
    # 今日跟进数
    today_count = FollowUpRecord.query.filter(
        and_(
            FollowUpRecord.created_by == current_user_id,
            func.date(FollowUpRecord.created_at) == today
        )
    ).count()
    
    # 本周跟进数（周一到今天）
    from datetime import timedelta
    week_start = today - timedelta(days=today.weekday())
    week_count = FollowUpRecord.query.filter(
        and_(
            FollowUpRecord.created_by == current_user_id,
            func.date(FollowUpRecord.created_at) >= week_start
        )
    ).count()
    
    # 本月跟进数
    month_start = today.replace(day=1)
    month_count = FollowUpRecord.query.filter(
        and_(
            FollowUpRecord.created_by == current_user_id,
            func.date(FollowUpRecord.created_at) >= month_start
        )
    ).count()
    
    # 各跟进方式统计
    type_stats = db.session.query(
        FollowUpRecord.follow_up_type,
        func.count(FollowUpRecord.id).label('count')
    ).filter(
        and_(
            FollowUpRecord.created_by == current_user_id,
            func.date(FollowUpRecord.created_at) >= month_start
        )
    ).group_by(FollowUpRecord.follow_up_type).all()
    
    # 各跟进结果统计
    result_stats = db.session.query(
        FollowUpRecord.result,
        func.count(FollowUpRecord.id).label('count')
    ).filter(
        and_(
            FollowUpRecord.created_by == current_user_id,
            func.date(FollowUpRecord.created_at) >= month_start,
            FollowUpRecord.result.isnot(None)
        )
    ).group_by(FollowUpRecord.result).all()
    
    # 计算转化率（成交客户数/跟进客户数）
    total_customers = db.session.query(func.count(func.distinct(FollowUpRecord.customer_id))).filter(
        and_(
            FollowUpRecord.created_by == current_user_id,
            func.date(FollowUpRecord.created_at) >= month_start
        )
    ).scalar()
    
    deal_customers = db.session.query(func.count(func.distinct(FollowUpRecord.customer_id))).filter(
        and_(
            FollowUpRecord.created_by == current_user_id,
            FollowUpRecord.result == 'deal',
            func.date(FollowUpRecord.created_at) >= month_start
        )
    ).scalar()
    
    conversion_rate = round((deal_customers / total_customers * 100), 2) if total_customers > 0 else 0
    
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': {
            'today_count': today_count,
            'week_count': week_count,
            'month_count': month_count,
            'conversion_rate': conversion_rate,
            'total_customers': total_customers,
            'deal_customers': deal_customers,
            'type_statistics': [{'type': item[0], 'count': item[1]} for item in type_stats],
            'result_statistics': [{'result': item[0], 'count': item[1]} for item in result_stats]
        }
    })

@follow_up_records_bp.route('/follow-ups', methods=['GET'])
@jwt_required()
def get_all_follow_ups():
    """获取所有跟进记录（支持分页和筛选）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    follow_up_type = request.args.get('follow_up_type')
    result = request.args.get('result')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    customer_name = request.args.get('customer_name')
    created_by = request.args.get('created_by')
    
    query = FollowUpRecord.query
    
    # 筛选条件
    if follow_up_type:
        query = query.filter_by(follow_up_type=follow_up_type)
    if result:
        query = query.filter_by(result=result)
    if created_by:
        query = query.filter_by(created_by=created_by)
    if date_from:
        query = query.filter(FollowUpRecord.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(FollowUpRecord.created_at <= datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
    if customer_name:
        query = query.join(Customer).filter(Customer.wechat_name.like(f'%{customer_name}%'))
    
    # 按创建时间倒序
    query = query.order_by(desc(FollowUpRecord.created_at))
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # 获取详细信息
    records = [record.to_detail_dict() for record in pagination.items]
    
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': {
            'records': records,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })
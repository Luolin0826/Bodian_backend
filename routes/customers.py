# app/routes/customers.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date, timedelta
from sqlalchemy import and_, func, desc
from app.models import db, Customer, FollowUpRecord, FollowUpReminder
from app.services.customer_service import CustomerService
from app.utils.timezone import now

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/customers/health', methods=['GET'])
def customers_health():
    """客户模块健康检查（无需认证）"""
    return {'status': 'healthy', 'module': 'customers'}

@customers_bp.route('/customers', methods=['OPTIONS'])
def customers_options():
    """处理客户路由的OPTIONS请求"""
    return '', 200

@customers_bp.route('/customers', methods=['GET'])
@jwt_required()
def get_customers():
    """获取客户列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    channel = request.args.get('channel')
    keyword = request.args.get('keyword')
    subject = request.args.get('subject')  # 支持subject作为搜索关键词
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    # 如果没有keyword但有subject，使用subject作为关键词
    if not keyword and subject:
        keyword = subject
    
    query = Customer.query
    
    if status:
        query = query.filter_by(status=status)
    if channel:
        query = query.filter_by(channel=channel)
    if keyword:
        query = query.filter(
            db.or_(
                Customer.wechat_name.like(f'%{keyword}%'),
                Customer.phone.like(f'%{keyword}%'),
                Customer.remark.like(f'%{keyword}%')
            )
        )
    
    # 动态排序，仅允许安全的字段
    allowed_sort_fields = {
        'created_at': Customer.created_at,
        'customer_date': Customer.customer_date,
        'channel': Customer.channel,
        'status': Customer.status,
        'wechat_name': Customer.wechat_name,
        'phone': Customer.phone
    }
    
    if sort_by in allowed_sort_fields:
        sort_field = allowed_sort_fields[sort_by]
        if sort_order.lower() == 'asc':
            query = query.order_by(sort_field.asc())
        else:
            query = query.order_by(sort_field.desc())
    else:
        # 默认按创建时间倒序
        query = query.order_by(Customer.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'data': [c.to_dict() for c in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })

@customers_bp.route('/customers', methods=['POST'])
@jwt_required()
def create_customer():
    """创建客户"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())
    
    customer = Customer(
        customer_date=datetime.strptime(data.get('customer_date'), '%Y-%m-%d').date() if data.get('customer_date') else None,
        channel=data.get('channel'),
        wechat_name=data.get('wechat_name'),
        phone=data.get('phone'),
        status=data.get('status', '潜在'),
        remark=data.get('remark'),
        created_by=current_user_id
    )
    
    db.session.add(customer)
    db.session.commit()
    
    return jsonify({
        'message': '客户创建成功',
        'data': customer.to_dict()
    }), 201

@customers_bp.route('/customers/<int:id>', methods=['GET'])
@jwt_required()
def get_customer(id):
    """获取客户详情"""
    customer = Customer.query.get_or_404(id)
    return jsonify(customer.to_dict())

@customers_bp.route('/customers/<int:id>', methods=['PUT'])
@jwt_required()
def update_customer(id):
    """更新客户信息"""
    customer = Customer.query.get_or_404(id)
    data = request.get_json()
    
    # 更新字段
    for field in ['channel', 'wechat_name', 'phone', 'status', 'remark']:
        if field in data:
            setattr(customer, field, data[field])
    
    # 更新日期字段
    for date_field in ['customer_date', 'add_date', 'deal_date']:
        if date_field in data and data[date_field]:
            setattr(customer, date_field, 
                   datetime.strptime(data[date_field], '%Y-%m-%d').date())
    
    customer.updated_at = now()
    db.session.commit()
    
    return jsonify({
        'message': '客户更新成功',
        'data': customer.to_dict()
    })

@customers_bp.route('/customers/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_customer(id):
    """删除客户"""
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    
    return jsonify({'message': '客户删除成功'})

@customers_bp.route('/customers/<int:id>/detail', methods=['GET'])
@jwt_required()
def get_customer_detail(id):
    """获取客户详情（包含跟进记录）"""
    customer = Customer.query.get_or_404(id)
    
    # 获取最近的跟进记录（最多10条）
    recent_follow_ups = FollowUpRecord.query.filter_by(customer_id=id)\
        .order_by(desc(FollowUpRecord.created_at))\
        .limit(10).all()
    
    # 获取未完成的提醒
    pending_reminders = FollowUpReminder.query.filter(
        and_(
            FollowUpReminder.customer_id == id,
            FollowUpReminder.is_completed == False
        )
    ).order_by(FollowUpReminder.remind_date.asc()).all()
    
    # 跟进统计
    follow_up_stats = {
        'total_count': FollowUpRecord.query.filter_by(customer_id=id).count(),
        'last_follow_date': None,
        'next_follow_date': None
    }
    
    # 获取最后跟进日期
    last_follow_up = FollowUpRecord.query.filter_by(customer_id=id)\
        .order_by(desc(FollowUpRecord.created_at)).first()
    if last_follow_up:
        follow_up_stats['last_follow_date'] = last_follow_up.created_at.isoformat()
    
    # 获取下次跟进日期（从跟进记录和提醒中取最近的）
    next_from_record = FollowUpRecord.query.filter(
        and_(
            FollowUpRecord.customer_id == id,
            FollowUpRecord.next_follow_date.isnot(None),
            FollowUpRecord.next_follow_date >= date.today()
        )
    ).order_by(FollowUpRecord.next_follow_date.asc()).first()
    
    next_from_reminder = FollowUpReminder.query.filter(
        and_(
            FollowUpReminder.customer_id == id,
            FollowUpReminder.is_completed == False,
            FollowUpReminder.remind_date >= date.today()
        )
    ).order_by(FollowUpReminder.remind_date.asc()).first()
    
    next_dates = []
    if next_from_record and next_from_record.next_follow_date:
        next_dates.append(next_from_record.next_follow_date)
    if next_from_reminder:
        next_dates.append(next_from_reminder.remind_date)
    
    if next_dates:
        follow_up_stats['next_follow_date'] = min(next_dates).isoformat()
    
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': {
            'customer': customer.to_dict(),
            'recent_follow_ups': [record.to_detail_dict() for record in recent_follow_ups],
            'pending_reminders': [reminder.to_detail_dict() for reminder in pending_reminders],
            'follow_up_stats': follow_up_stats
        }
    })

@customers_bp.route('/customers/batch-follow-up', methods=['POST'])
@jwt_required()
def batch_follow_up():
    """批量更新客户跟进状态"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    customer_ids = data.get('customer_ids', [])
    follow_up_data = data.get('follow_up_data', {})
    
    if not customer_ids:
        return jsonify({
            'code': 400,
            'message': '客户ID列表不能为空'
        }), 400
    
    if not follow_up_data.get('follow_up_content'):
        return jsonify({
            'code': 400,
            'message': '跟进内容不能为空'
        }), 400
    
    # 验证客户是否存在
    customers = Customer.query.filter(Customer.id.in_(customer_ids)).all()
    if len(customers) != len(customer_ids):
        return jsonify({
            'code': 400,
            'message': '部分客户不存在'
        }), 400
    
    success_count = 0
    follow_up_records = []
    
    for customer in customers:
        try:
            # 记录跟进前状态
            status_before = customer.status
            
            # 创建跟进记录
            follow_up_record = FollowUpRecord(
                customer_id=customer.id,
                follow_up_type=follow_up_data.get('follow_up_type', 'phone'),
                follow_up_content=follow_up_data['follow_up_content'],
                result=follow_up_data.get('result'),
                status_before=status_before,
                created_by=current_user_id
            )
            
            # 处理下次跟进日期
            if follow_up_data.get('next_follow_date'):
                follow_up_record.next_follow_date = datetime.strptime(
                    follow_up_data['next_follow_date'], '%Y-%m-%d'
                ).date()
            
            # 如果有状态变化，更新客户状态
            if follow_up_data.get('status_after') and follow_up_data['status_after'] != status_before:
                customer.status = follow_up_data['status_after']
                customer.updated_at = now()
                follow_up_record.status_after = follow_up_data['status_after']
                
                # 如果状态变为已成交，记录成交日期
                if follow_up_data['status_after'] == '已成交':
                    customer.deal_date = date.today()
            
            db.session.add(follow_up_record)
            follow_up_records.append(follow_up_record)
            success_count += 1
            
        except Exception as e:
            continue
    
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'message': f'批量跟进成功，共处理{success_count}个客户',
        'data': {
            'success_count': success_count,
            'total_count': len(customer_ids)
        }
    })

@customers_bp.route('/customers/need-follow-up', methods=['GET'])
@jwt_required()
def get_customers_need_follow_up():
    """获取需要跟进的客户列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    urgency_level = request.args.get('urgency_level')  # urgent, high, medium, low
    days_since_last_contact = request.args.get('days_since_last_contact', 7, type=int)
    status = request.args.get('status')
    
    # 基础查询：状态为潜在或跟进中的客户
    base_statuses = ['潜在', '跟进中']
    if status and status in base_statuses:
        base_statuses = [status]
    
    # 计算需要跟进的客户
    cutoff_date = date.today() - timedelta(days=days_since_last_contact)
    
    # 子查询：获取每个客户最后跟进时间
    last_follow_up_subquery = db.session.query(
        FollowUpRecord.customer_id,
        func.max(FollowUpRecord.created_at).label('last_follow_up')
    ).group_by(FollowUpRecord.customer_id).subquery()
    
    # 主查询
    query = db.session.query(Customer)\
        .outerjoin(last_follow_up_subquery, Customer.id == last_follow_up_subquery.c.customer_id)\
        .filter(Customer.status.in_(base_statuses))\
        .filter(
            db.or_(
                last_follow_up_subquery.c.last_follow_up.is_(None),  # 从未跟进过的客户
                func.date(last_follow_up_subquery.c.last_follow_up) <= cutoff_date  # 超过指定天数未跟进
            )
        )
    
    # 紧急程度筛选
    if urgency_level:
        if urgency_level == 'urgent':
            # 超过30天未跟进或从未跟进
            urgent_cutoff = date.today() - timedelta(days=30)
            query = query.filter(
                db.or_(
                    last_follow_up_subquery.c.last_follow_up.is_(None),
                    func.date(last_follow_up_subquery.c.last_follow_up) <= urgent_cutoff
                )
            )
        elif urgency_level == 'high':
            # 14-30天未跟进
            high_start = date.today() - timedelta(days=30)
            high_end = date.today() - timedelta(days=14)
            query = query.filter(
                and_(
                    last_follow_up_subquery.c.last_follow_up.isnot(None),
                    func.date(last_follow_up_subquery.c.last_follow_up) > high_start,
                    func.date(last_follow_up_subquery.c.last_follow_up) <= high_end
                )
            )
        elif urgency_level == 'medium':
            # 7-14天未跟进
            medium_start = date.today() - timedelta(days=14)
            medium_end = date.today() - timedelta(days=7)
            query = query.filter(
                and_(
                    last_follow_up_subquery.c.last_follow_up.isnot(None),
                    func.date(last_follow_up_subquery.c.last_follow_up) > medium_start,
                    func.date(last_follow_up_subquery.c.last_follow_up) <= medium_end
                )
            )
    
    # 按最后跟进时间排序（越久未跟进的越靠前）
    # MySQL不支持NULLS FIRST语法，使用ISNULL()函数替代
    from sqlalchemy import case
    query = query.order_by(
        case(
            (last_follow_up_subquery.c.last_follow_up.is_(None), 0),
            else_=1
        ).asc(),
        last_follow_up_subquery.c.last_follow_up.asc()
    )
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # 为每个客户添加跟进统计信息
    customers_with_stats = []
    for customer in pagination.items:
        customer_dict = customer.to_dict()
        
        # 获取最后跟进记录
        last_follow_up = FollowUpRecord.query.filter_by(customer_id=customer.id)\
            .order_by(desc(FollowUpRecord.created_at)).first()
        
        customer_dict['last_follow_up_date'] = None
        customer_dict['days_since_last_follow_up'] = None
        customer_dict['urgency'] = 'low'
        
        if last_follow_up:
            customer_dict['last_follow_up_date'] = last_follow_up.created_at.isoformat()
            days_diff = (date.today() - last_follow_up.created_at.date()).days
            customer_dict['days_since_last_follow_up'] = days_diff
            
            # 计算紧急程度
            if days_diff >= 30:
                customer_dict['urgency'] = 'urgent'
            elif days_diff >= 14:
                customer_dict['urgency'] = 'high'
            elif days_diff >= 7:
                customer_dict['urgency'] = 'medium'
        else:
            # 从未跟进过的客户标记为紧急
            customer_dict['urgency'] = 'urgent'
            days_since_create = (date.today() - customer.created_at.date()).days
            customer_dict['days_since_last_follow_up'] = days_since_create
        
        customers_with_stats.append(customer_dict)
    
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': {
            'customers': customers_with_stats,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })

@customers_bp.route('/customers/<int:id>/timeline', methods=['GET'])
@jwt_required()
def get_customer_timeline(id):
    """获取客户跟进时间线"""
    customer = Customer.query.get_or_404(id)
    
    # 获取所有跟进记录
    follow_ups = FollowUpRecord.query.filter_by(customer_id=id)\
        .order_by(desc(FollowUpRecord.created_at)).all()
    
    # 获取所有提醒（包括已完成的）
    reminders = FollowUpReminder.query.filter_by(customer_id=id)\
        .order_by(desc(FollowUpReminder.created_at)).all()
    
    # 构建时间线数据
    timeline_items = []
    
    # 添加跟进记录到时间线
    for record in follow_ups:
        timeline_items.append({
            'type': 'follow_up',
            'id': record.id,
            'date': record.created_at.isoformat(),
            'title': f'{record.follow_up_type} 跟进',
            'content': record.follow_up_content,
            'result': record.result,
            'status_change': {
                'before': record.status_before,
                'after': record.status_after
            } if record.status_after != record.status_before else None,
            'next_follow_date': record.next_follow_date.isoformat() if record.next_follow_date else None,
            'creator_name': record.creator.username if record.creator else None
        })
    
    # 添加提醒到时间线
    for reminder in reminders:
        timeline_items.append({
            'type': 'reminder',
            'id': reminder.id,
            'date': reminder.created_at.isoformat(),
            'remind_date': reminder.remind_date.isoformat(),
            'title': f'跟进提醒 - {reminder.priority}',
            'content': reminder.remind_content,
            'is_completed': reminder.is_completed,
            'completed_at': reminder.completed_at.isoformat() if reminder.completed_at else None,
            'creator_name': reminder.creator.username if reminder.creator else None
        })
    
    # 按日期排序（最新的在前）
    timeline_items.sort(key=lambda x: x['date'], reverse=True)
    
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': {
            'customer': customer.to_dict(),
            'timeline': timeline_items,
            'total_items': len(timeline_items)
        }
    })
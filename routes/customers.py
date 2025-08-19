# app/routes/customers.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.models import db, Customer
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
# app/routes/stats.py
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
from app.models import db, Customer, Script, KnowledgeBase
from sqlalchemy import func
from app.utils.timezone import now, today

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """获取仪表板统计数据"""
    # 客户统计
    total_customers = Customer.query.count()
    potential_customers = Customer.query.filter_by(status='潜在').count()
    deal_customers = Customer.query.filter_by(status='已成交').count()
    
    # 今日新增
    today_date = today()
    today_customers = Customer.query.filter(
        func.date(Customer.created_at) == today_date
    ).count()
    
    # 本月新增
    month_start = now().replace(day=1).date()
    month_customers = Customer.query.filter(
        func.date(Customer.created_at) >= month_start
    ).count()
    
    # 渠道分布
    channel_stats = db.session.query(
        Customer.channel,
        func.count(Customer.id).label('count')
    ).group_by(Customer.channel).all()
    
    # 话术使用统计
    popular_scripts = Script.query.filter_by(is_active=True)\
        .order_by(Script.usage_count.desc())\
        .limit(5).all()
    
    # 知识库热门
    popular_knowledge = KnowledgeBase.query.filter_by(is_published=True)\
        .order_by(KnowledgeBase.view_count.desc())\
        .limit(5).all()
    
    return jsonify({
        'customer_stats': {
            'total': total_customers,
            'potential': potential_customers,
            'deal': deal_customers,
            'today_new': today_customers,
            'month_new': month_customers
        },
        'channel_distribution': [
            {'channel': c[0] or '未知', 'count': c[1]} 
            for c in channel_stats
        ],
        'popular_scripts': [
            {'id': s.id, 'title': s.title, 'count': s.usage_count}
            for s in popular_scripts
        ],
        'popular_knowledge': [
            {'id': k.id, 'question': k.question[:50], 'count': k.view_count}
            for k in popular_knowledge
        ]
    })
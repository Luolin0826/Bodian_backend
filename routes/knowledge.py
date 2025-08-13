# app/routes/knowledge.py
from flask import Blueprint, request, jsonify
from app.models import db, KnowledgeBase

knowledge_bp = Blueprint('knowledge', __name__)

@knowledge_bp.route('/search', methods=['GET'])
def search_knowledge():
    """搜索知识库"""
    keyword = request.args.get('keyword', '')
    type_ = request.args.get('type')
    category = request.args.get('category')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = KnowledgeBase.query.filter_by(is_published=True)
    
    if type_:
        query = query.filter_by(type=type_)
    
    if category:
        query = query.filter_by(category=category)
    
    if keyword:
        query = query.filter(
            db.or_(
                KnowledgeBase.question.like(f'%{keyword}%'),
                KnowledgeBase.answer.like(f'%{keyword}%'),
                KnowledgeBase.tags.like(f'%{keyword}%')
            )
        )
    
    # 按查看次数排序
    query = query.order_by(KnowledgeBase.view_count.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # 增加查看次数
    for item in pagination.items:
        item.increment_view()
    db.session.commit()
    
    return jsonify({
        'data': [k.to_dict() for k in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page
    })

@knowledge_bp.route('/types', methods=['GET'])
def get_types():
    """获取知识类型"""
    return jsonify(['电网考试', '考研', '校招', '其他'])
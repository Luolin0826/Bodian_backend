# app/routes/scripts.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_required
from app.models import db, Script

scripts_bp = Blueprint('scripts', __name__)

@scripts_bp.route('/search', methods=['GET'])
def search_scripts():
    """搜索话术"""
    keyword = request.args.get('keyword', '')
    category = request.args.get('category')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Script.query.filter_by(is_active=True)
    
    if category:
        query = query.filter_by(category=category)
    
    if keyword:
        query = query.filter(
            db.or_(
                Script.question.like(f'%{keyword}%'),
                Script.answer.like(f'%{keyword}%'),
                Script.keywords.like(f'%{keyword}%'),
                Script.title.like(f'%{keyword}%')
            )
        )
    
    # 按使用次数排序
    query = query.order_by(Script.usage_count.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # 增加使用次数
    for script in pagination.items:
        script.increment_usage()
    db.session.commit()
    
    return jsonify({
        'data': [s.to_dict() for s in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page
    })

@scripts_bp.route('/categories', methods=['GET'])
def get_categories():
    """获取话术分类"""
    categories = db.session.query(Script.category).distinct().all()
    return jsonify([c[0] for c in categories if c[0]])

@scripts_bp.route('', methods=['POST'])
@jwt_required()
def create_script():
    """创建话术"""
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    script = Script(
        category=data.get('category'),
        title=data.get('title'),
        question=data.get('question'),
        answer=data.get('answer', ''),
        keywords=data.get('keywords'),
        created_by=current_user_id
    )
    
    db.session.add(script)
    db.session.commit()
    
    return jsonify({
        'message': '话术创建成功',
        'data': script.to_dict()
    }), 201
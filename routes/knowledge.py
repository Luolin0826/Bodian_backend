# app/routes/knowledge.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from app.models import db, KnowledgeBase
from sqlalchemy import func, desc, or_

knowledge_bp = Blueprint('knowledge', __name__)

@knowledge_bp.route('/search', methods=['GET'])
def search_knowledge():
    """搜索知识库"""
    keyword = request.args.get('keyword', '')
    type_ = request.args.get('type')
    category = request.args.get('category')
    unit = request.args.get('unit')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = KnowledgeBase.query.filter_by(is_published=True)
    
    if type_:
        query = query.filter_by(type=type_)
    
    if category:
        query = query.filter_by(category=category)
    
    if unit:
        query = query.filter_by(unit=unit)
    
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

@knowledge_bp.route('/categories', methods=['GET'])
def get_categories():
    """获取知识分类"""
    type_ = request.args.get('type')
    
    query = KnowledgeBase.query.filter_by(is_published=True)
    
    if type_:
        query = query.filter_by(type=type_)
    
    categories = db.session.query(KnowledgeBase.category).filter(
        KnowledgeBase.category.isnot(None)
    ).distinct().all()
    
    return jsonify([c[0] for c in categories if c[0]])

@knowledge_bp.route('/stats', methods=['GET'])
def get_knowledge_stats():
    """获取知识库统计数据"""
    try:
        # 总数
        total = KnowledgeBase.query.filter_by(is_published=True).count()
        
        # 热门（查看次数>10的）
        popular = KnowledgeBase.query.filter(
            KnowledgeBase.is_published == True,
            KnowledgeBase.view_count > 10
        ).count()
        
        # 分类数量
        categories = db.session.query(KnowledgeBase.category).filter(
            KnowledgeBase.category.isnot(None),
            KnowledgeBase.is_published == True
        ).distinct().count()
        
        # 最近7天新增
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent = KnowledgeBase.query.filter(
            KnowledgeBase.is_published == True,
            KnowledgeBase.created_at >= seven_days_ago
        ).count()
        
        return jsonify({
            'total': total,
            'popular': popular,
            'categories': categories,
            'recent': recent
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@knowledge_bp.route('/type-stats', methods=['GET'])
def get_knowledge_type_stats():
    """获取知识库类型统计"""
    try:
        type_stats = db.session.query(
            KnowledgeBase.type,
            func.count(KnowledgeBase.id).label('count')
        ).filter(KnowledgeBase.is_published == True).group_by(KnowledgeBase.type).all()
        
        # 转换为前端需要的格式
        result = []
        type_labels = {
            '电网考试': '电网考试',
            '校招': '校园招聘', 
            '考研': '考研信息',
            '其他': '其他信息'
        }
        
        for type_name, count in type_stats:
            result.append({
                'value': type_name,
                'label': type_labels.get(type_name, type_name),
                'count': count
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@knowledge_bp.route('/unit-stats', methods=['GET'])
def get_knowledge_unit_stats():
    """获取省份电网统计"""
    try:
        unit_stats = db.session.query(
            KnowledgeBase.unit,
            func.count(KnowledgeBase.id).label('count')
        ).filter(
            KnowledgeBase.is_published == True,
            KnowledgeBase.unit.isnot(None)
        ).group_by(KnowledgeBase.unit).order_by(desc('count')).limit(10).all()
        
        result = []
        for unit, count in unit_stats:
            result.append({
                'value': unit,
                'label': f'{unit}电网',
                'count': count
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@knowledge_bp.route('/popular-tags', methods=['GET'])
def get_popular_tags():
    """获取热门标签"""
    try:
        # 从所有知识库中提取标签
        all_tags = []
        knowledges = KnowledgeBase.query.filter(
            KnowledgeBase.is_published == True,
            KnowledgeBase.tags.isnot(None)
        ).all()
        
        for knowledge in knowledges:
            if knowledge.tags:
                tags = [tag.strip() for tag in knowledge.tags.split(',') if tag.strip()]
                all_tags.extend(tags)
        
        # 统计标签频率
        from collections import Counter
        tag_counts = Counter(all_tags)
        
        # 返回前20个最热门的标签
        popular_tags = [tag for tag, count in tag_counts.most_common(20)]
        
        return jsonify(popular_tags)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@knowledge_bp.route('/category-options', methods=['GET'])
def get_category_options():
    """获取指定类型的分类选项"""
    try:
        type_ = request.args.get('type')
        if not type_:
            return jsonify([])
        
        categories = db.session.query(KnowledgeBase.category).filter(
            KnowledgeBase.type == type_,
            KnowledgeBase.category.isnot(None),
            KnowledgeBase.is_published == True
        ).distinct().all()
        
        result = []
        for category in categories:
            if category[0]:
                result.append({
                    'value': category[0],
                    'label': category[0]
                })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@knowledge_bp.route('', methods=['POST'])
@knowledge_bp.route('/', methods=['POST'])
@jwt_required()
def create_knowledge():
    """创建知识条目"""
    try:
        data = request.get_json()
        current_user_id = int(get_jwt_identity())
        
        knowledge = KnowledgeBase(
            type=data.get('type'),
            category=data.get('category'),
            question=data.get('question'),
            answer=data.get('answer'),
            related_questions=data.get('related_questions'),
            tags=data.get('tags'),
            unit=data.get('unit'),
            site=data.get('site'),
            source=data.get('source'),
            meta_data=data.get('metadata'),
            is_published=data.get('is_published', True),
            created_by=current_user_id
        )
        
        db.session.add(knowledge)
        db.session.commit()
        
        return jsonify({
            'message': '知识条目创建成功',
            'data': knowledge.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@knowledge_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_knowledge(id):
    """更新知识条目"""
    try:
        knowledge = KnowledgeBase.query.get_or_404(id)
        data = request.get_json()
        
        # 更新字段
        updateable_fields = [
            'type', 'category', 'question', 'answer', 'related_questions',
            'tags', 'unit', 'site', 'source', 'is_published'
        ]
        
        for field in updateable_fields:
            if field in data:
                setattr(knowledge, field, data[field])
        
        if 'metadata' in data:
            knowledge.meta_data = data['metadata']
        
        knowledge.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': '知识条目更新成功',
            'data': knowledge.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@knowledge_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_knowledge(id):
    """删除知识条目"""
    try:
        knowledge = KnowledgeBase.query.get_or_404(id)
        db.session.delete(knowledge)
        db.session.commit()
        
        return jsonify({'message': '知识条目删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
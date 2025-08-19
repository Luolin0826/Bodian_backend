# app/routes/scripts.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_required
from app.models import db, Script
from app.utils.auth_decorators import require_permission, log_operation

scripts_bp = Blueprint('scripts', __name__)

@scripts_bp.route('/search', methods=['GET'])
def search_scripts():
    """搜索话术"""
    try:
        keyword = request.args.get('keyword', '')
        category = request.args.get('category')
        script_type = request.args.get('type')
        data_source = request.args.get('source')
        platform = request.args.get('platform')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        sort_by = request.args.get('sort', 'usage_count')  # 排序字段
        
        query = Script.query.filter_by(is_active=True)
        
        # 筛选条件
        if category:
            query = query.filter_by(category=category)
        if script_type:
            query = query.filter_by(type=script_type)  # 修复：使用正确的字段名
        if data_source:
            query = query.filter_by(source=data_source)  # 修复：使用正确的字段名
        if platform:
            query = query.filter_by(platform=platform)
        
        # 关键词搜索
        if keyword:
            query = query.filter(
                db.or_(
                    Script.question.like(f'%{keyword}%'),
                    Script.answer.like(f'%{keyword}%'),
                    Script.keywords.like(f'%{keyword}%'),
                    Script.title.like(f'%{keyword}%')
                )
            )
        
        # 排序
        if sort_by == 'usage_count':
            query = query.order_by(Script.usage_count.desc())
        elif sort_by == 'created_at':
            query = query.order_by(Script.created_at.desc())
        elif sort_by == 'effectiveness':
            query = query.order_by(Script.effectiveness.desc())
        else:
            query = query.order_by(Script.usage_count.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': [s.to_dict() for s in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'搜索话术失败: {str(e)}'
        }), 500

@scripts_bp.route('/categories', methods=['GET'])
def get_categories():
    """获取话术分类"""
    try:
        categories = db.session.query(Script.category).distinct().filter(
            Script.category.isnot(None),
            Script.is_active == True
        ).all()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': [c[0] for c in categories if c[0]]
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取分类失败: {str(e)}'
        }), 500

@scripts_bp.route('/stats', methods=['GET'])
def get_script_stats():
    """获取话术统计数据"""
    try:
        stats = Script.get_stats()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取统计数据失败: {str(e)}'
        }), 500

@scripts_bp.route('/type-stats', methods=['GET'])
def get_script_type_stats():
    """获取话术类型统计"""
    try:
        stats = Script.get_type_stats()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取类型统计失败: {str(e)}'
        }), 500

@scripts_bp.route('/source-stats', methods=['GET'])
def get_script_source_stats():
    """获取数据来源统计"""
    try:
        stats = Script.get_source_stats()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取来源统计失败: {str(e)}'
        }), 500

@scripts_bp.route('/platform-stats', methods=['GET'])
def get_script_platform_stats():
    """获取平台统计"""
    try:
        stats = Script.get_platform_stats()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取平台统计失败: {str(e)}'
        }), 500

@scripts_bp.route('/<int:script_id>/copy', methods=['POST'])
def copy_script(script_id):
    """记录话术复制使用"""
    try:
        script = Script.query.get(script_id)
        if not script:
            return jsonify({
                'code': 404,
                'message': '话术不存在'
            }), 404
        
        # 增加使用次数
        script.increment_usage()
        db.session.commit()
        
        # 简单记录操作（可选）
        try:
            print(f'话术复制记录: 话术ID={script_id}, 新使用次数={script.usage_count}')
        except:
            pass
        
        return jsonify({
            'code': 200,
            'message': '使用次数已更新',
            'data': {
                'id': script.id,
                'usage_count': script.usage_count
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'更新使用次数失败: {str(e)}'
        }), 500

@scripts_bp.route('', methods=['POST'])
@jwt_required()
@require_permission('operation', 'script.create')
def create_script():
    """创建话术"""
    try:
        data = request.get_json()
        current_user_id = int(get_jwt_identity())
        
        script = Script(
            category=data.get('category'),
            title=data.get('title'),
            question=data.get('question'),
            answer=data.get('answer', ''),
            keywords=data.get('keywords'),
            # 处理字段映射：前端可能发送 type/source，也可能发送 script_type/data_source
            type=data.get('type') or data.get('script_type'),
            source=data.get('source') or data.get('data_source'), 
            platform=data.get('platform'),
            created_by=current_user_id
        )
        
        db.session.add(script)
        db.session.commit()
        
        # 手动记录操作日志（简化版本）
        try:
            from flask_jwt_extended import get_current_user
            current_user = get_current_user()
            if current_user:
                print(f'话术创建记录: 用户={current_user.username}, 话术ID={script.id}, 标题={script.title}')
        except Exception as log_error:
            print(f'记录创建日志失败: {str(log_error)}')
        
        return jsonify({
            'code': 201,
            'message': '话术创建成功',
            'data': script.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'创建话术失败: {str(e)}'
        }), 500

@scripts_bp.route('/<int:script_id>', methods=['PUT'])
@jwt_required()
@require_permission('operation', 'script.edit')
def update_script(script_id):
    """更新话术"""
    try:
        script = Script.query.get(script_id)
        if not script:
            return jsonify({
                'code': 404,
                'message': '话术不存在'
            }), 404
        
        data = request.get_json()
        
        # 更新字段（包括适配原有字段和新字段）
        field_mapping = {
            'category': 'category',
            'title': 'title',
            'question': 'question',
            'answer': 'answer',
            'keywords': 'keywords',
            'script_type': 'script_type',
            'data_source': 'data_source',
            'platform': 'platform',
            'effectiveness': 'effectiveness',
            'usage_count': 'usage_count',
            # 兼容原有字段
            'type': 'type',
            'source': 'source'
        }
        
        for field_name, model_attr in field_mapping.items():
            if field_name in data:
                setattr(script, model_attr, data[field_name])
        
        db.session.commit()
        
        # 手动记录操作日志（简化版本，避免装饰器问题）
        try:
            from flask_jwt_extended import get_current_user
            current_user = get_current_user()
            if current_user:
                from app.models import OperationLog
                log = OperationLog(
                    user_id=current_user.id,
                    username=current_user.username,
                    action='update',
                    resource='script',
                    resource_id=str(script_id),
                    description='更新话术',
                    ip_address=request.remote_addr or '127.0.0.1',
                    user_agent=request.headers.get('User-Agent', ''),
                    sensitive_operation=False
                )
                db.session.add(log)
                db.session.commit()
        except Exception as log_error:
            # 日志记录失败不应该影响主要业务
            print(f'记录操作日志失败: {str(log_error)}')
        
        return jsonify({
            'code': 200,
            'message': '话术更新成功',
            'data': script.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'更新话术失败: {str(e)}'
        }), 500

@scripts_bp.route('/<int:script_id>', methods=['DELETE'])
@jwt_required()
@require_permission('operation', 'script.delete')
@log_operation('delete', 'script', '删除话术', sensitive=True)
def delete_script(script_id):
    """删除话术"""
    try:
        script = Script.query.get(script_id)
        if not script:
            return jsonify({
                'code': 404,
                'message': '话术不存在'
            }), 404
        
        # 软删除
        script.is_active = False
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '话术删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'删除话术失败: {str(e)}'
        }), 500
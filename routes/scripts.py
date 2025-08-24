# app/routes/scripts.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_required
from app.models import db, Script, ScriptFavorite
from app.utils.auth_decorators import require_permission, log_operation

scripts_bp = Blueprint('scripts', __name__)

@scripts_bp.route('/search', methods=['GET'])
@jwt_required()
def search_scripts():
    """搜索话术"""
    try:
        keyword = request.args.get('keyword', '')
        category = request.args.get('category')
        script_type = request.args.get('type')
        data_source = request.args.get('source')
        platform = request.args.get('platform')
        
        # 新的三维分类筛选参数
        script_type_new = request.args.get('script_type_new')
        content_type_new = request.args.get('content_type_new')
        platform_new = request.args.get('platform_new')
        
        # 新分类体系筛选参数
        primary_category = request.args.get('primary_category')
        secondary_category = request.args.get('secondary_category')
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        sort_by = request.args.get('sort', 'usage_count')  # 排序字段
        
        current_user_id = int(get_jwt_identity())
        
        # 使用LEFT JOIN关联收藏表，获取当前用户的收藏状态
        from sqlalchemy import and_
        query = db.session.query(Script, ScriptFavorite.id.label('favorite_id')).outerjoin(
            ScriptFavorite, and_(
                ScriptFavorite.script_id == Script.id,
                ScriptFavorite.user_id == current_user_id
            )
        ).filter(Script.is_active == True)
        
        # 原有筛选条件（注意需要用Script.字段名）
        if category:
            query = query.filter(Script.category == category)
        if script_type:
            query = query.filter(Script.type == script_type)
        if data_source:
            query = query.filter(Script.source == data_source)
        if platform:
            query = query.filter(Script.platform == platform)
            
        # 新的三维分类筛选条件
        if script_type_new:
            query = query.filter(Script.script_type_new == script_type_new)
        if content_type_new:
            query = query.filter(Script.content_type_new == content_type_new)
        if platform_new:
            query = query.filter(Script.platform_new == platform_new)
            
        # 新分类体系筛选条件
        if primary_category:
            query = query.filter(Script.primary_category == primary_category)
        if secondary_category:
            query = query.filter(Script.secondary_category == secondary_category)
        
        # 关键词搜索（支持新旧关键词字段）
        if keyword:
            query = query.filter(
                db.or_(
                    Script.question.like(f'%{keyword}%'),
                    Script.answer.like(f'%{keyword}%'),
                    Script.keywords.like(f'%{keyword}%'),
                    Script.keywords_new.like(f'%{keyword}%'),
                    Script.title.like(f'%{keyword}%')
                )
            )
        
        # 三级排序（置顶 > 收藏 > 普通 > 原有排序）
        if sort_by == 'usage_count':
            query = query.order_by(
                Script.is_pinned.desc(),
                ScriptFavorite.id.isnot(None).desc(),
                Script.usage_count.desc()
            )
        elif sort_by == 'created_at':
            query = query.order_by(
                Script.is_pinned.desc(),
                ScriptFavorite.id.isnot(None).desc(),
                Script.created_at.desc()
            )
        elif sort_by == 'effectiveness':
            query = query.order_by(
                Script.is_pinned.desc(),
                ScriptFavorite.id.isnot(None).desc(),
                Script.effectiveness.desc()
            )
        else:
            query = query.order_by(
                Script.is_pinned.desc(),
                ScriptFavorite.id.isnot(None).desc(),
                Script.usage_count.desc()
            )
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 处理结果，添加收藏状态
        scripts_data = []
        for item in pagination.items:
            try:
                # SQLAlchemy Row对象解包
                if len(item) == 2:
                    script, favorite_id = item[0], item[1]
                else:
                    script, favorite_id = item, None
                
                script_dict = script.to_dict()
                script_dict['is_favorited'] = favorite_id is not None
                scripts_data.append(script_dict)
            except Exception as inner_e:
                # 如果解包失败，使用备用方法
                print(f'解包失败，使用备用方法: {inner_e}')
                if hasattr(item, 'to_dict'):
                    script_dict = item.to_dict()
                    script_dict['is_favorited'] = False
                    scripts_data.append(script_dict)
                else:
                    raise Exception(f'无法处理项目类型: {type(item)}')
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': scripts_data,
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
@jwt_required()
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
@jwt_required()
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
@jwt_required()
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
@jwt_required()
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
@jwt_required()
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

@scripts_bp.route('/script-type-new-stats', methods=['GET'])
@jwt_required()
def get_script_type_new_stats():
    """获取新话术类型统计"""
    try:
        stats = Script.get_script_type_new_stats()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取话术类型统计失败: {str(e)}'
        }), 500

@scripts_bp.route('/content-type-stats', methods=['GET'])
@jwt_required()
def get_content_type_stats():
    """获取内容类型统计"""
    try:
        stats = Script.get_content_type_stats()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取内容类型统计失败: {str(e)}'
        }), 500

@scripts_bp.route('/platform-new-stats', methods=['GET'])
@jwt_required()
def get_platform_new_stats():
    """获取新平台统计"""
    try:
        stats = Script.get_platform_new_stats()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取新平台统计失败: {str(e)}'
        }), 500

@scripts_bp.route('/three-dimension-stats', methods=['GET'])
@jwt_required()
def get_three_dimension_stats():
    """获取三维分类综合统计"""
    try:
        stats = Script.get_three_dimension_stats()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取三维分类统计失败: {str(e)}'
        }), 500

@scripts_bp.route('/primary-category-stats', methods=['GET'])
@jwt_required()
def get_primary_category_stats():
    """获取主分类统计"""
    try:
        stats = Script.get_primary_category_stats()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取主分类统计失败: {str(e)}'
        }), 500

@scripts_bp.route('/secondary-category-stats', methods=['GET'])
@jwt_required()
def get_secondary_category_stats():
    """获取子分类统计"""
    try:
        stats = Script.get_secondary_category_stats()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取子分类统计失败: {str(e)}'
        }), 500

@scripts_bp.route('/new-classification-stats', methods=['GET'])
@jwt_required()
def get_new_classification_stats():
    """获取新分类体系综合统计"""
    try:
        stats = Script.get_new_classification_stats()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取新分类体系统计失败: {str(e)}'
        }), 500

@scripts_bp.route('/<int:script_id>/copy', methods=['POST'])
@jwt_required()
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
        
        # 根据内容类型自动设置category
        content_type_to_category = {
            'exam_guidance': '考试指导',
            'course_introduction': '课程介绍', 
            'career_planning': '职业规划',
            'application_process': '申请流程',
            'company_service': '公司服务',
            'general_support': '综合支持'
        }
        
        # 如果没有传统category，从content_type_new推导
        category = data.get('category')
        if not category and data.get('content_type_new'):
            category = content_type_to_category.get(data.get('content_type_new'), '其他')
        elif not category:
            category = '其他'  # 默认分类
        
        # 根据script_type_new推导旧的type字段
        script_type_to_type = {
            'consultation': 'postgrad_consult',
            'sales_promotion': 'sales_conversation', 
            'service_support': 'grid_exam',
            'content_marketing': 'social_media_reply',
            'expert_guidance': 'grid_exam'
        }
        
        # 为了兼容，从新字段推导旧字段的值
        old_type = data.get('type') or data.get('script_type')
        if not old_type and data.get('script_type_new'):
            old_type = script_type_to_type.get(data.get('script_type_new'), 'grid_exam')
        elif not old_type:
            old_type = 'grid_exam'  # 默认值
        
        script = Script(
            category=category,
            title=data.get('title') or '未命名话术',  # 确保title不为空
            question=data.get('question'),
            answer=data.get('answer', ''),
            keywords=data.get('keywords', ''),
            # 旧字段（保持兼容性）
            type=old_type,
            source=data.get('source') or data.get('data_source') or '用户创建', 
            platform=data.get('platform'),
            # 新分类体系字段
            primary_category=data.get('primary_category'),
            secondary_category=data.get('secondary_category'),
            # 新的三维分类字段（向后兼容）
            script_type_new=data.get('script_type_new'),
            content_type_new=data.get('content_type_new'),
            platform_new=data.get('platform_new'),
            keywords_new=data.get('keywords_new', data.get('keywords', '')),
            classification_status='completed',
            classification_version='v2.0',
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
            'source': 'source',
            # 新分类体系字段
            'primary_category': 'primary_category',
            'secondary_category': 'secondary_category',
            # 新的三维分类字段（向后兼容）
            'script_type_new': 'script_type_new',
            'content_type_new': 'content_type_new',
            'platform_new': 'platform_new',
            'keywords_new': 'keywords_new',
            'classification_meta': 'classification_meta',
            'classification_status': 'classification_status',
            'classification_version': 'classification_version'
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

@scripts_bp.route('/<int:script_id>/pin', methods=['PUT'])
@jwt_required()
@require_permission('operation', 'script.edit')
def pin_script(script_id):
    """置顶话术"""
    try:
        script = Script.query.get(script_id)
        if not script:
            return jsonify({
                'code': 404,
                'message': '话术不存在'
            }), 404
        
        script.is_pinned = True
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '话术置顶成功',
            'data': script.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'置顶话术失败: {str(e)}'
        }), 500

@scripts_bp.route('/<int:script_id>/unpin', methods=['PUT'])
@jwt_required()
@require_permission('operation', 'script.edit')
def unpin_script(script_id):
    """取消置顶话术"""
    try:
        script = Script.query.get(script_id)
        if not script:
            return jsonify({
                'code': 404,
                'message': '话术不存在'
            }), 404
        
        script.is_pinned = False
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '取消置顶成功',
            'data': script.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'取消置顶失败: {str(e)}'
        }), 500

@scripts_bp.route('/<int:script_id>/favorite', methods=['POST'])
@jwt_required()
def favorite_script(script_id):
    """收藏话术"""
    try:
        current_user_id = int(get_jwt_identity())
        
        # 检查话术是否存在
        script = Script.query.get(script_id)
        if not script or not script.is_active:
            return jsonify({
                'code': 404,
                'message': '话术不存在'
            }), 404
        
        # 检查是否已收藏
        existing_favorite = ScriptFavorite.query.filter_by(
            user_id=current_user_id,
            script_id=script_id
        ).first()
        
        if existing_favorite:
            return jsonify({
                'code': 400,
                'message': '话术已收藏'
            }), 400
        
        # 创建收藏记录
        favorite = ScriptFavorite(
            user_id=current_user_id,
            script_id=script_id
        )
        
        db.session.add(favorite)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '收藏成功',
            'data': favorite.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'收藏失败: {str(e)}'
        }), 500

@scripts_bp.route('/<int:script_id>/favorite', methods=['DELETE'])
@jwt_required()
def unfavorite_script(script_id):
    """取消收藏话术"""
    try:
        current_user_id = int(get_jwt_identity())
        
        # 查找收藏记录
        favorite = ScriptFavorite.query.filter_by(
            user_id=current_user_id,
            script_id=script_id
        ).first()
        
        if not favorite:
            return jsonify({
                'code': 404,
                'message': '收藏记录不存在'
            }), 404
        
        db.session.delete(favorite)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '取消收藏成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'取消收藏失败: {str(e)}'
        }), 500

@scripts_bp.route('/favorites', methods=['GET'])
@jwt_required()
def get_user_favorites():
    """获取用户收藏的话术列表"""
    try:
        current_user_id = int(get_jwt_identity())
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 获取用户收藏的话术
        pagination = ScriptFavorite.get_user_favorites(
            user_id=current_user_id,
            page=page,
            per_page=per_page
        )
        
        # 转换为字典格式并添加收藏状态
        scripts_data = []
        for script in pagination.items:
            script_dict = script.to_dict()
            script_dict['is_favorited'] = True  # 收藏列表中的话术都是已收藏
            scripts_data.append(script_dict)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': scripts_data,
            'total': pagination.total,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取收藏列表失败: {str(e)}'
        }), 500
# app/routes/avatars.py
"""
头像相关API接口
"""
from flask import Blueprint, jsonify, request
from datetime import datetime
from app.utils.avatar_utils import (
    get_all_avatar_ids, 
    get_avatar_categories, 
    get_avatar_by_id,
    DEFAULT_AVATARS
)

avatars_bp = Blueprint('avatars', __name__)

@avatars_bp.route('/list', methods=['GET', 'OPTIONS'])
def get_avatar_list():
    """获取所有可用头像列表"""
    # 处理预检请求
    if request.method == 'OPTIONS':
        return '', 200
        
    categories = get_avatar_categories()
    
    # 构建完整的头像数据
    avatar_data = {}
    for category, avatar_ids in categories.items():
        avatar_data[category] = []
        for avatar_id in avatar_ids:
            avatar_data[category].append({
                'id': avatar_id,
                'name': get_avatar_name(avatar_id),
                'data_url': get_avatar_by_id(avatar_id)
            })
    
    return jsonify({
        'categories': avatar_data,
        'total': len(get_all_avatar_ids())
    }), 200

@avatars_bp.route('/categories', methods=['GET', 'OPTIONS'])
def get_categories():
    """获取头像分类信息"""
    # 处理预检请求
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify(get_avatar_categories()), 200

@avatars_bp.route('/<avatar_id>', methods=['GET', 'OPTIONS'])
def get_avatar(avatar_id):
    """根据ID获取单个头像"""
    # 处理预检请求
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        if avatar_id not in get_all_avatar_ids():
            return jsonify({
                'success': False,
                'message': '头像ID不存在',
                'data': None,
                'available_ids': get_all_avatar_ids()
            }), 404
        
        # 获取头像数据
        data_url = get_avatar_by_id(avatar_id)
        if not data_url:
            return jsonify({
                'success': False,
                'message': '头像数据获取失败',
                'data': None
            }), 500
        
        # 成功响应
        response_data = {
            'success': True,
            'message': '获取成功',
            'data': {
                'id': avatar_id,
                'name': get_avatar_name(avatar_id),
                'data_url': data_url
            }
        }
        
        # 兼容旧格式，直接返回data字段内容
        response_data.update(response_data['data'])
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}',
            'data': None
        }), 500

def get_avatar_name(avatar_id: str) -> str:
    """获取头像的中文名称"""
    name_mapping = {
        # 动物系列
        'cat': '可爱小猫',
        'dog': '忠诚小狗', 
        'bear': '憨厚小熊',
        'rabbit': '萌萌小兔',
        'panda': '呆萌熊猫',
        'fox': '聪明小狐',
        
        # 角色系列
        'robot': '酷炫机器人',
        'princess': '优雅公主',
        'superhero': '超级英雄',
        'ninja': '神秘忍者',
        'pirate': '勇敢海盗',
        'astronaut': '太空宇航员',
        
        # 表情系列
        'smile': '开心笑脸',
        'wink': '俏皮眨眼',
        'cool': '酷炫墨镜',
        'shy': '害羞脸红',
        'happy': '超级开心',
        'playful': '调皮捣蛋'
    }
    
    return name_mapping.get(avatar_id, avatar_id)

@avatars_bp.route('/debug/<avatar_id>', methods=['GET', 'OPTIONS'])
def debug_avatar(avatar_id):
    """调试用头像接口 - 提供额外的调试信息"""
    # 处理预检请求
    if request.method == 'OPTIONS':
        return '', 200
    
    # 检查头像ID是否存在
    all_ids = get_all_avatar_ids()
    
    debug_info = {
        'request_avatar_id': avatar_id,
        'avatar_id_exists': avatar_id in all_ids,
        'all_available_ids': all_ids,
        'request_headers': dict(request.headers),
        'request_method': request.method,
        'timestamp': str(datetime.now())
    }
    
    if avatar_id not in all_ids:
        return jsonify({
            'success': False,
            'message': '头像ID不存在',
            'debug': debug_info
        }), 404
    
    try:
        avatar_data = {
            'id': avatar_id,
            'name': get_avatar_name(avatar_id),
            'data_url': get_avatar_by_id(avatar_id)
        }
        
        return jsonify({
            'success': True,
            'data': avatar_data,
            'debug': debug_info
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取头像数据失败: {str(e)}',
            'debug': debug_info
        }), 500
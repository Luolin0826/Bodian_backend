# app/routes/operation_logs.py
from flask import Blueprint, request, jsonify
from app.models import db, OperationLog, User, Department
from app.utils.auth_decorators import require_permission, data_scope_filter
from flask_jwt_extended import jwt_required
from datetime import datetime

operation_logs_bp = Blueprint('operation_logs', __name__)

@operation_logs_bp.route('/operation-logs', methods=['GET'])
@jwt_required()
@require_permission('menu', 'log.operation')
def get_operation_logs():
    """获取操作日志列表"""
    try:
        # 获取查询参数
        keyword = request.args.get('keyword', '').strip()
        action = request.args.get('action', '').strip()
        resource = request.args.get('resource', '').strip()
        department_id = request.args.get('department_id', type=int)
        user_id = request.args.get('user_id', type=int)
        date_start = request.args.get('date_start', '').strip()
        date_end = request.args.get('date_end', '').strip()
        sensitive_only = request.args.get('sensitive_only', '').strip().lower() == 'true'
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # 构建查询
        query = OperationLog.query
        
        if keyword:
            query = query.filter(
                db.or_(
                    OperationLog.username.like(f'%{keyword}%'),
                    OperationLog.employee_no.like(f'%{keyword}%'),
                    OperationLog.description.like(f'%{keyword}%'),
                    OperationLog.ip_address.like(f'%{keyword}%')
                )
            )
        
        if action:
            query = query.filter(OperationLog.action == action)
        
        if resource:
            query = query.filter(OperationLog.resource == resource)
        
        if department_id:
            # 通过用户表关联查询部门
            query = query.join(User, OperationLog.user_id == User.id).filter(
                User.department_id == department_id
            )
        
        if user_id:
            query = query.filter(OperationLog.user_id == user_id)
        
        if date_start:
            try:
                start_date = datetime.strptime(date_start, '%Y-%m-%d')
                query = query.filter(OperationLog.created_at >= start_date)
            except ValueError:
                return jsonify({'code': 400, 'message': '开始时间格式错误'}), 400
        
        if date_end:
            try:
                end_date = datetime.strptime(date_end, '%Y-%m-%d')
                # 设置为当天的23:59:59
                end_date = end_date.replace(hour=23, minute=59, second=59)
                query = query.filter(OperationLog.created_at <= end_date)
            except ValueError:
                return jsonify({'code': 400, 'message': '结束时间格式错误'}), 400
        
        if sensitive_only:
            query = query.filter(OperationLog.sensitive_operation == True)
        
        # 分页查询，按时间倒序
        pagination = query.order_by(OperationLog.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        logs = [log.to_dict() for log in pagination.items]
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': logs,
            'total': pagination.total,
            'page': page,
            'per_page': per_page
        })
    
    except Exception as e:
        return jsonify({'code': 500, 'message': f'获取操作日志失败: {str(e)}'}), 500

@operation_logs_bp.route('/operation-logs/<int:log_id>', methods=['GET'])
@jwt_required()
@require_permission('menu', 'log.operation')
def get_operation_log_detail(log_id):
    """获取操作日志详情"""
    try:
        log = OperationLog.query.get(log_id)
        if not log:
            return jsonify({'code': 404, 'message': '操作日志不存在'}), 404
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': log.to_dict()
        })
    
    except Exception as e:
        return jsonify({'code': 500, 'message': f'获取操作日志详情失败: {str(e)}'}), 500

@operation_logs_bp.route('/operation-logs/stats', methods=['GET'])
@jwt_required()
@require_permission('menu', 'log.operation')
def get_operation_logs_stats():
    """获取操作日志统计"""
    try:
        # 获取时间范围参数
        days = int(request.args.get('days', 7))  # 默认最近7天
        
        # 计算开始时间
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=days)
        
        # 按操作类型统计
        action_stats = db.session.query(
            OperationLog.action,
            db.func.count(OperationLog.id).label('count')
        ).filter(
            OperationLog.created_at >= start_date
        ).group_by(OperationLog.action).all()
        
        # 按资源类型统计
        resource_stats = db.session.query(
            OperationLog.resource,
            db.func.count(OperationLog.id).label('count')
        ).filter(
            OperationLog.created_at >= start_date
        ).group_by(OperationLog.resource).all()
        
        # 按用户统计（前10名）
        user_stats = db.session.query(
            OperationLog.username,
            OperationLog.department_name,
            db.func.count(OperationLog.id).label('count')
        ).filter(
            OperationLog.created_at >= start_date
        ).group_by(
            OperationLog.username,
            OperationLog.department_name
        ).order_by(
            db.func.count(OperationLog.id).desc()
        ).limit(10).all()
        
        # 敏感操作统计
        sensitive_count = OperationLog.query.filter(
            OperationLog.created_at >= start_date,
            OperationLog.sensitive_operation == True
        ).count()
        
        # 总操作数
        total_count = OperationLog.query.filter(
            OperationLog.created_at >= start_date
        ).count()
        
        # 按天统计（折线图数据）
        daily_stats = db.session.query(
            db.func.date(OperationLog.created_at).label('date'),
            db.func.count(OperationLog.id).label('count')
        ).filter(
            OperationLog.created_at >= start_date
        ).group_by(
            db.func.date(OperationLog.created_at)
        ).order_by(
            db.func.date(OperationLog.created_at)
        ).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'total_count': total_count,
                'sensitive_count': sensitive_count,
                'action_stats': [{'action': item[0], 'count': item[1]} for item in action_stats],
                'resource_stats': [{'resource': item[0], 'count': item[1]} for item in resource_stats],
                'user_stats': [
                    {
                        'username': item[0],
                        'department_name': item[1] or '未分配',
                        'count': item[2]
                    } for item in user_stats
                ],
                'daily_stats': [
                    {
                        'date': item[0].strftime('%Y-%m-%d'),
                        'count': item[1]
                    } for item in daily_stats
                ]
            }
        })
    
    except Exception as e:
        return jsonify({'code': 500, 'message': f'获取操作日志统计失败: {str(e)}'}), 500

@operation_logs_bp.route('/operation-logs/export', methods=['GET'])
@jwt_required()
@require_permission('operation', 'log.export')
def export_operation_logs():
    """导出操作日志"""
    try:
        # 获取查询参数（与获取列表相同的参数）
        keyword = request.args.get('keyword', '').strip()
        action = request.args.get('action', '').strip()
        resource = request.args.get('resource', '').strip()
        department_id = request.args.get('department_id', type=int)
        user_id = request.args.get('user_id', type=int)
        date_start = request.args.get('date_start', '').strip()
        date_end = request.args.get('date_end', '').strip()
        sensitive_only = request.args.get('sensitive_only', '').strip().lower() == 'true'
        
        # 构建查询（与获取列表相同的逻辑）
        query = OperationLog.query
        
        if keyword:
            query = query.filter(
                db.or_(
                    OperationLog.username.like(f'%{keyword}%'),
                    OperationLog.employee_no.like(f'%{keyword}%'),
                    OperationLog.description.like(f'%{keyword}%'),
                    OperationLog.ip_address.like(f'%{keyword}%')
                )
            )
        
        if action:
            query = query.filter(OperationLog.action == action)
        
        if resource:
            query = query.filter(OperationLog.resource == resource)
        
        if department_id:
            query = query.join(User, OperationLog.user_id == User.id).filter(
                User.department_id == department_id
            )
        
        if user_id:
            query = query.filter(OperationLog.user_id == user_id)
        
        if date_start:
            try:
                start_date = datetime.strptime(date_start, '%Y-%m-%d')
                query = query.filter(OperationLog.created_at >= start_date)
            except ValueError:
                return jsonify({'code': 400, 'message': '开始时间格式错误'}), 400
        
        if date_end:
            try:
                end_date = datetime.strptime(date_end, '%Y-%m-%d')
                end_date = end_date.replace(hour=23, minute=59, second=59)
                query = query.filter(OperationLog.created_at <= end_date)
            except ValueError:
                return jsonify({'code': 400, 'message': '结束时间格式错误'}), 400
        
        if sensitive_only:
            query = query.filter(OperationLog.sensitive_operation == True)
        
        # 获取所有符合条件的日志（限制最大导出数量）
        max_export = 10000
        logs = query.order_by(OperationLog.created_at.desc()).limit(max_export).all()
        
        # 构建导出数据
        export_data = []
        for log in logs:
            export_data.append({
                'ID': log.id,
                '用户名': log.username,
                '工号': log.employee_no or '',
                '部门': log.department_name or '',
                '操作类型': log.action,
                '操作对象': log.resource,
                '对象ID': log.resource_id or '',
                '操作描述': log.description,
                'IP地址': log.ip_address,
                '是否敏感操作': '是' if log.sensitive_operation else '否',
                '操作时间': log.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': export_data,
            'total': len(export_data)
        })
    
    except Exception as e:
        return jsonify({'code': 500, 'message': f'导出操作日志失败: {str(e)}'}), 500
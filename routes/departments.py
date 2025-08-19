# app/routes/departments.py
from flask import Blueprint, request, jsonify
from app.models import db, Department, User
from app.utils.auth_decorators import require_permission, log_operation
from flask_jwt_extended import jwt_required

departments_bp = Blueprint('departments', __name__)

@departments_bp.route('/departments', methods=['GET'])
@jwt_required()
@require_permission('menu', 'department.list')
def get_departments():
    """获取部门列表"""
    try:
        # 获取查询参数
        keyword = request.args.get('keyword', '').strip()
        type_filter = request.args.get('type', '').strip()
        region_filter = request.args.get('region', '').strip()
        is_active = request.args.get('is_active')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # 构建查询
        query = Department.query
        
        if keyword:
            query = query.filter(
                db.or_(
                    Department.name.like(f'%{keyword}%'),
                    Department.code.like(f'%{keyword}%'),
                    Department.description.like(f'%{keyword}%')
                )
            )
        
        if type_filter:
            query = query.filter(Department.type == type_filter)
        
        if region_filter:
            query = query.filter(Department.region == region_filter)
        
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            query = query.filter(Department.is_active == is_active_bool)
        
        # 分页查询
        pagination = query.order_by(Department.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        departments = [dept.to_dict() for dept in pagination.items]
        
        # 前端期望直接返回数组格式，如果需要分页信息，通过headers传递
        return jsonify(departments)
    
    except Exception as e:
        return jsonify({'code': 500, 'message': f'获取部门列表失败: {str(e)}'}), 500

@departments_bp.route('/departments/tree', methods=['GET'])
@jwt_required()
@require_permission('menu', 'department.list')
def get_departments_tree():
    """获取部门树形结构"""
    try:
        # 获取所有启用的部门
        departments = Department.query.filter_by(is_active=True).all()
        
        # 构建树形结构
        def build_tree(parent_id=None):
            tree = []
            for dept in departments:
                if dept.parent_id == parent_id:
                    node = dept.to_tree_dict()
                    node['children'] = build_tree(dept.id)
                    tree.append(node)
            return tree
        
        tree_data = build_tree()
        
        # 前端期望直接返回数组格式
        return jsonify(tree_data)
    
    except Exception as e:
        return jsonify({'code': 500, 'message': f'获取部门树失败: {str(e)}'}), 500

@departments_bp.route('/departments', methods=['POST'])
@jwt_required()
@require_permission('operation', 'department.create')
@log_operation('create', 'department', '创建部门')
def create_department():
    """创建部门"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['code', 'name', 'type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'code': 400, 'message': f'缺少必需字段: {field}'}), 400
        
        # 检查部门编码是否已存在
        existing_dept = Department.query.filter_by(code=data['code']).first()
        if existing_dept:
            return jsonify({'code': 400, 'message': '部门编码已存在'}), 400
        
        # 验证上级部门
        parent_id = data.get('parent_id')
        if parent_id:
            # 处理前端可能传递的事件对象或其他非数字类型
            if isinstance(parent_id, dict):
                return jsonify({'code': 400, 'message': '上级部门ID格式错误，应为数字'}), 400
            try:
                parent_id = int(parent_id) if parent_id else None
            except (ValueError, TypeError):
                return jsonify({'code': 400, 'message': '上级部门ID必须是数字'}), 400
            
            if parent_id:
                parent_dept = Department.query.get(parent_id)
                if not parent_dept:
                    return jsonify({'code': 400, 'message': '上级部门不存在'}), 400
        
        # 验证部门负责人
        if data.get('manager_id'):
            manager = User.query.get(data['manager_id'])
            if not manager:
                return jsonify({'code': 400, 'message': '部门负责人不存在'}), 400
        
        # 处理manager_id
        manager_id = data.get('manager_id')
        if manager_id:
            try:
                manager_id = int(manager_id) if manager_id else None
            except (ValueError, TypeError):
                return jsonify({'code': 400, 'message': '部门负责人ID必须是数字'}), 400
        
        # 创建部门
        department = Department(
            code=data['code'],
            name=data['name'],
            type=data['type'],
            parent_id=parent_id,
            region=data.get('region'),
            manager_id=manager_id,
            description=data.get('description')
        )
        
        db.session.add(department)
        db.session.commit()
        
        return jsonify({
            'code': 201,
            'message': '部门创建成功',
            'data': {'id': department.id}
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'创建部门失败: {str(e)}'}), 500

@departments_bp.route('/departments/<int:dept_id>', methods=['PUT'])
@jwt_required()
@require_permission('operation', 'department.edit')
@log_operation('update', 'department', '更新部门')
def update_department(dept_id):
    """更新部门"""
    try:
        department = Department.query.get(dept_id)
        if not department:
            return jsonify({'code': 404, 'message': '部门不存在'}), 404
        
        data = request.get_json()
        
        # 检查部门编码是否已被其他部门使用
        if data.get('code') and data['code'] != department.code:
            existing_dept = Department.query.filter_by(code=data['code']).first()
            if existing_dept:
                return jsonify({'code': 400, 'message': '部门编码已存在'}), 400
        
        # 验证上级部门
        update_parent_id = data.get('parent_id')
        if update_parent_id is not None:
            # 处理前端可能传递的事件对象或其他非数字类型
            if isinstance(update_parent_id, dict):
                return jsonify({'code': 400, 'message': '上级部门ID格式错误，应为数字'}), 400
            try:
                update_parent_id = int(update_parent_id) if update_parent_id else None
            except (ValueError, TypeError):
                return jsonify({'code': 400, 'message': '上级部门ID必须是数字'}), 400
                
            if update_parent_id != department.parent_id:
                if update_parent_id == department.id:
                    return jsonify({'code': 400, 'message': '不能设置自己为上级部门'}), 400
                
                if update_parent_id:
                    parent_dept = Department.query.get(update_parent_id)
                    if not parent_dept:
                        return jsonify({'code': 400, 'message': '上级部门不存在'}), 400
        
        # 验证部门负责人
        update_manager_id = data.get('manager_id')
        if update_manager_id is not None:
            if isinstance(update_manager_id, dict):
                return jsonify({'code': 400, 'message': '部门负责人ID格式错误，应为数字'}), 400
            try:
                update_manager_id = int(update_manager_id) if update_manager_id else None
            except (ValueError, TypeError):
                return jsonify({'code': 400, 'message': '部门负责人ID必须是数字'}), 400
                
            if update_manager_id != department.manager_id:
                if update_manager_id:
                    manager = User.query.get(update_manager_id)
                    if not manager:
                        return jsonify({'code': 400, 'message': '部门负责人不存在'}), 400
        
        # 更新部门信息
        for field in ['code', 'name', 'type', 'region', 'description']:
            if field in data:
                setattr(department, field, data[field])
        
        # 单独处理ID字段
        if 'parent_id' in data:
            setattr(department, 'parent_id', update_parent_id)
        if 'manager_id' in data:
            setattr(department, 'manager_id', update_manager_id)
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '部门更新成功'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'更新部门失败: {str(e)}'}), 500

@departments_bp.route('/departments/<int:dept_id>', methods=['DELETE'])
@jwt_required()
@require_permission('operation', 'department.delete')
@log_operation('delete', 'department', '删除部门', sensitive=True)
def delete_department(dept_id):
    """删除部门"""
    try:
        department = Department.query.get(dept_id)
        if not department:
            return jsonify({'code': 404, 'message': '部门不存在'}), 404
        
        # 检查是否有子部门
        child_departments = Department.query.filter_by(parent_id=dept_id).count()
        if child_departments > 0:
            return jsonify({'code': 400, 'message': '该部门下还有子部门，无法删除'}), 400
        
        # 检查是否有员工
        employees = User.query.filter_by(department_id=dept_id, is_active=True).count()
        if employees > 0:
            return jsonify({'code': 400, 'message': '该部门下还有员工，无法删除'}), 400
        
        db.session.delete(department)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '部门删除成功'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'删除部门失败: {str(e)}'}), 500

@departments_bp.route('/departments/<int:dept_id>/employees', methods=['GET'])
@jwt_required()
@require_permission('menu', 'department.employee')
def get_department_employees(dept_id):
    """获取部门员工"""
    try:
        department = Department.query.get(dept_id)
        if not department:
            return jsonify({'code': 404, 'message': '部门不存在'}), 404
        
        employees = User.query.filter_by(department_id=dept_id, is_active=True).all()
        
        employee_list = []
        for employee in employees:
            employee_dict = employee.to_dict()
            # 只返回需要的字段
            employee_data = {
                'id': employee_dict['id'],
                'username': employee_dict['username'],
                'real_name': employee_dict['real_name'],
                'employee_no': employee_dict['employee_no'],
                'role': employee_dict['role'],
                'avatar': employee_dict['avatar'],
                'is_active': employee_dict['is_active']
            }
            employee_list.append(employee_data)
        
        # 前端期望直接返回数组格式
        return jsonify(employee_list)
    
    except Exception as e:
        return jsonify({'code': 500, 'message': f'获取部门员工失败: {str(e)}'}), 500

@departments_bp.route('/departments/stats', methods=['GET'])
@jwt_required()
@require_permission('menu', 'department.list')
def get_department_stats():
    """获取部门统计信息"""
    try:
        # 统计部门总数
        total_departments = Department.query.filter_by(is_active=True).count()
        
        # 统计员工总数
        total_employees = User.query.filter_by(is_active=True).count()
        
        # 统计覆盖地区数
        regions = db.session.query(Department.region).filter(
            Department.is_active == True,
            Department.region.isnot(None),
            Department.region != ''
        ).distinct().count()
        
        # 统计销售部门数
        sales_departments = Department.query.filter_by(
            type='sales',
            is_active=True
        ).count()
        
        stats = {
            'total': total_departments,
            'totalEmployees': total_employees,
            'regions': regions,
            'salesDepts': sales_departments
        }
        
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({'error': f'获取部门统计信息失败: {str(e)}'}), 500
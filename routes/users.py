# app/routes/users.py
from flask import Blueprint, request, jsonify
from app.models import db, User, Department
from app.utils.auth_decorators import require_permission, log_operation, data_scope_filter, mask_sensitive_fields
from app.utils.employee_utils import EmployeeUtils
from flask_jwt_extended import jwt_required
import pandas as pd
import io
from datetime import datetime

users_bp = Blueprint('users', __name__)

@users_bp.route('/users', methods=['GET'])
@jwt_required()
@require_permission('menu', 'user.list')
def get_users():
    """获取用户列表"""
    try:
        # 获取查询参数
        keyword = request.args.get('keyword', '').strip()
        # 支持单个department_id或department_id[]数组
        department_ids = request.args.getlist('department_id[]')
        if not department_ids:
            single_dept_id = request.args.get('department_id', type=int)
            if single_dept_id:
                department_ids = [single_dept_id]
        else:
            # 转换为整数列表
            department_ids = [int(dept_id) for dept_id in department_ids if dept_id.isdigit()]
        
        role_filter = request.args.get('role', '').strip()
        is_active = request.args.get('is_active')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # 构建查询
        query = User.query
        
        # 应用数据权限过滤
        query = data_scope_filter(query, User, 'id', 'department_id')
        
        if keyword:
            query = query.filter(
                db.or_(
                    User.username.like(f'%{keyword}%'),
                    User.real_name.like(f'%{keyword}%'),
                    User.employee_no.like(f'%{keyword}%'),
                    User.email.like(f'%{keyword}%'),
                    User.phone.like(f'%{keyword}%')
                )
            )
        
        if department_ids:
            query = query.filter(User.department_id.in_(department_ids))
        
        if role_filter:
            query = query.filter(User.role == role_filter)
        
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            query = query.filter(User.is_active == is_active_bool)
        
        # 分页查询
        pagination = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        users = [user.to_dict() for user in pagination.items]
        
        # 敏感字段脱敏
        users = mask_sensitive_fields(users)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': users,
            'total': pagination.total,
            'page': page,
            'per_page': per_page
        })
    
    except Exception as e:
        return jsonify({'code': 500, 'message': f'获取用户列表失败: {str(e)}'}), 500

@users_bp.route('/users/generate-employee-no', methods=['POST'])
@jwt_required()
@require_permission('operation', 'user.create')
def generate_employee_no():
    """生成员工工号"""
    try:
        data = request.get_json()
        department_id = data.get('department_id')
        hire_date_str = data.get('hire_date')
        
        if not department_id:
            return jsonify({'code': 400, 'message': '部门ID不能为空'}), 400
        
        # 解析入职日期
        hire_date = None
        if hire_date_str:
            try:
                hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'code': 400, 'message': '入职日期格式错误，应为YYYY-MM-DD'}), 400
        
        # 生成工号
        employee_no = EmployeeUtils.generate_employee_no(department_id, hire_date)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {'employee_no': employee_no}
        })
    
    except ValueError as e:
        return jsonify({'code': 400, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'code': 500, 'message': f'生成工号失败: {str(e)}'}), 500

@users_bp.route('/users', methods=['POST'])
@jwt_required()
@require_permission('operation', 'user.create')
@log_operation('create', 'user', '创建用户')
def create_user():
    """创建用户"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['username', 'real_name', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'code': 400, 'message': f'缺少必需字段: {field}'}), 400
        
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user:
            return jsonify({'code': 400, 'message': '用户名已存在'}), 400
        
        # 检查邮箱是否已存在
        if data.get('email'):
            existing_email = User.query.filter_by(email=data['email']).first()
            if existing_email:
                return jsonify({'code': 400, 'message': '邮箱已存在'}), 400
        
        # 验证部门
        if data.get('department_id'):
            department = Department.query.get(data['department_id'])
            if not department:
                return jsonify({'code': 400, 'message': '部门不存在'}), 400
        
        # 生成员工工号
        employee_no = None
        if data.get('department_id'):
            hire_date = None
            if data.get('hire_date'):
                try:
                    hire_date = datetime.strptime(data['hire_date'], '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'code': 400, 'message': '入职日期格式错误'}), 400
            
            employee_no = EmployeeUtils.generate_employee_no(data['department_id'], hire_date)
        
        # 创建用户
        user = User(
            username=data['username'],
            real_name=data['real_name'],
            email=data.get('email'),
            phone=data.get('phone'),
            role=data.get('role', 'viewer'),
            employee_no=employee_no,
            department_id=data.get('department_id'),
            hire_date=hire_date if data.get('hire_date') else None
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # 更新部门员工数量
        if user.department_id:
            department = Department.query.get(user.department_id)
            if department:
                department.update_employee_count()
        
        return jsonify({
            'code': 201,
            'message': '用户创建成功',
            'data': {
                'id': user.id,
                'employee_no': user.employee_no
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'创建用户失败: {str(e)}'}), 500

@users_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@require_permission('operation', 'user.edit')
@log_operation('update', 'user', '更新用户')
def update_user(user_id):
    """更新用户"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        data = request.get_json()
        
        # 检查用户名是否已被其他用户使用
        if data.get('username') and data['username'] != user.username:
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user:
                return jsonify({'code': 400, 'message': '用户名已存在'}), 400
        
        # 检查邮箱是否已被其他用户使用
        if data.get('email') and data['email'] != user.email:
            existing_email = User.query.filter_by(email=data['email']).first()
            if existing_email:
                return jsonify({'code': 400, 'message': '邮箱已存在'}), 400
        
        # 验证部门
        old_department_id = user.department_id
        if data.get('department_id'):
            # 处理department_id可能是数组的情况
            dept_id = data['department_id']
            if isinstance(dept_id, list):
                # 如果是数组，取第一个值
                dept_id = dept_id[0] if dept_id else None
            
            if dept_id and dept_id != user.department_id:
                department = Department.query.get(dept_id)
                if not department:
                    return jsonify({'code': 400, 'message': '部门不存在'}), 400
                # 更新data中的department_id为单个值
                data['department_id'] = dept_id
        
        # 更新用户信息
        for field in ['username', 'real_name', 'email', 'phone', 'role', 'department_id', 'is_active']:
            if field in data:
                setattr(user, field, data[field])
        
        # 处理入职日期
        if data.get('hire_date'):
            try:
                hire_date = datetime.strptime(data['hire_date'], '%Y-%m-%d').date()
                user.hire_date = hire_date
            except ValueError:
                return jsonify({'code': 400, 'message': '入职日期格式错误'}), 400
        
        db.session.commit()
        
        # 更新相关部门的员工数量
        if old_department_id and old_department_id != user.department_id:
            old_dept = Department.query.get(old_department_id)
            if old_dept:
                old_dept.update_employee_count()
        
        if user.department_id:
            new_dept = Department.query.get(user.department_id)
            if new_dept:
                new_dept.update_employee_count()
        
        return jsonify({
            'code': 200,
            'message': '用户更新成功'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'更新用户失败: {str(e)}'}), 500

@users_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@jwt_required()
@require_permission('operation', 'user.reset_password')
@log_operation('update', 'user.password', '重置用户密码', sensitive=True)
def reset_password(user_id):
    """重置用户密码"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        data = request.get_json()
        new_password = data.get('new_password') or data.get('password')
        
        if not new_password:
            return jsonify({'code': 400, 'message': '新密码不能为空'}), 400
        
        if len(new_password) < 6:
            return jsonify({'code': 400, 'message': '密码长度不能少于6位'}), 400
        
        # 使用bcrypt加密密码
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '密码重置成功'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'重置密码失败: {str(e)}'}), 500

@users_bp.route('/users/<int:user_id>/generate-temp-password', methods=['POST'])
@jwt_required()
@require_permission('operation', 'user.reset_password')
@log_operation('update', 'user.password', '生成临时密码', sensitive=True)
def generate_temp_password(user_id):
    """生成临时密码"""
    import secrets
    import string
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 生成8位随机密码（包含大小写字母和数字）
        alphabet = string.ascii_letters + string.digits
        temp_password = ''.join(secrets.choice(alphabet) for _ in range(8))
        
        # 设置临时密码
        user.set_password(temp_password)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '临时密码生成成功',
            'data': {
                'temp_password': temp_password,
                'note': '请提醒用户首次登录后立即修改密码'
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'生成临时密码失败: {str(e)}'}), 500

@users_bp.route('/users/batch-import', methods=['POST'])
@jwt_required()
@require_permission('operation', 'user.import')
@log_operation('import', 'user', '批量导入用户', sensitive=True)
def batch_import_users():
    """批量导入用户"""
    try:
        if 'file' not in request.files:
            return jsonify({'code': 400, 'message': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'code': 400, 'message': '没有选择文件'}), 400
        
        if not file.filename.endswith('.xlsx'):
            return jsonify({'code': 400, 'message': '只支持xlsx格式文件'}), 400
        
        # 读取Excel文件
        df = pd.read_excel(io.BytesIO(file.read()))
        
        success_count = 0
        fail_count = 0
        fail_details = []
        
        for index, row in df.iterrows():
            try:
                row_num = index + 2  # Excel行号（从第2行开始）
                
                # 验证必需字段
                if pd.isna(row.get('username')) or pd.isna(row.get('real_name')):
                    fail_count += 1
                    fail_details.append({
                        'row': row_num,
                        'error': '用户名和真实姓名不能为空'
                    })
                    continue
                
                username = str(row['username']).strip()
                real_name = str(row['real_name']).strip()
                
                # 检查用户名是否已存在
                existing_user = User.query.filter_by(username=username).first()
                if existing_user:
                    fail_count += 1
                    fail_details.append({
                        'row': row_num,
                        'error': '用户名已存在'
                    })
                    continue
                
                # 检查邮箱是否已存在
                email = str(row.get('email', '')).strip()
                if email and User.query.filter_by(email=email).first():
                    fail_count += 1
                    fail_details.append({
                        'row': row_num,
                        'error': '邮箱已存在'
                    })
                    continue
                
                # 验证部门
                department_id = None
                department_name = str(row.get('department', '')).strip()
                if department_name:
                    department = Department.query.filter_by(name=department_name).first()
                    if department:
                        department_id = department.id
                    else:
                        fail_count += 1
                        fail_details.append({
                            'row': row_num,
                            'error': f'部门不存在: {department_name}'
                        })
                        continue
                
                # 生成员工工号
                employee_no = None
                if department_id:
                    hire_date = None
                    if not pd.isna(row.get('hire_date')):
                        try:
                            hire_date = pd.to_datetime(row['hire_date']).date()
                        except:
                            pass
                    
                    employee_no = EmployeeUtils.generate_employee_no(department_id, hire_date)
                
                # 创建用户
                user = User(
                    username=username,
                    real_name=real_name,
                    email=email if email else None,
                    phone=str(row.get('phone', '')).strip() if not pd.isna(row.get('phone')) else None,
                    role=str(row.get('role', 'viewer')).strip(),
                    employee_no=employee_no,
                    department_id=department_id,
                    hire_date=hire_date
                )
                user.set_password(str(row.get('password', '123456')))  # 默认密码
                
                db.session.add(user)
                success_count += 1
                
            except Exception as e:
                fail_count += 1
                fail_details.append({
                    'row': row_num,
                    'error': str(e)
                })
        
        db.session.commit()
        
        # 更新所有相关部门的员工数量
        departments = Department.query.all()
        for dept in departments:
            dept.update_employee_count()
        
        return jsonify({
            'code': 200,
            'message': '批量导入完成',
            'data': {
                'success_count': success_count,
                'fail_count': fail_count,
                'fail_details': fail_details[:10]  # 只返回前10个错误
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'批量导入失败: {str(e)}'}), 500

@users_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@require_permission('operation', 'user.delete')
@log_operation('delete', 'user', '删除用户')
def delete_user(user_id):
    """删除用户"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 记录被删除用户的部门ID，用于后续更新部门员工数量
        department_id = user.department_id
        username = user.username
        
        # 检查是否是最后一个超级管理员
        if user.role == 'super_admin':
            super_admin_count = User.query.filter_by(role='super_admin', is_active=True).count()
            if super_admin_count <= 1:
                return jsonify({'code': 400, 'message': '不能删除最后一个超级管理员'}), 400
        
        # 软删除：设置为非活跃状态而不是物理删除
        user.is_active = False
        user.username = f"{user.username}_deleted_{user.id}_{int(datetime.utcnow().timestamp())}"
        db.session.commit()
        
        # 更新部门员工数量
        if department_id:
            department = Department.query.get(department_id)
            if department:
                department.update_employee_count()
        
        return jsonify({
            'code': 200,
            'message': f'用户 {username} 删除成功'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'删除用户失败: {str(e)}'}), 500
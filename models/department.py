# app/models/department.py
from datetime import datetime
from . import db
from app.utils.timezone import now

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='部门编码，如：SH-SALES')
    name = db.Column(db.String(100), nullable=False, comment='部门名称')
    type = db.Column(db.Enum('sales', 'teaching', 'admin', 'other'), nullable=False, comment='部门类型')
    parent_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True, comment='上级部门ID')
    region = db.Column(db.String(50), nullable=True, comment='所属地区')
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='部门负责人ID')
    description = db.Column(db.Text, nullable=True, comment='部门描述')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    employee_count = db.Column(db.Integer, default=0, comment='员工数量')
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)
    
    # 建立关系
    parent = db.relationship('Department', remote_side=[id], backref='children')
    manager = db.relationship('User', foreign_keys=[manager_id])
    employees = db.relationship('User', foreign_keys='User.department_id', backref='department')
    
    # 创建索引
    __table_args__ = (
        db.Index('idx_parent_id', 'parent_id'),
        db.Index('idx_manager_id', 'manager_id'),
        db.Index('idx_type', 'type'),
        db.Index('idx_region', 'region'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'type': self.type,
            'parent_id': self.parent_id,
            'region': self.region,
            'manager_id': self.manager_id,
            'manager_name': self.manager.real_name if self.manager else None,
            'description': self.description,
            'is_active': self.is_active,
            'employee_count': self.employee_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_tree_dict(self):
        """转换为树形结构字典"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'type': self.type,
            'region': self.region,
            'employee_count': self.employee_count,
            'manager_name': self.manager.real_name if self.manager else None,
            'is_active': self.is_active,
            'children': [child.to_tree_dict() for child in self.children if child.is_active]
        }
    
    def update_employee_count(self):
        """更新员工数量"""
        from .user import User
        self.employee_count = User.query.filter_by(department_id=self.id, is_active=True).count()
        db.session.commit()
    
    def get_region_code(self):
        """获取地区代码，用于生成员工工号"""
        region_codes = {
            '北京': 'BJ',
            '上海': 'SH',
            '广州': 'GZ',
            '深圳': 'SZ',
            '杭州': 'HZ',
            '南京': 'NJ',
            '成都': 'CD',
            '武汉': 'WH',
            '西安': 'XA',
            '重庆': 'CQ'
        }
        return region_codes.get(self.region, 'HQ')  # 默认返回HQ（总部）
    
    def __repr__(self):
        return f'<Department {self.code}>'
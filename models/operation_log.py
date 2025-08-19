# app/models/operation_log.py
from datetime import datetime
from . import db

class OperationLog(db.Model):
    __tablename__ = 'operation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='操作用户ID')
    username = db.Column(db.String(50), nullable=False, comment='操作用户名')
    employee_no = db.Column(db.String(20), nullable=True, comment='操作用户工号')
    department_name = db.Column(db.String(100), nullable=True, comment='操作用户部门')
    action = db.Column(db.String(50), nullable=False, comment='操作类型：login,logout,create,update,delete,export,import,approve')
    resource = db.Column(db.String(50), nullable=False, comment='操作对象：user,department,customer,sales,knowledge,script,system')
    resource_id = db.Column(db.String(50), nullable=True, comment='操作对象ID')
    description = db.Column(db.Text, nullable=False, comment='操作描述')
    ip_address = db.Column(db.String(45), nullable=False, comment='IP地址')
    user_agent = db.Column(db.Text, nullable=True, comment='用户代理')
    sensitive_operation = db.Column(db.Boolean, default=False, comment='是否敏感操作')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 建立关系
    user = db.relationship('User', foreign_keys=[user_id])
    
    # 创建索引
    __table_args__ = (
        db.Index('idx_user_id', 'user_id'),
        db.Index('idx_action', 'action'),
        db.Index('idx_resource', 'resource'),
        db.Index('idx_created_at', 'created_at'),
        db.Index('idx_sensitive', 'sensitive_operation'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'employee_no': self.employee_no,
            'department_name': self.department_name,
            'action': self.action,
            'resource': self.resource,
            'resource_id': self.resource_id,
            'description': self.description,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'sensitive_operation': self.sensitive_operation,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def create_log(cls, user, action, resource, description, request=None, resource_id=None, sensitive=False):
        """创建操作日志"""
        log = cls(
            user_id=user.id,
            username=user.username,
            employee_no=getattr(user, 'employee_no', None),
            department_name=user.department.name if hasattr(user, 'department') and user.department else None,
            action=action,
            resource=resource,
            resource_id=str(resource_id) if resource_id else None,
            description=description,
            ip_address=request.remote_addr if request else '127.0.0.1',
            user_agent=request.headers.get('User-Agent') if request else None,
            sensitive_operation=sensitive
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    @classmethod
    def is_sensitive_action(cls, action, resource):
        """判断是否为敏感操作"""
        sensitive_operations = {
            'delete': ['user', 'department', 'customer'],
            'export': ['user', 'customer', 'sales'],
            'import': ['user', 'customer'],
            'update': ['user.password', 'system.config'],
            'login': ['system'],
            'approve': ['*']
        }
        
        if action in sensitive_operations:
            resources = sensitive_operations[action]
            return '*' in resources or resource in resources
        
        return False
    
    def __repr__(self):
        return f'<OperationLog {self.username} {self.action} {self.resource}>'
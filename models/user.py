# app/models/user.py
from datetime import datetime
import bcrypt
from . import db
from app.utils.timezone import now
from app.utils.avatar_utils import process_avatar_value, get_default_avatar

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(50))
    role = db.Column(db.Enum('super_admin', 'admin', 'manager', 'sales', 'teacher', 'viewer'), default='viewer')
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    employee_no = db.Column(db.String(20), unique=True, nullable=True, comment='工号')
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True, comment='部门ID')
    hire_date = db.Column(db.Date, nullable=True, comment='入职日期')
    avatar = db.Column(db.String(255), nullable=True, comment='头像URL')
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)
    
    # 创建索引
    __table_args__ = (
        db.Index('idx_employee_no', 'employee_no'),
        db.Index('idx_department_id', 'department_id'),
    )
    
    def to_dict(self):
        # 避免循环导入，使用hasattr检查
        department_name = None
        if hasattr(self, 'department') and self.department:
            department_name = self.department.name
        
        return {
            'id': self.id,
            'username': self.username,
            'real_name': self.real_name,
            'role': self.role,
            'phone': self.phone,
            'email': self.email,
            'employee_no': self.employee_no,
            'department_id': self.department_id,
            'department_name': department_name,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
            'avatar': process_avatar_value(self.avatar),
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def set_password(self, password):
        """设置加密密码"""
        if isinstance(password, str):
            password = password.encode('utf-8')
        self.password = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """验证密码"""
        import hashlib
        from werkzeug.security import check_password_hash
        
        stored_password = self.password
        
        # 处理不同的密码格式
        if stored_password.startswith('pbkdf2:'):
            # Werkzeug pbkdf2 格式
            return check_password_hash(stored_password, password)
        elif stored_password.startswith('$2b$') or stored_password.startswith('$2a$') or stored_password.startswith('$2y$'):
            # bcrypt 格式
            if isinstance(password, str):
                password = password.encode('utf-8')
            if isinstance(stored_password, str):
                stored_password = stored_password.encode('utf-8')
            return bcrypt.checkpw(password, stored_password)
        elif len(stored_password) == 64 and all(c in '0123456789abcdef' for c in stored_password.lower()):
            # SHA256 hex 格式
            return hashlib.sha256(password.encode('utf-8')).hexdigest() == stored_password
        else:
            # 明文密码(不安全，但为了向后兼容)
            return stored_password == password
    
    def __repr__(self):
        return f'<User {self.username}>'
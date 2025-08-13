# app/models/user.py
from datetime import datetime
from . import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(50))
    role = db.Column(db.Enum('admin', 'sales', 'teacher', 'viewer'), default='viewer')
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'real_name': self.real_name,
            'role': self.role,
            'phone': self.phone,
            'email': self.email,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def check_password(self, password):
        """验证密码（实际应用中应使用加密）"""
        return self.password == password
    
    def __repr__(self):
        return f'<User {self.username}>'
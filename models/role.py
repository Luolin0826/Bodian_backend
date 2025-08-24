# app/models/role.py
from datetime import datetime
from . import db
import json
from app.utils.timezone import now

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='角色名称（英文）')
    display_name = db.Column(db.String(100), nullable=False, comment='显示名称（中文）')
    level = db.Column(db.Integer, default=1, comment='角色等级，数字越大权限越高')
    description = db.Column(db.Text, nullable=True, comment='角色描述')
    permissions = db.Column(db.JSON, nullable=True, comment='权限配置JSON')
    is_system = db.Column(db.Boolean, default=False, comment='是否为系统内置角色')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)
    
    # 创建索引
    __table_args__ = (
        db.Index('idx_level', 'level'),
        db.Index('idx_is_system', 'is_system'),
    )
    
    def to_dict(self, include_permissions=False):
        result = {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'level': self.level,
            'description': self.description,
            'is_system': self.is_system,
            'is_active': self.is_active,
            'user_count': self.get_user_count(),
            'permission_count': self.count_permissions() if self.permissions else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_permissions and self.permissions:
            result['permissions'] = self.permissions
            
        return result
    
    def get_user_count(self):
        """获取该角色的用户数量"""
        from .user import User
        return User.query.filter_by(role=self.name, is_active=True).count()
    
    def count_permissions(self):
        """计算权限总数"""
        if not self.permissions:
            return 0
            
        count = 0
        
        # 菜单权限
        menu_perms = self.permissions.get('menu', [])
        if isinstance(menu_perms, list):
            count += len(menu_perms)
        
        # 操作权限
        operation = self.permissions.get('operation', {})
        for module_perms in operation.values():
            if isinstance(module_perms, list):
                count += len(module_perms)
        
        # 数据权限
        data = self.permissions.get('data', {})
        if data.get('custom_scopes'):
            count += len(data['custom_scopes'])
        if data.get('sensitive'):
            count += len(data['sensitive'])
            
        return count
    
    def has_permission(self, permission_type, permission_key):
        """检查是否有特定权限"""
        if not self.permissions:
            return False
            
        if permission_type == 'menu':
            return permission_key in self.permissions.get('menu', [])
        elif permission_type == 'operation':
            module, action = permission_key.split('.', 1) if '.' in permission_key else (permission_key, '')
            return action in self.permissions.get('operation', {}).get(module, [])
        elif permission_type == 'data':
            return permission_key in self.permissions.get('data', {}).get('custom_scopes', [])
            
        return False
    
    def validate_permissions(self):
        """验证权限配置的合法性"""
        if not self.permissions:
            return True, []
            
        errors = []
        
        # 检查必要的权限结构
        if 'menu' not in self.permissions:
            self.permissions['menu'] = []
        if 'operation' not in self.permissions:
            self.permissions['operation'] = {}
        if 'data' not in self.permissions:
            self.permissions['data'] = {
                'scope': 'self',
                'custom_scopes': [],
                'sensitive': []
            }
        if 'time' not in self.permissions:
            self.permissions['time'] = {
                'enable_login_time': False,
                'session_timeout': 60,
                'max_sessions': 3
            }
            
        return len(errors) == 0, errors
    
    def __repr__(self):
        return f'<Role {self.name}>'

class PermissionTemplate(db.Model):
    __tablename__ = 'permission_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='模板名称')
    description = db.Column(db.Text, nullable=True, comment='模板描述')
    role_type = db.Column(db.String(50), nullable=False, comment='适用角色类型')
    permissions = db.Column(db.JSON, nullable=False, comment='权限配置JSON')
    is_builtin = db.Column(db.Boolean, default=False, comment='是否为内置模板')
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'role_type': self.role_type,
            'permissions': self.permissions,
            'is_builtin': self.is_builtin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<PermissionTemplate {self.name}>'
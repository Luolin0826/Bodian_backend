# app/models/script_category.py
from datetime import datetime
from . import db
from sqlalchemy import func
from app.utils.timezone import now

class ScriptCategory(db.Model):
    """话术分类模型"""
    __tablename__ = 'script_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='分类名称')
    parent_id = db.Column(db.Integer, db.ForeignKey('script_categories.id'), comment='父分类ID')
    description = db.Column(db.Text, comment='分类描述')
    icon = db.Column(db.String(50), comment='图标类名')
    sort_order = db.Column(db.Integer, default=0, comment='排序')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    is_system = db.Column(db.Boolean, default=False, comment='是否系统分类（不可删除）')
    
    # 创建者和时间戳
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='创建者ID')
    created_at = db.Column(db.DateTime, default=now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=now, onupdate=now, comment='更新时间')
    
    # 关系定义
    parent = db.relationship('ScriptCategory', remote_side=[id], backref='children')
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def to_dict(self, include_children=False, include_stats=False):
        """转换为字典格式"""
        data = {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'description': self.description,
            'icon': self.icon,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'is_system': self.is_system,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        # 包含子分类
        if include_children:
            data['children'] = [child.to_dict(include_children=False, include_stats=include_stats) 
                              for child in self.children if child.is_active]
            
        # 包含统计信息
        if include_stats:
            data['script_count'] = self.get_script_count()
            
        return data
    
    def get_script_count(self, include_children=True):
        """获取该分类下的话术数量"""
        from app.models.script import Script
        
        if include_children:
            # 获取所有子分类ID
            child_ids = self.get_all_child_ids()
            child_ids.append(self.id)
            
            return Script.query.filter(
                Script.category_id.in_(child_ids),
                Script.is_active == True
            ).count()
        else:
            return Script.query.filter(
                Script.category_id == self.id,
                Script.is_active == True
            ).count()
    
    def get_all_child_ids(self):
        """递归获取所有子分类ID"""
        child_ids = []
        for child in self.children:
            if child.is_active:
                child_ids.append(child.id)
                child_ids.extend(child.get_all_child_ids())
        return child_ids
    
    def can_delete(self):
        """检查是否可以删除"""
        # 系统分类不可删除
        if self.is_system:
            return False, "系统分类不可删除"
        
        # 有子分类时不可删除
        active_children = [child for child in self.children if child.is_active]
        if active_children:
            return False, f"该分类下还有{len(active_children)}个子分类，请先删除或移动子分类"
        
        # 有话术时不可删除
        script_count = self.get_script_count(include_children=False)
        if script_count > 0:
            return False, f"该分类下还有{script_count}个话术，请先移动或删除话术"
        
        return True, "可以删除"
    
    def can_edit(self, user):
        """检查用户是否可以编辑该分类"""
        # 超级管理员可以编辑所有分类
        if user.role == 'super_admin':
            return True
        
        # 系统分类只有超级管理员可以编辑
        if self.is_system:
            return False
        
        # 创建者可以编辑自己的分类
        if self.created_by == user.id:
            return True
        
        # 检查是否有编辑权限
        from app.models.role import Role
        role = Role.query.filter_by(name=user.role, is_active=True).first()
        if role and role.has_permission('operation', 'script.category.edit'):
            return True
        
        return False
    
    @classmethod
    def get_tree(cls, include_stats=False, parent_id=None):
        """获取分类树结构"""
        query = cls.query.filter_by(is_active=True, parent_id=parent_id).order_by(cls.sort_order, cls.name)
        categories = query.all()
        
        tree = []
        for category in categories:
            category_data = category.to_dict(include_children=True, include_stats=include_stats)
            tree.append(category_data)
            
        return tree
    
    @classmethod
    def get_user_categories(cls, user_id, include_system=True):
        """获取用户可管理的分类"""
        query = cls.query.filter_by(is_active=True)
        
        # 如果不包含系统分类，过滤掉系统分类
        if not include_system:
            query = query.filter_by(is_system=False)
        
        # 非超级管理员只能看到自己创建的分类
        from app.models.user import User
        user = User.query.get(user_id)
        if user and user.role != 'super_admin':
            query = query.filter_by(created_by=user_id)
            
        return query.order_by(cls.sort_order, cls.name).all()
    
    @classmethod
    def create_default_categories(cls):
        """创建默认分类"""
        default_categories = [
            {'name': '电网考试', 'description': '电网招聘考试相关话术', 'icon': 'zap', 'is_system': True},
            {'name': '考研咨询', 'description': '考研相关咨询话术', 'icon': 'book', 'is_system': True},
            {'name': '销售对话', 'description': '销售转化话术', 'icon': 'phone', 'is_system': True},
            {'name': '社媒回复', 'description': '社交媒体回复话术', 'icon': 'message-circle', 'is_system': True},
            {'name': '客服话术', 'description': '客服支持话术', 'icon': 'headphones', 'is_system': True},
            {'name': '通用话术', 'description': '通用场景话术', 'icon': 'star', 'is_system': True}
        ]
        
        created_categories = []
        for idx, category_data in enumerate(default_categories):
            # 检查是否已存在
            existing = cls.query.filter_by(name=category_data['name'], is_system=True).first()
            if not existing:
                category = cls(
                    name=category_data['name'],
                    description=category_data['description'],
                    icon=category_data['icon'],
                    sort_order=idx + 1,
                    is_system=category_data['is_system'],
                    created_by=None  # 系统创建
                )
                db.session.add(category)
                created_categories.append(category)
        
        if created_categories:
            db.session.commit()
            
        return created_categories
    
    @classmethod
    def get_stats(cls):
        """获取分类统计信息"""
        total = cls.query.filter_by(is_active=True).count()
        system = cls.query.filter_by(is_active=True, is_system=True).count()
        user_created = total - system
        
        # 最近新增（7天内）
        from datetime import datetime, timedelta
        recent_date = datetime.utcnow() - timedelta(days=7)
        recent = cls.query.filter(
            cls.is_active == True,
            cls.created_at >= recent_date
        ).count()
        
        return {
            'total': total,
            'system': system,
            'user_created': user_created,
            'recent': recent
        }
    
    def __repr__(self):
        return f'<ScriptCategory {self.name}>'
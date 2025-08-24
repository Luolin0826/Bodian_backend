# app/models/script_favorite.py
from datetime import datetime
from . import db
from app.utils.timezone import now

class ScriptFavorite(db.Model):
    __tablename__ = 'script_favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    script_id = db.Column(db.Integer, db.ForeignKey('scripts.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=now)
    
    # 创建复合唯一索引和单独索引
    __table_args__ = (
        db.UniqueConstraint('user_id', 'script_id', name='unique_user_script'),
        db.Index('idx_user_id', 'user_id'),
        db.Index('idx_script_id', 'script_id'),
    )
    
    # 建立关系
    user = db.relationship('User', backref='script_favorites')
    script = db.relationship('Script', backref='favorited_by')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'script_id': self.script_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def is_favorited_by_user(cls, script_id, user_id):
        """检查用户是否收藏了某个话术"""
        return cls.query.filter_by(script_id=script_id, user_id=user_id).first() is not None
    
    @classmethod
    def get_user_favorites(cls, user_id, page=1, per_page=20):
        """获取用户收藏的话术列表"""
        from .script import Script
        
        query = db.session.query(Script).join(
            cls, cls.script_id == Script.id
        ).filter(
            cls.user_id == user_id,
            Script.is_active == True
        ).order_by(cls.created_at.desc())
        
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    @classmethod
    def get_user_favorite_count(cls, user_id):
        """获取用户收藏话术的总数"""
        from .script import Script
        
        return db.session.query(cls).join(
            Script, cls.script_id == Script.id
        ).filter(
            cls.user_id == user_id,
            Script.is_active == True
        ).count()
    
    def __repr__(self):
        return f'<ScriptFavorite user_id={self.user_id} script_id={self.script_id}>'
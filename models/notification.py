# app/models/notification.py
from . import db
from app.utils.timezone import now
from sqlalchemy import func
import json

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # system/email/push
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text)
    priority = db.Column(db.String(10), default='medium')  # low/medium/high/urgent
    is_read = db.Column(db.Boolean, default=False)
    sender = db.Column(db.String(100))
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # 元数据
    data = db.Column(db.JSON)  # 额外数据，如链接、参数等
    expires_at = db.Column(db.DateTime)  # 过期时间
    
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)
    
    # 关系
    user = db.relationship('User', foreign_keys=[user_id], backref='notifications')
    sender_user = db.relationship('User', foreign_keys=[sender_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'content': self.content,
            'priority': self.priority,
            'is_read': self.is_read,
            'sender': self.sender,
            'data': self.data,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def get_unread_count(cls, user_id):
        """获取未读通知数量"""
        total_unread = cls.query.filter_by(user_id=user_id, is_read=False).count()
        
        # 按类型统计未读数量
        type_counts = db.session.query(
            cls.type,
            func.count(cls.id).label('count')
        ).filter(
            cls.user_id == user_id,
            cls.is_read == False
        ).group_by(cls.type).all()
        
        result = {
            'total_unread': total_unread,
            'system_unread': 0,
            'email_unread': 0,
            'push_unread': 0
        }
        
        for type_name, count in type_counts:
            result[f'{type_name}_unread'] = count
            
        return result
    
    @classmethod
    def create_notification(cls, user_id, title, content=None, **kwargs):
        """创建通知"""
        notification = cls(
            user_id=user_id,
            title=title,
            content=content,
            type=kwargs.get('type', 'system'),
            priority=kwargs.get('priority', 'medium'),
            sender=kwargs.get('sender'),
            sender_id=kwargs.get('sender_id'),
            data=kwargs.get('data'),
            expires_at=kwargs.get('expires_at')
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    
    @classmethod
    def mark_as_read(cls, user_id, notification_id=None):
        """标记通知为已读"""
        if notification_id:
            # 标记单个通知
            notification = cls.query.filter_by(
                id=notification_id, 
                user_id=user_id
            ).first()
            if notification:
                notification.is_read = True
                notification.updated_at = now()
                db.session.commit()
                return True
        else:
            # 标记所有通知为已读
            cls.query.filter_by(
                user_id=user_id, 
                is_read=False
            ).update({
                'is_read': True,
                'updated_at': now()
            })
            db.session.commit()
            return True
        
        return False
    
    def is_expired(self):
        """检查通知是否过期"""
        if self.expires_at:
            return now() > self.expires_at
        return False
    
    def __repr__(self):
        return f'<Notification {self.title}>'
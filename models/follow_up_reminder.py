# app/models/follow_up_reminder.py
from datetime import datetime
from . import db
from app.utils.timezone import now

class FollowUpReminder(db.Model):
    __tablename__ = 'follow_up_reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False, index=True)
    remind_date = db.Column(db.Date, nullable=False, index=True, comment='提醒日期')
    remind_content = db.Column(db.Text, nullable=False, comment='提醒内容')
    priority = db.Column(
        db.Enum('low', 'medium', 'high', 'urgent'),
        default='medium',
        comment='优先级'
    )
    is_completed = db.Column(db.Boolean, default=False, nullable=False, index=True, comment='是否已完成')
    completed_at = db.Column(db.DateTime, nullable=True, comment='完成时间')
    completed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='完成人ID')
    follow_up_record_id = db.Column(db.Integer, db.ForeignKey('follow_up_records.id'), nullable=True, comment='关联的跟进记录ID')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='创建人ID')
    created_at = db.Column(db.DateTime, default=now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=now, onupdate=now, comment='更新时间')
    
    # 关联关系
    customer = db.relationship('Customer', backref='follow_up_reminders')
    creator = db.relationship('User', foreign_keys=[created_by])
    completer = db.relationship('User', foreign_keys=[completed_by])
    follow_up_record = db.relationship('FollowUpRecord', backref='reminders')
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'remind_date': self.remind_date.isoformat() if self.remind_date else None,
            'remind_content': self.remind_content,
            'priority': self.priority,
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'completed_by': self.completed_by,
            'follow_up_record_id': self.follow_up_record_id,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_detail_dict(self):
        """返回详细信息，包括关联数据"""
        result = self.to_dict()
        if self.creator:
            result['creator_name'] = self.creator.username
        if self.completer:
            result['completer_name'] = self.completer.username
        if self.customer:
            result['customer_name'] = self.customer.wechat_name
            result['customer_phone'] = self.customer.phone
            result['customer_status'] = self.customer.status
        return result
    
    def mark_completed(self, user_id):
        """标记提醒为已完成"""
        self.is_completed = True
        self.completed_at = now()
        self.completed_by = user_id
        self.updated_at = now()
    
    def __repr__(self):
        return f'<FollowUpReminder {self.id}>'
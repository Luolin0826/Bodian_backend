# app/models/follow_up_record.py
from datetime import datetime
from . import db
from app.utils.timezone import now

class FollowUpRecord(db.Model):
    __tablename__ = 'follow_up_records'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False, index=True)
    follow_up_type = db.Column(
        db.Enum('phone', 'wechat', 'meeting', 'email', 'other'),
        nullable=False,
        default='phone',
        comment='跟进方式'
    )
    follow_up_content = db.Column(db.Text, nullable=False, comment='跟进内容')
    next_follow_date = db.Column(db.Date, nullable=True, comment='下次跟进日期')
    result = db.Column(
        db.Enum('interested', 'not_interested', 'no_answer', 'deal', 'reschedule', 'other'),
        nullable=True,
        comment='跟进结果'
    )
    status_before = db.Column(
        db.Enum('潜在', '跟进中', '已成交', '已流失'),
        nullable=True,
        comment='跟进前状态'
    )
    status_after = db.Column(
        db.Enum('潜在', '跟进中', '已成交', '已流失'),
        nullable=True,
        comment='跟进后状态'
    )
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='跟进人ID')
    created_at = db.Column(db.DateTime, default=now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=now, onupdate=now, comment='更新时间')
    
    # 关联关系
    customer = db.relationship('Customer', backref='follow_up_records')
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'follow_up_type': self.follow_up_type,
            'follow_up_content': self.follow_up_content,
            'next_follow_date': self.next_follow_date.isoformat() if self.next_follow_date else None,
            'result': self.result,
            'status_before': self.status_before,
            'status_after': self.status_after,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_detail_dict(self):
        """返回详细信息，包括关联数据"""
        result = self.to_dict()
        if self.creator:
            result['creator_name'] = self.creator.username
        if self.customer:
            result['customer_name'] = self.customer.wechat_name
        return result
    
    def __repr__(self):
        return f'<FollowUpRecord {self.id}>'
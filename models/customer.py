# app/models/customer.py
from datetime import datetime
from . import db

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_date = db.Column(db.Date, index=True)
    channel = db.Column(db.String(50), index=True)
    wechat_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    add_date = db.Column(db.Date)
    deal_date = db.Column(db.Date)
    status = db.Column(
        db.Enum('潜在', '跟进中', '已成交', '已流失'), 
        default='潜在',
        index=True
    )
    remark = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    creator = db.relationship('User', backref='created_customers')
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_date': self.customer_date.isoformat() if self.customer_date else None,
            'channel': self.channel,
            'wechat_name': self.wechat_name,
            'phone': self.phone,
            'add_date': self.add_date.isoformat() if self.add_date else None,
            'deal_date': self.deal_date.isoformat() if self.deal_date else None,
            'status': self.status,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Customer {self.wechat_name}>'
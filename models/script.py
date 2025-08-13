# app/models/script.py
from datetime import datetime
from . import db

class Script(db.Model):
    __tablename__ = 'scripts'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), index=True)
    title = db.Column(db.String(200))
    question = db.Column(db.Text)
    answer = db.Column(db.Text, nullable=False)
    keywords = db.Column(db.String(500))
    usage_count = db.Column(db.Integer, default=0)
    effectiveness = db.Column(db.Float, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'title': self.title,
            'question': self.question,
            'answer': self.answer,
            'keywords': self.keywords,
            'usage_count': self.usage_count,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def increment_usage(self):
        """增加使用次数"""
        self.usage_count += 1
    
    def __repr__(self):
        return f'<Script {self.title}>'
# app/models/knowledge_base.py
from datetime import datetime
from . import db

class KnowledgeBase(db.Model):
    __tablename__ = 'knowledge_base'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(
        db.Enum('电网考试', '考研', '校招', '其他'), 
        nullable=False,
        index=True
    )
    category = db.Column(db.String(100), index=True)
    question = db.Column(db.Text)
    answer = db.Column(db.Text)
    related_questions = db.Column(db.Text)
    tags = db.Column(db.String(500))
    view_count = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'category': self.category,
            'question': self.question,
            'answer': self.answer,
            'related_questions': self.related_questions,
            'tags': self.tags,
            'view_count': self.view_count,
            'is_published': self.is_published,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def increment_view(self):
        """增加查看次数"""
        self.view_count += 1
    
    def __repr__(self):
        return f'<Knowledge {self.question[:50]}>'
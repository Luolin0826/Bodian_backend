# app/models/knowledge_base.py
from datetime import datetime
from . import db
from app.utils.timezone import now

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
    unit = db.Column(db.String(100))  # 省份电网（如：浙江、山东等）
    site = db.Column(db.String(100))  # 站点信息
    source = db.Column(db.String(100))  # 数据来源
    meta_data = db.Column(db.Text)  # JSON格式的元数据
    view_count = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'category': self.category,
            'question': self.question,
            'answer': self.answer,
            'related_questions': self.related_questions,
            'tags': self.tags,
            'unit': self.unit,
            'site': self.site,
            'source': self.source,
            'metadata': self.meta_data,
            'view_count': self.view_count,
            'is_published': self.is_published,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def increment_view(self):
        """增加查看次数"""
        self.view_count += 1
    
    def __repr__(self):
        return f'<Knowledge {self.question[:50]}>'
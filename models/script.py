# app/models/script.py
from datetime import datetime
from . import db
from sqlalchemy import func

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
    
    # 话术筛选字段（适配现有表结构）
    type = db.Column(db.Enum('grid_exam', 'postgrad_consult', 'sales_conversation', 'social_media_reply'), index=True, comment='话术类型')
    source = db.Column(db.String(100), index=True, comment='数据来源')
    platform = db.Column(db.String(50), index=True, comment='适用平台')
    customer_info = db.Column(db.Text, comment='客户信息')
    
    # 保持新字段用于扩展
    script_type = db.Column(db.String(50), index=True, comment='扩展话术类型')
    data_source = db.Column(db.String(100), index=True, comment='扩展数据来源')
    
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
            'effectiveness': self.effectiveness,
            'is_active': self.is_active,
            'type': self.type,
            'source': self.source,
            'platform': self.platform,
            'customer_info': self.customer_info,
            'script_type': self.script_type,
            'data_source': self.data_source,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def increment_usage(self):
        """增加使用次数"""
        self.usage_count += 1
    
    @classmethod
    def get_stats(cls):
        """获取话术统计数据"""
        total = cls.query.filter_by(is_active=True).count()
        
        # 热门话术（使用次数 > 10）
        popular = cls.query.filter(
            cls.is_active == True,
            cls.usage_count > 10
        ).count()
        
        # 最近新增（7天内）
        from datetime import datetime, timedelta
        recent_date = datetime.utcnow() - timedelta(days=7)
        recent = cls.query.filter(
            cls.is_active == True,
            cls.created_at >= recent_date
        ).count()
        
        # 分类数量
        categories = db.session.query(cls.category).distinct().filter(
            cls.category.isnot(None),
            cls.is_active == True
        ).count()
        
        return {
            'total': total,
            'popular': popular,
            'recent': recent,
            'categories': categories
        }
    
    @classmethod 
    def get_type_stats(cls):
        """获取话术类型统计"""
        # 先尝试使用原有字段
        stats = db.session.query(
            cls.type,
            func.count(cls.id).label('count')
        ).filter(
            cls.is_active == True,
            cls.type.isnot(None)
        ).group_by(cls.type).all()
        
        # 如果没有数据，尝试使用新字段
        if not stats:
            stats = db.session.query(
                cls.script_type,
                func.count(cls.id).label('count')
            ).filter(
                cls.is_active == True,
                cls.script_type.isnot(None)
            ).group_by(cls.script_type).all()
        
        # 类型映射
        type_mapping = {
            'grid_exam': '电网考试',
            'sales_conversation': '销售对话',
            'social_media_reply': '社媒回复',
            'postgrad_consult': '考研咨询',
            'customer_service': '客服话术',
            'recruitment': '招聘话术',
            'training': '培训话术'
        }
        
        return [
            {
                'value': stat[0] if stat[0] else 'unknown',
                'label': type_mapping.get(stat[0], stat[0] or '未分类'),
                'count': stat[1]
            }
            for stat in stats
        ]
    
    @classmethod
    def get_source_stats(cls):
        """获取数据来源统计"""
        # 先尝试使用原有字段
        stats = db.session.query(
            cls.source,
            func.count(cls.id).label('count')
        ).filter(
            cls.is_active == True,
            cls.source.isnot(None)
        ).group_by(cls.source).all()
        
        # 如果没有数据，尝试使用新字段
        if not stats:
            stats = db.session.query(
                cls.data_source,
                func.count(cls.id).label('count')
            ).filter(
                cls.is_active == True,
                cls.data_source.isnot(None)
            ).group_by(cls.data_source).all()
        
        return [
            {
                'value': stat[0] if stat[0] else 'unknown',
                'label': stat[0] or '未知来源',
                'count': stat[1]
            }
            for stat in stats
        ]
    
    @classmethod
    def get_platform_stats(cls):
        """获取平台统计"""
        stats = db.session.query(
            cls.platform,
            func.count(cls.id).label('count')
        ).filter(
            cls.is_active == True,
            cls.platform.isnot(None)
        ).group_by(cls.platform).all()
        
        return [
            {
                'value': stat[0],
                'label': stat[0],
                'count': stat[1]
            }
            for stat in stats
        ]
    
    def __repr__(self):
        return f'<Script {self.title}>'
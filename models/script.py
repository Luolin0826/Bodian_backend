# app/models/script.py
from datetime import datetime
from . import db
from sqlalchemy import func
from app.utils.timezone import now

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
    is_pinned = db.Column(db.Boolean, default=False, comment='是否置顶')
    
    # 话术筛选字段（适配现有表结构）
    type = db.Column(db.Enum('grid_exam', 'postgrad_consult', 'sales_conversation', 'social_media_reply'), index=True, comment='话术类型')
    source = db.Column(db.String(100), index=True, comment='数据来源')
    platform = db.Column(db.String(50), index=True, comment='适用平台')
    customer_info = db.Column(db.Text, comment='客户信息')
    
    # 保持新字段用于扩展
    script_type = db.Column(db.String(50), index=True, comment='扩展话术类型')
    data_source = db.Column(db.String(100), index=True, comment='扩展数据来源')
    
    # 新的分类字段
    primary_category = db.Column(db.Enum('project_category', 'product_intro', 'marketing', 'faq', 'learning_guidance', 'study_planning'), 
                                index=True, comment='主分类')
    secondary_category = db.Column(db.Enum('power_grid', 'electrical_exam', 'application_guide', 'review_planning', 'consultation', 'general'), 
                                  index=True, comment='子分类')
    
    # 保留原有三维分类字段（向后兼容）
    script_type_new = db.Column(db.String(50), index=True, comment='话术类型（旧）')
    content_type_new = db.Column(db.String(50), index=True, comment='内容类型（旧）')
    platform_new = db.Column(db.String(50), index=True, comment='适用平台')
    keywords_new = db.Column(db.String(1000), comment='关键词标签')
    classification_meta = db.Column(db.Text, comment='分类元数据')
    classification_status = db.Column(db.Enum('pending', 'processing', 'completed', 'failed'), 
                                    default='completed', comment='分类处理状态')
    classification_version = db.Column(db.String(20), default='v2.0', comment='分类体系版本')
    
    # 新分类系统外键
    category_id = db.Column(db.Integer, db.ForeignKey('script_categories.id'), comment='分类ID')
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)
    
    def to_dict(self):
        data = {
            'id': self.id,
            'category': self.category,
            'title': self.title,
            'question': self.question,
            'answer': self.answer,
            'keywords': self.keywords,
            'usage_count': self.usage_count,
            'effectiveness': self.effectiveness,
            'is_active': self.is_active,
            'is_pinned': self.is_pinned,
            'type': self.type,
            'source': self.source,
            'platform': self.platform,
            'customer_info': self.customer_info,
            'script_type': self.script_type,
            'data_source': self.data_source,
            # 新分类系统字段
            'category_id': self.category_id,
            # 三维分类字段
            # 新分类字段
            'primary_category': self.primary_category,
            'secondary_category': self.secondary_category,
            # 旧分类字段（向后兼容）
            'script_type_new': self.script_type_new,
            'content_type_new': self.content_type_new,
            'platform_new': self.platform_new,
            'keywords_new': self.keywords_new,
            'classification_meta': self.classification_meta,
            'classification_status': self.classification_status,
            'classification_version': self.classification_version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        # 包含分类信息（如果有）
        if hasattr(self, 'script_category') and self.script_category:
            data['category_info'] = {
                'id': self.script_category.id,
                'name': self.script_category.name,
                'description': self.script_category.description,
                'icon': self.script_category.icon
            }
        
        return data
    
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
    
    @classmethod
    def get_script_type_new_stats(cls):
        """获取新话术类型统计"""
        stats = db.session.query(
            cls.script_type_new,
            func.count(cls.id).label('count')
        ).filter(
            cls.is_active == True,
            cls.script_type_new.isnot(None)
        ).group_by(cls.script_type_new).all()
        
        # 话术类型映射（包含所有设计的选项）
        type_mapping = {
            'consultation': '咨询引导',
            'sales_promotion': '销售转化',
            'service_support': '服务支持',
            'content_marketing': '内容营销',
            'expert_guidance': '专业指导'
        }
        
        # 创建结果字典，包含所有设计的类型
        result_dict = {}
        for type_val, type_label in type_mapping.items():
            result_dict[type_val] = {'value': type_val, 'label': type_label, 'count': 0}
        
        # 填入实际统计数据
        for stat in stats:
            if stat[0] in result_dict:
                result_dict[stat[0]]['count'] = stat[1]
        
        # 返回按设计顺序排列的完整列表
        return [result_dict[key] for key in type_mapping.keys()]
    
    @classmethod
    def get_content_type_stats(cls):
        """获取内容类型统计"""
        stats = db.session.query(
            cls.content_type_new,
            func.count(cls.id).label('count')
        ).filter(
            cls.is_active == True,
            cls.content_type_new.isnot(None)
        ).group_by(cls.content_type_new).all()
        
        # 内容类型映射
        content_mapping = {
            'exam_guidance': '考试指导',
            'course_introduction': '课程介绍',
            'career_planning': '职业规划',
            'application_process': '申请流程',
            'company_service': '公司服务',
            'general_support': '综合支持'
        }
        
        return [
            {
                'value': stat[0] if stat[0] else 'unknown',
                'label': content_mapping.get(stat[0], stat[0] or '未分类'),
                'count': stat[1]
            }
            for stat in stats
        ]
    
    @classmethod
    def get_platform_new_stats(cls):
        """获取新平台统计"""
        stats = db.session.query(
            cls.platform_new,
            func.count(cls.id).label('count')
        ).filter(
            cls.is_active == True,
            cls.platform_new.isnot(None)
        ).group_by(cls.platform_new).all()
        
        # 平台映射（包含所有设计的选项）
        platform_mapping = {
            'wechat': '微信平台',
            'xiaohongshu': '小红书',
            'qq': 'QQ平台',
            'phone': '电话沟通',
            'universal': '通用平台'
        }
        
        # 创建结果字典，包含所有设计的平台
        result_dict = {}
        for platform_val, platform_label in platform_mapping.items():
            result_dict[platform_val] = {'value': platform_val, 'label': platform_label, 'count': 0}
        
        # 填入实际统计数据
        for stat in stats:
            if stat[0] in result_dict:
                result_dict[stat[0]]['count'] = stat[1]
        
        # 返回按设计顺序排列的完整列表
        return [result_dict[key] for key in platform_mapping.keys()]
    
    @classmethod
    def get_primary_category_stats(cls):
        """获取主分类统计"""
        stats = db.session.query(
            cls.primary_category,
            func.count(cls.id).label('count')
        ).filter(
            cls.is_active == True,
            cls.primary_category.isnot(None)
        ).group_by(cls.primary_category).all()
        
        # 主分类映射
        category_mapping = {
            'project_category': '项目分类',
            'product_intro': '产品介绍',
            'marketing': '营销话术',
            'faq': '常见问题',
            'learning_guidance': '学习指导',
            'study_planning': '学习规划'
        }
        
        # 创建结果字典，包含所有设计的类型
        result_dict = {}
        for cat_val, cat_label in category_mapping.items():
            result_dict[cat_val] = {'value': cat_val, 'label': cat_label, 'count': 0}
        
        # 填入实际统计数据
        for stat in stats:
            if stat[0] in result_dict:
                result_dict[stat[0]]['count'] = stat[1]
        
        return [result_dict[key] for key in category_mapping.keys()]
    
    @classmethod
    def get_secondary_category_stats(cls):
        """获取子分类统计"""
        stats = db.session.query(
            cls.secondary_category,
            func.count(cls.id).label('count')
        ).filter(
            cls.is_active == True,
            cls.secondary_category.isnot(None)
        ).group_by(cls.secondary_category).all()
        
        # 子分类映射
        subcategory_mapping = {
            'power_grid': '电网',
            'electrical_exam': '电气考研',
            'application_guide': '网申',
            'review_planning': '复习规划',
            'consultation': '报考咨询',
            'general': '通用'
        }
        
        return [
            {
                'value': stat[0] if stat[0] else 'unknown',
                'label': subcategory_mapping.get(stat[0], stat[0] or '未分类'),
                'count': stat[1]
            }
            for stat in stats
        ]
    
    @classmethod
    def get_new_classification_stats(cls):
        """获取新分类体系统计"""
        return {
            'primary_categories': cls.get_primary_category_stats(),
            'secondary_categories': cls.get_secondary_category_stats(),
            'total_new_classified': db.session.query(cls).filter(
                cls.is_active == True,
                cls.primary_category.isnot(None)
            ).count()
        }
    
    @classmethod
    def get_three_dimension_stats(cls):
        """获取三维分类综合统计（向后兼容）"""
        return {
            'script_types': cls.get_script_type_new_stats(),
            'content_types': cls.get_content_type_stats(),
            'platforms': cls.get_platform_new_stats(),
            'total_classified': db.session.query(cls).filter(
                cls.is_active == True,
                cls.script_type_new.isnot(None),
                cls.content_type_new.isnot(None),
                cls.platform_new.isnot(None)
            ).count()
        }
    
    # 关系定义（需要在类的最后定义）
    script_category = db.relationship('ScriptCategory', foreign_keys=[category_id], lazy='select')
    
    def __repr__(self):
        return f'<Script {self.title}>'
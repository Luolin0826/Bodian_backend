# app/models/user_preferences.py
from . import db
from app.utils.timezone import now

class UserPreferences(db.Model):
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # 界面设置
    theme_mode = db.Column(db.String(10), default='light')  # light/dark/auto
    sidebar_collapsed = db.Column(db.Boolean, default=False)
    show_breadcrumb = db.Column(db.Boolean, default=True)
    language = db.Column(db.String(10), default='zh-CN')
    font_size = db.Column(db.String(10), default='medium')
    
    # 通知设置
    system_notification = db.Column(db.Boolean, default=True)
    email_notification = db.Column(db.Boolean, default=False)
    sound_notification = db.Column(db.Boolean, default=True)
    browser_notification = db.Column(db.Boolean, default=True)
    
    # 安全设置
    auto_logout_time = db.Column(db.Integer, default=60)  # 分钟，0表示永不
    session_timeout = db.Column(db.Integer, default=30)
    enable_two_factor = db.Column(db.Boolean, default=False)
    
    # 工作区设置
    default_page = db.Column(db.String(255), default='/dashboard')
    items_per_page = db.Column(db.Integer, default=20)
    date_format = db.Column(db.String(20), default='YYYY-MM-DD')
    time_format = db.Column(db.String(10), default='24h')
    
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)
    
    # 关系
    user = db.relationship('User', backref='preferences')
    
    def to_dict(self):
        """转换为分组的字典格式"""
        return {
            'appearance': {
                'theme_mode': self.theme_mode,
                'sidebar_collapsed': self.sidebar_collapsed,
                'show_breadcrumb': self.show_breadcrumb,
                'language': self.language,
                'font_size': self.font_size
            },
            'notification': {
                'system_notification': self.system_notification,
                'email_notification': self.email_notification,
                'sound_notification': self.sound_notification,
                'browser_notification': self.browser_notification
            },
            'security': {
                'auto_logout_time': self.auto_logout_time,
                'session_timeout': self.session_timeout,
                'enable_two_factor': self.enable_two_factor
            },
            'workspace': {
                'default_page': self.default_page,
                'items_per_page': self.items_per_page,
                'date_format': self.date_format,
                'time_format': self.time_format
            }
        }
    
    @classmethod
    def create_default(cls, user_id):
        """为用户创建默认偏好设置"""
        preferences = cls(user_id=user_id)
        db.session.add(preferences)
        db.session.commit()
        return preferences
    
    def update_from_dict(self, data):
        """从分组字典更新偏好设置"""
        mapping = {
            'appearance': {
                'theme_mode': 'theme_mode',
                'sidebar_collapsed': 'sidebar_collapsed',
                'show_breadcrumb': 'show_breadcrumb',
                'language': 'language',
                'font_size': 'font_size'
            },
            'notification': {
                'system_notification': 'system_notification',
                'email_notification': 'email_notification',
                'sound_notification': 'sound_notification',
                'browser_notification': 'browser_notification'
            },
            'security': {
                'auto_logout_time': 'auto_logout_time',
                'session_timeout': 'session_timeout',
                'enable_two_factor': 'enable_two_factor'
            },
            'workspace': {
                'default_page': 'default_page',
                'items_per_page': 'items_per_page',
                'date_format': 'date_format',
                'time_format': 'time_format'
            }
        }
        
        for category, settings in data.items():
            if category in mapping:
                for key, value in settings.items():
                    if key in mapping[category]:
                        attr_name = mapping[category][key]
                        if hasattr(self, attr_name):
                            setattr(self, attr_name, value)
        
        self.updated_at = now()
    
    def __repr__(self):
        return f'<UserPreferences {self.user_id}>'
# app/models/user_login_log.py
from . import db
from app.utils.timezone import now
from sqlalchemy import func

class UserLoginLog(db.Model):
    __tablename__ = 'user_login_logs'
    
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(100))
    
    # 登录信息
    login_time = db.Column(db.DateTime, nullable=False)
    logout_time = db.Column(db.DateTime)
    ip_address = db.Column(db.String(45))  # 支持IPv6
    user_agent = db.Column(db.Text)
    device_type = db.Column(db.String(50))  # Desktop/Mobile/Tablet
    browser = db.Column(db.String(50))
    os = db.Column(db.String(50))
    location = db.Column(db.String(100))  # 地理位置
    
    # 状态
    status = db.Column(db.String(10), nullable=False)  # success/failed
    failure_reason = db.Column(db.String(255))
    
    created_at = db.Column(db.DateTime, default=now)
    
    # 关系
    user = db.relationship('User', backref='login_logs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'login_time': self.login_time.isoformat() if self.login_time else None,
            'logout_time': self.logout_time.isoformat() if self.logout_time else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'device_type': self.device_type,
            'browser': self.browser,
            'os': self.os,
            'location': self.location,
            'status': self.status,
            'failure_reason': self.failure_reason
        }
    
    @classmethod
    def create_login_log(cls, user_id, ip_address=None, user_agent=None, status='success', **kwargs):
        """创建登录日志"""
        # 解析用户代理信息
        device_info = cls._parse_user_agent(user_agent) if user_agent else {}
        
        log = cls(
            user_id=user_id,
            login_time=now(),
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=device_info.get('device_type'),
            browser=device_info.get('browser'),
            os=device_info.get('os'),
            location=kwargs.get('location'),
            status=status,
            failure_reason=kwargs.get('failure_reason'),
            session_id=kwargs.get('session_id')
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    @classmethod
    def update_logout_time(cls, session_id, logout_time=None):
        """更新登出时间"""
        if logout_time is None:
            logout_time = now()
            
        log = cls.query.filter_by(session_id=session_id, status='success').first()
        if log:
            log.logout_time = logout_time
            db.session.commit()
            return log
        return None
    
    @classmethod
    def get_user_login_stats(cls, user_id, days=30):
        """获取用户登录统计"""
        from datetime import timedelta
        
        start_date = now() - timedelta(days=days)
        
        # 总登录次数
        total_logins = cls.query.filter(
            cls.user_id == user_id,
            cls.login_time >= start_date,
            cls.status == 'success'
        ).count()
        
        # 失败登录次数
        failed_logins = cls.query.filter(
            cls.user_id == user_id,
            cls.login_time >= start_date,
            cls.status == 'failed'
        ).count()
        
        # 最近登录
        latest_login = cls.query.filter(
            cls.user_id == user_id,
            cls.status == 'success'
        ).order_by(cls.login_time.desc()).first()
        
        return {
            'total_logins': total_logins,
            'failed_logins': failed_logins,
            'success_rate': (total_logins / (total_logins + failed_logins) * 100) if (total_logins + failed_logins) > 0 else 0,
            'latest_login': latest_login.to_dict() if latest_login else None
        }
    
    @staticmethod
    def _parse_user_agent(user_agent):
        """解析用户代理字符串（简单版本）"""
        user_agent = user_agent.lower()
        
        # 设备类型检测
        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
            device_type = 'Mobile'
        elif 'tablet' in user_agent or 'ipad' in user_agent:
            device_type = 'Tablet'
        else:
            device_type = 'Desktop'
        
        # 浏览器检测
        if 'chrome' in user_agent:
            browser = 'Chrome'
        elif 'firefox' in user_agent:
            browser = 'Firefox'
        elif 'safari' in user_agent:
            browser = 'Safari'
        elif 'edge' in user_agent:
            browser = 'Edge'
        else:
            browser = 'Unknown'
        
        # 操作系统检测
        if 'windows' in user_agent:
            os = 'Windows'
        elif 'mac' in user_agent:
            os = 'macOS'
        elif 'linux' in user_agent:
            os = 'Linux'
        elif 'android' in user_agent:
            os = 'Android'
        elif 'ios' in user_agent:
            os = 'iOS'
        else:
            os = 'Unknown'
        
        return {
            'device_type': device_type,
            'browser': browser,
            'os': os
        }
    
    def __repr__(self):
        return f'<UserLoginLog {self.user_id} - {self.status}>'
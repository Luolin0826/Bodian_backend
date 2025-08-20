# app/models/user_session.py
from . import db
from app.utils.timezone import now
import hashlib
import secrets

class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    token_hash = db.Column(db.String(255), nullable=False)
    
    # 会话信息
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    device_fingerprint = db.Column(db.String(255))
    is_current = db.Column(db.Boolean, default=False)
    
    # 时间
    created_at = db.Column(db.DateTime, default=now)
    last_activity = db.Column(db.DateTime, default=now)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    # 关系
    user = db.relationship('User', backref='sessions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'device_fingerprint': self.device_fingerprint,
            'is_current': self.is_current,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
    
    @classmethod
    def create_session(cls, user_id, token, ip_address=None, user_agent=None, expires_at=None, **kwargs):
        """创建新会话"""
        if expires_at is None:
            from datetime import timedelta
            expires_at = now() + timedelta(hours=24)
        
        # 生成会话ID和token哈希
        session_id = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # 生成设备指纹
        device_fingerprint = cls._generate_device_fingerprint(ip_address, user_agent)
        
        session = cls(
            user_id=user_id,
            session_id=session_id,
            token_hash=token_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            expires_at=expires_at,
            is_current=kwargs.get('is_current', True)
        )
        
        # 将其他会话标记为非当前会话
        if session.is_current:
            cls.query.filter_by(user_id=user_id, is_current=True).update({'is_current': False})
        
        db.session.add(session)
        db.session.commit()
        return session
    
    @classmethod
    def get_by_token(cls, token):
        """通过token获取会话"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return cls.query.filter_by(token_hash=token_hash).first()
    
    @classmethod
    def cleanup_expired_sessions(cls):
        """清理过期会话"""
        current_time = now()
        expired_sessions = cls.query.filter(cls.expires_at < current_time).all()
        
        for session in expired_sessions:
            db.session.delete(session)
        
        db.session.commit()
        return len(expired_sessions)
    
    @classmethod
    def logout_other_sessions(cls, user_id, current_session_id=None):
        """登出其他会话"""
        query = cls.query.filter_by(user_id=user_id)
        
        if current_session_id:
            query = query.filter(cls.session_id != current_session_id)
        
        other_sessions = query.all()
        count = len(other_sessions)
        
        for session in other_sessions:
            db.session.delete(session)
        
        db.session.commit()
        return count
    
    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity = now()
        db.session.commit()
    
    def is_expired(self):
        """检查会话是否过期"""
        return now() > self.expires_at
    
    def extend_expiry(self, hours=24):
        """延长会话过期时间"""
        from datetime import timedelta
        self.expires_at = now() + timedelta(hours=hours)
        db.session.commit()
    
    @staticmethod
    def _generate_device_fingerprint(ip_address, user_agent):
        """生成设备指纹"""
        if not ip_address or not user_agent:
            return None
        
        fingerprint_data = f"{ip_address}:{user_agent}"
        return hashlib.md5(fingerprint_data.encode()).hexdigest()
    
    def __repr__(self):
        return f'<UserSession {self.session_id}>'
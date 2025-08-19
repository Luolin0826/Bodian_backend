# app/services/auth_service.py
from app.models import db, User

class AuthService:
    @staticmethod
    def create_user(username, password, real_name=None, role='viewer'):
        """创建用户"""
        user = User(
            username=username,
            real_name=real_name,
            role=role
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def verify_password(user, password):
        """验证密码"""
        return user.check_password(password)
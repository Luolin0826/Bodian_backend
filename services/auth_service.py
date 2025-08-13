# app/services/auth_service.py
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User

class AuthService:
    @staticmethod
    def create_user(username, password, real_name=None, role='viewer'):
        """创建用户"""
        hashed_password = generate_password_hash(password)
        user = User(
            username=username,
            password=hashed_password,
            real_name=real_name,
            role=role
        )
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def verify_password(user, password):
        """验证密码"""
        return check_password_hash(user.password, password)
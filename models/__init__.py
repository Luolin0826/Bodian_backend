# app/models/__init__.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 导入所有模型
from .user import User
from .customer import Customer
from .script import Script
from .knowledge_base import KnowledgeBase

__all__ = ['db', 'User', 'Customer', 'Script', 'KnowledgeBase']

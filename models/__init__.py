# app/models/__init__.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 导入所有模型
from .user import User
from .customer import Customer
from .script import Script
from .knowledge_base import KnowledgeBase
from .department import Department
from .role import Role, PermissionTemplate
from .operation_log import OperationLog
from .user_preferences import UserPreferences
from .notification import Notification
from .user_login_log import UserLoginLog
from .user_session import UserSession
from .follow_up_record import FollowUpRecord
from .follow_up_reminder import FollowUpReminder
from .script_favorite import ScriptFavorite

__all__ = ['db', 'User', 'Customer', 'Script', 'KnowledgeBase', 'Department', 'Role', 'PermissionTemplate', 'OperationLog', 'UserPreferences', 'Notification', 'UserLoginLog', 'UserSession', 'FollowUpRecord', 'FollowUpReminder', 'ScriptFavorite']

# app/routes/__init__.py
from flask import Blueprint

# 导入所有蓝图
from .auth import auth_bp
from .customers import customers_bp
from .scripts import scripts_bp
from .knowledge import knowledge_bp
from .stats import stats_bp
from .departments import departments_bp
from .users import users_bp
from .roles import roles_bp
from .operation_logs import operation_logs_bp

__all__ = ['auth_bp', 'customers_bp', 'scripts_bp', 'knowledge_bp', 'stats_bp', 'departments_bp', 'users_bp', 'roles_bp', 'operation_logs_bp']
# app/routes/__init__.py
from flask import Blueprint

# 导入所有蓝图
from .auth import auth_bp
from .customers import customers_bp
from .scripts import scripts_bp
from .knowledge import knowledge_bp
from .stats import stats_bp

__all__ = ['auth_bp', 'customers_bp', 'scripts_bp', 'knowledge_bp', 'stats_bp']
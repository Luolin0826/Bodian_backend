# app/config/config.py
import os
from datetime import timedelta

class Config:
    """基础配置"""
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://AzMysql:AaBb19990826@luolin.mysql.database.azure.com:3306/bodiandev?charset=utf8mb4'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # JWT配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # 分页配置
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # Redis配置（如果需要）
    REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    
    # 跨域配置
    CORS_ORIGINS = "*"

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_ECHO = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
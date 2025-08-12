import os
from datetime import timedelta

class Config:
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://AzMysql:AaBb19990826@luolin.mysql.database.azure.com:3306/bodiandev?charset=utf8mb4'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'ab990826123456')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Redis配置
    REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    
    # 分页配置
    PAGE_SIZE = 20
    
    # 文件上传配置
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
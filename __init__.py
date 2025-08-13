# app/__init__.py
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
import pymysql

# 使用pymysql作为MySQL驱动
pymysql.install_as_MySQLdb()

def create_app(config_name='development'):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 加载配置
    from app.config.config import config
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    from app.models import db
    db.init_app(app)
    
    migrate = Migrate(app, db)
    CORS(app, origins=app.config.get('CORS_ORIGINS', '*'))
    jwt = JWTManager(app)
    
    # 注册蓝图
    from app.routes import auth_bp, customers_bp, scripts_bp, knowledge_bp, stats_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(customers_bp, url_prefix='/api/v1/customers')
    app.register_blueprint(scripts_bp, url_prefix='/api/v1/scripts')
    app.register_blueprint(knowledge_bp, url_prefix='/api/v1/knowledge')
    app.register_blueprint(stats_bp, url_prefix='/api/v1/stats')
    
    # 健康检查路由
    @app.route('/api/health')
    def health_check():
        try:
            # 使用正确的语法执行SQL
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db_status = 'connected'
        except Exception as e:
            db_status = f'error: {str(e)}'
        
        return {
            'status': 'healthy',
            'database': db_status,
            'environment': config_name
        }
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    return app

# 导出create_app函数
__all__ = ['create_app']
# app/__init__.py
from flask import Flask, request, make_response
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
    
    # 配置CORS - 只配置一次，支持所有方法包括OPTIONS
    CORS(app, 
         origins=[
             "http://localhost:13686", 
             "http://localhost:*", 
             "http://dev_frontend:3000",
             "http://dev_frontend:8088",
             "http://127.0.0.1:*",
             "http://0.0.0.0:*"
         ],
         resources={r"/api/*": {"origins": "*"}},
         allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Origin"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
         supports_credentials=True)
    
    jwt = JWTManager(app)
    
    # JWT用户加载函数
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        # 如果传入的是字符串，直接返回；如果是用户对象，返回其ID
        return user if isinstance(user, str) else user.id
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return User.query.filter_by(id=int(identity)).one_or_none()
    
    # 初始化中间件
    from app.utils.middleware import init_middleware
    init_middleware(app)
    
    # 注册蓝图
    from app.routes import (auth_bp, customers_bp, scripts_bp, knowledge_bp, stats_bp,
                           departments_bp, users_bp, roles_bp, operation_logs_bp,
                           follow_up_records_bp, follow_up_reminders_bp)
    from app.routes.user_profile import user_profile_bp
    from app.routes.user_preferences import user_preferences_bp
    from app.routes.notifications import notifications_bp
    from app.routes.security import security_bp
    from app.models import User
    
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(customers_bp, url_prefix='/api/v1')
    app.register_blueprint(scripts_bp, url_prefix='/api/v1/scripts')
    app.register_blueprint(knowledge_bp, url_prefix='/api/v1/knowledge')
    app.register_blueprint(stats_bp, url_prefix='/api/v1/stats')
    app.register_blueprint(departments_bp, url_prefix='/api/v1')
    app.register_blueprint(users_bp, url_prefix='/api/v1')
    app.register_blueprint(roles_bp, url_prefix='/api/v1/roles')
    app.register_blueprint(operation_logs_bp, url_prefix='/api/v1')
    app.register_blueprint(follow_up_records_bp, url_prefix='/api/v1')
    app.register_blueprint(follow_up_reminders_bp, url_prefix='/api/v1')
    
    # 用户中心相关蓝图
    app.register_blueprint(user_profile_bp, url_prefix='/api/v1/user')
    app.register_blueprint(user_preferences_bp, url_prefix='/api/v1/user')
    app.register_blueprint(notifications_bp, url_prefix='/api/v1/notifications')
    app.register_blueprint(security_bp, url_prefix='/api/v1/user')
    
    # 健康检查路由
    @app.route('/api/health')
    def health_check():
        try:
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
    
    # 全局OPTIONS处理
    @app.before_request
    def handle_options():
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Access-Control-Allow-Origin'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            return response

    # 测试路由
    @app.route('/api/v1/test', methods=['GET', 'POST', 'OPTIONS'])
    def test_route():
        if request.method == 'OPTIONS':
            return '', 200
        return {'message': 'API is working', 'method': request.method}
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found', 'path': request.path}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    return app

# 导出create_app函数
__all__ = ['create_app']
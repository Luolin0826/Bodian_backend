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
             "http://0.0.0.0:*",
             # 生产环境域名
             "http://47.101.39.246",
             "http://47.101.39.246:*",
             "https://47.101.39.246",
             "https://47.101.39.246:*"
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
                           follow_up_records_bp, follow_up_reminders_bp, recruitment_bp)
    from app.routes.user_profile import user_profile_bp
    from app.routes.user_preferences import user_preferences_bp
    from app.routes.notifications import notifications_bp
    from app.routes.security import security_bp
    from app.routes.avatars import avatars_bp
    from app.models import User
    
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    # 临时兼容Nginx代理配置（去除/api前缀的路径）
    from app.routes.auth import auth_bp as auth_bp_proxy
    app.register_blueprint(auth_bp_proxy, url_prefix='/v1/auth', name='auth_proxy')
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
    # 临时禁用旧的recruitment_bp，使用新的updated_recruitment_api
    # app.register_blueprint(recruitment_bp, url_prefix='/api/v1')
    
    # 注册新的招聘数据API v2
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from updated_recruitment_api import updated_recruitment_bp
        from frontend_analytics_api import frontend_analytics_bp
        from data_search_api import data_search_bp
        
        app.register_blueprint(updated_recruitment_bp, url_prefix='/api/v1')
        app.register_blueprint(frontend_analytics_bp, url_prefix='/api/v1')
        app.register_blueprint(data_search_bp, url_prefix='/api/v1/data-search')
        print("✓ 已注册新招聘数据API (v1)")
        print("✓ 已注册前端分析API (v1)")
        print("✓ 已注册数查一点通API (v1)")
    except Exception as e:
        print(f"⚠ 注册新API失败: {e}")
    
    # 用户中心相关蓝图
    app.register_blueprint(user_profile_bp, url_prefix='/api/v1/user')
    app.register_blueprint(user_preferences_bp, url_prefix='/api/v1/user')
    app.register_blueprint(notifications_bp, url_prefix='/api/v1/notifications')
    app.register_blueprint(security_bp, url_prefix='/api/v1/user')
    app.register_blueprint(avatars_bp, url_prefix='/api/v1/avatars')
    # 临时兼容Nginx代理配置（去除/api前缀的路径）
    from app.routes.avatars import avatars_bp as avatars_bp_proxy
    app.register_blueprint(avatars_bp_proxy, url_prefix='/v1/avatars', name='avatars_proxy')
    
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
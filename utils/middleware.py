# app/utils/middleware.py
from flask import request, g
from flask_jwt_extended import get_current_user, verify_jwt_in_request
from app.models import OperationLog, User

class LoggingMiddleware:
    """操作日志记录中间件"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化中间件"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """请求前处理"""
        # 记录请求开始时间
        g.request_start_time = request.environ.get('REQUEST_START_TIME')
        
        # 尝试获取当前用户
        try:
            if request.headers.get('Authorization'):
                verify_jwt_in_request(optional=True)
                current_user = get_current_user()
                g.current_user = current_user
        except:
            g.current_user = None
    
    def after_request(self, response):
        """请求后处理"""
        # 记录登录/登出操作
        if request.endpoint in ['auth.login', 'auth.logout']:
            self._log_auth_operation(response)
        
        return response
    
    def _log_auth_operation(self, response):
        """记录认证操作"""
        try:
            current_user = g.get('current_user')
            
            if request.endpoint == 'auth.login':
                if response.status_code == 200:
                    # 登录成功
                    if current_user:
                        OperationLog.create_log(
                            user=current_user,
                            action='login',
                            resource='system',
                            description=f'用户登录成功',
                            request=request,
                            sensitive=True
                        )
                        
                        # 更新最后登录时间
                        from datetime import datetime
                        current_user.last_login = datetime.utcnow()
                        from app.models import db
                        db.session.commit()
                else:
                    # 登录失败 - 需要从请求数据中获取用户名
                    username = request.get_json().get('username') if request.get_json() else None
                    if username:
                        user = User.query.filter_by(username=username).first()
                        if user:
                            OperationLog.create_log(
                                user=user,
                                action='login_failed',
                                resource='system',
                                description=f'用户登录失败',
                                request=request,
                                sensitive=True
                            )
            
            elif request.endpoint == 'auth.logout':
                if current_user:
                    OperationLog.create_log(
                        user=current_user,
                        action='logout',
                        resource='system',
                        description=f'用户退出登录',
                        request=request,
                        sensitive=False
                    )
        
        except Exception as e:
            # 记录日志失败不影响主流程
            print(f"记录认证操作日志失败: {str(e)}")

class SecurityMiddleware:
    """安全中间件"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化中间件"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """请求前安全检查"""
        # IP白名单检查（可配置）
        # self._check_ip_whitelist()
        
        # 请求频率限制（可配置）
        # self._check_rate_limit()
        
        pass
    
    def after_request(self, response):
        """请求后安全处理"""
        # 添加安全头
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        return response
    
    def _check_ip_whitelist(self):
        """检查IP白名单"""
        # 可以根据需要实现IP白名单检查
        pass
    
    def _check_rate_limit(self):
        """检查请求频率限制"""
        # 可以根据需要实现请求频率限制
        pass

def init_middleware(app):
    """初始化所有中间件"""
    LoggingMiddleware(app)
    SecurityMiddleware(app)
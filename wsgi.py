import os
import sys
import traceback

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    print("开始导入 create_app...")
    from app import create_app
    print("create_app 导入成功")
    
    # 修复环境变量读取 - 优先使用 ENVIRONMENT，其次 FLASK_ENV
    env = os.getenv('ENVIRONMENT') or os.getenv('FLASK_ENV', 'development')
    print(f"使用环境: {env}")
    
    print("开始创建应用...")
    app = create_app(env)
    print("应用创建成功")
    
except Exception as e:
    print(f"WSGI 启动失败: {str(e)}")
    traceback.print_exc()
    # 创建一个简单的应用作为fallback
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/error')
    def error():
        return {'error': 'Application failed to start', 'details': str(e)}, 500

if __name__ == '__main__':
    # 开发环境配置
    debug_mode = env == 'development'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)

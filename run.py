import os
from app import create_app
from app.models import db

# 获取环境配置 - 修复环境变量读取
env = os.getenv('ENVIRONMENT') or os.getenv('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == '__main__':
    with app.app_context():
        # 创建数据库表
        db.create_all()
        print(f"✅ 应用启动成功 - 环境: {env}")
    
    # 启动应用
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    app.run(
        host='0.0.0.0', 
        port=port, 
        debug=(env == 'development')
    )
# app.py - Flask主应用文件
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import pymysql
import os

# 使用pymysql作为MySQL驱动
pymysql.install_as_MySQLdb()

# 初始化Flask应用
app = Flask(__name__)

# 配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://AzMysql:AaBb19990826@luolin.mysql.database.azure.com:3306/bodiandev?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key-change-this'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# 初始化扩展
db = SQLAlchemy(app)
CORS(app)
jwt = JWTManager(app)

# ==================== 数据模型 ====================

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(50))
    role = db.Column(db.Enum('admin', 'sales', 'teacher', 'viewer'), default='viewer')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    customer_date = db.Column(db.Date)
    channel = db.Column(db.String(50))
    wechat_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    add_date = db.Column(db.Date)
    deal_date = db.Column(db.Date)
    status = db.Column(db.Enum('潜在', '跟进中', '已成交', '已流失'), default='潜在')
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Script(db.Model):
    __tablename__ = 'scripts'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100))
    title = db.Column(db.String(200))
    question = db.Column(db.Text)
    answer = db.Column(db.Text, nullable=False)
    keywords = db.Column(db.String(500))
    usage_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class KnowledgeBase(db.Model):
    __tablename__ = 'knowledge_base'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum('电网考试', '考研', '校招', '其他'), nullable=False)
    category = db.Column(db.String(100))
    question = db.Column(db.Text)
    answer = db.Column(db.Text)
    tags = db.Column(db.String(500))
    view_count = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== API路由 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    try:
        # 测试数据库连接
        db.session.execute(db.text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # 这里应该验证密码，暂时简化处理
    user = User.query.filter_by(username=username).first()
    
    if user:
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'real_name': user.real_name,
                'role': user.role
            }
        })
    
    return jsonify({'message': '用户名或密码错误'}), 401

@app.route('/api/v1/customers', methods=['GET'])
@jwt_required()
def get_customers():
    """获取客户列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    channel = request.args.get('channel')
    
    query = Customer.query
    
    if status:
        query = query.filter_by(status=status)
    if channel:
        query = query.filter_by(channel=channel)
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    customers = [{
        'id': c.id,
        'customer_date': c.customer_date.isoformat() if c.customer_date else None,
        'channel': c.channel,
        'wechat_name': c.wechat_name,
        'phone': c.phone,
        'status': c.status,
        'remark': c.remark
    } for c in pagination.items]
    
    return jsonify({
        'data': customers,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })

@app.route('/api/v1/customers', methods=['POST'])
@jwt_required()
def create_customer():
    """创建客户"""
    data = request.get_json()
    
    customer = Customer(
        customer_date=datetime.strptime(data.get('customer_date'), '%Y-%m-%d').date() if data.get('customer_date') else None,
        channel=data.get('channel'),
        wechat_name=data.get('wechat_name'),
        phone=data.get('phone'),
        status=data.get('status', '潜在'),
        remark=data.get('remark')
    )
    
    db.session.add(customer)
    db.session.commit()
    
    return jsonify({
        'message': '客户创建成功',
        'id': customer.id
    }), 201

@app.route('/api/v1/scripts/search', methods=['GET'])
def search_scripts():
    """搜索话术"""
    keyword = request.args.get('keyword', '')
    category = request.args.get('category')
    
    query = Script.query.filter_by(is_active=True)
    
    if category:
        query = query.filter_by(category=category)
    
    if keyword:
        query = query.filter(
            db.or_(
                Script.question.like(f'%{keyword}%'),
                Script.answer.like(f'%{keyword}%'),
                Script.keywords.like(f'%{keyword}%')
            )
        )
    
    scripts = query.limit(20).all()
    
    results = [{
        'id': s.id,
        'category': s.category,
        'title': s.title,
        'question': s.question,
        'answer': s.answer,
        'usage_count': s.usage_count
    } for s in scripts]
    
    # 增加使用次数
    for s in scripts:
        s.usage_count += 1
    db.session.commit()
    
    return jsonify({'data': results})

@app.route('/api/v1/knowledge/search', methods=['GET'])
def search_knowledge():
    """搜索知识库"""
    keyword = request.args.get('keyword', '')
    type_ = request.args.get('type')
    
    query = KnowledgeBase.query.filter_by(is_published=True)
    
    if type_:
        query = query.filter_by(type=type_)
    
    if keyword:
        query = query.filter(
            db.or_(
                KnowledgeBase.question.like(f'%{keyword}%'),
                KnowledgeBase.answer.like(f'%{keyword}%'),
                KnowledgeBase.tags.like(f'%{keyword}%')
            )
        )
    
    knowledge = query.limit(20).all()
    
    results = [{
        'id': k.id,
        'type': k.type,
        'category': k.category,
        'question': k.question,
        'answer': k.answer,
        'view_count': k.view_count
    } for k in knowledge]
    
    # 增加查看次数
    for k in knowledge:
        k.view_count += 1
    db.session.commit()
    
    return jsonify({'data': results})

@app.route('/api/v1/stats/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """获取仪表板统计数据"""
    # 客户统计
    total_customers = Customer.query.count()
    potential_customers = Customer.query.filter_by(status='潜在').count()
    deal_customers = Customer.query.filter_by(status='已成交').count()
    
    # 今日新增
    today = datetime.now().date()
    today_customers = Customer.query.filter(
        db.func.date(Customer.created_at) == today
    ).count()
    
    # 渠道分布
    channel_stats = db.session.query(
        Customer.channel,
        db.func.count(Customer.id).label('count')
    ).group_by(Customer.channel).all()
    
    return jsonify({
        'customer_stats': {
            'total': total_customers,
            'potential': potential_customers,
            'deal': deal_customers,
            'today_new': today_customers
        },
        'channel_distribution': [
            {'channel': c[0], 'count': c[1]} for c in channel_stats
        ]
    })

# ==================== 数据初始化 ====================

@app.route('/api/v1/init', methods=['POST'])
def init_database():
    """初始化数据库（仅开发环境使用）"""
    try:
        # 创建所有表
        db.create_all()
        
        # 创建默认用户
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password='admin123',  # 实际应用中应该加密
                real_name='管理员',
                role='admin'
            )
            db.session.add(admin)
        
        # 添加示例话术分类
        sample_scripts = [
            {'category': '销售话术', 'title': '价格咨询', 
             'question': '课程多少钱？', 
             'answer': '了解了一下课程体系用开课的进度，一次付费没有二次隐形收费，价格公开透明，买贵退还差价'},
            {'category': '考试咨询', 'title': '考试科目', 
             'question': '考试科目有哪些？', 
             'answer': '本科：电路，电机，电分，继保，高压，发电厂，电力电子，企业文化（800题），行测，时政'},
            {'category': '小红书回复', 'title': '专升本出路', 
             'question': '专升本民办二本的出路', 
             'answer': '考国网性价比是最高的，但是一定要努力，只有一次机会，每年都有专升本成功上岸国网的学员'},
        ]
        
        for script_data in sample_scripts:
            if not Script.query.filter_by(title=script_data['title']).first():
                script = Script(**script_data)
                db.session.add(script)
        
        # 添加示例知识库
        sample_knowledge = [
            {'type': '电网考试', 'category': '考试规划', 
             'question': '大四开始备考来得及不', 
             'answer': '可以冲一下，之前有同学3个月干到80+，但是时间比较紧，复习的时候需要调整一下思路'},
            {'type': '考研', 'category': '目标院校', 
             'question': '本科985/211目标985/211', 
             'answer': '在校成绩只要不是垫底的，学习态度没啥问题的，一般都可以起码考本校'},
        ]
        
        for knowledge_data in sample_knowledge:
            if not KnowledgeBase.query.filter_by(question=knowledge_data['question']).first():
                knowledge = KnowledgeBase(**knowledge_data)
                db.session.add(knowledge)
        
        db.session.commit()
        
        return jsonify({'message': '数据库初始化成功'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# ==================== 主程序入口 ====================

if __name__ == '__main__':
    with app.app_context():
        # 测试数据库连接
        try:
            db.session.execute(db.text('SELECT 1'))
            print("✅ 数据库连接成功！")
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
    
    # 启动应用
    app.run(host='0.0.0.0', port=5000, debug=True)
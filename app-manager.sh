#!/bin/bash
# app-manager.sh - Flask应用统一管理脚本
# 融合了 dev.sh, deploy.sh, start_production.sh, manage.sh 的功能

# 配置变量
APP_NAME="Flask应用"
PID_FILE="./gunicorn.pid"
VENV_DIR="venv"
LOGS_DIR="./logs"
ACCESS_LOG="${LOGS_DIR}/access.log"
ERROR_LOG="${LOGS_DIR}/error.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 创建必要目录
create_dirs() {
    mkdir -p ${LOGS_DIR}
}

# 激活虚拟环境
activate_venv() {
    if [ -d "${VENV_DIR}" ]; then
        print_info "激活虚拟环境..."
        source ${VENV_DIR}/bin/activate
        return 0
    else
        print_warning "虚拟环境不存在，使用系统Python"
        return 1
    fi
}

# 停止应用
stop_app() {
    print_info "停止应用..."
    
    # 方式1: 通过PID文件停止
    if [ -f ${PID_FILE} ]; then
        local pid=$(cat ${PID_FILE})
        if kill ${pid} 2>/dev/null; then
            print_success "通过PID停止应用 (PID: ${pid})"
            rm -f ${PID_FILE}
        else
            print_warning "PID文件存在但进程不存在，清理PID文件"
            rm -f ${PID_FILE}
        fi
    fi
    
    # 方式2: 强制停止所有相关进程
    pkill -f gunicorn 2>/dev/null && print_info "强制停止gunicorn进程"
    pkill -f "python run.py" 2>/dev/null && print_info "强制停止开发服务器"
    
    sleep 2
    
    # 检查是否还有残留进程
    if pgrep -f "gunicorn\|python run.py" > /dev/null; then
        print_error "仍有进程残留，请手动检查"
        return 1
    else
        print_success "应用已完全停止"
        return 0
    fi
}

# 检查应用状态
check_status() {
    if pgrep -f gunicorn > /dev/null; then
        print_success "生产服务正在运行"
        echo "进程信息："
        ps aux | grep gunicorn | grep -v grep
        return 0
    elif pgrep -f "python run.py" > /dev/null; then
        print_success "开发服务正在运行"
        echo "进程信息："
        ps aux | grep "python run.py" | grep -v grep
        return 0
    else
        print_error "应用未运行"
        return 1
    fi
}

# 健康检查
health_check() {
    local max_attempts=5
    local attempt=1
    
    print_info "执行健康检查..."
    
    while [ ${attempt} -le ${max_attempts} ]; do
        if curl -s -f http://localhost:5000/api/health > /dev/null 2>&1; then
            print_success "健康检查通过 (尝试 ${attempt}/${max_attempts})"
            curl -s http://localhost:5000/api/health | python3 -m json.tool 2>/dev/null || echo "API响应正常但JSON格式异常"
            return 0
        else
            print_warning "健康检查失败 (尝试 ${attempt}/${max_attempts})"
            sleep 2
            attempt=$((attempt + 1))
        fi
    done
    
    print_error "健康检查失败，服务可能未正常启动"
    return 1
}

# 启动开发服务器
start_dev() {
    print_info "启动开发环境..."
    
    # 停止现有服务
    stop_app
    
    # 设置开发环境变量
    export FLASK_ENV=development
    export FLASK_DEBUG=1
    
    # 激活虚拟环境
    activate_venv
    
    # 创建目录
    create_dirs
    
    print_info "启动Flask开发服务器..."
    print_info "访问地址: http://localhost:5000"
    print_info "使用 Ctrl+C 停止服务器"
    
    # 启动开发服务器（前台运行）
    python run.py
}

# 启动生产服务器
start_prod() {
    print_info "启动生产环境..."
    
    # 停止现有服务
    stop_app
    
    # 设置生产环境变量
    export FLASK_ENV=production
    
    # 激活虚拟环境
    activate_venv
    
    # 创建目录
    create_dirs
    
    print_info "启动配置:"
    echo "  - Workers: 2"
    echo "  - Worker类型: sync"
    echo "  - 绑定地址: 0.0.0.0:5000"
    echo "  - 超时时间: 300s"
    echo "  - 日志级别: info"
    
    # 启动Gunicorn
    python -m gunicorn -w 2 \
        -k sync \
        -b 0.0.0.0:5000 \
        --access-logfile ${ACCESS_LOG} \
        --error-logfile ${ERROR_LOG} \
        --log-level info \
        --timeout 300 \
        --keep-alive 5 \
        --max-requests 500 \
        --max-requests-jitter 25 \
        --worker-connections 1000 \
        --daemon \
        --pid ${PID_FILE} \
        wsgi:app
    
    # 等待启动（延长等待时间）
    sleep 10
    
    # 检查启动状态
    if [ -f ${PID_FILE} ] && pgrep -f gunicorn > /dev/null; then
        print_success "生产服务启动成功"
        echo "PID: $(cat ${PID_FILE})"
        echo "访问地址: http://0.0.0.0:5000"
        
        # 执行健康检查
        health_check
    else
        print_error "生产服务启动失败"
        echo "错误日志："
        tail -20 ${ERROR_LOG} 2>/dev/null || echo "无法读取错误日志"
        return 1
    fi
}

# 完整部署（包含依赖安装和数据库初始化）
deploy() {
    print_info "执行完整部署..."
    
    # 设置生产环境变量
    export FLASK_ENV=production
    export DATABASE_URL="mysql+pymysql://AzMysql:AaBb19990826@luolin.mysql.database.azure.com:3306/bodiandev?charset=utf8mb4"
    export JWT_SECRET_KEY="your-production-secret-key-change-this-in-production"
    
    # 停止现有服务
    stop_app
    
    # 激活虚拟环境
    activate_venv
    
    # 安装依赖
    print_info "安装/更新依赖..."
    pip install -r requirements.txt
    pip install gevent
    
    # 数据库初始化
    print_info "初始化数据库..."
    python -c "
from app import create_app
from app.models import db
app = create_app('production')
with app.app_context():
    db.create_all()
    print('✅ 数据库表创建成功')
" || print_error "数据库初始化失败"
    
    # 启动生产服务
    start_prod
}

# 重启应用
restart() {
    print_info "重启应用..."
    stop_app
    sleep 2
    start_prod
}

# 查看日志
show_logs() {
    if [ ! -f ${ACCESS_LOG} ] && [ ! -f ${ERROR_LOG} ]; then
        print_error "日志文件不存在"
        return 1
    fi
    
    print_info "查看实时日志 (Ctrl+C 退出)..."
    tail -f ${ACCESS_LOG} ${ERROR_LOG} 2>/dev/null
}

# 运行测试
run_tests() {
    print_info "运行测试..."
    
    # 激活虚拟环境
    activate_venv
    
    # 设置测试环境
    export FLASK_ENV=testing
    
    # 运行测试
    python -m pytest tests/ -v
}

# 显示帮助信息
show_help() {
    echo "Flask应用统一管理脚本"
    echo ""
    echo "用法: $0 <命令> [选项]"
    echo ""
    echo "命令:"
    echo "  dev       启动开发服务器 (前台运行)"
    echo "  start     启动生产服务器 (后台运行)"
    echo "  stop      停止所有服务"
    echo "  restart   重启生产服务器"
    echo "  status    查看服务状态"
    echo "  deploy    完整部署 (安装依赖+数据库+启动)"
    echo "  logs      查看实时日志"
    echo "  test      运行测试"
    echo "  health    健康检查"
    echo "  help      显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 dev              # 开发环境"
    echo "  $0 start            # 生产环境"
    echo "  $0 deploy           # 完整部署"
    echo "  $0 logs             # 查看日志"
}

# 主程序入口
main() {
    case "$1" in
        dev)
            start_dev
            ;;
        start)
            start_prod
            ;;
        stop)
            stop_app
            ;;
        restart)
            restart
            ;;
        status)
            check_status
            ;;
        deploy)
            deploy
            ;;
        logs)
            show_logs
            ;;
        test)
            run_tests
            ;;
        health)
            health_check
            ;;
        help|--help|-h)
            show_help
            ;;
        "")
            print_error "请指定命令"
            show_help
            exit 1
            ;;
        *)
            print_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主程序
main "$@"
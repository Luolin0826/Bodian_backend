# 启停脚本对比与整合说明

## 📋 现有脚本功能对比

| 脚本名称 | 主要功能 | 环境 | 运行方式 | 特殊功能 |
|---------|---------|------|---------|----------|
| `dev.sh` | 开发环境启动 | development | 前台 | 简单的Flask开发服务器 |
| `manage.sh` | 基础管理 | production | 后台 | start/stop/restart/status/logs/test |
| `start_production.sh` | 生产启动 | production | 后台 | 详细的状态检查和健康测试 |
| `deploy.sh` | 完整部署 | production | 后台 | 依赖安装+数据库初始化+启动 |

## 🆕 新的统一脚本 `app-manager.sh`

### ✨ 融合的功能

```bash
# 开发环境 (融合 dev.sh)
./app-manager.sh dev

# 生产环境启动 (融合 manage.sh + start_production.sh)
./app-manager.sh start

# 完整部署 (融合 deploy.sh)
./app-manager.sh deploy

# 其他管理功能
./app-manager.sh stop      # 停止服务
./app-manager.sh restart   # 重启服务
./app-manager.sh status    # 查看状态
./app-manager.sh logs      # 查看日志
./app-manager.sh test      # 运行测试
./app-manager.sh health    # 健康检查
```

### 🔧 增强功能

1. **彩色输出** - 更清晰的状态显示
2. **智能进程管理** - 多种方式停止进程，确保完全清理
3. **健康检查** - 自动验证服务启动状态
4. **统一配置** - 集中管理所有配置参数
5. **错误处理** - 更好的错误提示和日志显示
6. **虚拟环境支持** - 自动检测和激活虚拟环境

## 📂 建议的文件清理

### 🗑️ 可以删除的脚本
- `dev.sh` → 功能已整合到 `app-manager.sh dev`
- `start_production.sh` → 功能已整合到 `app-manager.sh start`  
- `deploy.sh` → 功能已整合到 `app-manager.sh deploy`

### 🤔 可选保留
- `manage.sh` → 如果您习惯了原有的简单命令，可以保留作为备份

## 🚀 使用建议

**日常开发：**
```bash
./app-manager.sh dev    # 开发调试
```

**生产部署：**
```bash
./app-manager.sh deploy # 首次部署或更新部署
./app-manager.sh start  # 日常启动
./app-manager.sh stop   # 停止服务
```

**运维监控：**
```bash
./app-manager.sh status # 检查状态
./app-manager.sh health # 健康检查
./app-manager.sh logs   # 查看日志
```

## ⚡ 快速迁移

如果您同意整合，可以执行：
```bash
# 备份原有脚本（可选）
mkdir backup-scripts
mv dev.sh deploy.sh start_production.sh backup-scripts/

# 使用新的统一脚本
./app-manager.sh help
```
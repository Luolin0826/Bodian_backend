# 🧹 脚本清理完成

## ✅ 清理结果

### 🗂️ 当前活跃脚本
- `app-manager.sh` - 统一管理脚本（新）

### 📦 已备份的旧脚本
移动到 `backup-scripts/` 目录：
- `dev.sh` - 开发环境启动脚本
- `deploy.sh` - 完整部署脚本  
- `start_production.sh` - 生产环境启动脚本
- `manage.sh` - 基础管理脚本

## 🚀 新的使用方式

### 常用命令
```bash
# 查看帮助
./app-manager.sh help

# 开发环境（替代 dev.sh）
./app-manager.sh dev

# 生产环境启动（替代 manage.sh start）
./app-manager.sh start

# 完整部署（替代 deploy.sh）
./app-manager.sh deploy

# 服务管理
./app-manager.sh stop
./app-manager.sh restart
./app-manager.sh status
./app-manager.sh logs
```

### 命令对照表
| 旧命令 | 新命令 |
|--------|--------|
| `./dev.sh` | `./app-manager.sh dev` |
| `./manage.sh start` | `./app-manager.sh start` |
| `./manage.sh stop` | `./app-manager.sh stop` |
| `./manage.sh restart` | `./app-manager.sh restart` |
| `./manage.sh status` | `./app-manager.sh status` |
| `./manage.sh logs` | `./app-manager.sh logs` |
| `./deploy.sh` | `./app-manager.sh deploy` |
| `./start_production.sh` | `./app-manager.sh start` |

## 🔧 如果需要恢复旧脚本

如果出现问题需要回退：
```bash
# 恢复所有旧脚本
mv backup-scripts/* .

# 或恢复特定脚本
mv backup-scripts/manage.sh .
```

## 🗑️ 完全清理（可选）

如果确定不再需要旧脚本，可以完全删除备份：
```bash
rm -rf backup-scripts/
```

---

**建议**: 使用新脚本1-2周后，如果一切正常，可以删除备份目录。
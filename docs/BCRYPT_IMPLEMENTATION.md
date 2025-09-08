# 密码加密实现文档

## 概述
本项目已完成从明文密码存储到bcrypt加密存储的升级，提供更安全的用户认证机制。

## 实现内容

### 1. 依赖安装
- 添加了 `bcrypt>=4.0.0` 到 `requirements.txt`
- bcrypt提供了安全的密码哈希功能

### 2. 用户模型更新 (`app/models/user.py`)
```python
# 新增方法
def set_password(self, password):
    """设置加密密码"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    self.password = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

def check_password(self, password):
    """验证密码"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    if isinstance(self.password, str):
        stored_password = self.password.encode('utf-8')
    else:
        stored_password = self.password
    return bcrypt.checkpw(password, stored_password)
```

### 3. 认证服务更新 (`app/services/auth_service.py`)
- 移除了Werkzeug密码哈希依赖
- 使用User模型的`set_password()`和`check_password()`方法
- 提供统一的密码处理接口

### 4. 登录逻辑改进 (`app/routes/auth.py`)
```python
# 改进的登录验证
if not user:
    return jsonify({'message': '用户名或密码错误'}), 401

if not user.check_password(password):
    return jsonify({'message': '用户名或密码错误'}), 401

if not user.is_active:
    return jsonify({'message': '账号已被禁用'}), 403
```

**特点：**
- 用户不存在和密码错误返回相同错误信息，防止用户名枚举
- 具体的错误信息（如"账号已被禁用"）仅在必要时显示
- 符合前端要求的401状态码和错误信息格式

### 5. 用户管理功能更新 (`app/routes/users.py`)

#### 用户创建
```python
user = User(username=data['username'], real_name=data['real_name'], ...)
user.set_password(data['password'])
```

#### 密码重置
```python
@users_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
def reset_password(user_id):
    # 密码长度验证
    if len(new_password) < 6:
        return jsonify({'code': 400, 'message': '密码长度不能少于6位'}), 400
    
    user.set_password(new_password)
```

#### 临时密码生成
```python
@users_bp.route('/users/<int:user_id>/generate-temp-password', methods=['POST'])
def generate_temp_password(user_id):
    # 生成8位随机密码
    temp_password = ''.join(secrets.choice(alphabet) for _ in range(8))
    user.set_password(temp_password)
    return {'temp_password': temp_password}
```

### 6. 密码迁移脚本 (`migrate_passwords.py`)

提供了安全的密码迁移工具：

```bash
# 备份现有密码
python migrate_passwords.py --backup

# 迁移密码到bcrypt
python migrate_passwords.py
```

**功能：**
- 自动检测已经加密的密码（以$2b$开头）
- 提供密码备份功能
- 验证迁移结果
- 支持回滚操作

## 安全特性

### 1. 密码哈希
- 使用bcrypt算法，具有自适应成本
- 每次哈希自动生成唯一盐值
- 密码格式：`$2b$12$salt22charsalt22charsalthash31chars`

### 2. 错误处理
- 统一的错误信息避免信息泄露
- 登录失败不暴露用户是否存在
- 具体错误仅在必要时返回

### 3. 密码策略
- 最小长度6位
- 支持临时密码机制
- 管理员可重置用户密码

### 4. 兼容性
- 向后兼容现有数据库结构
- 渐进式迁移，不影响现有用户
- 保持现有API接口不变

## 使用说明

### 开发环境
1. 安装依赖：`pip install -r requirements.txt`
2. 运行迁移：`python migrate_passwords.py`
3. 启动应用：`python run.py`

### 生产环境部署
1. 备份数据库
2. 备份现有密码：`python migrate_passwords.py --backup`
3. 执行密码迁移：`python migrate_passwords.py`
4. 验证登录功能
5. 部署新版本

### API使用

#### 登录接口
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

#### 重置密码
```bash
curl -X POST http://localhost:5000/api/v1/users/1/reset-password \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"new_password": "newpassword123"}'
```

#### 生成临时密码
```bash
curl -X POST http://localhost:5000/api/v1/users/1/generate-temp-password \
  -H "Authorization: Bearer <token>"
```

## 测试验证

运行测试脚本验证实现：
```bash
python test_bcrypt.py
```

## 注意事项

1. **密码迁移是不可逆的**：一旦迁移完成，无法直接恢复明文密码
2. **备份重要**：迁移前请务必备份数据库和密码
3. **测试验证**：在生产环境部署前请在测试环境充分验证
4. **用户通知**：如使用临时密码功能，请及时通知用户修改密码

## 故障排除

### 登录失败
1. 检查用户是否已迁移密码
2. 确认密码是否正确
3. 查看应用日志获取详细错误信息

### 迁移失败
1. 检查数据库连接
2. 确认用户权限
3. 查看迁移脚本输出的错误信息

### 性能问题
bcrypt的加密过程相对较慢，这是安全性的体现。如果需要优化性能，可以考虑：
1. 调整bcrypt的成本参数（当前为默认值12）
2. 使用异步处理登录请求
3. 实现登录缓存机制
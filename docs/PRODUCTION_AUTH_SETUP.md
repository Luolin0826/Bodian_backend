# 生产环境鉴权启用指南

## 当前状态分析

✅ **好消息**: 你的生产环境鉴权已经**正常工作**！

通过测试发现，访问 `http://47.101.39.246:5000/api/v1/customers` 返回：
```json
{"msg":"Missing Authorization Header"}
```

这表明JWT鉴权已经启用并正常工作。

## 系统配置确认

### 1. JWT配置已启用
- `JWT_SECRET_KEY` 已设置
- 所有API接口都有 `@jwt_required()` 装饰器保护
- Flask-JWT-Extended 正常运行

### 2. 无需鉴权的接口（正常）
以下接口不需要鉴权，这是设计上的合理选择：
- `/api/health` - 健康检查
- `/api/v1/auth/login` - 用户登录
- `/api/v1/test` - 测试接口
- `/api/v1/customers/health` - 客户模块健康检查

## 前端适配方案

### 1. 前端必须添加的功能

#### 1.1 登录流程
```javascript
// 登录API调用
async function login(username, password) {
    const response = await fetch('http://47.101.39.246:5000/api/v1/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
    });
    
    if (response.ok) {
        const data = await response.json();
        // 保存token到localStorage
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('user_info', JSON.stringify(data.user));
        return data;
    } else {
        throw new Error('登录失败');
    }
}
```

#### 1.2 Token管理
```javascript
// 获取存储的token
function getToken() {
    return localStorage.getItem('access_token');
}

// 清除token（登出时）
function clearToken() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_info');
}

// 检查token是否存在
function isLoggedIn() {
    return !!getToken();
}
```

#### 1.3 API请求拦截器
```javascript
// 为所有API请求添加Authorization头
async function apiRequest(url, options = {}) {
    const token = getToken();
    
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    // 添加Authorization头
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(url, {
        ...options,
        headers
    });
    
    // 如果token过期，跳转到登录页
    if (response.status === 401) {
        clearToken();
        window.location.href = '/login';
        return;
    }
    
    return response;
}
```

### 2. 使用示例

#### 2.1 获取客户列表
```javascript
async function getCustomers() {
    try {
        const response = await apiRequest('http://47.101.39.246:5000/api/v1/customers');
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.error('获取客户列表失败:', error);
    }
}
```

#### 2.2 创建客户
```javascript
async function createCustomer(customerData) {
    try {
        const response = await apiRequest('http://47.101.39.246:5000/api/v1/customers', {
            method: 'POST',
            body: JSON.stringify(customerData)
        });
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.error('创建客户失败:', error);
    }
}
```

### 3. 路由守卫（推荐）

```javascript
// React Router示例
import { Navigate } from 'react-router-dom';

function ProtectedRoute({ children }) {
    if (!isLoggedIn()) {
        return <Navigate to="/login" replace />;
    }
    return children;
}

// Vue Router示例
router.beforeEach((to, from, next) => {
    if (to.meta.requiresAuth && !isLoggedIn()) {
        next('/login');
    } else {
        next();
    }
});
```

### 4. Axios 配置示例（如果使用Axios）

```javascript
import axios from 'axios';

// 创建axios实例
const api = axios.create({
    baseURL: 'http://47.101.39.246:5000/api/v1'
});

// 请求拦截器 - 添加token
api.interceptors.request.use(
    config => {
        const token = getToken();
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    error => Promise.reject(error)
);

// 响应拦截器 - 处理401错误
api.interceptors.response.use(
    response => response,
    error => {
        if (error.response?.status === 401) {
            clearToken();
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);
```

## 测试鉴权是否正常

### 1. 测试未授权访问
```bash
curl -X GET "http://47.101.39.246:5000/api/v1/customers"
# 应该返回: {"msg":"Missing Authorization Header"}
```

### 2. 测试登录获取token
```bash
curl -X POST "http://47.101.39.246:5000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"ab990826"}'
```

### 3. 测试带token访问
```bash
# 使用上一步获取的token
curl -X GET "http://47.101.39.246:5000/api/v1/customers" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 常见问题解决

### 1. CORS问题
如果前端域名不在CORS允许列表中，需要更新 `app/__init__.py` 中的CORS配置：

```python
CORS(app, 
     origins=[
         "http://localhost:13686", 
         "http://your-frontend-domain.com",  # 添加你的前端域名
         # ... 其他域名
     ],
     # ... 其他配置
)
```

### 2. Token过期处理
Token默认24小时过期，前端需要：
- 监听401错误并跳转登录页
- 可选：实现token自动刷新机制

### 3. 生产环境安全建议
- 修改 `JWT_SECRET_KEY` 为强密码
- 启用HTTPS
- 设置合适的token过期时间

## 总结

🎉 **你的鉴权系统已经正常工作！** 

只需要前端添加：
1. 登录页面和登录逻辑
2. Token存储管理
3. API请求时添加Authorization头
4. 401错误处理和路由守卫

不需要修改后端代码，鉴权已经完全启用并正常工作。
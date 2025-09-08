# 用户中心API文档

## 概述

用户中心模块提供了完整的用户个人信息管理、偏好设置、通知系统和安全管理功能。所有API都需要JWT认证。

## API端点列表

### 1. 用户个人信息相关API

#### GET /api/v1/user/profile
获取用户个人信息

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "username": "admin",
    "real_name": "系统管理员",
    "email": "admin@example.com",
    "phone": "13800138000",
    "avatar": "/uploads/avatars/admin.jpg",
    "role": "super_admin",
    "role_display_name": "超级管理员",
    "department_id": 1,
    "department_name": "系统管理部",
    "employee_no": "EMP001",
    "hire_date": "2023-01-01",
    "last_login": "2024-01-15T10:30:00",
    "login_count": 156,
    "is_active": true,
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2024-01-15T10:30:00"
  }
}
```

#### PUT /api/v1/user/profile
更新用户个人信息

**请求参数:**
```json
{
  "real_name": "新的真实姓名",
  "email": "newemail@example.com",
  "phone": "13900139000",
  "avatar": "/uploads/avatars/new_avatar.jpg"
}
```

**响应示例:**
```json
{
  "code": 0,
  "message": "个人信息更新成功"
}
```

#### POST /api/v1/user/change-password
修改密码

**请求参数:**
```json
{
  "old_password": "oldpassword123",
  "new_password": "newpassword456",
  "confirm_password": "newpassword456"
}
```

**响应示例:**
```json
{
  "code": 0,
  "message": "密码修改成功"
}
```

### 2. 用户偏好设置相关API

#### GET /api/v1/user/preferences
获取用户偏好设置

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "appearance": {
      "theme_mode": "light",
      "sidebar_collapsed": false,
      "show_breadcrumb": true,
      "language": "zh-CN",
      "font_size": "medium"
    },
    "notification": {
      "system_notification": true,
      "email_notification": false,
      "sound_notification": true,
      "browser_notification": true
    },
    "security": {
      "auto_logout_time": 60,
      "session_timeout": 30,
      "enable_two_factor": false
    },
    "workspace": {
      "default_page": "/dashboard",
      "items_per_page": 20,
      "date_format": "YYYY-MM-DD",
      "time_format": "24h"
    }
  }
}
```

#### PUT /api/v1/user/preferences
更新用户偏好设置（支持部分更新）

**请求参数:**
```json
{
  "appearance": {
    "theme_mode": "dark",
    "sidebar_collapsed": true,
    "show_breadcrumb": false
  },
  "notification": {
    "system_notification": true,
    "email_notification": true
  }
}
```

**响应示例:**
```json
{
  "code": 0,
  "message": "偏好设置更新成功"
}
```

#### POST /api/v1/user/preferences/reset
重置用户偏好设置为默认值

**响应示例:**
```json
{
  "code": 0,
  "message": "偏好设置已重置为默认值"
}
```

### 3. 系统通知相关API

#### GET /api/v1/notifications
获取用户通知列表

**查询参数:**
- `page`: 页码 (默认: 1)
- `per_page`: 每页条数 (默认: 20, 最大: 100)
- `type`: 通知类型 (system/email/push/all, 默认: all)
- `status`: 状态 (read/unread/all, 默认: all)
- `start_date`: 开始日期 (YYYY-MM-DD)
- `end_date`: 结束日期 (YYYY-MM-DD)

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "notifications": [
      {
        "id": 1,
        "type": "system",
        "title": "系统维护通知",
        "content": "系统将于今晚22:00-24:00进行维护",
        "priority": "high",
        "is_read": false,
        "sender": "系统管理员",
        "created_at": "2024-01-15T10:00:00"
      }
    ],
    "total": 50,
    "unread_count": 5,
    "page": 1,
    "per_page": 20,
    "pages": 3
  }
}
```

#### GET /api/v1/notifications/unread-count
获取未读通知数量

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total_unread": 5,
    "system_unread": 3,
    "email_unread": 1,
    "push_unread": 1
  }
}
```

#### PUT /api/v1/notifications/{id}/read
标记通知为已读

**响应示例:**
```json
{
  "code": 0,
  "message": "通知已标记为已读"
}
```

#### PUT /api/v1/notifications/read-all
标记所有通知为已读

**响应示例:**
```json
{
  "code": 0,
  "message": "所有通知已标记为已读"
}
```

#### DELETE /api/v1/notifications/{id}
删除通知

**响应示例:**
```json
{
  "code": 0,
  "message": "通知已删除"
}
```

### 4. 安全设置相关API

#### GET /api/v1/user/login-logs
获取用户登录日志

**查询参数:**
- `page`: 页码 (默认: 1)
- `per_page`: 每页条数 (默认: 20, 最大: 100)
- `start_date`: 开始日期 (YYYY-MM-DD)
- `end_date`: 结束日期 (YYYY-MM-DD)

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "logs": [
      {
        "id": 1,
        "login_time": "2024-01-15T10:30:00",
        "ip_address": "192.168.1.100",
        "user_agent": "Chrome 120.0.0.0",
        "location": "北京市",
        "device_type": "Desktop",
        "status": "success",
        "logout_time": "2024-01-15T18:30:00"
      }
    ],
    "total": 100,
    "page": 1,
    "per_page": 20,
    "pages": 5,
    "current_session": {
      "session_id": "sess_12345",
      "login_time": "2024-01-15T09:00:00",
      "ip_address": "192.168.1.100",
      "expires_at": "2024-01-16T09:00:00"
    }
  }
}
```

#### POST /api/v1/user/logout-other-sessions
登出其他会话

**响应示例:**
```json
{
  "code": 0,
  "message": "其他会话已登出",
  "data": {
    "logged_out_sessions": 3
  }
}
```

#### GET /api/v1/user/security-settings
获取安全设置

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "password_strength": "medium",
    "last_password_change": "2023-12-01T00:00:00",
    "password_expires_in": 60,
    "two_factor_enabled": false,
    "security_questions_set": true,
    "failed_login_attempts": 0,
    "account_locked_until": null,
    "trusted_devices": 2,
    "login_stats": {
      "total_logins": 156,
      "failed_logins": 2,
      "success_rate": 98.7
    }
  }
}
```

#### POST /api/v1/user/enable-two-factor
启用双因素认证

**响应示例:**
```json
{
  "code": 0,
  "message": "双因素认证已启用",
  "data": {
    "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANS...",
    "secret_key": "JBSWY3DPEHPK3PXP",
    "backup_codes": ["12345678", "87654321"]
  }
}
```

#### POST /api/v1/user/disable-two-factor
禁用双因素认证

**请求参数:**
```json
{
  "password": "current_password"
}
```

**响应示例:**
```json
{
  "code": 0,
  "message": "双因素认证已禁用"
}
```

#### GET /api/v1/user/active-sessions
获取活跃会话列表

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "sessions": [
      {
        "id": 1,
        "session_id": "sess_12345",
        "ip_address": "192.168.1.100",
        "device_fingerprint": "abc123",
        "is_current": true,
        "created_at": "2024-01-15T09:00:00",
        "last_activity": "2024-01-15T10:30:00",
        "expires_at": "2024-01-16T09:00:00"
      }
    ],
    "total": 2
  }
}
```

#### DELETE /api/v1/user/sessions/{session_id}
终止指定会话

**响应示例:**
```json
{
  "code": 0,
  "message": "会话已终止"
}
```

## 数据库表结构

### user_preferences - 用户偏好设置表
```sql
CREATE TABLE user_preferences (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    
    -- 界面设置
    theme_mode VARCHAR(10) DEFAULT 'light',
    sidebar_collapsed BOOLEAN DEFAULT FALSE,
    show_breadcrumb BOOLEAN DEFAULT TRUE,
    language VARCHAR(10) DEFAULT 'zh-CN',
    font_size VARCHAR(10) DEFAULT 'medium',
    
    -- 通知设置
    system_notification BOOLEAN DEFAULT TRUE,
    email_notification BOOLEAN DEFAULT FALSE,
    sound_notification BOOLEAN DEFAULT TRUE,
    browser_notification BOOLEAN DEFAULT TRUE,
    
    -- 安全设置
    auto_logout_time INT DEFAULT 60,
    session_timeout INT DEFAULT 30,
    enable_two_factor BOOLEAN DEFAULT FALSE,
    
    -- 工作区设置
    default_page VARCHAR(255) DEFAULT '/dashboard',
    items_per_page INT DEFAULT 20,
    date_format VARCHAR(20) DEFAULT 'YYYY-MM-DD',
    time_format VARCHAR(10) DEFAULT '24h',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_preferences (user_id)
);
```

### notifications - 系统通知表
```sql
CREATE TABLE notifications (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    type VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    priority VARCHAR(10) DEFAULT 'medium',
    is_read BOOLEAN DEFAULT FALSE,
    sender VARCHAR(100),
    sender_id INT,
    
    data JSON,
    expires_at DATETIME NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_type_read (user_id, type, is_read),
    INDEX idx_created_at (created_at)
);
```

### user_login_logs - 用户登录日志表
```sql
CREATE TABLE user_login_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    session_id VARCHAR(100),
    
    login_time DATETIME NOT NULL,
    logout_time DATETIME NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    device_type VARCHAR(50),
    browser VARCHAR(50),
    os VARCHAR(50),
    location VARCHAR(100),
    
    status VARCHAR(10) NOT NULL,
    failure_reason VARCHAR(255),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_login_time (user_id, login_time)
);
```

### user_sessions - 用户会话表
```sql
CREATE TABLE user_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    
    ip_address VARCHAR(45),
    user_agent TEXT,
    device_fingerprint VARCHAR(255),
    is_current BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_expires (user_id, expires_at)
);
```

## 响应状态码说明

- `200`: 成功
- `400`: 请求参数错误
- `401`: 未认证
- `403`: 权限不足
- `404`: 资源不存在
- `500`: 服务器内部错误

## 认证说明

所有API都需要在请求头中包含JWT令牌：
```
Authorization: Bearer <jwt_token>
```

## 时区说明

所有时间字段都使用上海时区（UTC+8），格式为ISO 8601标准。

## 安全特性

1. **密码安全**: 密码使用bcrypt加密存储
2. **会话管理**: 支持多设备登录和会话管理
3. **登录日志**: 记录详细的登录历史和安全事件
4. **双因素认证**: 支持TOTP双因素认证（预留接口）
5. **设备指纹**: 基于IP和User-Agent生成设备指纹
6. **操作日志**: 所有重要操作都记录操作日志

## 使用示例

### JavaScript/Axios示例
```javascript
// 获取用户个人信息
const response = await axios.get('/api/v1/user/profile', {
  headers: { 'Authorization': `Bearer ${token}` }
});

// 更新用户偏好
await axios.put('/api/v1/user/preferences', {
  appearance: {
    theme_mode: 'dark',
    sidebar_collapsed: true
  }
}, {
  headers: { 'Authorization': `Bearer ${token}` }
});

// 获取通知列表
const notifications = await axios.get('/api/v1/notifications?status=unread', {
  headers: { 'Authorization': `Bearer ${token}` }
});
```

### Python/requests示例
```python
import requests

headers = {'Authorization': f'Bearer {token}'}

# 获取用户个人信息
response = requests.get('http://localhost:5000/api/v1/user/profile', headers=headers)

# 更新偏好设置
preferences = {
    'appearance': {
        'theme_mode': 'dark'
    }
}
requests.put('http://localhost:5000/api/v1/user/preferences', json=preferences, headers=headers)
```
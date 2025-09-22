# 角色管理接口文档

## 概述

角色管理系统提供完整的CRUD操作，支持角色的创建、查询、更新、删除以及权限管理功能。所有接口都需要JWT认证，并需要相应的权限。

**基础URL:** `/api/v1/roles`

## 接口列表

### 1. 查询角色列表

**接口:** `GET /api/v1/roles/`

**权限要求:** `menu.system.role`

**功能:** 获取系统中所有角色的列表

**请求参数:** 无

**响应示例:**
```json
[
  {
    "id": 1,
    "name": "admin",
    "display_name": "管理员",
    "description": "系统管理员角色",
    "level": 99,
    "is_system": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "permissions": {
      "menu": ["dashboard", "system"],
      "operation": {"user": ["create", "update", "delete"]},
      "data": {"scope": "all"}
    }
  }
]
```

---

### 2. 创建角色

**接口:** `POST /api/v1/roles/`

**权限要求:** `operation.role.create`

**功能:** 创建新的系统角色

**请求体:**
```json
{
  "name": "manager",
  "display_name": "经理",
  "description": "部门经理角色",
  "level": 50,
  "permissions": {
    "menu": ["dashboard", "customer"],
    "operation": {"customer": ["create", "update", "view"]}
  },
  "is_system": false
}
```

**必填字段:**
- `name` - 角色名称（英文，唯一标识）
- `display_name` - 显示名称（中文名称）
- `description` - 角色描述

**可选字段:**
- `level` - 角色级别（默认1，数值越高权限越大）
- `permissions` - 权限配置对象（默认{}）
- `is_system` - 是否为系统角色（默认false）

**响应示例:**
```json
{
  "message": "角色创建成功",
  "data": {
    "id": 5,
    "name": "manager",
    "display_name": "经理",
    "description": "部门经理角色",
    "level": 50,
    "is_system": false,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

**错误响应:**
- `400` - 角色名称已存在或缺少必填字段
- `403` - 权限不足
- `500` - 服务器内部错误

---

### 3. 更新角色信息

**接口:** `PUT /api/v1/roles/{role_name}`

**权限要求:** `operation.role.update`

**功能:** 更新角色的基本信息（不包括权限配置）

**路径参数:**
- `role_name` - 角色名称

**请求体:**
```json
{
  "name": "senior_manager",
  "display_name": "高级经理",
  "description": "高级部门经理角色",
  "level": 60
}
```

**可更新字段:**
- `name` - 角色名称（如果修改会检查是否冲突）
- `display_name` - 显示名称
- `description` - 角色描述
- `level` - 角色级别
- `is_system` - 是否为系统角色

**响应示例:**
```json
{
  "message": "角色更新成功",
  "data": {
    "id": 5,
    "name": "senior_manager",
    "display_name": "高级经理",
    "description": "高级部门经理角色",
    "level": 60,
    "is_system": false,
    "updated_at": "2024-01-15T14:20:00Z"
  }
}
```

**错误响应:**
- `404` - 角色不存在
- `403` - 系统角色不允许修改或权限不足
- `400` - 新角色名称已存在
- `500` - 服务器内部错误

---

### 4. 删除角色

**接口:** `DELETE /api/v1/roles/{role_name}`

**权限要求:** `operation.role.delete`

**功能:** 删除指定角色

**路径参数:**
- `role_name` - 角色名称

**响应示例:**
```json
{
  "message": "角色 \"manager\" 删除成功"
}
```

**错误响应:**
- `404` - 角色不存在
- `403` - 系统角色不允许删除或权限不足
- `400` - 角色正在被用户使用，无法删除
- `500` - 服务器内部错误

**安全限制:**
- 系统角色（is_system=true）不允许删除
- 如果有用户正在使用该角色，将无法删除

---

### 5. 查询角色权限

**接口:** `GET /api/v1/roles/{role_name}/permissions`

**权限要求:** `menu.system.role`

**功能:** 获取指定角色的权限配置

**路径参数:**
- `role_name` - 角色名称

**响应示例:**
```json
{
  "menu": ["dashboard", "customer", "customer.list"],
  "operation": {
    "user": ["create", "update"],
    "customer": ["create", "update", "delete", "view_detail"]
  },
  "data": {
    "scope": "department",
    "regional_permissions": ["own_region"],
    "department_permissions": ["own_department"],
    "customer_permissions": ["own_customers"],
    "data_types": ["customer_data"],
    "sensitive": ["phone", "email"]
  },
  "time": {
    "enable_login_time": false,
    "session_timeout": 240,
    "max_sessions": 2
  }
}
```

---

### 6. 更新角色权限

**接口:** `PUT /api/v1/roles/{role_name}/permissions`

**权限要求:** `operation.role.edit_permissions`

**功能:** 更新角色的权限配置

**路径参数:**
- `role_name` - 角色名称

**请求体:**
```json
{
  "permissions": {
    "menu": ["dashboard", "customer", "sales"],
    "operation": {
      "customer": ["create", "update", "view_detail"],
      "sales": ["record_create", "view_stats"]
    },
    "data": {
      "scope": "own_data",
      "customer_permissions": ["own_customers"],
      "sensitive": ["phone"]
    }
  }
}
```

**权限结构说明:**
- `menu` - 菜单访问权限数组
- `operation` - 操作权限对象，按模块分组
- `data` - 数据访问权限配置
- `time` - 时间和会话限制配置

**响应示例:**
```json
{
  "message": "角色权限更新成功",
  "updated_permissions": {
    "menu": ["dashboard", "customer", "sales"],
    "operation": {...},
    "data": {...}
  }
}
```

---

### 7. 查询角色下的用户

**接口:** `GET /api/v1/roles/{role_name}/users`

**权限要求:** `menu.system.role`

**功能:** 获取指定角色下的所有用户

**路径参数:**
- `role_name` - 角色名称

**查询参数:**
- `page` - 页码（默认1）
- `per_page` - 每页数量（默认20）

**响应示例:**
```json
{
  "users": [
    {
      "id": 10,
      "username": "manager01",
      "real_name": "张经理",
      "email": "manager01@example.com",
      "phone": "13800138001",
      "department_name": "销售部",
      "is_active": true,
      "last_login": "2024-01-15T09:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "pages": 2,
    "per_page": 20,
    "total": 25,
    "has_prev": false,
    "has_next": true
  }
}
```

---

## 辅助接口

### 8. 获取权限树结构

**接口:** `GET /api/v1/roles/permissions/tree`

**权限要求:** `menu.system.role`

**功能:** 获取完整的权限树结构，用于权限配置界面

**响应示例:**
```json
{
  "menu_tree": [
    {
      "key": "dashboard",
      "title": "工作台",
      "description": "系统主页和概览信息",
      "icon": "DashboardOutlined",
      "level": "low",
      "risk": "safe"
    },
    {
      "key": "customer",
      "title": "客户管理",
      "description": "客户信息管理和维护",
      "icon": "UserOutlined",
      "level": "medium",
      "risk": "safe",
      "children": [
        {
          "key": "customer.list",
          "title": "客户列表",
          "description": "查看和管理客户信息"
        }
      ]
    }
  ],
  "operation_tree": [...],
  "data_permissions": [...]
}
```

### 9. 获取权限模板

**接口:** `GET /api/v1/roles/templates`

**权限要求:** `menu.system.role`

**功能:** 获取预定义的权限模板

**响应示例:**
```json
[
  {
    "id": 1,
    "name": "basic_user",
    "display_name": "基础用户模板",
    "description": "适用于普通员工的基础权限",
    "permissions": {
      "menu": ["dashboard", "user-center"],
      "operation": {},
      "data": {"scope": "own_data"}
    }
  }
]
```

### 10. 导入权限配置

**接口:** `POST /api/v1/roles/{role_name}/permissions/import`

**权限要求:** `operation.role.edit_permissions`

**功能:** 从模板导入权限配置

**请求体:**
```json
{
  "template_id": 1,
  "merge_mode": "replace"
}
```

### 11. 验证权限配置

**接口:** `POST /api/v1/roles/validate-permissions`

**权限要求:** `menu.system.role`

**功能:** 验证权限配置的有效性

**请求体:**
```json
{
  "permissions": {
    "menu": ["dashboard", "invalid_menu"],
    "operation": {"user": ["invalid_operation"]}
  }
}
```

---

## 权限系统说明

### 权限级别
- `super_admin` - 超级管理员（最高权限）
- `admin` - 系统管理员
- `manager` - 部门经理
- `sales` - 销售人员
- `teacher` - 教师
- `viewer` - 查看者
- `student` - 学生
- `agent` - 代理人员

### 权限类型

1. **菜单权限 (menu)**
   - 控制用户可以访问的页面和功能模块
   - 支持层级结构（如 customer.list）

2. **操作权限 (operation)**
   - 控制用户在各模块中可以执行的操作
   - 按模块分组（user, customer, sales等）

3. **数据权限 (data)**
   - 控制用户可以访问的数据范围
   - 支持敏感数据脱敏

4. **时间权限 (time)**
   - 控制登录时间限制和会话管理

### 安全特性

- **系统角色保护**: 系统角色不允许修改或删除
- **引用检查**: 删除角色前检查是否有用户使用
- **权限验证**: 所有操作都需要相应权限
- **操作日志**: 所有角色操作都会记录日志
- **缓存管理**: 权限变更后自动清除相关缓存

### 错误码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 操作成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误或业务逻辑错误 |
| 401 | 未授权或token无效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 使用示例

### 创建一个新角色
```bash
curl -X POST /api/v1/roles/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "sales_manager",
    "display_name": "销售经理",
    "description": "销售部门经理角色",
    "level": 40,
    "permissions": {
      "menu": ["dashboard", "customer", "sales"],
      "operation": {
        "customer": ["create", "update", "view_detail"],
        "sales": ["record_create", "record_update", "view_stats"]
      }
    }
  }'
```

### 更新角色信息
```bash
curl -X PUT /api/v1/roles/sales_manager \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "高级销售经理",
    "level": 50
  }'
```

### 删除角色
```bash
curl -X DELETE /api/v1/roles/sales_manager \
  -H "Authorization: Bearer {token}"
```

---

*最后更新: 2024-01-15*
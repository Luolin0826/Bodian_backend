● 后端API接口文档

  基础信息

  - Base URL: http://dev_backend:5000/api/v1/
  - 认证方式: JWT Bearer Token
  - 响应格式: JSON

  1. 认证模块 (/api/v1/auth)

  用户登录

  - POST /api/v1/auth/login
  - 参数: {"username": "string", "password": "string"}
  - 响应: {"access_token": "string", "user": {用户信息}}

  用户登出

  - POST /api/v1/auth/logout 🔒
  - 响应: {"message": "登出成功"}

  刷新令牌

  - POST /api/v1/auth/refresh 🔒
  - 响应: {"access_token": "string"}

  获取当前用户

  - GET /api/v1/auth/me 🔒
  - 响应: 用户详细信息

  2. 客户管理 (/api/v1/customers)

  客户列表

  - GET /api/v1/customers 🔒
  - 参数: page, per_page, status, channel, keyword, subject
  - 响应: 分页的客户列表

  创建客户

  - POST /api/v1/customers 🔒
  - 参数: {"customer_date": "YYYY-MM-DD", "channel": "string", "wechat_name": "string", "phone": 
  "string", "status": "潜在", "remark": "string"}

  获取客户详情

  - GET /api/v1/customers/{id} 🔒
  - 响应: 客户详细信息

  更新客户

  - PUT /api/v1/customers/{id} 🔒
  - 参数: 客户更新字段

  删除客户

  - DELETE /api/v1/customers/{id} 🔒

  健康检查

  - GET /api/v1/customers/health
  - 响应: {"status": "healthy", "module": "customers"}

  3. 话术管理 (/api/v1/scripts)

  搜索话术

  - GET /api/v1/scripts/search
  - 参数: keyword, category, page, per_page
  - 响应: 话术搜索结果

  获取话术分类

  - GET /api/v1/scripts/categories
  - 响应: 话术分类列表

  创建话术

  - POST /api/v1/scripts 🔒
  - 参数: {"category": "string", "title": "string", "question": "string", "answer": "string", 
  "keywords": "string"}

  4. 知识库管理 (/api/v1/knowledge)

  搜索知识库

  - GET /api/v1/knowledge/search
  - 参数: keyword, type, category, page, per_page
  - 响应: 知识库搜索结果

  获取知识类型

  - GET /api/v1/knowledge/types
  - 响应: ["电网考试", "考研", "校招", "其他"]

  获取知识分类

  - GET /api/v1/knowledge/categories
  - 参数: type (可选)
  - 响应: 知识分类列表

  5. 统计分析 (/api/v1/stats)

  仪表板统计

  - GET /api/v1/stats/dashboard 🔒
  - 响应:
    - 客户统计 (总数、潜在、已成交、今日新增、本月新增)
    - 渠道分布
    - 热门话术
    - 热门知识库

  6. 部门管理 (/api/v1/departments)

  部门列表

  - GET /api/v1/departments 🔒 📋
  - 权限: menu.department.list
  - 参数: keyword, type, region, is_active, page, per_page

  部门树形结构

  - GET /api/v1/departments/tree 🔒 📋
  - 权限: menu.department.list
  - 响应: 树形结构的部门列表

  创建部门

  - POST /api/v1/departments 🔒 📋 📝
  - 权限: operation.department.create
  - 参数: {"code": "string", "name": "string", "type": "string", "parent_id": number, "region": 
  "string", "manager_id": number, "description": "string"}

  更新部门

  - PUT /api/v1/departments/{dept_id} 🔒 📋 📝
  - 权限: operation.department.edit

  删除部门

  - DELETE /api/v1/departments/{dept_id} 🔒 📋 📝 ⚠️
  - 权限: operation.department.delete

  获取部门员工

  - GET /api/v1/departments/{dept_id}/employees 🔒 📋
  - 权限: menu.department.employee

  7. 用户管理 (/api/v1/users)

  用户列表

  - GET /api/v1/users 🔒 📋 🔍
  - 权限: menu.user.list
  - 参数: keyword, department_id, role, is_active, page, per_page

  生成员工工号

  - POST /api/v1/users/generate-employee-no 🔒 📋
  - 权限: operation.user.create
  - 参数: {"department_id": number, "hire_date": "YYYY-MM-DD"}

  创建用户

  - POST /api/v1/users 🔒 📋 📝
  - 权限: operation.user.create
  - 参数: {"username": "string", "real_name": "string", "password": "string", "email": "string", 
  "phone": "string", "role": "string", "department_id": number, "hire_date": "YYYY-MM-DD"}

  更新用户

  - PUT /api/v1/users/{user_id} 🔒 📋 📝
  - 权限: operation.user.edit

  重置密码

  - POST /api/v1/users/{user_id}/reset-password 🔒 📋 📝 ⚠️
  - 权限: operation.user.reset_password
  - 参数: {"new_password": "string"}

  批量导入用户

  - POST /api/v1/users/batch-import 🔒 📋 📝 ⚠️
  - 权限: operation.user.import
  - 参数: Excel文件 (.xlsx)

  8. 角色管理 (/api/v1/roles)

  角色列表

  - GET /api/v1/roles 🔒 📋
  - 权限: menu.role.list

  获取角色权限

  - GET /api/v1/roles/{role_name}/permissions 🔒 📋
  - 权限: menu.role.permission

  更新角色权限

  - PUT /api/v1/roles/{role_name}/permissions 🔒 📋 📝 ⚠️
  - 权限: operation.role.edit_permission

  创建角色

  - POST /api/v1/roles 🔒 📋 📝
  - 权限: operation.role.create

  更新角色

  - PUT /api/v1/roles/{role_id} 🔒 📋 📝
  - 权限: operation.role.edit

  删除角色

  - DELETE /api/v1/roles/{role_id} 🔒 📋 📝 ⚠️
  - 权限: operation.role.delete

  权限配置模板

  - GET /api/v1/roles/permissions/template 🔒 📋
  - 权限: menu.role.permission

  9. 操作日志 (/api/v1/operation-logs)

  操作日志列表

  - GET /api/v1/operation-logs 🔒 📋
  - 权限: menu.log.operation
  - 参数: keyword, action, resource, department_id, user_id, date_start, date_end, sensitive_only,
  page, per_page

  操作日志详情

  - GET /api/v1/operation-logs/{log_id} 🔒 📋
  - 权限: menu.log.operation

  操作日志统计

  - GET /api/v1/operation-logs/stats 🔒 📋
  - 权限: menu.log.operation
  - 参数: days (默认7天)

  导出操作日志

  - GET /api/v1/operation-logs/export 🔒 📋
  - 权限: operation.log.export

  10. 系统接口

  健康检查

  - GET /api/health
  - 响应: {"status": "healthy", "database": "connected", "environment": "development"}

  测试接口

  - GET/POST /api/v1/test
  - 响应: {"message": "API is working", "method": "GET|POST"}

  图标说明

  - 🔒 需要JWT认证
  - 📋 需要权限验证
  - 📝 会记录操作日志
  - ⚠️ 敏感操作
  - 🔍 支持数据权限过滤

● Update Todos
  ⎿  ☒ 整理后端所有可用的API接口
     ☒ 生成API文档格式的接口列表

● 已完成后端API接口整理！总共包含10个模块，60+个接口：

  核心模块:
  - 认证模块 (4个接口)
  - 客户管理 (6个接口)
  - 话术管理 (3个接口)
  - 知识库管理 (3个接口)
  - 统计分析 (1个接口)

  系统管理模块:
  - 部门管理 (5个接口)
  - 用户管理 (6个接口)
  - 角色管理 (6个接口)
  - 操作日志 (4个接口)

  系统接口: 健康检查、测试接口

  所有接口都支持CORS，包含完整的权限控制、操作日志记录和数据权限过滤功能。
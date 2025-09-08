# 三级政策管理系统权限控制设计

## 问题分析

目前政策管理系统已解决：
✅ 四川省地市区县数据补充完整（14个地级市，53个区县）
✅ 为所有缺失的区县创建默认公司政策
✅ 新增API端点支持通过region_id更新公司政策
✅ API `/api/v1/policy-management/company-policies/by-region/{region_id}` 正常工作

需要解决的问题：
⚠️ 缺乏权限控制机制，任何用户都可以修改任何地区的政策

## 权限控制方案设计

### 1. 权限分级模型

#### 权限级别定义
```
超级管理员 (super_admin)
├── 省级管理员 (province_admin)
│   ├── 市级管理员 (city_admin) 
│   │   └── 区县管理员 (company_admin)
│   └── 直管区县管理员 (direct_company_admin)
└── 只读用户 (readonly_user)
```

#### 权限矩阵
| 角色 | 省级政策 | 市级管理 | 区县政策 | 行政区划管理 |
|------|----------|----------|----------|------------|
| 超级管理员 | 全部读写 | 全部读写 | 全部读写 | 全部读写 |
| 省级管理员 | 本省读写 | 本省读写 | 本省读写 | 本省读写 |
| 市级管理员 | 本省只读 | 本市读写 | 本市读写 | 本市读写 |
| 区县管理员 | 本省只读 | 本市只读 | 本区县读写 | 本区县只读 |
| 只读用户 | 全部只读 | 全部只读 | 全部只读 | 全部只读 |

### 2. 数据库设计扩展

#### 用户权限表扩展
```sql
-- 扩展现有users表
ALTER TABLE users ADD COLUMN permission_level ENUM('super_admin', 'province_admin', 'city_admin', 'company_admin', 'readonly_user') DEFAULT 'readonly_user';
ALTER TABLE users ADD COLUMN assigned_region_id INT NULL COMMENT '分配的管理区域ID';
ALTER TABLE users ADD CONSTRAINT fk_users_region FOREIGN KEY (assigned_region_id) REFERENCES administrative_regions(region_id);

-- 权限日志表
CREATE TABLE permission_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id INT NOT NULL,
    old_values JSON,
    new_values JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 3. API权限控制实现

#### 权限装饰器
```python
from functools import wraps
from flask_jwt_extended import get_current_user

def require_permission(required_level, resource_type='general'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user = get_current_user()
            if not current_user:
                return jsonify({'error': '需要登录'}), 401
            
            # 权限验证逻辑
            if not has_permission(current_user, required_level, resource_type, kwargs):
                return jsonify({'error': '权限不足'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def has_permission(user, required_level, resource_type, kwargs):
    """权限验证核心逻辑"""
    user_level = user.permission_level
    user_region = user.assigned_region_id
    
    # 超级管理员拥有所有权限
    if user_level == 'super_admin':
        return True
    
    # 只读用户只能查看
    if user_level == 'readonly_user':
        return resource_type == 'read'
    
    # 根据资源类型和用户级别进行权限检查
    if resource_type == 'company_policy':
        return check_company_policy_permission(user, kwargs)
    elif resource_type == 'province_policy':
        return check_province_policy_permission(user, kwargs)
    elif resource_type == 'region_management':
        return check_region_management_permission(user, kwargs)
    
    return False
```

#### 具体权限检查函数
```python
def check_company_policy_permission(user, kwargs):
    """检查公司政策操作权限"""
    region_id = kwargs.get('region_id') or kwargs.get('policy_region_id')
    
    if user.permission_level == 'province_admin':
        # 省级管理员可以管理本省所有区县
        return is_same_province(user.assigned_region_id, region_id)
    
    elif user.permission_level == 'city_admin':
        # 市级管理员只能管理本市区县
        return is_same_city(user.assigned_region_id, region_id)
    
    elif user.permission_level == 'company_admin':
        # 区县管理员只能管理自己的区县
        return user.assigned_region_id == region_id
    
    return False

def is_same_province(user_region_id, target_region_id):
    """检查是否在同一省份"""
    # 查询数据库获取省份信息进行比较
    # 实现省份层级检查逻辑
    pass

def is_same_city(user_region_id, target_region_id):
    """检查是否在同一市"""
    # 查询数据库获取城市信息进行比较
    # 实现城市层级检查逻辑
    pass
```

### 4. API路由权限应用

#### 示例：公司政策更新接口
```python
@policy_management_bp.route('/company-policies/by-region/<int:region_id>', methods=['PUT'])
@require_permission('company_admin', 'company_policy')
def update_company_policy_by_region(region_id):
    """通过region_id更新区县公司政策 - 需要权限验证"""
    try:
        policy_data = request.get_json()
        
        if not policy_data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        # 添加操作用户信息
        current_user = get_current_user()
        policy_data['updated_by'] = current_user.id
        
        result = policy_mgmt_api.update_company_policy_by_region(region_id, policy_data)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        
        # 记录操作日志
        log_permission_action(current_user.id, 'UPDATE', 'company_policy', region_id, policy_data)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"通过region_id更新公司政策失败: {e}")
        return jsonify({'error': f'通过region_id更新公司政策失败: {str(e)}'}), 500
```

### 5. 前端权限控制

#### 权限按钮显示
```javascript
// 根据用户权限动态显示操作按钮
const userPermissions = getUserPermissions();

function canEditPolicy(regionId, userRegionId, userLevel) {
    if (userLevel === 'super_admin') return true;
    if (userLevel === 'readonly_user') return false;
    
    // 根据层级关系判断权限
    return checkRegionPermission(regionId, userRegionId, userLevel);
}

// 在页面渲染时控制按钮显示
if (canEditPolicy(region.id, user.assignedRegionId, user.permissionLevel)) {
    showEditButton();
} else {
    hideEditButton();
}
```

### 6. 实施计划

#### 第一阶段：基础权限框架
1. 扩展users表添加权限字段
2. 实现权限装饰器和验证函数
3. 创建权限管理界面

#### 第二阶段：API权限应用
1. 为所有政策管理API添加权限验证
2. 实现操作日志记录
3. 测试各级权限功能

#### 第三阶段：前端权限集成
1. 前端权限状态管理
2. 动态UI权限控制
3. 权限提示和错误处理

#### 第四阶段：权限审计
1. 权限日志查询界面
2. 权限变更审计
3. 异常权限监控

### 7. 安全考虑

#### 防护措施
1. **JWT令牌验证**：所有API调用需要有效JWT
2. **权限缓存**：用户权限信息缓存，避免频繁数据库查询
3. **操作日志**：记录所有权限相关操作
4. **IP白名单**：可选的IP访问限制
5. **会话管理**：权限变更后强制重新登录

#### 数据安全
1. **敏感数据脱敏**：日志中敏感信息脱敏处理
2. **权限最小化原则**：用户只获得必要的最小权限
3. **定期权限审查**：定期检查和清理无效权限
4. **权限继承控制**：严格控制权限继承关系

## 总结

这套权限控制方案提供了：
- ✅ 分层权限管理（省/市/区县）
- ✅ 细粒度权限控制
- ✅ 操作审计日志
- ✅ 前后端一致的权限验证
- ✅ 安全防护措施

建议按阶段实施，先完成基础框架，再逐步完善功能。
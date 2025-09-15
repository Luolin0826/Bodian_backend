# 话术库项目分类功能实现

## 功能概述
为话术库增加了项目分类功能，支持按项目筛选显示话术。

### 项目分类
- **电网** - 电网相关话术（默认分类）
- **电气考研** - 电气考研相关话术
- **408** - 408考试相关话术
- **医学306** - 医学306考试相关话术
- **一建二建考证** - 一建二建考证相关话术

## 实现详情

### 1. 数据库模型更新
**文件**: `app/models/script.py:11`

```python
category = db.Column(db.Enum('电网', '电气考研', '408', '医学306', '一建二建考证'), index=True, comment='项目分类')
```

- 将原有的 `category` 字段更新为枚举类型
- 支持5个预定义的项目分类
- 添加了数据库索引提升查询性能

### 2. 数据迁移
**脚本**: `update_script_categories.py`

- 将所有现有话术的分类统一设置为"电网"
- 成功更新了186条话术记录
- 原有分类统计：
  - 课程介绍: 56条
  - 申请流程: 51条
  - 职业规划: 28条
  - 考试指导: 30条
  - 综合支持: 12条
  - 公司服务: 9条

### 3. API接口扩展

#### 3.1 新增项目分类列表接口
**端点**: `GET /api/v1/scripts/project-categories`
**文件**: `app/routes/scripts.py:1210-1268`

```json
{
  "code": 200,
  "data": [
    {
      "value": "电网",
      "label": "电网", 
      "description": "电网相关话术",
      "count": 186
    },
    {
      "value": "电气考研",
      "label": "电气考研",
      "description": "电气考研相关话术",
      "count": 0
    }
    // ... 其他分类
  ]
}
```

**功能**:
- 返回所有可用的项目分类
- 包含每个分类的话术数量统计
- 需要JWT认证

#### 3.2 现有搜索接口支持分类筛选
**端点**: `GET /api/v1/scripts/search?category=电网`
**文件**: `app/routes/scripts.py:46-47`

- 原有搜索接口已支持 `category` 参数进行筛选
- 可与其他搜索参数组合使用

## 使用方式

### 前端集成指南

1. **获取项目分类列表**
```javascript
// 获取所有项目分类
const response = await fetch('/api/v1/scripts/project-categories', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const { data: categories } = await response.json();
```

2. **按分类筛选话术**
```javascript
// 筛选特定项目的话术
const response = await fetch(`/api/v1/scripts/search?category=电网&page=1&per_page=20`, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const { data } = await response.json();
```

3. **前端UI建议**
```html
<!-- 项目分类选择器 -->
<select id="project-category" onchange="filterByCategory()">
  <option value="">全部项目</option>
  <option value="电网">电网 (186)</option>
  <option value="电气考研">电气考研 (0)</option>
  <option value="408">408 (0)</option>
  <option value="医学306">医学306 (0)</option>
  <option value="一建二建考证">一建二建考证 (0)</option>
</select>
```

## 数据库结构
```sql
-- scripts表的category字段
ALTER TABLE scripts MODIFY COLUMN category ENUM('电网','电气考研','408','医学306','一建二建考证');

-- 为category字段添加索引
CREATE INDEX idx_scripts_category ON scripts(category);
```

## 测试验证
- ✅ 数据库模型更新完成
- ✅ 现有数据迁移完成（186条记录）
- ✅ API接口功能正常
- ✅ 分类筛选功能测试通过

## 后续扩展
1. 支持动态添加新项目分类
2. 分类权限管理
3. 分类使用情况统计
4. 批量修改话术分类功能

---
*实现时间：2025-09-10*
*涉及文件：app/models/script.py, app/routes/scripts.py, update_script_categories.py*
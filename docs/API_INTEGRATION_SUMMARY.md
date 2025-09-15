# 集成化反馈管理系统 - API接口说明

## 实现完成情况 ✅

### 1. 脚本搜索修复
- **问题**: 原始 `primary_category=13` 查询返回空结果
- **解决方案**: 支持数值类型 category_id 查询，包含子分类
- **API**: `/api/v1/scripts/search` 和 `/api/v1/scripts/test-search`

### 2. 数据库迁移 ✅
- **新增字段**:
  - `province_name` VARCHAR(100) - 省份名称（文本字段）
  - `station_name_text` VARCHAR(200) - 站点名称（文本字段）
  - `recruitment_requirements` TEXT - 招聘要求
  - `announcement_url` VARCHAR(500) - 公告链接
- **数据迁移**: 已自动填充现有数据（3条记录）

### 3. 集成化反馈管理接口 ✅

#### 3.1 获取集成化反馈列表
- **接口**: `GET /api/v1/advance-batch/feedback/integrated`
- **参数**: 
  - `page`: 页码（默认1）
  - `size`: 每页数量（默认20，最大100）
  - `province`: 省份过滤（可选）
- **返回**: 包含省份名称、站点名称、招聘要求、公告链接等完整信息
- **时间字段**: 
  - `created_at`: 创建时间（ISO格式）
  - `updated_at`: 更新时间（ISO格式）

#### 3.2 创建反馈（管理员）
- **接口**: `POST /api/v1/advance-batch/admin/feedback`
- **权限**: 需要管理员权限
- **输入参数**:
```json
{
  "feedback_type": "经验分享",
  "title": "反馈标题",
  "content": "反馈内容",
  "province_name": "省份名称",
  "station_name_text": "站点名称", 
  "recruitment_requirements": "招聘要求",
  "announcement_url": "公告链接",
  "author": "作者",
  "author_background": "作者背景"
}
```

#### 3.3 更新反馈（管理员）
- **接口**: `PUT /api/v1/advance-batch/admin/feedback/{feedback_id}`
- **权限**: 需要管理员权限
- **输入**: 支持部分字段更新

### 4. 省份管理接口 ✅

#### 4.1 创建省份（管理员）
- **接口**: `POST /api/v1/advance-batch/admin/provinces`
- **权限**: 需要管理员权限
- **输入参数**:
```json
{
  "province": "省份名称",
  "batch_id": 1,
  "secondary_unit_name": "二级单位名称",
  "recruitment_count": 10,
  "other_requirements": "其他要求",
  "notice_url": "公告链接"
}
```

#### 4.2 更新省份（管理员）
- **接口**: `PUT /api/v1/advance-batch/admin/provinces/{province_id}`
- **权限**: 需要管理员权限

#### 4.3 删除省份（管理员）
- **接口**: `DELETE /api/v1/advance-batch/admin/provinces/{province_id}`
- **权限**: 需要管理员权限

#### 4.4 省份列表
- **接口**: `GET /api/v1/advance-batch/provinces/list`
- **返回**: 所有可用省份名称列表

#### 4.5 省份详细信息
- **接口**: `GET /api/v1/advance-batch/provinces`
- **参数**: 
  - `batch_id`: 批次ID（可选）
  - `province`: 省份名称（可选）
- **返回**: 包含完整省份信息，含详细时间字段
- **时间字段**:
  - `created_at`: 创建时间（ISO格式）
  - `updated_at`: 更新时间（ISO格式）

### 5. 站点管理接口 ✅

#### 5.1 站点管理列表
- **接口**: `GET /api/v1/advance-batch/stations/management`
- **参数**:
  - `page`: 页码
  - `size`: 每页数量
  - `province`: 省份过滤
- **返回**: 包含省份信息的简化站点列表
- **时间字段**: 
  - `created_at`: 创建时间（ISO格式）
  - `updated_at`: 更新时间（ISO格式）

#### 5.2 站点详细信息
- **接口**: `GET /api/v1/advance-batch/stations`
- **参数**:
  - `province_plan_id`: 省份计划ID
  - `province`: 省份名称
  - `university_name`: 大学名称
- **返回**: 包含完整站点信息，含详细时间字段
- **时间字段**:
  - `created_at`: 创建时间（ISO格式）
  - `updated_at`: 更新时间（ISO格式）

### 6. 现有接口增强 ✅

#### 6.1 反馈管理列表
- **接口**: `GET /api/v1/advance-batch/feedback/management`
- **增强**: 现在包含省份名称等集成化字段信息

## 技术架构

### 数据模型增强
- `StudentFeedbackTemplates` 模型新增4个集成化管理字段
- 支持both关联查询和文本存储，提高查询效率
- 数据迁移脚本自动填充历史数据

### 服务层方法
- `create_feedback_with_auto_province()` - 支持自动省份创建
- `update_feedback_integrated()` - 集成化更新
- `create_province_standalone()` - 独立省份创建
- `update_province_info()` - 省份信息更新
- `delete_province_info()` - 省份删除（软删除）

### 权限控制
- 管理员权限检查：`check_admin_permission()`
- 支持JWT Token验证
- 创建/更新/删除操作需要管理员权限

## 测试结果 ✅

1. **脚本搜索修复**: `primary_category=13` 现在返回46条结果
2. **集成化反馈API**: 成功返回3条记录，包含完整集成化字段
3. **省份列表API**: 返回3个省份（上海、北京、江苏）
4. **站点管理API**: 返回3个站点，包含省份信息
5. **权限控制**: 未授权请求正确返回403错误

## API使用示例

### 获取集成化反馈列表
```bash
curl -X GET "http://localhost:5000/api/v1/advance-batch/feedback/integrated?page=1&size=5"
```

### 获取省份列表
```bash
curl -X GET "http://localhost:5000/api/v1/advance-batch/provinces/list"
```

### 获取站点管理列表
```bash
curl -X GET "http://localhost:5000/api/v1/advance-batch/stations/management?page=1&size=3"
```

### 修复后的脚本搜索
```bash
curl -X GET "http://localhost:5000/api/v1/scripts/test-search?primary_category=13&page=1&per_page=3"
```

## 前端集成要点

1. **省份选择**: 使用 `/provinces/list` 获取省份选项
2. **站点管理**: 使用 `/stations/management` 进行站点管理
3. **反馈管理**: 使用 `/feedback/integrated` 进行集成化反馈管理
4. **文本输入**: 支持直接输入省份名称、站点名称等，无需先创建关联记录
5. **权限管理**: 管理员功能需要JWT Token认证

## 性能优化

1. **索引创建**: 为 province_name、created_at、is_featured 字段创建索引
2. **分页查询**: 所有列表接口支持分页，限制单页最大数量
3. **字段过滤**: 返回数据根据需要提供简化版本和完整版本
4. **缓存友好**: 接口设计支持后续添加缓存层
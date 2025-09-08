# 客户跟进管理API文档

## 概述

客户跟进管理模块提供了完整的客户跟进记录管理、跟进提醒、批量操作和统计分析功能。所有API都需要JWT认证。

## 数据模型

### 跟进记录 (FollowUpRecord)
```typescript
interface FollowUpRecord {
  id: number
  customer_id: number           // 关联客户ID
  follow_up_type: string        // 跟进方式: 'phone' | 'wechat' | 'meeting' | 'email' | 'other'
  follow_up_content: string     // 跟进内容
  next_follow_date?: string     // 下次跟进日期 (YYYY-MM-DD)
  result?: string               // 跟进结果: 'interested' | 'not_interested' | 'no_answer' | 'deal' | 'reschedule' | 'other'
  status_before?: string        // 跟进前状态: '潜在' | '跟进中' | '已成交' | '已流失'
  status_after?: string         // 跟进后状态: '潜在' | '跟进中' | '已成交' | '已流失'
  created_by?: number           // 跟进人ID
  created_at: string            // 创建时间
  updated_at: string            // 更新时间
  creator_name?: string         // 跟进人姓名（详细查询时返回）
  customer_name?: string        // 客户名称（详细查询时返回）
}
```

### 跟进提醒 (FollowUpReminder)
```typescript
interface FollowUpReminder {
  id: number
  customer_id: number
  remind_date: string           // 提醒日期 (YYYY-MM-DD)
  remind_content: string        // 提醒内容
  priority: string              // 优先级: 'low' | 'medium' | 'high' | 'urgent'
  is_completed: boolean         // 是否已完成
  completed_at?: string         // 完成时间
  completed_by?: number         // 完成人ID
  follow_up_record_id?: number  // 关联的跟进记录ID
  created_by: number            // 创建人ID
  created_at: string            // 创建时间
  updated_at: string            // 更新时间
  creator_name?: string         // 创建人姓名（详细查询时返回）
  completer_name?: string       // 完成人姓名（详细查询时返回）
  customer_name?: string        // 客户名称（详细查询时返回）
  customer_phone?: string       // 客户电话（详细查询时返回）
  customer_status?: string      // 客户状态（详细查询时返回）
}
```

## API端点列表

### 1. 跟进记录相关API

#### GET /api/v1/customers/{customer_id}/follow-ups
获取客户跟进记录列表

**查询参数:**
- `page`: 页码 (默认: 1)
- `per_page`: 每页记录数 (默认: 20)
- `follow_up_type`: 跟进方式筛选
- `date_from`: 开始日期 (YYYY-MM-DD)
- `date_to`: 结束日期 (YYYY-MM-DD)
- `result`: 跟进结果筛选

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "records": [
      {
        "id": 1,
        "customer_id": 123,
        "follow_up_type": "phone",
        "follow_up_content": "客户表示对产品有兴趣，约定下周详谈",
        "next_follow_date": "2024-01-20",
        "result": "interested",
        "status_before": "潜在",
        "status_after": "跟进中",
        "created_by": 1,
        "created_at": "2024-01-15T10:30:00",
        "updated_at": "2024-01-15T10:30:00",
        "creator_name": "张三",
        "customer_name": "李四"
      }
    ],
    "total": 25,
    "page": 1,
    "per_page": 20,
    "pages": 2,
    "customer": {
      "id": 123,
      "wechat_name": "李四",
      "phone": "13800138000",
      "status": "跟进中"
    }
  }
}
```

#### POST /api/v1/customers/{customer_id}/follow-ups
创建跟进记录

**请求参数:**
```json
{
  "follow_up_type": "phone",
  "follow_up_content": "客户表示对产品有兴趣，约定下周详谈",
  "next_follow_date": "2024-01-20",
  "result": "interested",
  "status_after": "跟进中"
}
```

**响应示例:**
```json
{
  "code": 0,
  "message": "跟进记录创建成功",
  "data": {
    "id": 1,
    "customer_id": 123,
    "follow_up_type": "phone",
    "follow_up_content": "客户表示对产品有兴趣，约定下周详谈",
    "next_follow_date": "2024-01-20",
    "result": "interested",
    "status_before": "潜在",
    "status_after": "跟进中",
    "created_by": 1,
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00",
    "creator_name": "张三",
    "customer_name": "李四"
  }
}
```

#### PUT /api/v1/follow-ups/{id}
更新跟进记录

**请求参数:**
```json
{
  "follow_up_type": "wechat",
  "follow_up_content": "通过微信发送了产品资料",
  "next_follow_date": "2024-01-22",
  "result": "interested"
}
```

#### DELETE /api/v1/follow-ups/{id}
删除跟进记录

**响应示例:**
```json
{
  "code": 0,
  "message": "跟进记录删除成功"
}
```

#### GET /api/v1/follow-ups/statistics
获取跟进统计数据

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "today_count": 5,
    "week_count": 15,
    "month_count": 48,
    "conversion_rate": 15.5,
    "total_customers": 31,
    "deal_customers": 5,
    "type_statistics": [
      {"type": "phone", "count": 25},
      {"type": "wechat", "count": 15},
      {"type": "meeting", "count": 8}
    ],
    "result_statistics": [
      {"result": "interested", "count": 20},
      {"result": "not_interested", "count": 10},
      {"result": "deal", "count": 5},
      {"result": "no_answer", "count": 13}
    ]
  }
}
```

#### GET /api/v1/follow-ups
获取所有跟进记录（支持分页和筛选）

**查询参数:**
- `page`: 页码 (默认: 1)
- `per_page`: 每页记录数 (默认: 20)
- `follow_up_type`: 跟进方式筛选
- `result`: 跟进结果筛选
- `date_from`: 开始日期 (YYYY-MM-DD)
- `date_to`: 结束日期 (YYYY-MM-DD)
- `customer_name`: 客户名称筛选
- `created_by`: 创建人ID筛选

### 2. 跟进提醒相关API

#### GET /api/v1/follow-up-reminders
获取跟进提醒列表

**查询参数:**
- `page`: 页码 (默认: 1)
- `per_page`: 每页记录数 (默认: 20)
- `date`: 提醒日期 (YYYY-MM-DD)
- `is_completed`: 是否已完成 (true/false)
- `customer_id`: 客户ID
- `priority`: 优先级筛选
- `customer_name`: 客户名称筛选

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "reminders": [
      {
        "id": 1,
        "customer_id": 123,
        "remind_date": "2024-01-20",
        "remind_content": "跟进李四客户产品需求",
        "priority": "high",
        "is_completed": false,
        "completed_at": null,
        "completed_by": null,
        "follow_up_record_id": 5,
        "created_by": 1,
        "created_at": "2024-01-15T10:30:00",
        "updated_at": "2024-01-15T10:30:00",
        "creator_name": "张三",
        "customer_name": "李四",
        "customer_phone": "13800138000",
        "customer_status": "跟进中"
      }
    ],
    "total": 10,
    "page": 1,
    "per_page": 20,
    "pages": 1
  }
}
```

#### POST /api/v1/follow-up-reminders
创建跟进提醒

**请求参数:**
```json
{
  "customer_id": 123,
  "remind_date": "2024-01-20",
  "remind_content": "跟进李四客户产品需求",
  "priority": "high",
  "follow_up_record_id": 5
}
```

#### PUT /api/v1/follow-up-reminders/{id}
更新跟进提醒

**请求参数:**
```json
{
  "remind_date": "2024-01-22",
  "remind_content": "跟进李四客户产品需求（已延期）",
  "priority": "urgent"
}
```

#### PUT /api/v1/follow-up-reminders/{id}/complete
标记提醒为已完成

**响应示例:**
```json
{
  "code": 0,
  "message": "提醒已标记为完成",
  "data": {
    "id": 1,
    "customer_id": 123,
    "remind_date": "2024-01-20",
    "remind_content": "跟进李四客户产品需求",
    "priority": "high",
    "is_completed": true,
    "completed_at": "2024-01-20T14:30:00",
    "completed_by": 1,
    "follow_up_record_id": 5,
    "created_by": 1,
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-20T14:30:00"
  }
}
```

#### PUT /api/v1/follow-up-reminders/{id}/reopen
重新打开已完成的提醒

#### DELETE /api/v1/follow-up-reminders/{id}
删除跟进提醒

#### GET /api/v1/follow-up-reminders/today
获取今日提醒

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "today_reminders": [
      {
        "id": 1,
        "customer_id": 123,
        "remind_date": "2024-01-20",
        "remind_content": "跟进李四客户产品需求",
        "priority": "high",
        "is_completed": false,
        "customer_name": "李四",
        "customer_phone": "13800138000",
        "customer_status": "跟进中"
      }
    ],
    "overdue_reminders": [
      {
        "id": 2,
        "customer_id": 124,
        "remind_date": "2024-01-18",
        "remind_content": "跟进王五客户合作意向",
        "priority": "medium",
        "is_completed": false,
        "customer_name": "王五",
        "customer_phone": "13800138001",
        "customer_status": "潜在"
      }
    ],
    "total_count": 2
  }
}
```

#### GET /api/v1/follow-up-reminders/statistics
获取提醒统计数据

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "today_count": 3,
    "overdue_count": 2,
    "total_pending": 8,
    "completed_this_month": 15,
    "priority_statistics": [
      {"priority": "urgent", "count": 2},
      {"priority": "high", "count": 3},
      {"priority": "medium", "count": 2},
      {"priority": "low", "count": 1}
    ]
  }
}
```

### 3. 增强的客户相关API

#### GET /api/v1/customers/{id}/detail
获取客户详情（包含跟进记录）

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "customer": {
      "id": 123,
      "wechat_name": "李四",
      "phone": "13800138000",
      "status": "跟进中",
      "channel": "朋友圈",
      "add_date": "2024-01-10",
      "created_at": "2024-01-10T09:00:00"
    },
    "recent_follow_ups": [
      {
        "id": 1,
        "follow_up_type": "phone",
        "follow_up_content": "客户表示对产品有兴趣",
        "result": "interested",
        "created_at": "2024-01-15T10:30:00",
        "creator_name": "张三"
      }
    ],
    "pending_reminders": [
      {
        "id": 1,
        "remind_date": "2024-01-20",
        "remind_content": "跟进李四客户产品需求",
        "priority": "high",
        "creator_name": "张三"
      }
    ],
    "follow_up_stats": {
      "total_count": 5,
      "last_follow_date": "2024-01-15T10:30:00",
      "next_follow_date": "2024-01-20"
    }
  }
}
```

#### POST /api/v1/customers/batch-follow-up
批量更新客户跟进状态

**请求参数:**
```json
{
  "customer_ids": [123, 124, 125],
  "follow_up_data": {
    "follow_up_type": "phone",
    "follow_up_content": "电话确认客户需求",
    "result": "interested",
    "next_follow_date": "2024-01-25",
    "status_after": "跟进中"
  }
}
```

**响应示例:**
```json
{
  "code": 0,
  "message": "批量跟进成功，共处理3个客户",
  "data": {
    "success_count": 3,
    "total_count": 3
  }
}
```

#### GET /api/v1/customers/need-follow-up
获取需要跟进的客户列表

**查询参数:**
- `page`: 页码 (默认: 1)
- `per_page`: 每页记录数 (默认: 20)
- `urgency_level`: 紧急程度 ('urgent' | 'high' | 'medium' | 'low')
- `days_since_last_contact`: 距离上次联系天数 (默认: 7)
- `status`: 客户状态筛选 ('潜在' | '跟进中')

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "customers": [
      {
        "id": 123,
        "wechat_name": "李四",
        "phone": "13800138000",
        "status": "跟进中",
        "channel": "朋友圈",
        "last_follow_up_date": "2024-01-10T10:30:00",
        "days_since_last_follow_up": 5,
        "urgency": "medium"
      },
      {
        "id": 124,
        "wechat_name": "王五",
        "phone": "13800138001",
        "status": "潜在",
        "channel": "广告",
        "last_follow_up_date": null,
        "days_since_last_follow_up": 15,
        "urgency": "urgent"
      }
    ],
    "total": 25,
    "page": 1,
    "per_page": 20,
    "pages": 2
  }
}
```

#### GET /api/v1/customers/{id}/timeline
获取客户跟进时间线

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "customer": {
      "id": 123,
      "wechat_name": "李四",
      "phone": "13800138000",
      "status": "跟进中"
    },
    "timeline": [
      {
        "type": "follow_up",
        "id": 1,
        "date": "2024-01-15T10:30:00",
        "title": "phone 跟进",
        "content": "客户表示对产品有兴趣，约定下周详谈",
        "result": "interested",
        "status_change": {
          "before": "潜在",
          "after": "跟进中"
        },
        "next_follow_date": "2024-01-20",
        "creator_name": "张三"
      },
      {
        "type": "reminder",
        "id": 1,
        "date": "2024-01-15T10:35:00",
        "remind_date": "2024-01-20",
        "title": "跟进提醒 - high",
        "content": "跟进李四客户产品需求",
        "is_completed": false,
        "completed_at": null,
        "creator_name": "张三"
      }
    ],
    "total_items": 2
  }
}
```

## 错误代码说明

- `400`: 请求参数错误
- `401`: 未认证或JWT令牌无效
- `403`: 无权限访问（只能操作自己创建的记录）
- `404`: 资源不存在
- `500`: 服务器内部错误

## 使用说明

### 1. 认证
所有API都需要在请求头中包含JWT令牌：
```http
Authorization: Bearer <your_jwt_token>
```

### 2. 日期格式
所有日期字段使用ISO 8601格式：
- 日期: `YYYY-MM-DD`
- 日期时间: `YYYY-MM-DDTHH:MM:SS`

### 3. 权限控制
- 用户只能查看、修改和删除自己创建的跟进记录和提醒
- 批量操作只能操作有权限的客户

### 4. 状态流转
客户状态变更会自动记录在跟进记录中：
- `status_before`: 跟进前的客户状态
- `status_after`: 跟进后的客户状态（如有变更）

### 5. 统计数据
- 跟进统计基于当前用户的数据
- 转化率 = 成交客户数 / 跟进客户数
- 紧急程度基于距离上次跟进的天数自动计算

## 集成建议

### 前端页面改进
1. **客户管理页面**:
   - 添加"查看跟进记录"按钮
   - 显示最后跟进时间和下次跟进日期
   - 支持批量跟进操作

2. **跟进管理页面**:
   - 展示完整的跟进历史时间线
   - 支持创建和管理跟进提醒
   - 添加跟进统计图表

3. **仪表板**:
   - 显示今日待跟进客户数量
   - 显示逾期提醒数量
   - 展示跟进转化率趋势

### 工作流程优化
1. 创建跟进记录时自动创建下次跟进提醒
2. 客户状态变更时自动记录跟进历史
3. 支持跟进模板，提高录入效率
4. 定期生成跟进效果分析报告
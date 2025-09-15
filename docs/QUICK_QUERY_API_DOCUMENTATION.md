# 数查一点通快捷查询API接口文档

## 概述

快捷查询功能提供本科信息、硕士信息、录取统计数据的查询服务，支持按省份、学历层次等条件进行筛选查询。

**基础URL**: `/api/v1/quick-query`

## 认证

部分接口需要JWT认证，在请求头中添加：
```
Authorization: Bearer <your_jwt_token>
```

## 通用响应格式

### 成功响应
```json
{
  "success": true,
  "data": <数据内容>,
  "message": "操作成功",
  "pagination": {  // 分页接口才有
    "page": 1,
    "limit": 20,
    "total": 100,
    "pages": 5
  }
}
```

### 错误响应
```json
{
  "success": false,
  "error": "错误信息",
  "message": "详细错误描述"
}
```

## API接口列表

### 1. 本科信息查询

#### GET /undergraduate
查询本科招聘信息列表

**请求参数**:
- `province` (string, 可选): 省份名称筛选
- `page` (int, 可选): 页码，默认1
- `limit` (int, 可选): 每页数量，默认20，最大100

**请求示例**:
```bash
GET /api/v1/quick-query/undergraduate?page=1&limit=10
GET /api/v1/quick-query/undergraduate?province=山东&limit=5
```

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "province": "山东",
      "org_type": "国网省公司",
      "undergraduate_english": "四六级",
      "undergraduate_computer": "二级明确要求",
      "undergraduate_qualification": "应届毕业生",
      "undergraduate_age": "35岁以下",
      "scores": {
        "2025_batch1": "57分",
        "2025_batch2": "55分",
        "2024_batch1": "56分",
        "2024_batch2": "54分",
        "2023_batch1": "55分",
        "2023_batch2": "53分"
      },
      "updated_at": "2025-09-13T07:36:24"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 25,
    "pages": 3
  }
}
```

#### GET /undergraduate/:province
查询指定省份的本科信息

**路径参数**:
- `province` (string): 省份名称

**请求示例**:
```bash
GET /api/v1/quick-query/undergraduate/山东
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "province": "山东", 
    "org_type": "国网省公司",
    "undergraduate_english": "四六级",
    "undergraduate_computer": "二级明确要求",
    "undergraduate_qualification": "应届毕业生",
    "undergraduate_age": "35岁以下",
    "scores": {
      "2025_batch1": "57分",
      "2025_batch2": "55分",
      "2024_batch1": "56分", 
      "2024_batch2": "54分",
      "2023_batch1": "55分",
      "2023_batch2": "53分"
    },
    "updated_at": "2025-09-13T07:36:24"
  }
}
```

### 2. 硕士信息查询

#### GET /graduate
查询硕士招聘信息列表

**请求参数**:
- `province` (string, 可选): 省份名称筛选
- `page` (int, 可选): 页码，默认1
- `limit` (int, 可选): 每页数量，默认20，最大100

**请求示例**:
```bash
GET /api/v1/quick-query/graduate?page=1&limit=10
GET /api/v1/quick-query/graduate?province=江苏
```

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "province": "江苏",
      "org_type": "国网省公司", 
      "graduate_english": "六级",
      "graduate_computer": "二级（国家或省级）明确要求",
      "graduate_qualification": "应届毕业生优先",
      "graduate_age": "35岁以下",
      "scores": {
        "2025_batch1": "65分",
        "2025_batch2": "63分",
        "2024_batch1": "64分",
        "2024_batch2": "62分", 
        "2023_batch1": "63分",
        "2023_batch2": "61分"
      },
      "updated_at": "2025-09-13T07:36:24"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 25,
    "pages": 3
  }
}
```

#### GET /graduate/:province
查询指定省份的硕士信息

**路径参数**:
- `province` (string): 省份名称

**请求示例**:
```bash
GET /api/v1/quick-query/graduate/江苏
```

**响应格式**: 同上，返回单个省份的硕士信息

### 3. 录取统计查询

#### GET /admission-stats
查询录取人数统计信息

**请求参数**:
- `province` (string, 可选): 省份名称筛选
- `year` (string, 可选): 年份筛选 (2023/2024/2025)
- `batch` (string, 可选): 批次筛选 (batch1/batch2)
- `page` (int, 可选): 页码，默认1
- `limit` (int, 可选): 每页数量，默认20，最大100

**请求示例**:
```bash
GET /api/v1/quick-query/admission-stats
GET /api/v1/quick-query/admission-stats?year=2025&batch=batch1
GET /api/v1/quick-query/admission-stats?province=北京
```

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "province": "山东",
      "org_type": "国网省公司",
      "admission_stats": {
        "2025": {
          "batch1": 1283,
          "batch2": 856
        },
        "2024": {
          "batch1": 1245,
          "batch2": 820
        },
        "2023": {
          "batch1": 1198,
          "batch2": 795
        }
      },
      "updated_at": "2025-09-13T07:36:24"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 25,
    "pages": 2
  }
}
```

#### GET /admission-stats/:province
查询指定省份的录取统计

**路径参数**:
- `province` (string): 省份名称

**响应格式**: 同上，返回单个省份的录取统计信息

### 4. 综合信息查询

#### GET /complete
查询所有省份的完整信息（本科+硕士+统计）

**请求参数**:
- `page` (int, 可选): 页码，默认1
- `limit` (int, 可选): 每页数量，默认20，最大100

**请求示例**:
```bash
GET /api/v1/quick-query/complete?page=1&limit=5
```

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "province": "山东",
      "org_type": "国网省公司",
      "undergraduate": {
        "english": "四六级",
        "computer": "二级明确要求",
        "qualification": "应届毕业生",
        "age": "35岁以下",
        "scores": {
          "2025_batch1": "57分",
          "2025_batch2": "55分",
          "2024_batch1": "56分",
          "2024_batch2": "54分",
          "2023_batch1": "55分",
          "2023_batch2": "53分"
        }
      },
      "graduate": {
        "english": "四六级",
        "computer": "二级明确要求",
        "qualification": "应届毕业生优先",
        "age": "35岁以下", 
        "scores": {
          "2025_batch1": "65分",
          "2025_batch2": "63分",
          "2024_batch1": "64分",
          "2024_batch2": "62分",
          "2023_batch1": "63分",
          "2023_batch2": "61分"
        }
      },
      "admission_stats": {
        "2025": {"batch1": 1283, "batch2": 856},
        "2024": {"batch1": 1245, "batch2": 820},
        "2023": {"batch1": 1198, "batch2": 795}
      },
      "updated_at": "2025-09-13T07:36:24"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 5,
    "total": 25,
    "pages": 5
  }
}
```

#### GET /complete/:province
查询指定省份的完整信息

**路径参数**:
- `province` (string): 省份名称

**请求示例**:
```bash
GET /api/v1/quick-query/complete/山东
```

**响应格式**: 同上，返回单个省份的完整信息

### 5. 省份管理

#### GET /provinces
获取所有省份列表

**请求示例**:
```bash
GET /api/v1/quick-query/provinces
```

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "unit_id": 1,
      "unit_name": "广东",
      "org_type": "南网省公司",
      "has_data": true,
      "updated_at": "2025-09-13T07:36:24"
    },
    {
      "unit_id": 3,
      "unit_name": "山东", 
      "org_type": "国网省公司",
      "has_data": true,
      "updated_at": "2025-09-13T07:36:24"
    }
  ]
}
```

#### GET /provinces/with-data
获取有快捷查询数据的省份列表

**请求示例**:
```bash
GET /api/v1/quick-query/provinces/with-data
```

**响应格式**: 同上，只返回有快捷查询数据的省份

### 6. 数据管理接口 (需要认证)

#### POST /data
创建新的快捷查询记录

**请求体**:
```json
{
  "unit_id": 1,
  "undergraduate_english": "四六级",
  "undergraduate_computer": "二级明确要求",
  "undergraduate_qualification": "应届毕业生",
  "undergraduate_age": "35岁以下",
  "undergrad_2025_batch1_score": "57分",
  "graduate_english": "四六级", 
  "admission_2025_batch1_count": 1283
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 28,
    "unit_id": 1,
    "created_at": "2025-09-13T07:45:00"
  },
  "message": "快捷查询记录创建成功"
}
```

#### PUT /data/:id
更新快捷查询记录

**路径参数**:
- `id` (int): 记录ID

**请求体**: 同创建接口，包含要更新的字段

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "updated_at": "2025-09-13T07:45:00"
  },
  "message": "快捷查询记录更新成功"
}
```

#### DELETE /data/:id
删除快捷查询记录

**路径参数**:
- `id` (int): 记录ID

**响应示例**:
```json
{
  "success": true,
  "message": "快捷查询记录删除成功"
}
```

#### GET /data/:id
获取单条快捷查询记录详情

**路径参数**:
- `id` (int): 记录ID

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "unit_id": 3,
    "province": "山东",
    "org_type": "国网省公司",
    "undergraduate_english": "四六级",
    "undergraduate_computer": "二级明确要求",
    // ... 其他字段
    "created_at": "2025-09-13T07:36:24",
    "updated_at": "2025-09-13T07:36:24"
  }
}
```

### 7. 批量操作接口 (需要认证)

#### POST /data/batch
批量创建快捷查询记录

**请求体**:
```json
{
  "items": [
    {
      "unit_id": 1,
      "undergraduate_english": "四六级",
      "graduate_english": "六级",
      "admission_2025_batch1_count": 1000
    },
    {
      "unit_id": 2,
      "undergraduate_english": "四级",
      "graduate_english": "四级",
      "admission_2025_batch1_count": 800
    }
  ]
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "created_count": 2,
    "created_ids": [29, 30]
  },
  "message": "批量创建成功"
}
```

#### PUT /data/batch
批量更新快捷查询记录

**请求体**:
```json
{
  "updates": [
    {
      "id": 1,
      "fields": {
        "undergraduate_english": "四级",
        "undergrad_2025_batch1_score": "65分"
      }
    },
    {
      "id": 2,
      "fields": {
        "graduate_english": "六级优先",
        "admission_2025_batch1_count": 150
      }
    }
  ]
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "updated_count": 2,
    "updated_ids": [1, 2]
  },
  "message": "批量更新成功"
}
```

#### DELETE /data/batch
批量删除快捷查询记录

**请求体**:
```json
{
  "ids": [1, 2, 3, 5, 8]
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "deleted_count": 5,
    "deleted_ids": [1, 2, 3, 5, 8]
  },
  "message": "批量删除成功"
}
```

### 8. 数据导入导出接口 (需要认证)

#### POST /import/excel
Excel文件批量导入

**请求**: Form-data格式
- `file`: Excel文件
- `sheet_name` (可选): 工作表名称，默认"Sheet1"

**响应示例**:
```json
{
  "success": true,
  "data": {
    "imported_count": 25,
    "failed_count": 2,
    "errors": [
      "第5行: 省份名称为空",
      "第10行: 找不到对应的unit_id"
    ]
  },
  "message": "Excel导入完成"
}
```

#### GET /export/excel
导出快捷查询数据为Excel

**请求参数**:
- `province` (string, 可选): 省份筛选
- `format` (string, 可选): 导出格式，默认"complete"

**响应**: Excel文件下载

#### GET /template/excel
下载Excel导入模板

**响应**: Excel模板文件下载

## 数据字段说明

### 省份组织类型
- `国网省公司`: 国家电网省级公司
- `国网直属单位`: 国家电网直属单位 
- `南网省公司`: 南方电网省级公司
- `南网直属单位`: 南方电网直属单位

### 分数线字段格式
- 一般为"XX分"格式，如"65分"
- 特殊情况可能包含详细说明，如"电工类本科生 48 分（985、211 / 原电力部属院校电工类本科 44 分）"

### 录取人数字段
- 整数类型，表示具体录取人数
- null表示暂无数据

## 错误码说明

- `400`: 请求参数错误
- `401`: 未授权访问  
- `403`: 权限不足
- `404`: 资源不存在
- `500`: 服务器内部错误

## 注意事项

1. 所有时间字段采用ISO 8601格式 (YYYY-MM-DDTHH:mm:ss)
2. 分页查询最大限制为100条/页
3. 省份名称需要与数据库中的`unit_name`完全匹配
4. 数据管理接口需要管理员权限
5. 文件上传限制：Excel文件最大10MB

## 使用示例

### JavaScript调用示例
```javascript
// 查询山东省本科信息
const response = await fetch('/api/v1/quick-query/undergraduate/山东');
const data = await response.json();

// 分页查询硕士信息
const response = await fetch('/api/v1/quick-query/graduate?page=1&limit=10');
const data = await response.json();

// 查询省份列表
const response = await fetch('/api/v1/quick-query/provinces');
const provinces = await response.json();
```

### Python调用示例
```python
import requests

# 查询本科信息
response = requests.get('http://localhost:5000/api/v1/quick-query/undergraduate', 
                       params={'province': '江苏', 'limit': 5})
data = response.json()

# 创建新记录 (需要认证)
headers = {'Authorization': 'Bearer your_jwt_token'}
payload = {
    'unit_id': 1,
    'undergraduate_english': '四六级',
    'admission_2025_batch1_count': 1000
}
response = requests.post('http://localhost:5000/api/v1/quick-query/data', 
                        json=payload, headers=headers)
```
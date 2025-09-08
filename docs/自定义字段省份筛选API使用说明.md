# 自定义字段省份筛选API使用说明

## 功能概述

自定义字段管理API现已支持按省份和专栏（section）进行灵活筛选，提供多种筛选模式满足不同业务需求。

## API端点

### 1. 获取省份列表
```http
GET /api/v1/custom-fields/provinces
```

**响应示例：**
```json
{
  "success": true,
  "provinces": [
    {
      "province": "广东省",
      "field_count": 2,
      "visible_field_count": 2,
      "required_field_count": 0
    }
  ],
  "common_fields": {
    "total_common_fields": 0,
    "visible_common_fields": 0,
    "required_common_fields": 0
  }
}
```

### 2. 字段管理接口（支持省份筛选）
```http
GET /api/v1/custom-fields/manage/<section>
```

**支持的筛选参数：**
- `province` - 省份名称（需URL编码）
- `strict_province` - 严格省份匹配（boolean）
- `only_common` - 仅显示通用字段（boolean）

## 筛选模式详解

### 1. 显示全部字段（默认）
```http
GET /api/v1/custom-fields/manage/basic
```
返回所有字段，不进行任何筛选。

### 2. 省份筛选（默认行为）
```http
GET /api/v1/custom-fields/manage/basic?province=广东省
```
返回指定省份的字段 + 通用字段（province为NULL的字段）。
- 🎯 **适用场景：** 获取特定省份相关的所有可用字段

### 3. 严格省份匹配
```http
GET /api/v1/custom-fields/manage/basic?province=广东省&strict_province=true
```
仅返回指定省份的字段，不包含通用字段。
- 🎯 **适用场景：** 只管理省份特定的自定义配置

### 4. 仅显示通用字段
```http
GET /api/v1/custom-fields/manage/basic?only_common=true
```
仅返回通用字段（province为NULL的字段）。
- 🎯 **适用场景：** 管理全局通用的字段配置

## URL编码说明

由于省份名称包含中文字符，在URL中需要进行编码：

| 省份 | URL编码 |
|------|---------|
| 广东省 | %E5%B9%BF%E4%B8%9C%E7%9C%81 |
| 北京市 | %E5%8C%97%E4%BA%AC%E5%B8%82 |
| 上海市 | %E4%B8%8A%E6%B5%B7%E5%B8%82 |

## 实际使用示例

### 前端下拉选择省份
```javascript
// 1. 获取省份列表
fetch('/api/v1/custom-fields/provinces')
  .then(res => res.json())
  .then(data => {
    const provinces = data.provinces.map(p => ({
      label: `${p.province} (${p.field_count}个字段)`,
      value: p.province
    }));
    // 填充省份下拉框
  });
```

### 根据用户选择筛选字段
```javascript
// 2. 根据选择的省份和筛选模式获取字段
function loadFields(province, strictMode = false, commonOnly = false) {
  let url = '/api/v1/custom-fields/manage/basic';
  const params = new URLSearchParams();
  
  if (commonOnly) {
    params.append('only_common', 'true');
  } else if (province) {
    params.append('province', province);
    if (strictMode) {
      params.append('strict_province', 'true');
    }
  }
  
  if (params.toString()) {
    url += '?' + params.toString();
  }
  
  return fetch(url).then(res => res.json());
}
```

### 场景化使用
```javascript
// 场景1：用户选择广东省，显示广东省+通用字段
loadFields('广东省', false, false);

// 场景2：仅管理广东省特有字段
loadFields('广东省', true, false);

// 场景3：管理全局通用字段
loadFields(null, false, true);
```

## 参数优先级
当多个筛选参数同时存在时，优先级如下：
1. `only_common=true` - 最高优先级，忽略province参数
2. `province` + `strict_province=true` - 严格省份匹配
3. `province` - 默认省份匹配（包含通用字段）
4. 无参数 - 显示全部字段

## 响应格式
所有接口返回统一格式：
```json
{
  "success": true,
  "data": {
    "fields": [...],
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 2,
      "total_pages": 1
    }
  }
}
```

## 测试验证
功能已通过以下测试验证：
- ✅ 省份列表接口
- ✅ 严格省份筛选
- ✅ 通用字段筛选  
- ✅ 默认省份筛选行为
- ✅ URL编码处理

## 向后兼容性
- 现有API调用不受影响
- 新参数为可选参数，默认行为保持不变
- 支持渐进式升级
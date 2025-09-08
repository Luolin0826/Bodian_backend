# Data-Query页面后端适配方案 - 基于现有bdprod数据库

## 方案概述

本方案基于现有的bdprod数据库（包含32,740条recruitment_records和65个secondary_units），通过扩展表结构和API接口，完美支持data-query页面的左右两栏布局需求。

### 核心优势

1. **充分利用现有数据**: 基于32,740条真实录取数据进行分析
2. **零迁移风险**: 在现有表基础上扩展，不影响现有功能
3. **完全兼容**: 与现有系统保持100%兼容
4. **渐进式升级**: 可以分阶段实施，降低风险

## 实施步骤

### 第1步：执行数据库扩展脚本

```bash
# 在MySQL中执行扩展脚本
mysql -h rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com \
      -u dms_user_9332d9e \
      -p bdprod < bdprod_extension_schema.sql
```

这个脚本会：
- 扩展secondary_units表，添加org_type等字段
- 创建4个扩展表（政策规则、提前批、农网、展示配置）
- 自动分类现有的65个单位（国网/南网）
- 初始化字段配置数据

### 第2步：运行数据初始化脚本

```bash
python bdprod_data_initialization.py
```

这个脚本会：
- 为主要单位添加政策规则示例数据
- 添加提前批和农网政策示例
- 更新单位的薪资和分数信息

### 第3步：启动Flask应用测试

```bash
python run.py
```

## API接口说明

### 左栏政策查询接口

#### 1. 获取筛选选项
```
GET /api/v1/policies/filter-options

Response:
{
  "success": true,
  "data": {
    "gw_provinces": [     // 国网省公司
      {"unit_id": 5, "unit_name": "四川", "unit_code": "UNIT0005"},
      {"unit_id": 3, "unit_name": "山东", "unit_code": "UNIT0003"}
    ],
    "gw_direct_units": [], // 国网直属单位
    "nw_provinces": [     // 南网省公司  
      {"unit_id": 1, "unit_name": "广东", "unit_code": "UNIT0001"}
    ],
    "nw_direct_units": [] // 南网直属单位
  }
}
```

#### 2. 获取单位政策详情
```
GET /api/v1/policies/unit-details?unit_id=5

Response:
{
  "success": true,
  "data": {
    "unit_info": {
      "unit_id": 5,
      "unit_name": "四川", 
      "org_type": "国网省公司",
      "salary_range": "6-8万",
      "estimated_score_range": "70-75分"
    },
    "policy_info": {
      "recruitment_count": {
        "display_name": "录取人数",
        "value": 200,
        "type": "number"
      },
      "english_requirement": {
        "display_name": "英语等级",
        "value": "四级425分以上", 
        "type": "select"
      }
      // ... 其他23个政策字段
    }
  }
}
```

#### 3. 获取地市县概览
```
GET /api/v1/policies/regional-overview?unit_id=5

Response:
{
  "success": true,
  "data": {
    "org_type": "国网省公司",
    "total_count": 25,
    "regional_overview": [
      {
        "unit_id": 5,
        "city": "四川",
        "county": "西南",
        "apply_status": "网申通过率中等",
        "salary_range": "6-8万",
        "estimated_score": "70-75分"
      }
    ]
  }
}
```

#### 4. 获取提前批信息
```
GET /api/v1/policies/early-batch?unit_id=5

Response:
{
  "success": true,
  "data": {
    "early_batch_info": {
      "schedule_arrangement": {
        "display_name": "行程安排",
        "value": "每年10月中旬，为期3天的现场面试",
        "type": "textarea"
      }
      // ... 其他9个提前批字段
    },
    "has_data": true
  }
}
```

#### 5. 获取农网信息
```
GET /api/v1/policies/rural-grid?unit_id=5

Response:
{
  "success": true,
  "data": {
    "rural_grid_info": {
      "salary_benefits": {
        "display_name": "农网待遇",
        "value": "基本工资5-7万，加上补贴约6-8万/年",
        "type": "text"
      }
      // ... 其他8个农网字段
    },
    "has_data": true
  }
}
```

### 右栏学校录取统计接口

#### 1. 按批次获取学校统计
```
GET /api/v1/analytics/schools-by-batch?unit_id=5&batch=一批&page=1&limit=20

Response:
{
  "success": true,
  "data": {
    "schools": [
      {
        "university_id": 123,
        "university_name": "电子科技大学",
        "university_type": "985工程", 
        "batch": "一批",
        "admission_count": 15,
        "male_count": 9,
        "female_count": 6
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 85,
      "total_pages": 5
    },
    "summary": {
      "total_schools": 85,
      "total_admissions": 1274
    }
  }
}
```

#### 2. 获取录取概览
```
GET /api/v1/analytics/admission-overview?unit_id=5&batch=一批

Response:
{
  "success": true,
  "data": {
    "batch_distribution": [
      {"batch": "一批", "school_count": 85, "total_admissions": 800},
      {"batch": "二批", "school_count": 45, "total_admissions": 400}
    ],
    "school_type_distribution": [
      {"school_type": "985工程", "admission_count": 300, "percentage": 23.5},
      {"school_type": "211工程", "admission_count": 450, "percentage": 35.3}
    ],
    "gender_distribution": [
      {"gender": "男", "count": 850, "percentage": 66.7},
      {"gender": "女", "count": 424, "percentage": 33.3}
    ]
  }
}
```

#### 3. 获取批次对比
```
GET /api/v1/analytics/batch-comparison?unit_id=5

Response:
{
  "success": true,
  "data": {
    "batch_comparison": [
      {
        "batch": "一批",
        "school_count": 85,
        "total_admissions": 800,
        "male_count": 534,
        "female_count": 266,
        "male_percentage": 66.75,
        "female_percentage": 33.25
      }
    ]
  }
}
```

## 前端对接方案

### 左栏实现流程

1. **页面加载时**
   ```javascript
   // 获取四个筛选选项
   const options = await api.get('/api/v1/policies/filter-options');
   renderFilterOptions(options.data);
   ```

2. **用户选择单位时**
   ```javascript
   // 清空其他筛选项（互斥逻辑）
   clearOtherFilters();
   
   // 获取单位详情
   const details = await api.get(`/api/v1/policies/unit-details?unit_id=${unitId}`);
   renderPolicyDetails(details.data);
   
   // 获取地市县概览
   const overview = await api.get(`/api/v1/policies/regional-overview?unit_id=${unitId}`);
   renderRegionalOverview(overview.data);
   ```

3. **查看专项政策**
   ```javascript
   // 查看提前批
   const earlyBatch = await api.get(`/api/v1/policies/early-batch?unit_id=${unitId}`);
   renderEarlyBatchInfo(earlyBatch.data);
   
   // 查看农网
   const ruralGrid = await api.get(`/api/v1/policies/rural-grid?unit_id=${unitId}`);
   renderRuralGridInfo(ruralGrid.data);
   ```

### 右栏实现流程

1. **默认展示概览**
   ```javascript
   const overview = await api.get('/api/v1/analytics/admission-overview');
   renderAdmissionOverview(overview.data);
   ```

2. **左栏选择单位后**
   ```javascript
   // 右栏显示该单位的录取分析
   const schools = await api.get(`/api/v1/analytics/schools-by-batch?unit_id=${unitId}`);
   renderSchoolsTable(schools.data);
   ```

3. **批次筛选**
   ```javascript
   // 用户选择批次后
   const filteredSchools = await api.get(`/api/v1/analytics/schools-by-batch?unit_id=${unitId}&batch=${batch}`);
   renderSchoolsTable(filteredSchools.data);
   ```

## 数据映射说明

### 现有数据利用

1. **secondary_units表** (65条记录)
   - 已自动分类为4种组织类型
   - 扩展了薪资、分数等字段
   - 作为筛选选项的数据源

2. **recruitment_records表** (32,740条记录)
   - 直接用于学校录取统计
   - 支持按单位、批次筛选
   - 提供性别分布、学校类型分析

3. **universities表**
   - 提供学校名称、类型信息
   - 支持985/211分类统计

### 扩展表数据

1. **policy_rules_extended**: 存储23个政策字段
2. **early_batch_policies_extended**: 存储9个提前批字段  
3. **rural_grid_policies_extended**: 存储8个农网字段
4. **display_config_extended**: 支持字段动态配置

## 字段配置管理

### 动态字段配置

系统支持通过display_config_extended表动态配置每个板块显示的字段：

```javascript
// 获取基本信息板块的字段配置
const config = await api.get('/api/v1/policies/display-config?category=基本信息');

// 根据配置渲染字段
config.data.fields.forEach(field => {
    if (field.is_enabled) {
        renderField(field.field_name, field.display_name, policyData[field.field_name]);
    }
});
```

### 支持的板块

1. **基本信息**: 23个可配置字段
2. **提前批**: 9个可配置字段
3. **农网**: 8个可配置字段
4. **地市县信息**: 5个可配置字段

## 性能优化

### 数据库优化

1. **索引策略**
   - org_type字段索引：优化筛选查询
   - unit_id外键索引：优化关联查询
   - batch字段索引：优化批次筛选

2. **查询优化**
   - 使用JOIN避免N+1查询
   - 合理的分页限制
   - 统计查询缓存

### API性能

1. **响应优化**
   - 合理的数据结构设计
   - 避免冗余数据传输
   - 支持字段按需返回

2. **缓存策略**
   - 筛选选项数据可缓存1小时
   - 政策数据可缓存30分钟
   - 统计数据实时更新

## 监控和维护

### 健康检查

```bash
# 检查政策API健康状态
curl http://localhost:5000/api/v1/policies/health

# 检查分析API健康状态  
curl http://localhost:5000/api/v1/analytics/health
```

### 数据验证

定期检查：
1. 扩展表数据完整性
2. 外键关联关系
3. 字段配置有效性

## 总结

这个基于bdprod数据库的扩展方案：

1. **完全利用现有数据**: 32,740条录取记录 + 65个单位信息
2. **零风险扩展**: 不影响现有任何功能
3. **功能完整**: 支持左右两栏的所有需求
4. **易于维护**: 标准的扩展表设计
5. **性能优秀**: 基于真实数据的高效查询

通过这个方案，data-query页面可以获得：
- 四个互斥的筛选选项
- 完整的单位政策信息（23个字段可配置）
- 专业的提前批和农网政策
- 基于真实数据的学校录取统计
- 灵活的批次筛选和分析功能

整个方案既满足了功能需求，又最大化了现有数据的价值，是一个非常实用的优化方案。
# 数查一点通 - 完整API接口文档

## 📖 系统概述

**数查一点通**是一个综合性的国网和南网录取信息查询系统，提供从基础数据查询到高级数据分析的全套API接口。

### 🏗️ 系统架构

- **技术栈**: Flask + PyMySQL + MySQL 8.0 (阿里云RDS)
- **服务地址**: http://localhost:5000
- **API版本**: enhanced_v1.0
- **数据规模**: 1900条录取记录 + 36条政策规则

### 📊 核心数据结构

#### 数据表统计
| 表名 | 记录数 | 用途 |
|-----|-------|------|
| **recruitment_records** | 1,900条 | 录取记录数据 |
| **recruitment_rules** | 36条 | 政策规则数据 |
| **field_notes** | 4条 | 字段备注说明 |

#### 数据分布概况
- **公司类型**: 国网900条 + 南网1000条
- **学校层次**: 普通本科(803) > 985(484) > 学院(330) > 211(258) > 其他(25)
- **政策覆盖**: 省级(5) + 市级(2) + 区县级(29)

---

## 🗄️ 数据库表结构详情

### 1. recruitment_records (录取记录表) - 1,900条

录取人员的详细信息表，包含个人基本信息、学校信息、录取信息等。

#### 表结构
| 字段名 | 数据类型 | 约束 | 说明 |
|--------|---------|------|------|
| **id** | int | PRIMARY KEY | 主键ID |
| **name** | varchar(50) | NOT NULL | 姓名 |
| **gender** | enum('男','女') | NOT NULL | 性别 |
| **school** | varchar(100) | NOT NULL | 毕业院校 |
| **major** | varchar(100) | NULL | 专业 |
| **education_level** | enum('本科','硕士','博士') | NOT NULL | 学历层次 |
| **school_type** | varchar(50) | NULL, INDEX | 学校类型(985/211/普通本科/学院/其他) |
| **phone** | varchar(20) | NULL | 联系电话 |
| **province** | varchar(50) | NOT NULL, INDEX | 录取省份 |
| **city** | varchar(50) | NULL | 录取城市 |
| **company** | varchar(100) | NULL | 录取单位 |
| **position** | varchar(100) | NULL | 录取岗位 |
| **batch_type** | enum | NOT NULL, INDEX | 录取批次(提前批/一批/二批/三批/南网) |
| **company_type** | enum('国网','南网') | NOT NULL | 公司类型 |
| **written_score** | decimal(5,2) | NULL | 笔试成绩 |
| **interview_score** | decimal(5,2) | NULL | 面试成绩 |
| **comprehensive_score** | decimal(5,2) | NULL | 综合成绩 |
| **admission_year** | year | NOT NULL, INDEX | 录取年份 |
| **created_at** | timestamp | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

#### 重要索引
- `idx_province_city` - 支持按省份和城市查询
- `idx_school_type` - 支持按学校类型统计
- `idx_batch_company` - 支持按批次和公司类型查询
- `idx_admission_year` - 支持按年份查询

---

### 2. recruitment_rules (政策规则表) - 36条

详细的录取政策和要求信息表，包含各地区的录取政策、薪资待遇、学历要求等。

#### 表结构
| 字段名 | 数据类型 | 约束 | 说明 |
|--------|---------|------|------|
| **id** | int | PRIMARY KEY | 主键ID |
| **province** | varchar(50) | NOT NULL, INDEX | 省份 |
| **city** | varchar(50) | NULL | 城市 |
| **company** | varchar(100) | NULL | 具体单位/区县 |
| **data_level** | enum | NOT NULL, INDEX | 数据层级(省级汇总/市级汇总/区县详情) |
| **region_type** | tinyint | INDEX, DEFAULT 0 | 地区类型(0:普通省,1:直辖市,2:特别行政区,3:自治区) |

#### 基本要求字段
| 字段名 | 数据类型 | 说明 |
|--------|---------|------|
| **cet_requirement** | varchar(20) | 英语等级要求 |
| **computer_requirement** | varchar(20) | 计算机等级要求 |
| **overage_allowed** | varchar(20) | 超龄限制 |
| **household_priority** | varchar(20) | 户口优先政策 |
| **non_first_choice_pass** | varchar(20) | 非第一志愿通过情况 |

#### 详细规则字段
| 字段名 | 数据类型 | 说明 |
|--------|---------|------|
| **detailed_rules** | text | 详细录取规则 |
| **unwritten_rules** | text | 潜规则信息 |
| **stable_score_range** | varchar(100) | 稳定通过分数范围 |
| **single_cert_probability** | text | 单证通过概率 |
| **admission_ratio** | varchar(50) | 录取比例 |

#### 本科学历要求字段
| 字段名 | 说明 |
|--------|------|
| **bachelor_985** | 985本科要求 |
| **bachelor_211** | 211本科要求 |
| **bachelor_provincial_double_first** | 省内双一流本科 |
| **bachelor_external_double_first** | 省外双一流本科 |
| **bachelor_provincial_non_double** | 省内双非本科 |
| **bachelor_external_non_double** | 省外双非本科 |
| **bachelor_provincial_second** | 省内二本 |
| **bachelor_external_second** | 省外二本 |
| **bachelor_private** | 民办本科 |
| **bachelor_upgrade** | 专升本 |
| **bachelor_college** | 专科 |

#### 硕士学历要求字段
| 字段名 | 说明 |
|--------|------|
| **master_985** | 985硕士要求 |
| **master_211** | 211硕士要求 |
| **master_provincial_double_first** | 省内双一流硕士 |
| **master_external_double_first** | 省外双一流硕士 |
| **master_provincial_non_double** | 省内双非硕士 |
| **master_external_non_double** | 省外双非硕士 |

#### 薪资和分数线字段
| 字段名 | 数据类型 | 说明 |
|--------|---------|------|
| **bachelor_salary** | varchar(50) | 本科薪资范围 |
| **bachelor_interview_line** | varchar(20) | 本科面试分数线 |
| **bachelor_comprehensive_score** | decimal(5,2) | 本科综合分数要求 |
| **master_salary** | varchar(50) | 硕士薪资范围 |
| **master_interview_line** | decimal(5,2) | 硕士面试分数线 |

#### 录取政策字段
| 字段名 | 数据类型 | 说明 |
|--------|---------|------|
| **major_mismatch_allowed** | varchar(20) | 专业不对口是否允许 |
| **first_batch_fail_second_batch** | varchar(20) | 一批失败能否走二批 |
| **deferred_graduation_impact** | varchar(20) | 延迟毕业影响 |
| **second_choice_available** | varchar(20) | 是否有二志愿 |
| **position_selection_method** | text | 岗位选择方式 |
| **early_batch_difference** | text | 提前批区别 |
| **campus_recruit_then_first_batch** | varchar(20) | 校招失败能否走统招 |

#### 性价比标识字段
| 字段名 | 数据类型 | 说明 |
|--------|---------|------|
| **is_best_value_city** | varchar(10) | 是否为性价比最高的市 |
| **is_best_value_county** | varchar(10) | 是否为性价比最高的县 |

#### 时间字段
| 字段名 | 数据类型 | 说明 |
|--------|---------|------|
| **created_at** | timestamp | 创建时间 |
| **updated_at** | timestamp | 更新时间 |

---

### 3. field_notes (字段备注表) - 4条

用户自定义的字段备注和说明信息表，支持对政策规则的个性化注释。

#### 表结构
| 字段名 | 数据类型 | 约束 | 说明 |
|--------|---------|------|------|
| **id** | int | PRIMARY KEY | 主键ID |
| **rule_id** | int | NOT NULL, INDEX, FOREIGN KEY | 关联的政策规则ID |
| **field_name** | varchar(50) | NOT NULL, INDEX | 字段名称 |
| **note_content** | text | NOT NULL | 备注内容 |
| **note_type** | enum | DEFAULT '说明' | 备注类型(说明/限制/特殊情况/警告) |
| **created_at** | timestamp | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| **updated_at** | timestamp | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

#### 备注类型说明
- **说明**: 一般性说明信息
- **限制**: 限制性条件说明  
- **特殊情况**: 特殊情况处理说明
- **警告**: 重要提醒信息

#### 外键关系
- `rule_id` → `recruitment_rules.id` (CASCADE DELETE)

---

### 4. 数据表关系图

```
┌─────────────────────┐       ┌─────────────────────┐
│  recruitment_rules  │ 1───N │    field_notes      │
│    (政策规则表)      │ ────→ │   (字段备注表)       │
│ - id (PK)           │       │ - rule_id (FK)      │
│ - province          │       │ - field_name        │  
│ - city              │       │ - note_content      │
│ - company           │       └─────────────────────┘
│ - data_level        │
│ - bachelor_985      │       
│ - bachelor_211      │       ┌─────────────────────┐
│ - master_985        │       │ recruitment_records │
│ - bachelor_salary   │       │   (录取记录表)       │
│ - is_best_value_*   │ ◄───┐ │ - id (PK)           │
└─────────────────────┘     │ │ - name              │
                            │ │ - school            │
        关联查询关系          │ │ - school_type       │
    (通过province/city)      │ │ - province          │
                            │ │ - city              │
                            └─► │ - company           │
                              │ - company_type      │
                              │ - batch_type        │
                              └─────────────────────┘

说明：
- recruitment_rules 与 field_notes 是 1:N 外键关系
- recruitment_records 与 recruitment_rules 通过 province/city 进行关联查询
- 无直接外键约束，使用业务逻辑关联
```

### 5. 数据完整性约束

#### 枚举值定义
- **gender**: '男', '女'
- **education_level**: '本科', '硕士', '博士'  
- **batch_type**: '提前批', '一批', '二批', '三批', '南网'
- **company_type**: '国网', '南网'
- **data_level**: '省级汇总', '市级汇总', '区县详情'
- **note_type**: '说明', '限制', '特殊情况', '警告'

#### 数据验证规则
- 分数字段范围: 0.00-100.00
- 年份范围: 1990-2030
- 电话号码格式验证
- 省份名称标准化

### 6. 实际数据样例

#### recruitment_records 表数据样例
| 姓名 | 性别 | 学校 | 学校类型 | 省份 | 公司类型 | 批次 |
|------|------|------|----------|------|----------|------|
| 白*晖 | 男 | 东南大学 | 985 | 江苏 | 国网 | 一批 |
| 白*廷 | 男 | 华北电力大学(保定) | 985 | 江苏 | 国网 | 一批 |
| 柏*音 | 男 | 南京理工大学 | 普通本科 | 江苏 | 国网 | 一批 |

#### recruitment_rules 表数据样例
| 省份 | 城市 | 单位 | 数据层级 | 本科薪资 | 本科面试线 |
|------|------|------|----------|----------|------------|
| 北京 | NULL | NULL | 省级汇总 | NULL | NULL |
| 四川 | 成都 | 城区+直管县 | 区县详情 | 16-18 | 75 |
| 重庆 | NULL | 市南 | 区县详情 | 13-16 | 65 |

#### field_notes 表数据样例
| 规则ID | 字段名 | 备注内容 | 备注类型 |
|--------|--------|----------|----------|
| 4 | master_985 | 985硕士具有参加提前批资格，在重庆报考一批可能过不了网申 | 特殊情况 |
| 4 | master_211 | 211硕士在重庆报考一批不会被优先考虑 | 限制 |
| 9 | bachelor_985 | 985本科需要本科211以上学历才能过网审 | 限制 |

---

## 🚀 API接口分类

### 1️⃣ 基础查询接口

#### 1.1 获取查询选项
```http
GET /api/v1/recruitment/options
```

**功能**: 获取所有可用的查询参数选项  
**返回**: 省份、城市、单位、学校类型、批次类型等选项列表

**响应示例**:
```json
{
    "provinces": ["上海", "北京", "四川", "天津", "重庆"],
    "cities": ["东城区", "天府", "成都", "渝中区", "绵阳", "西城区", "黄浦区"],
    "companies": ["万州", "其他非直属局", "北培", "城区+直管县", ...],
    "school_types": ["211", "985", "其他", "学院", "普通本科"],
    "batch_types": ["一批", "二批", "三批", "南网"],
    "data_levels": ["省级汇总", "市级汇总", "区县详情"]
}
```

#### 1.2 系统健康检查
```http
GET /api/v1/recruitment/health
```

**功能**: 检查API服务状态和数据库连接  
**返回**: 系统状态和数据统计

**响应示例**:
```json
{
    "status": "healthy",
    "recruitment_records": 1900,
    "api_version": "enhanced_v1.0"
}
```

---

### 2️⃣ 级联查询接口

#### 2.1 根据省份获取城市
```http
GET /api/v1/recruitment/cities/{province}
```

**功能**: 动态获取指定省份下的所有城市选项  
**路径参数**: `province` - 省份名称  

**示例**:
```bash
GET /api/v1/recruitment/cities/四川
```

**响应**:
```json
{
    "province": "四川",
    "cities": ["天府", "成都", "绵阳"],
    "count": 3
}
```

#### 2.2 根据省份获取单位
```http
GET /api/v1/recruitment/companies/{province}
```

**功能**: 获取指定省份下的所有单位/区县  
**路径参数**: `province` - 省份名称  
**查询参数**: `city` (可选) - 城市名称

**示例**:
```bash
GET /api/v1/recruitment/companies/重庆
GET /api/v1/recruitment/companies/四川?city=成都
```

**响应**:
```json
{
    "province": "重庆",
    "city": null,
    "companies": ["万州", "其他非直属局", "北培", "市北", "市区", "市南", ...],
    "count": 10
}
```

#### 2.3 根据省份和城市获取单位
```http
GET /api/v1/recruitment/cities/{province}/{city}/companies
```

**功能**: 获取特定省市下的具体单位列表  

**示例**:
```bash
GET /api/v1/recruitment/cities/四川/成都/companies
```

---

### 3️⃣ 录取数据查询接口

#### 3.1 按省份查询录取情况
```http
GET /api/v1/recruitment/province/{province}
```

**功能**: 查询指定省份的录取统计和学校分布  
**查询参数**: `include_school_details` - 是否包含学校详情 (true/false)

**示例**:
```bash
GET /api/v1/recruitment/province/江苏?include_school_details=true
```

**响应结构**:
```json
{
    "province": "江苏",
    "total_count": 900,
    "by_batch": {
        "一批": 500,
        "二批": 300,
        "三批": 100
    },
    "by_school_type": {
        "985": 259,
        "211": 76,
        "普通本科": 378,
        "学院": 265,
        "其他": 22
    },
    "top_schools": [
        {"school": "华北电力大学", "school_type": "985", "count": 85},
        {"school": "河海大学", "school_type": "211", "count": 32}
    ]
}
```

#### 3.2 查询录取政策
```http
GET /api/v1/recruitment/policies
```

**功能**: 查询录取政策信息  
**查询参数**: 
- `province` - 省份名称
- `city` - 城市名称 (可选)

**示例**:
```bash
GET /api/v1/recruitment/policies?province=江苏&city=南京
```

---

### 4️⃣ 高级分析接口

#### 4.1 区县级精确政策查询
```http
GET /api/v1/recruitment/district-policies
```

**功能**: 获取区县级精确录取政策  
**查询参数**:
- `province` - 省份名称
- `city` - 城市名称 (可选)  
- `company` - 单位名称 (可选)

**响应结构**:
```json
{
    "query_params": {
        "province": "四川",
        "city": "成都",
        "company": "高新区"
    },
    "policies": [
        {
            "id": 1,
            "province": "四川",
            "city": "成都",
            "company": "高新区",
            "basic_requirements": {
                "cet_requirement": "英语四级425分以上",
                "computer_requirement": "计算机二级",
                "overage_allowed": "不超过25周岁"
            },
            "salary_info": {
                "bachelor_salary": "月薪6000-8000",
                "master_salary": "月薪8000-12000",
                "bachelor_interview_line": "65分"
            },
            "admission_policies": {
                "first_batch_fail_second_batch": "支持",
                "second_choice_available": "有二志愿"
            }
        }
    ],
    "summary": {
        "total_records": 5,
        "by_level": {"省级汇总": 2, "区县详情": 3}
    }
}
```

#### 4.2 按学校层次查询网申情况
```http
GET /api/v1/recruitment/admission-by-school-level
```

**功能**: 按985/211等学校层次查询网申通过情况  
**查询参数**:
- `school_levels` - 学校层次列表 (985,211,双一流等)
- `provinces` - 省份列表
- `cities` - 城市列表 (可选)
- `education_level` - 学历层次 (bachelor/master)

**示例**:
```bash
GET /api/v1/recruitment/admission-by-school-level?school_levels=985&school_levels=211&provinces=江苏&education_level=bachelor
```

#### 4.3 录取数据分析
```http
GET /api/v1/recruitment/analytics
```

**功能**: 多维度录取数据统计分析  
**查询参数**:
- `analysis_type` - 分析类型 (comprehensive/school/regional/trend)
- `group_by` - 分组字段 (province,school_type,batch_type,company_type)
- `provinces` - 省份过滤 (可选)
- `school_types` - 学校类型过滤 (可选)
- `years` - 年度过滤 (可选)

**示例**:
```bash
GET /api/v1/recruitment/analytics?analysis_type=comprehensive&group_by=province&group_by=school_type
```

**响应结构**:
```json
{
    "analysis_type": "comprehensive",
    "analytics": {
        "total_count": 1900,
        "grouped_stats": [
            {"province": "江苏", "school_type": "985", "count": 259},
            {"province": "广东", "school_type": "985", "count": 311}
        ],
        "batch_distribution": [
            {"batch_type": "国网", "company_type": "国网", "count": 900},
            {"batch_type": "南网", "company_type": "南网", "count": 1000}
        ]
    },
    "insights": [
        "录取最多的组合是：广东省985学校，共311人"
    ]
}
```

#### 4.4 性价比地区查询
```http
GET /api/v1/recruitment/best-value
```

**功能**: 基于录取难度和薪资待遇推荐性价比地区  
**查询参数**: `region_level` - 地区级别 (city/county/all)

**示例**:
```bash
GET /api/v1/recruitment/best-value?region_level=all
```

**响应结构**:
```json
{
    "region_level": "all",
    "best_value_cities": [
        {
            "province": "四川",
            "city": "绵阳",
            "company": "涪城区",
            "salary_info": {
                "bachelor_salary": "14-17",
                "master_salary": "14-17",
                "bachelor_interview_line": "60"
            }
        }
    ],
    "comprehensive_ranking": [
        {
            "province": "重庆",
            "company": "市南", 
            "recruitment_data": {
                "total_recruitment": 5,
                "key_school_recruitment": 1,
                "key_school_ratio": 20.0
            },
            "value_tags": {
                "is_best_value_city": false,
                "is_best_value_county": true
            }
        }
    ]
}
```

---

## 🎯 数据覆盖范围

### 地理覆盖
- **省份**: 上海、北京、四川、天津、重庆等5个省市
- **城市**: 成都、绵阳、天府、渝中区等7个城市
- **区县**: 25个具体区县/单位

### 学校覆盖
- **985高校**: 华北电力大学、华南理工大学、中山大学等
- **211高校**: 河海大学、广东工业大学、三峡大学等
- **普通本科**: 暨南大学、华南师范大学等
- **专业院校**: 各类学院和专科院校

### 公司覆盖
- **国网系统**: 江苏、安徽民生电力等
- **南网系统**: 广东电网、超高压公司等

---

## 🔧 API调用示例

### 前端集成示例

#### 1. 级联选择器
```javascript
// 省份选择后获取城市
const getCitiesByProvince = async (province) => {
    const response = await fetch(`/api/v1/recruitment/cities/${province}`);
    const data = await response.json();
    return data.cities;
};

// 城市选择后获取单位
const getCompaniesByCity = async (province, city) => {
    const response = await fetch(`/api/v1/recruitment/cities/${province}/${city}/companies`);
    const data = await response.json();
    return data.companies;
};
```

#### 2. 数据查询
```javascript
// 查询省份录取情况
const getProvinceData = async (province) => {
    const response = await fetch(`/api/v1/recruitment/province/${province}?include_school_details=true`);
    return await response.json();
};

// 性价比地区推荐
const getBestValueRegions = async (level = 'all') => {
    const response = await fetch(`/api/v1/recruitment/best-value?region_level=${level}`);
    return await response.json();
};
```

#### 3. 高级分析
```javascript
// 学校层次分析
const getSchoolLevelAnalysis = async (levels, provinces) => {
    const params = new URLSearchParams();
    levels.forEach(level => params.append('school_levels', level));
    provinces.forEach(province => params.append('provinces', province));
    
    const response = await fetch(`/api/v1/recruitment/admission-by-school-level?${params}`);
    return await response.json();
};
```

---

## 📊 性能规格

### 响应时间指标
- **基础查询**: < 200ms
- **复杂分析**: < 500ms  
- **级联查询**: < 100ms

### 并发支持
- **开发环境**: 50+ 并发请求
- **生产环境**: 500+ 并发请求 (建议使用Gunicorn)

### 数据更新频率
- **录取记录**: 按需更新 (1900条)
- **政策规则**: 定期维护 (36条)
- **字段备注**: 用户自定义 (4条)

---

## 🛠️ 开发指南

### 错误处理
所有API统一返回错误格式：
```json
{
    "error": "错误描述信息"
}
```

### HTTP状态码
- `200` - 请求成功
- `400` - 请求参数错误
- `500` - 服务器内部错误  
- `503` - 服务不可用

### 参数验证
- 省份名称: 必须是有效的省份名称
- 学校层次: 限定为 985/211/普通本科/学院/其他
- 地区级别: 限定为 city/county/all

---

## 🔄 版本历史

### v1.0 (Current)
- ✅ 完整的录取数据查询功能
- ✅ 级联选择器支持
- ✅ 高级数据分析接口  
- ✅ 性价比地区推荐
- ✅ 1900条录取记录 + 36条政策规则

### 计划功能
- 📝 用户自定义查询保存
- 📊 数据可视化接口
- 🔍 全文搜索功能
- 📈 历史趋势分析

---

## 📞 技术支持

- **服务状态**: 运行中 (Flask开发服务器)
- **数据库**: MySQL 8.0 (阿里云RDS)  
- **监控地址**: http://localhost:5000/api/v1/recruitment/health
- **文档版本**: v1.0
- **最后更新**: 2025年1月

🎉 **数查一点通** - 您的智能录取信息查询助手！
# Data-Query页面后端适配完整方案

## 概述

本方案为data-query页面重新设计了优化的数据库架构和API接口，支持左右两栏布局：
- **左栏**: 网申政策栏（组织筛选、政策详情、提前批、农网、地市县概览）
- **右栏**: 学校录取统计（数据分析、批次筛选、录取概览）

## 架构设计

### 数据库架构

#### 核心表结构

1. **organizations** - 组织架构表
   - 支持国网/南网的省公司和直属单位管理
   - 四种组织类型：国网省公司、国网直属单位、南网省公司、南网直属单位

2. **regional_units** - 地区单位表
   - 存储省、市、区县级别的具体单位信息
   - 包含薪资范围、预估分数、网申情况等

3. **policy_rules** - 政策规则表
   - 存储详细的录取政策规则
   - 支持23个政策字段的完整管理

4. **early_batch_policies** - 提前批政策表
   - 专门存储提前批相关政策
   - 包含行程安排、录用因素、难度排行等

5. **rural_grid_policies** - 农网政策表
   - 专门存储农网相关政策
   - 包含待遇、考试、测评等信息

6. **batch_admission_stats** - 批次录取统计表
   - 存储按批次的学校录取统计
   - 支持一批、二批、三批数据分析

7. **display_config** - 可配置展示字段表
   - 支持页面展示字段的动态配置
   - 可以增删改展示项目

### API接口设计

#### 左栏政策查询接口 (/api/v1/policies/)

```
GET /filter-options          # 获取四个筛选项的选项数据
GET /unit-details            # 获取单位详细政策信息  
GET /regional-overview       # 获取地市县概览信息
GET /early-batch             # 获取提前批信息
GET /rural-grid              # 获取农网信息
GET /display-config          # 获取可配置展示字段
GET /health                  # 健康检查
```

#### 右栏学校统计接口 (/api/v1/analytics/)

```
GET /schools-by-batch        # 按批次获取学校录取统计
GET /admission-overview      # 获取录取概览数据
GET /batch-comparison        # 获取批次对比数据
GET /search-schools          # 搜索学校
GET /export-data             # 导出录取数据
GET /health                  # 健康检查
```

## 文件结构

```
workspace/
├── data_query_schema.sql           # 完整数据库架构设计
├── data_initialization.py          # 数据初始化脚本
├── app/routes/
│   ├── policies.py                 # 左栏政策查询API路由
│   └── analytics.py                # 右栏学校统计API路由
└── app/__init__.py                 # 已更新蓝图注册
```

## 使用说明

### 1. 数据库初始化

```bash
# 执行数据库架构创建
mysql -h your_host -u your_user -p < data_query_schema.sql

# 运行数据初始化脚本
python data_initialization.py
```

### 2. 启动API服务

```bash
# 启动Flask应用
python run.py
```

### 3. API使用示例

#### 获取筛选选项
```javascript
GET /api/v1/policies/filter-options

Response:
{
  "success": true,
  "data": {
    "gw_provinces": [...],      // 国网省公司列表
    "gw_direct_units": [...],   // 国网直属单位列表
    "nw_provinces": [...],      // 南网省公司列表
    "nw_direct_units": [...]    // 南网直属单位列表
  }
}
```

#### 获取单位政策详情
```javascript
GET /api/v1/policies/unit-details?org_id=19

Response:
{
  "success": true,
  "data": {
    "org_info": {...},          // 组织基本信息
    "policy_info": {...},       // 政策详情（按可配置字段返回）
    "detailed_rules": [...],    // 详细规则列表
    "display_fields": [...]     // 展示字段配置
  }
}
```

#### 按批次获取学校统计
```javascript
GET /api/v1/analytics/schools-by-batch?org_id=19&batch=一批&page=1&limit=20

Response:
{
  "success": true,
  "data": {
    "schools": [...],           // 学校统计列表
    "pagination": {...},        // 分页信息
    "summary": {...}           // 统计摘要
  }
}
```

## 核心特性

### 1. 筛选器互斥逻辑
- 四个筛选项（国网省公司、国网直属单位、南网省公司、南网直属单位）互斥
- 选择一项时自动清空其他项
- 后端API支持单一组织ID筛选

### 2. 动态配置展示
- display_config表支持动态配置页面展示字段
- 支持字段启用/禁用、排序、类型定义
- 前端可以根据配置动态渲染界面

### 3. 层级化数据展示
- 支持省级汇总 → 市级汇总 → 区县详情的层级展示
- 数据粒度从粗到细，满足不同查询需求

### 4. 批次关联筛选
- 左侧选择组织 → 右侧默认显示该组织全部录取分析
- 右侧批次筛选 → 显示对应批次的录取情况
- 支持一批、二批、三批的独立分析

### 5. 专门化政策管理
- 提前批政策和农网政策分表存储
- 每个专门政策都有独立的字段和展示配置
- 支持政策的精细化管理

## 性能优化

### 1. 索引策略
- 组织类型索引优化筛选查询
- 组合索引支持常用查询模式
- 分页查询优化

### 2. 查询优化
- 使用视图简化复杂查询
- 合理的JOIN操作减少数据传输
- 分页和限制结果集大小

### 3. 缓存策略（建议）
- 组织结构数据（长期缓存）
- 政策规则数据（中期缓存）
- 统计数据（短期缓存）

## 扩展性设计

### 1. 新增组织类型
只需在organizations表中添加新的org_type枚举值即可

### 2. 新增政策字段
- 在policy_rules表中添加字段
- 在display_config表中配置展示
- API自动支持新字段

### 3. 新增批次类型
在batch_admission_stats表的batch_type枚举中添加即可

## 数据迁移建议

### 从现有系统迁移
1. 分析现有recruitment_records和recruitment_rules表结构
2. 编写数据转换脚本将现有数据映射到新架构
3. 保持向后兼容性，渐进式迁移

### 数据验证
- 确保组织层级关系正确
- 验证政策数据完整性
- 检查统计数据准确性

## 监控和维护

### 1. 健康检查
- /api/v1/policies/health
- /api/v1/analytics/health
- 监控数据库连接和表结构

### 2. 日志记录
- API请求日志
- 数据库操作日志
- 错误日志跟踪

### 3. 性能监控
- 接口响应时间
- 数据库查询性能
- 并发请求处理能力

## 总结

这个优化方案通过重新设计数据库架构和API接口，完美支持了data-query页面的新需求：

1. **清晰的架构**: 专门化的表结构和API设计
2. **灵活的配置**: 支持动态字段配置和展示控制  
3. **高效的查询**: 优化的索引和查询策略
4. **良好的扩展性**: 易于添加新功能和字段
5. **完整的功能**: 覆盖左右两栏的所有功能需求

该方案为data-query页面提供了强大而灵活的后端支持，能够满足当前需求并为未来扩展提供良好基础。
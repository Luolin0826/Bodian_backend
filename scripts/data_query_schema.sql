-- ========================================
-- Data-Query 页面优化数据库架构设计
-- 支持左右两栏布局的完整政策查询和学校录取统计
-- ========================================

-- 创建数据查一点通优化数据库
CREATE DATABASE IF NOT EXISTS data_query_optimized DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE data_query_optimized;

-- ========================================
-- 1. 组织架构表 (organizations)
-- 支持国网/南网的省公司和直属单位层级管理
-- ========================================
CREATE TABLE organizations (
    org_id INT PRIMARY KEY AUTO_INCREMENT,
    org_code VARCHAR(20) UNIQUE NOT NULL COMMENT '组织编码，如GW_SC, NW_GD等',
    org_name VARCHAR(100) NOT NULL COMMENT '组织名称，如国网四川、南网广东',
    org_type ENUM('国网省公司', '国网直属单位', '南网省公司', '南网直属单位') NOT NULL COMMENT '组织类型',
    parent_org_id INT COMMENT '父级组织ID，支持层级关系',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    sort_order INT DEFAULT 0 COMMENT '排序权重',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_org_id) REFERENCES organizations(org_id) ON DELETE SET NULL,
    INDEX idx_org_type (org_type),
    INDEX idx_parent (parent_org_id),
    INDEX idx_active (is_active)
) COMMENT='组织架构表，支持国网/南网层级管理';

-- ========================================
-- 2. 地区单位表 (regional_units)
-- 存储省、市、区县级别的具体单位信息
-- ========================================
CREATE TABLE regional_units (
    unit_id INT PRIMARY KEY AUTO_INCREMENT,
    org_id INT NOT NULL COMMENT '关联组织ID',
    province VARCHAR(50) COMMENT '省份',
    city VARCHAR(50) COMMENT '地级市', 
    district VARCHAR(100) COMMENT '区县/具体单位名称',
    unit_level ENUM('省级', '市级', '区县级') NOT NULL COMMENT '单位层级',
    unit_full_name VARCHAR(200) COMMENT '单位全称',
    
    -- 薪资和录取信息
    salary_range VARCHAR(50) COMMENT '薪资范围，如8-12万',
    estimated_score_range VARCHAR(50) COMMENT '预估上岸分数范围',
    apply_status VARCHAR(100) COMMENT '网申情况描述',
    
    -- 地理和发展信息
    economic_level ENUM('发达', '一般', '欠发达') DEFAULT '一般' COMMENT '经济发展水平',
    is_key_city BOOLEAN DEFAULT FALSE COMMENT '是否重点城市',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    INDEX idx_org_level (org_id, unit_level),
    INDEX idx_location (province, city),
    INDEX idx_full_name (unit_full_name)
) COMMENT='地区单位表，存储具体的省市区县单位信息';

-- ========================================
-- 3. 政策规则表 (policy_rules)
-- 存储详细的录取政策规则信息
-- ========================================
CREATE TABLE policy_rules (
    rule_id INT PRIMARY KEY AUTO_INCREMENT,
    org_id INT NOT NULL COMMENT '关联组织ID',
    unit_id INT COMMENT '关联具体单位ID，为空表示全省规则',
    
    -- 基本录取信息
    recruitment_count INT COMMENT '录取人数',
    unwritten_rules TEXT COMMENT '网申不成文规定',
    english_requirement VARCHAR(50) COMMENT '英语等级要求',
    computer_requirement VARCHAR(50) COMMENT '计算机等级要求', 
    age_requirement VARCHAR(50) COMMENT '年龄要求',
    
    -- 政策规则
    second_choice_available BOOLEAN COMMENT '是否有二次志愿填报',
    household_priority VARCHAR(50) COMMENT '是否非常看重户籍',
    major_consistency_required BOOLEAN COMMENT '本硕专业不一致可否通过网申',
    written_test_score_line DECIMAL(5,2) COMMENT '笔试分数线',
    detailed_admission_rules TEXT COMMENT '详细录取规则',
    comprehensive_score_line DECIMAL(5,2) COMMENT '综合分数线',
    position_selection_method TEXT COMMENT '具体选岗方式',
    
    -- 特殊情况处理
    first_batch_fail_second_ok BOOLEAN COMMENT '一批进面没录取可以正常报考二批吗',
    deferred_graduation_impact VARCHAR(100) COMMENT '延毕休学影响网申吗',
    non_first_choice_pass BOOLEAN COMMENT '非第一志愿是否通过网申',
    campus_recruit_then_batch VARCHAR(100) COMMENT '校招给了地方但是不满意是否还可以参加一批',
    
    -- 证书和资格要求
    single_cert_probability TEXT COMMENT '有一个证书网申概率',
    qualification_review_requirements TEXT COMMENT '资格审查三方要求',
    application_ratio VARCHAR(50) COMMENT '报录比',
    
    -- 性价比和排行
    cost_effectiveness_rank INT COMMENT '性价比排行',
    best_value_city_rank INT COMMENT '性价比最高的市局排行',
    best_value_district_rank INT COMMENT '每个市下辖性价比最高的区县排行',
    difficulty_rank INT COMMENT '笔试难度排行',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    FOREIGN KEY (unit_id) REFERENCES regional_units(unit_id) ON DELETE CASCADE,
    INDEX idx_org_unit (org_id, unit_id),
    INDEX idx_org_only (org_id)
) COMMENT='政策规则表，存储详细的录取政策信息';

-- ========================================
-- 4. 提前批政策表 (early_batch_policies)
-- 专门存储提前批相关的政策信息
-- ========================================
CREATE TABLE early_batch_policies (
    policy_id INT PRIMARY KEY AUTO_INCREMENT,
    org_id INT NOT NULL COMMENT '关联组织ID',
    
    -- 提前批基本信息
    schedule_arrangement TEXT COMMENT '行程安排',
    education_requirement VARCHAR(100) COMMENT '学历要求',
    written_test_required BOOLEAN DEFAULT FALSE COMMENT '是否需要笔试',
    written_test_content TEXT COMMENT '笔试内容描述',
    
    -- 提前批特色
    station_chasing_allowed BOOLEAN DEFAULT FALSE COMMENT '能否追站',
    admission_factors TEXT COMMENT '录用影响因素',
    unit_admission_status TEXT COMMENT '各单位录用情况',
    difficulty_ranking TEXT COMMENT '难度排行',
    position_quality_difference TEXT COMMENT '提前批岗位和一二批岗位质量有什么差异',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    INDEX idx_org (org_id)
) COMMENT='提前批政策表，存储提前批专门政策信息';

-- ========================================
-- 5. 农网政策表 (rural_grid_policies) 
-- 专门存储农网相关的政策信息
-- ========================================
CREATE TABLE rural_grid_policies (
    policy_id INT PRIMARY KEY AUTO_INCREMENT,
    org_id INT NOT NULL COMMENT '关联组织ID',
    
    -- 农网基本信息
    salary_benefits VARCHAR(200) COMMENT '农网待遇',
    exam_schedule VARCHAR(100) COMMENT '考试时间',
    age_requirement VARCHAR(50) COMMENT '年龄要求',
    application_status VARCHAR(100) COMMENT '网申情况',
    
    -- 农网考试评估
    online_assessment TEXT COMMENT '线上测评内容',
    personality_test TEXT COMMENT '性格测试要求',
    qualification_review TEXT COMMENT '资格审查要求',
    written_test_content TEXT COMMENT '笔试内容',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    INDEX idx_org (org_id)
) COMMENT='农网政策表，存储农网专门政策信息';

-- ========================================
-- 6. 批次录取统计表 (batch_admission_stats)
-- 存储按批次的学校录取统计数据
-- ========================================
CREATE TABLE batch_admission_stats (
    stat_id INT PRIMARY KEY AUTO_INCREMENT,
    org_id INT NOT NULL COMMENT '关联组织ID',
    batch_type ENUM('一批', '二批', '三批') NOT NULL COMMENT '批次类型',
    university_id INT NOT NULL COMMENT '大学ID，关联现有universities表',
    
    -- 录取统计数据
    admission_count INT DEFAULT 0 COMMENT '录取人数',
    application_count INT DEFAULT 0 COMMENT '申请人数',
    admission_rate DECIMAL(5,2) COMMENT '录取率',
    
    -- 成绩统计
    min_score DECIMAL(5,2) COMMENT '最低录取分',
    max_score DECIMAL(5,2) COMMENT '最高录取分',
    avg_score DECIMAL(5,2) COMMENT '平均录取分',
    
    -- 时间信息
    admission_year YEAR NOT NULL COMMENT '录取年份',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    -- FOREIGN KEY (university_id) REFERENCES universities(university_id), -- 引用现有表
    INDEX idx_org_batch (org_id, batch_type),
    INDEX idx_year (admission_year),
    INDEX idx_university (university_id)
) COMMENT='批次录取统计表，存储不同批次的学校录取数据';

-- ========================================
-- 7. 可配置展示字段表 (display_config)
-- 支持页面展示字段的动态配置
-- ========================================
CREATE TABLE display_config (
    config_id INT PRIMARY KEY AUTO_INCREMENT,
    field_category ENUM('基本信息', '提前批', '农网', '地市县信息') NOT NULL COMMENT '字段分类',
    field_name VARCHAR(100) NOT NULL COMMENT '字段名称（数据库字段名）',
    display_name VARCHAR(100) NOT NULL COMMENT '显示名称',
    field_type ENUM('text', 'number', 'boolean', 'select', 'textarea') NOT NULL COMMENT '字段类型',
    
    -- 显示控制
    display_order INT DEFAULT 0 COMMENT '显示顺序',
    is_enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用显示',
    is_required BOOLEAN DEFAULT FALSE COMMENT '是否必填',
    is_searchable BOOLEAN DEFAULT FALSE COMMENT '是否可搜索',
    
    -- 字段配置
    field_description TEXT COMMENT '字段说明',
    default_value VARCHAR(200) COMMENT '默认值',
    validation_rules JSON COMMENT '验证规则（JSON格式）',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_category (field_category),
    INDEX idx_enabled (is_enabled),
    INDEX idx_order (display_order)
) COMMENT='可配置展示字段表，支持动态配置页面显示内容';

-- ========================================
-- 8. 创建视图简化常用查询
-- ========================================

-- 组织完整信息视图
CREATE VIEW v_org_full_info AS
SELECT 
    o.org_id,
    o.org_code,
    o.org_name,
    o.org_type,
    po.org_name AS parent_org_name,
    o.is_active
FROM organizations o
LEFT JOIN organizations po ON o.parent_org_id = po.org_id
WHERE o.is_active = TRUE;

-- 政策规则完整视图
CREATE VIEW v_policy_full AS
SELECT 
    pr.rule_id,
    o.org_name,
    o.org_type,
    ru.unit_full_name,
    ru.province,
    ru.city,
    ru.district,
    pr.recruitment_count,
    pr.english_requirement,
    pr.computer_requirement,
    pr.age_requirement,
    pr.written_test_score_line,
    pr.comprehensive_score_line,
    pr.cost_effectiveness_rank
FROM policy_rules pr
JOIN organizations o ON pr.org_id = o.org_id
LEFT JOIN regional_units ru ON pr.unit_id = ru.unit_id
WHERE o.is_active = TRUE;

-- 地市县概览视图
CREATE VIEW v_regional_overview AS
SELECT 
    ru.unit_id,
    o.org_name,
    o.org_type,
    ru.province,
    ru.city,
    ru.district AS county,
    ru.apply_status,
    ru.salary_range,
    ru.estimated_score_range
FROM regional_units ru
JOIN organizations o ON ru.org_id = o.org_id
WHERE o.is_active = TRUE
ORDER BY o.org_type, ru.province, ru.city, ru.district;

-- ========================================
-- 9. 初始化基础数据
-- ========================================

-- 插入国网省公司数据
INSERT INTO organizations (org_code, org_name, org_type, sort_order) VALUES 
('GW_BJ', '国家电网北京电力公司', '国网省公司', 1),
('GW_TJ', '国家电网天津电力公司', '国网省公司', 2),
('GW_HEB', '国家电网河北电力公司', '国网省公司', 3),
('GW_SX', '国家电网山西电力公司', '国网省公司', 4),
('GW_NMG', '国家电网内蒙古电力公司', '国网省公司', 5),
('GW_LN', '国家电网辽宁电力公司', '国网省公司', 6),
('GW_JL', '国家电网吉林电力公司', '国网省公司', 7),
('GW_HLJ', '国家电网黑龙江电力公司', '国网省公司', 8),
('GW_SH', '国家电网上海电力公司', '国网省公司', 9),
('GW_JS', '国家电网江苏电力公司', '国网省公司', 10),
('GW_ZJ', '国家电网浙江电力公司', '国网省公司', 11),
('GW_AH', '国家电网安徽电力公司', '国网省公司', 12),
('GW_FJ', '国家电网福建电力公司', '国网省公司', 13),
('GW_JX', '国家电网江西电力公司', '国网省公司', 14),
('GW_SD', '国家电网山东电力公司', '国网省公司', 15),
('GW_HEN', '国家电网河南电力公司', '国网省公司', 16),
('GW_HUB', '国家电网湖北电力公司', '国网省公司', 17),
('GW_HUN', '国家电网湖南电力公司', '国网省公司', 18),
('GW_SC', '国家电网四川电力公司', '国网省公司', 19),
('GW_CQ', '国家电网重庆电力公司', '国网省公司', 20),
('GW_SAX', '国家电网陕西电力公司', '国网省公司', 21),
('GW_GS', '国家电网甘肃电力公司', '国网省公司', 22),
('GW_QH', '国家电网青海电力公司', '国网省公司', 23),
('GW_NX', '国家电网宁夏电力公司', '国网省公司', 24),
('GW_XJ', '国家电网新疆电力公司', '国网省公司', 25);

-- 插入国网直属单位数据
INSERT INTO organizations (org_code, org_name, org_type, sort_order) VALUES 
('GW_HQ', '国家电网总部', '国网直属单位', 101),
('GW_SGRI', '国网电科院', '国网直属单位', 102),
('GW_NARI', '国电南瑞', '国网直属单位', 103),
('GW_EPRI', '国网经研院', '国网直属单位', 104),
('GW_INFO', '国网信通', '国网直属单位', 105),
('GW_FINANCE', '英大集团', '国网直属单位', 106);

-- 插入南网省公司数据
INSERT INTO organizations (org_code, org_name, org_type, sort_order) VALUES 
('NW_GD', '南方电网广东电网公司', '南网省公司', 201),
('NW_GX', '南方电网广西电网公司', '南网省公司', 202),
('NW_YN', '南方电网云南电网公司', '南网省公司', 203),
('NW_GZ', '南方电网贵州电网公司', '南网省公司', 204),
('NW_HAN', '南方电网海南电网公司', '南网省公司', 205);

-- 插入南网直属单位数据
INSERT INTO organizations (org_code, org_name, org_type, sort_order) VALUES 
('NW_HQ', '南方电网总部', '南网直属单位', 301),
('NW_CSRI', '南网科研院', '南网直属单位', 302),
('NW_DIGITAL', '南网数研院', '南网直属单位', 303),
('NW_SUPER', '超高压公司', '南网直属单位', 304);

-- 插入可配置展示字段的基础数据
INSERT INTO display_config (field_category, field_name, display_name, field_type, display_order, is_enabled) VALUES 
('基本信息', 'recruitment_count', '录取人数', 'number', 1, TRUE),
('基本信息', 'unwritten_rules', '网申不成文规定', 'textarea', 2, TRUE),
('基本信息', 'english_requirement', '英语等级', 'text', 3, TRUE),
('基本信息', 'computer_requirement', '计算机等级', 'text', 4, TRUE),
('基本信息', 'age_requirement', '年龄要求', 'text', 5, TRUE),
('基本信息', 'second_choice_available', '是否有二次志愿填报', 'boolean', 6, TRUE),
('基本信息', 'household_priority', '是否非常看重户籍', 'text', 7, TRUE),
('基本信息', 'major_consistency_required', '本硕专业不一致可否通过网申', 'boolean', 8, TRUE),
('基本信息', 'written_test_score_line', '笔试分数线', 'number', 9, TRUE),
('基本信息', 'detailed_admission_rules', '详细录取规则', 'textarea', 10, TRUE),
('基本信息', 'comprehensive_score_line', '综合分数线', 'number', 11, TRUE),
('基本信息', 'position_selection_method', '具体选岗方式', 'textarea', 12, TRUE),
('基本信息', 'first_batch_fail_second_ok', '一批进面没录取可以正常报考二批吗', 'boolean', 13, TRUE),
('基本信息', 'deferred_graduation_impact', '延毕休学影响网申吗', 'text', 14, TRUE),
('基本信息', 'non_first_choice_pass', '非第一志愿是否通过网申', 'boolean', 15, TRUE),
('基本信息', 'campus_recruit_then_batch', '校招给了地方但是不满意是否还可以参加一批', 'text', 16, TRUE),
('基本信息', 'single_cert_probability', '有一个证书网申概率', 'textarea', 17, TRUE),
('基本信息', 'cost_effectiveness_rank', '性价比最高的市局', 'number', 18, TRUE),
('基本信息', 'best_value_district_rank', '每个市下辖性价比最高的区县', 'number', 19, TRUE),
('基本信息', 'difficulty_rank', '笔试难度排行', 'number', 20, TRUE),
('基本信息', 'qualification_review_requirements', '资格审查三方', 'textarea', 21, TRUE),
('基本信息', 'application_ratio', '报录比', 'text', 22, TRUE),
('基本信息', 'best_value_city_rank', '本科进市局', 'number', 23, TRUE);

INSERT INTO display_config (field_category, field_name, display_name, field_type, display_order, is_enabled) VALUES 
('提前批', 'schedule_arrangement', '行程安排', 'textarea', 1, TRUE),
('提前批', 'education_requirement', '学历要求', 'text', 2, TRUE),
('提前批', 'written_test_required', '是否笔试及笔试内容', 'boolean', 3, TRUE),
('提前批', 'written_test_content', '笔试内容', 'textarea', 4, TRUE),
('提前批', 'station_chasing_allowed', '能否追站', 'boolean', 5, TRUE),
('提前批', 'admission_factors', '录用影响因素', 'textarea', 6, TRUE),
('提前批', 'unit_admission_status', '各单位录用情况', 'textarea', 7, TRUE),
('提前批', 'difficulty_ranking', '难度排行', 'textarea', 8, TRUE),
('提前批', 'position_quality_difference', '提前批岗位和一二批岗位质量有什么差异', 'textarea', 9, TRUE);

INSERT INTO display_config (field_category, field_name, display_name, field_type, display_order, is_enabled) VALUES 
('农网', 'salary_benefits', '农网待遇', 'text', 1, TRUE),
('农网', 'exam_schedule', '考试时间', 'text', 2, TRUE),
('农网', 'age_requirement', '年龄要求', 'text', 3, TRUE),
('农网', 'application_status', '网申情况', 'text', 4, TRUE),
('农网', 'online_assessment', '线上测评', 'textarea', 5, TRUE),
('农网', 'personality_test', '性格测试', 'textarea', 6, TRUE),
('农网', 'qualification_review', '资格审查', 'textarea', 7, TRUE),
('农网', 'written_test_content', '笔试内容', 'textarea', 8, TRUE);

INSERT INTO display_config (field_category, field_name, display_name, field_type, display_order, is_enabled) VALUES 
('地市县信息', 'city', '地市', 'text', 1, TRUE),
('地市县信息', 'county', '县', 'text', 2, TRUE),
('地市县信息', 'apply_status', '网申情况', 'text', 3, TRUE),
('地市县信息', 'salary_range', '薪资待遇', 'text', 4, TRUE),
('地市县信息', 'estimated_score_range', '预估上岸分数', 'text', 5, TRUE);

-- 创建索引优化查询性能
CREATE INDEX idx_policy_org_type ON policy_rules(org_id) USING BTREE;
CREATE INDEX idx_batch_stats_composite ON batch_admission_stats(org_id, batch_type, admission_year) USING BTREE;
CREATE INDEX idx_regional_units_location ON regional_units(province, city) USING BTREE;

-- 显示所有创建的表
SHOW TABLES;
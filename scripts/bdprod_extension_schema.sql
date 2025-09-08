-- ========================================
-- Data-Query页面 - 基于现有bdprod数据库的扩展方案
-- 利用现有secondary_units和recruitment_records表，添加政策管理功能
-- ========================================

USE bdprod;

-- ========================================
-- 1. 扩展secondary_units表结构
-- ========================================

-- 添加组织类型字段
ALTER TABLE secondary_units 
ADD COLUMN org_type ENUM('国网省公司', '国网直属单位', '南网省公司', '南网直属单位') 
AFTER unit_type COMMENT '组织类型分类';

-- 添加父级单位字段（支持层级关系）
ALTER TABLE secondary_units 
ADD COLUMN parent_unit_id INT 
AFTER unit_id COMMENT '父级单位ID';

-- 添加排序权重字段
ALTER TABLE secondary_units 
ADD COLUMN sort_order INT DEFAULT 0 
AFTER parent_unit_id COMMENT '显示排序权重';

-- 添加扩展信息字段
ALTER TABLE secondary_units 
ADD COLUMN salary_range VARCHAR(50) 
AFTER recruitment_count COMMENT '薪资范围';

ALTER TABLE secondary_units 
ADD COLUMN estimated_score_range VARCHAR(50) 
AFTER salary_range COMMENT '预估上岸分数范围';

ALTER TABLE secondary_units 
ADD COLUMN apply_status VARCHAR(100) 
AFTER estimated_score_range COMMENT '网申情况描述';

ALTER TABLE secondary_units 
ADD COLUMN economic_level ENUM('发达', '一般', '欠发达') DEFAULT '一般' 
AFTER apply_status COMMENT '经济发展水平';

ALTER TABLE secondary_units 
ADD COLUMN is_key_city BOOLEAN DEFAULT FALSE 
AFTER economic_level COMMENT '是否重点城市';

-- 添加索引优化查询
CREATE INDEX idx_org_type ON secondary_units(org_type);
CREATE INDEX idx_parent_unit ON secondary_units(parent_unit_id);

-- ========================================
-- 2. 根据现有数据自动分类组织类型
-- ========================================

-- 南网省公司（region='南方'且为省级电网公司）
UPDATE secondary_units 
SET org_type = '南网省公司', sort_order = 201 
WHERE region = '南方' AND unit_type = '省级电网公司';

-- 国网省公司（非南方region且为省级电网公司）
UPDATE secondary_units 
SET org_type = '国网省公司', 
    sort_order = CASE 
        WHEN region = '华北' THEN 1
        WHEN region = '华东' THEN 10  
        WHEN region = '华中' THEN 20
        WHEN region = '东北' THEN 30
        WHEN region = '西北' THEN 40
        WHEN region = '西南' THEN 50
        ELSE 60
    END + unit_id
WHERE region != '南方' AND unit_type = '省级电网公司';

-- 国网直属单位
UPDATE secondary_units 
SET org_type = '国网直属单位', sort_order = 100 + unit_id
WHERE unit_type IN ('科研院所', '超高压公司') OR 
      (unit_type = '其他单位' AND region != '南方');

-- 南网直属单位  
UPDATE secondary_units 
SET org_type = '南网直属单位', sort_order = 300 + unit_id
WHERE unit_type = '其他单位' AND region = '南方';

-- ========================================
-- 3. 政策规则扩展表
-- ========================================
CREATE TABLE policy_rules_extended (
    rule_id INT PRIMARY KEY AUTO_INCREMENT,
    unit_id INT NOT NULL COMMENT '关联secondary_units表的unit_id',
    
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
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 外键约束和索引
    FOREIGN KEY (unit_id) REFERENCES secondary_units(unit_id) ON DELETE CASCADE,
    INDEX idx_unit_id (unit_id)
) COMMENT='政策规则扩展表，关联secondary_units表';

-- ========================================
-- 4. 提前批政策扩展表
-- ========================================
CREATE TABLE early_batch_policies_extended (
    policy_id INT PRIMARY KEY AUTO_INCREMENT,
    unit_id INT NOT NULL COMMENT '关联secondary_units表的unit_id',
    
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
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 外键约束和索引
    FOREIGN KEY (unit_id) REFERENCES secondary_units(unit_id) ON DELETE CASCADE,
    INDEX idx_unit_id (unit_id)
) COMMENT='提前批政策扩展表，关联secondary_units表';

-- ========================================
-- 5. 农网政策扩展表
-- ========================================
CREATE TABLE rural_grid_policies_extended (
    policy_id INT PRIMARY KEY AUTO_INCREMENT,
    unit_id INT NOT NULL COMMENT '关联secondary_units表的unit_id',
    
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
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 外键约束和索引
    FOREIGN KEY (unit_id) REFERENCES secondary_units(unit_id) ON DELETE CASCADE,
    INDEX idx_unit_id (unit_id)
) COMMENT='农网政策扩展表，关联secondary_units表';

-- ========================================
-- 6. 可配置展示字段表
-- ========================================
CREATE TABLE display_config_extended (
    config_id INT PRIMARY KEY AUTO_INCREMENT,
    field_category ENUM('基本信息', '提前批', '农网', '地市县信息') NOT NULL COMMENT '字段分类',
    field_name VARCHAR(100) NOT NULL COMMENT '数据库字段名',
    display_name VARCHAR(100) NOT NULL COMMENT '前端显示名称',
    field_type ENUM('text', 'number', 'boolean', 'textarea', 'select') NOT NULL COMMENT '字段类型',
    display_order INT DEFAULT 0 COMMENT '显示顺序',
    is_enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用显示',
    is_required BOOLEAN DEFAULT FALSE COMMENT '是否必填',
    is_editable BOOLEAN DEFAULT TRUE COMMENT '是否可编辑',
    field_description TEXT COMMENT '字段说明',
    default_value VARCHAR(200) COMMENT '默认值',
    validation_rules JSON COMMENT '验证规则（JSON格式）',
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 索引
    INDEX idx_category_order (field_category, display_order),
    INDEX idx_enabled (is_enabled)
) COMMENT='可配置展示字段表，支持动态配置页面显示内容';

-- ========================================
-- 7. 创建视图简化查询
-- ========================================

-- 完整单位信息视图
CREATE VIEW v_units_full_info AS
SELECT 
    su.unit_id,
    su.unit_code,
    su.unit_name,
    su.unit_type,
    su.org_type,
    su.region,
    su.recruitment_count,
    su.salary_range,
    su.estimated_score_range,
    su.apply_status,
    su.economic_level,
    su.is_key_city,
    su.is_active,
    psu.unit_name AS parent_unit_name
FROM secondary_units su
LEFT JOIN secondary_units psu ON su.parent_unit_id = psu.unit_id
WHERE su.is_active = 1;

-- 政策规则完整信息视图
CREATE VIEW v_policy_rules_full AS
SELECT 
    pr.rule_id,
    su.unit_id,
    su.unit_name,
    su.org_type,
    su.region,
    pr.recruitment_count,
    pr.english_requirement,
    pr.computer_requirement,
    pr.age_requirement,
    pr.written_test_score_line,
    pr.comprehensive_score_line,
    pr.cost_effectiveness_rank,
    pr.difficulty_rank
FROM policy_rules_extended pr
JOIN secondary_units su ON pr.unit_id = su.unit_id
WHERE su.is_active = 1;

-- 录取统计完整信息视图（基于现有数据）
CREATE VIEW v_recruitment_stats_full AS
SELECT 
    su.unit_id,
    su.unit_name,
    su.org_type,
    su.region,
    rr.batch,
    rr.gender,
    u.standard_name as university_name,
    u.level as university_level,
    COUNT(*) as admission_count
FROM secondary_units su
JOIN recruitment_records rr ON su.unit_id = rr.secondary_unit_id
LEFT JOIN universities u ON rr.university_id = u.university_id
WHERE su.is_active = 1
GROUP BY su.unit_id, su.unit_name, su.org_type, su.region, 
         rr.batch, rr.gender, u.university_id, u.standard_name, u.level;

-- ========================================
-- 8. 初始化基本信息板块字段配置
-- ========================================
INSERT INTO display_config_extended (field_category, field_name, display_name, field_type, display_order, is_enabled, field_description) VALUES 
('基本信息', 'recruitment_count', '录取人数', 'number', 1, TRUE, '该单位年度录取总人数'),
('基本信息', 'unwritten_rules', '网申不成文规定', 'textarea', 2, TRUE, '网申过程中的潜规则和注意事项'),
('基本信息', 'english_requirement', '英语等级', 'select', 3, TRUE, '四六级等英语证书要求'),
('基本信息', 'computer_requirement', '计算机等级', 'select', 4, TRUE, '计算机等级证书要求'),
('基本信息', 'age_requirement', '年龄要求', 'text', 5, TRUE, '应聘者年龄限制要求'),
('基本信息', 'first_batch_fail_second_ok', '一批进面没录取可以正常报考二批吗', 'boolean', 6, TRUE, '批次间的报考政策'),
('基本信息', 'deferred_graduation_impact', '延毕休学影响网申吗', 'text', 7, TRUE, '学历异常情况的影响'),
('基本信息', 'household_priority', '是否非常看重户籍', 'select', 8, TRUE, '户籍要求的严格程度'),
('基本信息', 'major_consistency_required', '本硕专业不一致可否通过网申', 'boolean', 9, TRUE, '专业匹配度要求'),
('基本信息', 'written_test_score_line', '笔试分数线', 'number', 10, TRUE, '笔试最低录取分数'),
('基本信息', 'detailed_admission_rules', '详细录取规则', 'textarea', 11, TRUE, '完整的录取政策说明'),
('基本信息', 'comprehensive_score_line', '综合分数线', 'number', 12, TRUE, '综合评分最低线'),
('基本信息', 'position_selection_method', '具体选岗方式', 'textarea', 13, TRUE, '岗位分配的具体流程'),
('基本信息', 'non_first_choice_pass', '非第一志愿是否通过网申', 'boolean', 14, TRUE, '志愿优先级政策'),
('基本信息', 'campus_recruit_then_batch', '校招给了地方但是不满意是否还可以参加一批', 'text', 15, TRUE, '校招与统招的关系'),
('基本信息', 'single_cert_probability', '有一个证书网申概率', 'textarea', 16, TRUE, '证书对网申通过率的影响'),
('基本信息', 'cost_effectiveness_rank', '性价比最高的市局', 'number', 17, TRUE, '市局性价比排名'),
('基本信息', 'best_value_district_rank', '每个市下辖性价比最高的区县', 'textarea', 18, TRUE, '区县性价比分析'),
('基本信息', 'difficulty_rank', '笔试难度排行', 'number', 19, TRUE, '笔试难度等级'),
('基本信息', 'qualification_review_requirements', '资格审查三方', 'textarea', 20, TRUE, '资格审查所需材料'),
('基本信息', 'application_ratio', '报录比', 'text', 21, TRUE, '报名与录取人数比例'),
('基本信息', 'second_choice_available', '是否有二次志愿填报', 'boolean', 22, TRUE, '二次填报机会'),
('基本信息', 'best_value_city_rank', '本科进市局', 'number', 23, TRUE, '本科进入市局的难度排名');

-- ========================================
-- 9. 初始化提前批板块字段配置
-- ========================================
INSERT INTO display_config_extended (field_category, field_name, display_name, field_type, display_order, is_enabled, field_description) VALUES 
('提前批', 'schedule_arrangement', '行程安排', 'textarea', 1, TRUE, '提前批面试的时间和流程安排'),
('提前批', 'education_requirement', '学历要求', 'text', 2, TRUE, '提前批的学历门槛要求'),
('提前批', 'written_test_required', '是否笔试及笔试内容', 'boolean', 3, TRUE, '是否需要参加笔试'),
('提前批', 'written_test_content', '笔试内容', 'textarea', 4, TRUE, '笔试的具体内容和范围'),
('提前批', 'station_chasing_allowed', '能否追站', 'boolean', 5, TRUE, '是否允许跨地区面试'),
('提前批', 'admission_factors', '录用影响因素', 'textarea', 6, TRUE, '影响录用结果的关键因素'),
('提前批', 'unit_admission_status', '各单位录用情况', 'textarea', 7, TRUE, '不同单位的录用标准和情况'),
('提前批', 'difficulty_ranking', '难度排行', 'textarea', 8, TRUE, '各单位提前批难度排名'),
('提前批', 'position_quality_difference', '提前批岗位和一二批岗位质量有什么差异', 'textarea', 9, TRUE, '不同批次岗位的对比分析');

-- ========================================
-- 10. 初始化农网板块字段配置
-- ========================================
INSERT INTO display_config_extended (field_category, field_name, display_name, field_type, display_order, is_enabled, field_description) VALUES 
('农网', 'salary_benefits', '农网待遇', 'text', 1, TRUE, '农网岗位的薪资福利情况'),
('农网', 'exam_schedule', '考试时间', 'text', 2, TRUE, '农网招聘考试的时间安排'),
('农网', 'age_requirement', '年龄要求', 'text', 3, TRUE, '农网岗位的年龄限制'),
('农网', 'application_status', '网申情况', 'text', 4, TRUE, '农网岗位网申的通过情况'),
('农网', 'online_assessment', '线上测评', 'textarea', 5, TRUE, '线上测评的内容和要求'),
('农网', 'personality_test', '性格测试', 'textarea', 6, TRUE, '性格测试的内容和评判标准'),
('农网', 'qualification_review', '资格审查', 'textarea', 7, TRUE, '农网岗位的资格审查要求'),
('农网', 'written_test_content', '笔试内容', 'textarea', 8, TRUE, '农网笔试的具体内容');

-- ========================================
-- 11. 初始化地市县信息板块字段配置
-- ========================================
INSERT INTO display_config_extended (field_category, field_name, display_name, field_type, display_order, is_enabled, field_description) VALUES 
('地市县信息', 'unit_name', '地市', 'text', 1, TRUE, '地级市名称'),
('地市县信息', 'region', '区域', 'text', 2, TRUE, '所属区域'),
('地市县信息', 'apply_status', '网申情况', 'text', 3, TRUE, '该地区网申通过难度'),
('地市县信息', 'salary_range', '薪资待遇', 'text', 4, TRUE, '该地区薪资水平'),
('地市县信息', 'estimated_score_range', '预估上岸分数', 'text', 5, TRUE, '预计录取分数范围');

-- ========================================
-- 12. 显示创建的表和视图
-- ========================================
SHOW TABLES LIKE '%extended';
SHOW FULL TABLES WHERE Table_type = 'VIEW' AND Tables_in_bdprod LIKE 'v_%';

-- 查看secondary_units表的新结构
DESCRIBE secondary_units;
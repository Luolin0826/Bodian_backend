USE bdprod;

-- Add additional columns to secondary_units
ALTER TABLE secondary_units ADD COLUMN parent_unit_id INT AFTER unit_id;
ALTER TABLE secondary_units ADD COLUMN sort_order INT DEFAULT 0 AFTER parent_unit_id;
ALTER TABLE secondary_units ADD COLUMN salary_range VARCHAR(50) AFTER recruitment_count;
ALTER TABLE secondary_units ADD COLUMN estimated_score_range VARCHAR(50) AFTER salary_range;
ALTER TABLE secondary_units ADD COLUMN apply_status VARCHAR(100) AFTER estimated_score_range;
ALTER TABLE secondary_units ADD COLUMN economic_level ENUM('发达', '一般', '欠发达') DEFAULT '一般' AFTER apply_status;
ALTER TABLE secondary_units ADD COLUMN is_key_city BOOLEAN DEFAULT FALSE AFTER economic_level;

-- Create indexes
CREATE INDEX idx_org_type ON secondary_units(org_type);
CREATE INDEX idx_parent_unit ON secondary_units(parent_unit_id);

-- Update existing data with org_type classification
UPDATE secondary_units SET org_type = '南网省公司', sort_order = 201 WHERE region = '南方' AND unit_type = '省级电网公司';
UPDATE secondary_units SET org_type = '国网省公司', sort_order = 1 WHERE region != '南方' AND unit_type = '省级电网公司';
UPDATE secondary_units SET org_type = '国网直属单位', sort_order = 100 WHERE unit_type IN ('科研院所', '超高压公司') OR (unit_type = '其他单位' AND region != '南方');
UPDATE secondary_units SET org_type = '南网直属单位', sort_order = 300 WHERE unit_type = '其他单位' AND region = '南方';

-- Create extension tables
CREATE TABLE policy_rules_extended (
    rule_id INT PRIMARY KEY AUTO_INCREMENT,
    unit_id INT NOT NULL,
    recruitment_count INT,
    unwritten_rules TEXT,
    english_requirement VARCHAR(50),
    computer_requirement VARCHAR(50),
    age_requirement VARCHAR(50),
    second_choice_available BOOLEAN,
    household_priority VARCHAR(50),
    major_consistency_required BOOLEAN,
    written_test_score_line DECIMAL(5,2),
    detailed_admission_rules TEXT,
    comprehensive_score_line DECIMAL(5,2),
    position_selection_method TEXT,
    first_batch_fail_second_ok BOOLEAN,
    deferred_graduation_impact VARCHAR(100),
    non_first_choice_pass BOOLEAN,
    campus_recruit_then_batch VARCHAR(100),
    single_cert_probability TEXT,
    qualification_review_requirements TEXT,
    application_ratio VARCHAR(50),
    cost_effectiveness_rank INT,
    best_value_city_rank INT,
    best_value_district_rank INT,
    difficulty_rank INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (unit_id) REFERENCES secondary_units(unit_id) ON DELETE CASCADE,
    INDEX idx_unit_id (unit_id)
);

CREATE TABLE early_batch_policies_extended (
    policy_id INT PRIMARY KEY AUTO_INCREMENT,
    unit_id INT NOT NULL,
    schedule_arrangement TEXT,
    education_requirement VARCHAR(100),
    written_test_required BOOLEAN DEFAULT FALSE,
    written_test_content TEXT,
    station_chasing_allowed BOOLEAN DEFAULT FALSE,
    admission_factors TEXT,
    unit_admission_status TEXT,
    difficulty_ranking TEXT,
    position_quality_difference TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (unit_id) REFERENCES secondary_units(unit_id) ON DELETE CASCADE,
    INDEX idx_unit_id (unit_id)
);

CREATE TABLE rural_grid_policies_extended (
    policy_id INT PRIMARY KEY AUTO_INCREMENT,
    unit_id INT NOT NULL,
    salary_benefits VARCHAR(200),
    exam_schedule VARCHAR(100),
    age_requirement VARCHAR(50),
    application_status VARCHAR(100),
    online_assessment TEXT,
    personality_test TEXT,
    qualification_review TEXT,
    written_test_content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (unit_id) REFERENCES secondary_units(unit_id) ON DELETE CASCADE,
    INDEX idx_unit_id (unit_id)
);

CREATE TABLE display_config_extended (
    config_id INT PRIMARY KEY AUTO_INCREMENT,
    field_category ENUM('基本信息', '提前批', '农网', '地市县信息') NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    field_type ENUM('text', 'number', 'boolean', 'textarea', 'select') NOT NULL,
    display_order INT DEFAULT 0,
    is_enabled BOOLEAN DEFAULT TRUE,
    is_required BOOLEAN DEFAULT FALSE,
    is_editable BOOLEAN DEFAULT TRUE,
    field_description TEXT,
    default_value VARCHAR(200),
    validation_rules JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category_order (field_category, display_order),
    INDEX idx_enabled (is_enabled)
);

-- Insert field configurations for 基本信息
INSERT INTO display_config_extended (field_category, field_name, display_name, field_type, display_order, is_enabled, field_description) VALUES 
('基本信息', 'recruitment_count', '录取人数', 'number', 1, TRUE, '该单位年度录取总人数'),
('基本信息', 'unwritten_rules', '网申不成文规定', 'textarea', 2, TRUE, '网申过程中的潜规则和注意事项'),
('基本信息', 'english_requirement', '英语等级', 'select', 3, TRUE, '四六级等英语证书要求'),
('基本信息', 'computer_requirement', '计算机等级', 'select', 4, TRUE, '计算机等级证书要求'),
('基本信息', 'age_requirement', '年龄要求', 'text', 5, TRUE, '应聘者年龄限制要求'),
('基本信息', 'written_test_score_line', '笔试分数线', 'number', 10, TRUE, '笔试最低录取分数'),
('基本信息', 'comprehensive_score_line', '综合分数线', 'number', 12, TRUE, '综合评分最低线'),
('基本信息', 'cost_effectiveness_rank', '性价比最高的市局', 'number', 17, TRUE, '市局性价比排名'),
('基本信息', 'difficulty_rank', '笔试难度排行', 'number', 19, TRUE, '笔试难度等级'),
('基本信息', 'application_ratio', '报录比', 'text', 21, TRUE, '报名与录取人数比例');

-- Insert field configurations for 提前批
INSERT INTO display_config_extended (field_category, field_name, display_name, field_type, display_order, is_enabled, field_description) VALUES 
('提前批', 'schedule_arrangement', '行程安排', 'textarea', 1, TRUE, '提前批面试的时间和流程安排'),
('提前批', 'education_requirement', '学历要求', 'text', 2, TRUE, '提前批的学历门槛要求'),
('提前批', 'written_test_required', '是否笔试及笔试内容', 'boolean', 3, TRUE, '是否需要参加笔试'),
('提前批', 'written_test_content', '笔试内容', 'textarea', 4, TRUE, '笔试的具体内容和范围'),
('提前批', 'admission_factors', '录用影响因素', 'textarea', 6, TRUE, '影响录用结果的关键因素');

-- Insert field configurations for 农网
INSERT INTO display_config_extended (field_category, field_name, display_name, field_type, display_order, is_enabled, field_description) VALUES 
('农网', 'salary_benefits', '农网待遇', 'text', 1, TRUE, '农网岗位的薪资福利情况'),
('农网', 'exam_schedule', '考试时间', 'text', 2, TRUE, '农网招聘考试的时间安排'),
('农网', 'age_requirement', '年龄要求', 'text', 3, TRUE, '农网岗位的年龄限制'),
('农网', 'application_status', '网申情况', 'text', 4, TRUE, '农网岗位网申的通过情况'),
('农网', 'online_assessment', '线上测评', 'textarea', 5, TRUE, '线上测评的内容和要求');

-- Insert field configurations for 地市县信息
INSERT INTO display_config_extended (field_category, field_name, display_name, field_type, display_order, is_enabled, field_description) VALUES 
('地市县信息', 'unit_name', '地市', 'text', 1, TRUE, '地级市名称'),
('地市县信息', 'region', '区域', 'text', 2, TRUE, '所属区域'),
('地市县信息', 'apply_status', '网申情况', 'text', 3, TRUE, '该地区网申通过难度'),
('地市县信息', 'salary_range', '薪资待遇', 'text', 4, TRUE, '该地区薪资水平'),
('地市县信息', 'estimated_score_range', '预估上岸分数', 'text', 5, TRUE, '预计录取分数范围');
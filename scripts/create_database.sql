-- 创建数据查一点通数据库
CREATE DATABASE IF NOT EXISTS shucha_yidiantong DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE shucha_yidiantong;

-- ========================================
-- 主表：recruitment_rules (录取规则表)
-- 基于字段备注支持方案，采用扁平化设计+备注表的混合方案
-- ========================================
CREATE TABLE recruitment_rules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    
    -- 地理位置信息
    province VARCHAR(50) NOT NULL COMMENT '省份名称',
    city VARCHAR(50) COMMENT '地级市名称', 
    company VARCHAR(100) COMMENT '公司名称',
    data_level ENUM('省级汇总','市级汇总','区县详情') NOT NULL COMMENT '数据层级',
    region_type TINYINT DEFAULT 0 COMMENT '区域类型：0-普通省，1-直辖市，2-特别行政区，3-自治区',
    
    -- 省级通用录取规则
    cet_requirement VARCHAR(20) COMMENT '四六级要求',
    computer_requirement VARCHAR(20) COMMENT '计算机证书要求',
    overage_allowed VARCHAR(20) COMMENT '超龄能否通过',
    household_priority VARCHAR(20) COMMENT '是否非常看重户籍',
    non_first_choice_pass VARCHAR(20) COMMENT '非第一志愿是否通过网申',
    detailed_rules TEXT COMMENT '详细录取规则',
    unwritten_rules TEXT COMMENT '网申不成文规定',
    stable_score_range VARCHAR(100) COMMENT '综合成绩多少分稳一点',
    single_cert_probability TEXT COMMENT '有一个证书网申概率',
    admission_ratio VARCHAR(50) COMMENT '报录比',
    
    -- 本科学历要求
    bachelor_985 VARCHAR(20) COMMENT '985本科要求',
    bachelor_211 VARCHAR(20) COMMENT '211本科要求',
    bachelor_provincial_double_first VARCHAR(20) COMMENT '省内双一流本科',
    bachelor_external_double_first VARCHAR(20) COMMENT '省外双一流本科',
    bachelor_provincial_non_double VARCHAR(20) COMMENT '省内双非一本',
    bachelor_external_non_double VARCHAR(20) COMMENT '省外双非一本',
    bachelor_provincial_second VARCHAR(20) COMMENT '省内二本',
    bachelor_external_second VARCHAR(20) COMMENT '省外二本',
    bachelor_private VARCHAR(20) COMMENT '民办本科',
    bachelor_upgrade VARCHAR(20) COMMENT '专升本',
    bachelor_college VARCHAR(20) COMMENT '专科',
    
    -- 硕士学历要求
    master_985 VARCHAR(20) COMMENT '985硕士要求',
    master_211 VARCHAR(20) COMMENT '211硕士要求',
    master_provincial_double_first VARCHAR(20) COMMENT '省内双一流硕士',
    master_external_double_first VARCHAR(20) COMMENT '省外双一流硕士',
    master_provincial_non_double VARCHAR(20) COMMENT '省内双非硕士',
    master_external_non_double VARCHAR(20) COMMENT '省外双非硕士',
    
    -- 薪资分数信息
    bachelor_salary VARCHAR(50) COMMENT '本科薪资待遇',
    bachelor_interview_line VARCHAR(20) COMMENT '本科进面线',
    bachelor_comprehensive_score DECIMAL(5,2) COMMENT '本科综合分',
    master_salary VARCHAR(50) COMMENT '硕士薪资待遇',
    master_interview_line DECIMAL(5,2) COMMENT '硕士进面分',
    
    -- 录取政策
    major_mismatch_allowed VARCHAR(20) COMMENT '本硕专业不一致可否通过网申',
    first_batch_fail_second_batch VARCHAR(20) COMMENT '一批进面没录取可以正常报考二批吗',
    deferred_graduation_impact VARCHAR(20) COMMENT '延毕休学影响网申吗',
    second_choice_available VARCHAR(20) COMMENT '是否有二次志愿填报',
    position_selection_method TEXT COMMENT '具体选岗方式',
    early_batch_difference TEXT COMMENT '提前批岗位和一二批岗位质量有什么差异',
    campus_recruit_then_first_batch VARCHAR(20) COMMENT '校招给了地方但是不满意是否还可以参加一批',
    
    -- 性价比信息
    is_best_value_city VARCHAR(10) COMMENT '是否性价比最高的市',
    is_best_value_county VARCHAR(10) COMMENT '是否性价比最高的区县',
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 索引
    UNIQUE KEY unique_location (province, city, company, data_level),
    INDEX idx_province (province),
    INDEX idx_data_level (data_level),
    INDEX idx_region_type (region_type),
    INDEX idx_province_city (province, city)
);

-- ========================================
-- 备注表：field_notes (字段备注表)
-- 支持针对不同地区的字段个性化备注
-- ========================================
CREATE TABLE field_notes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    rule_id INT NOT NULL COMMENT '关联主表ID',
    field_name VARCHAR(50) NOT NULL COMMENT '字段名称',
    note_content TEXT NOT NULL COMMENT '备注内容',
    note_type ENUM('说明','限制','特殊情况','警告') DEFAULT '说明' COMMENT '备注类型',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (rule_id) REFERENCES recruitment_rules(id) ON DELETE CASCADE,
    INDEX idx_rule_field (rule_id, field_name),
    INDEX idx_field_name (field_name)
);

-- ========================================
-- 录取记录表：recruitment_records (用于存储历年录取数据)
-- ========================================
CREATE TABLE recruitment_records (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL COMMENT '姓名(脱敏)',
    gender ENUM('男','女') NOT NULL COMMENT '性别',
    school VARCHAR(100) NOT NULL COMMENT '院校名称',
    major VARCHAR(100) COMMENT '专业名称',
    education_level ENUM('本科','硕士','博士') NOT NULL COMMENT '学历层次',
    school_type VARCHAR(50) COMMENT '院校类型(985/211等)',
    phone VARCHAR(20) COMMENT '手机号(脱敏)',
    
    -- 录取信息
    province VARCHAR(50) NOT NULL COMMENT '录取省份',
    city VARCHAR(50) COMMENT '录取城市',
    company VARCHAR(100) COMMENT '录取公司',
    position VARCHAR(100) COMMENT '录取岗位',
    batch_type ENUM('提前批','一批','二批','三批','南网') NOT NULL COMMENT '批次类型',
    company_type ENUM('国网','南网') NOT NULL COMMENT '公司类型',
    
    -- 成绩信息
    written_score DECIMAL(5,2) COMMENT '笔试成绩',
    interview_score DECIMAL(5,2) COMMENT '面试成绩', 
    comprehensive_score DECIMAL(5,2) COMMENT '综合成绩',
    
    -- 时间信息
    admission_year YEAR NOT NULL COMMENT '录取年份',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_province_city (province, city),
    INDEX idx_school_type (school_type),
    INDEX idx_admission_year (admission_year),
    INDEX idx_batch_company (batch_type, company_type)
);

-- ========================================
-- 初始化直辖市数据
-- ========================================
INSERT INTO recruitment_rules (province, data_level, region_type) VALUES 
('北京', '省级汇总', 1),
('上海', '省级汇总', 1),
('天津', '省级汇总', 1),
('重庆', '省级汇总', 1);

-- 添加一些测试用的区县数据示例
INSERT INTO recruitment_rules (province, city, data_level, region_type) VALUES 
('北京', '东城区', '区县详情', 1),
('北京', '西城区', '区县详情', 1),
('上海', '黄浦区', '区县详情', 1),
('重庆', '渝中区', '区县详情', 1);

-- ========================================
-- 创建视图：便于查询不同层级的数据
-- ========================================

-- 省级汇总视图（包含直辖市）
CREATE VIEW v_provincial_summary AS
SELECT * FROM recruitment_rules 
WHERE data_level = '省级汇总';

-- 市级汇总视图（排除直辖市的区）
CREATE VIEW v_city_summary AS
SELECT * FROM recruitment_rules 
WHERE data_level = '市级汇总';

-- 区县详情视图
CREATE VIEW v_district_details AS
SELECT * FROM recruitment_rules 
WHERE data_level = '区县详情';

-- 直辖市区县视图
CREATE VIEW v_municipality_districts AS
SELECT * FROM recruitment_rules 
WHERE data_level = '区县详情' AND region_type = 1;

SHOW TABLES;
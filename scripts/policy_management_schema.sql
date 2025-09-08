-- 三级录取政策管理系统数据库结构
-- 创建日期: 2025-09-03
-- 描述: 支持省级、市级、区县级三级政策管理的完整数据库结构

USE bdprod;

-- 1. 行政区划表
CREATE TABLE IF NOT EXISTS administrative_regions (
    region_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '区域ID',
    province VARCHAR(50) NOT NULL COMMENT '省份名称',
    city VARCHAR(50) NULL COMMENT '地级市名称',
    company VARCHAR(100) NULL COMMENT '区县公司名称',
    region_level ENUM('province', 'city', 'company') NOT NULL COMMENT '行政级别',
    parent_region_id INT NULL COMMENT '父级区域ID',
    region_code VARCHAR(20) UNIQUE NULL COMMENT '区域编码',
    is_municipality TINYINT(1) DEFAULT 0 COMMENT '是否为直辖市',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否活跃',
    sort_order INT DEFAULT 0 COMMENT '排序权重',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_province (province),
    INDEX idx_level (region_level),
    INDEX idx_parent (parent_region_id),
    INDEX idx_active (is_active),
    FOREIGN KEY (parent_region_id) REFERENCES administrative_regions(region_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='行政区划表';

-- 2. 省级政策表
CREATE TABLE IF NOT EXISTS province_policies (
    policy_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '政策ID',
    region_id INT NOT NULL COMMENT '区域ID',
    
    -- 基础要求字段
    cet_requirement VARCHAR(100) NULL COMMENT '四六级要求',
    computer_requirement VARCHAR(100) NULL COMMENT '计算机等级要求',
    overage_allowed VARCHAR(50) NULL COMMENT '超龄能否通过',
    household_priority VARCHAR(50) NULL COMMENT '是否非常看重户籍',
    non_first_choice_pass VARCHAR(50) NULL COMMENT '非第一志愿是否通过网申',
    
    -- 详细规则字段
    detailed_rules TEXT NULL COMMENT '详细录取规则',
    unwritten_rules TEXT NULL COMMENT '网申不成文规定',
    stable_score_range VARCHAR(200) NULL COMMENT '综合成绩多少分稳一点',
    single_cert_probability TEXT NULL COMMENT '有一个证书网申概率',
    admission_ratio VARCHAR(50) NULL COMMENT '报录比',
    
    -- 专业和批次政策
    major_mismatch_allowed VARCHAR(50) NULL COMMENT '本硕专业不一致可否通过网申',
    first_batch_fail_second_ok VARCHAR(50) NULL COMMENT '一批进面没录取可以正常报考二批吗',
    deferred_graduation_impact VARCHAR(100) NULL COMMENT '延毕休学影响网申吗',
    second_choice_available VARCHAR(50) NULL COMMENT '是否有二次志愿填报',
    position_selection_method TEXT NULL COMMENT '具体选岗方式',
    
    -- 提前批和校招政策
    early_batch_difference TEXT NULL COMMENT '提前批岗位和一二批岗位质量差异',
    campus_recruit_then_batch VARCHAR(100) NULL COMMENT '校招给了地方但不满意是否还可参加一批',
    
    -- 元数据
    created_by INT NULL COMMENT '创建人ID',
    updated_by INT NULL COMMENT '更新人ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_region (region_id),
    FOREIGN KEY (region_id) REFERENCES administrative_regions(region_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='省级政策表';

-- 3. 市级政策表（预留扩展）
CREATE TABLE IF NOT EXISTS city_policies (
    policy_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '政策ID',
    region_id INT NOT NULL COMMENT '区域ID',
    
    -- 预留字段用于未来扩展
    reserved_field_1 VARCHAR(200) NULL COMMENT '预留字段1',
    reserved_field_2 VARCHAR(200) NULL COMMENT '预留字段2',
    reserved_field_3 TEXT NULL COMMENT '预留字段3',
    reserved_field_4 TEXT NULL COMMENT '预留字段4',
    reserved_field_5 VARCHAR(100) NULL COMMENT '预留字段5',
    reserved_field_6 VARCHAR(100) NULL COMMENT '预留字段6',
    reserved_field_7 VARCHAR(100) NULL COMMENT '预留字段7',
    reserved_field_8 VARCHAR(100) NULL COMMENT '预留字段8',
    reserved_field_9 TEXT NULL COMMENT '预留字段9',
    reserved_field_10 TEXT NULL COMMENT '预留字段10',
    
    -- 元数据
    created_by INT NULL COMMENT '创建人ID',
    updated_by INT NULL COMMENT '更新人ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_region (region_id),
    FOREIGN KEY (region_id) REFERENCES administrative_regions(region_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='市级政策表';

-- 4. 区县公司政策表
CREATE TABLE IF NOT EXISTS company_policies (
    policy_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '政策ID',
    region_id INT NOT NULL COMMENT '区域ID',
    
    -- 本科学历要求字段
    bachelor_985 VARCHAR(20) NULL COMMENT '985本科要求',
    bachelor_211 VARCHAR(20) NULL COMMENT '211本科要求', 
    bachelor_provincial_double_first VARCHAR(20) NULL COMMENT '省内双一流本科',
    bachelor_external_double_first VARCHAR(20) NULL COMMENT '省外双一流本科',
    bachelor_provincial_non_double VARCHAR(20) NULL COMMENT '省内双非一本',
    bachelor_external_non_double VARCHAR(20) NULL COMMENT '省外双非一本',
    bachelor_provincial_second VARCHAR(20) NULL COMMENT '省内二本',
    bachelor_external_second VARCHAR(20) NULL COMMENT '省外二本',
    bachelor_private VARCHAR(20) NULL COMMENT '民办本科',
    bachelor_upgrade VARCHAR(20) NULL COMMENT '专升本',
    bachelor_college VARCHAR(20) NULL COMMENT '专科',
    
    -- 硕士学历要求字段
    master_985 VARCHAR(20) NULL COMMENT '985硕士要求',
    master_211 VARCHAR(20) NULL COMMENT '211硕士要求',
    master_provincial_double_first VARCHAR(20) NULL COMMENT '省内双一流硕士',
    master_external_double_first VARCHAR(20) NULL COMMENT '省外双一流硕士',
    master_provincial_non_double VARCHAR(20) NULL COMMENT '省内双非硕士',
    master_external_non_double VARCHAR(20) NULL COMMENT '省外双非硕士',
    
    -- 薪资待遇字段
    bachelor_salary VARCHAR(50) NULL COMMENT '本科薪资待遇',
    bachelor_interview_line DECIMAL(5,2) NULL COMMENT '本科进面线',
    bachelor_comprehensive_score DECIMAL(5,2) NULL COMMENT '本科综合分',
    master_salary VARCHAR(50) NULL COMMENT '硕士薪资待遇',
    master_interview_line DECIMAL(5,2) NULL COMMENT '硕士进面分',
    
    -- 性价比评估
    is_best_value_city VARCHAR(10) NULL COMMENT '是否性价比最高的市',
    is_best_value_county VARCHAR(10) NULL COMMENT '是否性价比最高的区县',
    
    -- 元数据
    created_by INT NULL COMMENT '创建人ID',
    updated_by INT NULL COMMENT '更新人ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_region (region_id),
    FOREIGN KEY (region_id) REFERENCES administrative_regions(region_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='区县公司政策表';

-- 5. 政策变更历史表（用于审计）
CREATE TABLE IF NOT EXISTS policy_change_history (
    history_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '历史记录ID',
    policy_type ENUM('province', 'city', 'company') NOT NULL COMMENT '政策类型',
    policy_id INT NOT NULL COMMENT '政策ID',
    region_id INT NOT NULL COMMENT '区域ID',
    field_name VARCHAR(100) NOT NULL COMMENT '字段名称',
    old_value TEXT NULL COMMENT '原值',
    new_value TEXT NULL COMMENT '新值',
    change_type ENUM('create', 'update', 'delete') NOT NULL COMMENT '变更类型',
    changed_by INT NULL COMMENT '变更人ID',
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '变更时间',
    
    INDEX idx_policy_type (policy_type),
    INDEX idx_policy_id (policy_id),
    INDEX idx_region (region_id),
    INDEX idx_changed_at (changed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='政策变更历史表';

-- 6. 政策字段配置表（用于前端动态显示）
CREATE TABLE IF NOT EXISTS policy_field_config (
    config_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '配置ID',
    policy_level ENUM('province', 'city', 'company') NOT NULL COMMENT '政策级别',
    field_name VARCHAR(100) NOT NULL COMMENT '字段名称',
    display_name VARCHAR(100) NOT NULL COMMENT '显示名称',
    field_type ENUM('text', 'textarea', 'select', 'number', 'boolean') NOT NULL COMMENT '字段类型',
    field_category VARCHAR(50) NULL COMMENT '字段分类',
    is_required TINYINT(1) DEFAULT 0 COMMENT '是否必填',
    is_enabled TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    display_order INT DEFAULT 0 COMMENT '显示顺序',
    field_options TEXT NULL COMMENT '字段选项(JSON格式)',
    validation_rules TEXT NULL COMMENT '验证规则(JSON格式)',
    help_text VARCHAR(255) NULL COMMENT '帮助文本',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_level (policy_level),
    INDEX idx_enabled (is_enabled),
    INDEX idx_order (display_order),
    UNIQUE KEY uk_level_field (policy_level, field_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='政策字段配置表';
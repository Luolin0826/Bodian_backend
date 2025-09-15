-- ========================================
-- 数查一点通快捷查询功能数据库表结构
-- 支持本科信息、硕士信息、录取人数统计查询
-- ========================================

-- 创建快捷查询信息表
CREATE TABLE quick_query_info (
    id INT PRIMARY KEY AUTO_INCREMENT,
    unit_id INT NOT NULL COMMENT '关联secondary_units表的unit_id',
    
    -- 本科信息
    undergraduate_english VARCHAR(100) DEFAULT NULL COMMENT '本科英语要求',
    undergraduate_computer VARCHAR(100) DEFAULT NULL COMMENT '本科计算机要求', 
    undergraduate_qualification TEXT DEFAULT NULL COMMENT '本科资格审查',
    undergraduate_age VARCHAR(50) DEFAULT NULL COMMENT '本科年龄要求',
    
    -- 本科分数线(2023-2025)
    undergrad_2025_batch1_score VARCHAR(50) DEFAULT NULL COMMENT '25年一批本科录取分数',
    undergrad_2025_batch2_score VARCHAR(50) DEFAULT NULL COMMENT '25年二批本科录取分数',
    undergrad_2024_batch1_score VARCHAR(50) DEFAULT NULL COMMENT '24年一批本科录取分数线',
    undergrad_2024_batch2_score VARCHAR(50) DEFAULT NULL COMMENT '24年二批本科录取分数',
    undergrad_2023_batch1_score VARCHAR(50) DEFAULT NULL COMMENT '23年一批本科分数线',
    undergrad_2023_batch2_score VARCHAR(50) DEFAULT NULL COMMENT '23年二批本科分数线',
    
    -- 硕士信息
    graduate_english VARCHAR(100) DEFAULT NULL COMMENT '硕士英语要求',
    graduate_computer VARCHAR(100) DEFAULT NULL COMMENT '硕士计算机要求',
    graduate_qualification TEXT DEFAULT NULL COMMENT '硕士资格审查', 
    graduate_age VARCHAR(50) DEFAULT NULL COMMENT '硕士年龄要求',
    
    -- 硕士分数线(2023-2025)
    graduate_2025_batch1_score VARCHAR(50) DEFAULT NULL COMMENT '25年一批硕士录取分数',
    graduate_2025_batch2_score VARCHAR(50) DEFAULT NULL COMMENT '25年二批硕士录取分数',
    graduate_2024_batch1_score VARCHAR(50) DEFAULT NULL COMMENT '24年一批硕士录取分数线',
    graduate_2024_batch2_score VARCHAR(50) DEFAULT NULL COMMENT '24年二批硕士录取分数',
    graduate_2023_batch1_score VARCHAR(50) DEFAULT NULL COMMENT '23年一批硕士分数线',
    graduate_2023_batch2_score VARCHAR(50) DEFAULT NULL COMMENT '23年二批硕士分数线',
    
    -- 录取人数统计(2023-2025)
    admission_2025_batch1_count INT DEFAULT NULL COMMENT '25一批录取人数',
    admission_2025_batch2_count INT DEFAULT NULL COMMENT '25二批录取人数',
    admission_2024_batch1_count INT DEFAULT NULL COMMENT '24年一批录取人数',
    admission_2024_batch2_count INT DEFAULT NULL COMMENT '24年二批录取人数',
    admission_2023_batch1_count INT DEFAULT NULL COMMENT '23年一批录取人数',
    admission_2023_batch2_count INT DEFAULT NULL COMMENT '23年二批录取人数',
    
    -- 创建和更新时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 外键约束
    FOREIGN KEY (unit_id) REFERENCES secondary_units(unit_id) ON DELETE CASCADE,
    
    -- 唯一约束：每个unit_id只能有一条记录
    UNIQUE KEY uk_unit_id (unit_id),
    
    -- 索引
    INDEX idx_unit_id (unit_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='快捷查询信息表';

-- ========================================
-- 创建视图简化查询操作
-- ========================================

-- 本科信息视图
CREATE VIEW v_undergraduate_info AS
SELECT 
    q.id,
    q.unit_id,
    s.unit_name as province,
    s.org_type,
    q.undergraduate_english,
    q.undergraduate_computer,
    q.undergraduate_qualification,
    q.undergraduate_age,
    q.undergrad_2025_batch1_score,
    q.undergrad_2025_batch2_score,
    q.undergrad_2024_batch1_score,
    q.undergrad_2024_batch2_score,
    q.undergrad_2023_batch1_score,
    q.undergrad_2023_batch2_score,
    q.updated_at
FROM quick_query_info q
JOIN secondary_units s ON q.unit_id = s.unit_id
WHERE s.unit_type = '省级电网公司' AND s.is_active = 1;

-- 硕士信息视图
CREATE VIEW v_graduate_info AS
SELECT 
    q.id,
    q.unit_id,
    s.unit_name as province,
    s.org_type,
    q.graduate_english,
    q.graduate_computer,
    q.graduate_qualification,
    q.graduate_age,
    q.graduate_2025_batch1_score,
    q.graduate_2025_batch2_score,
    q.graduate_2024_batch1_score,
    q.graduate_2024_batch2_score,
    q.graduate_2023_batch1_score,
    q.graduate_2023_batch2_score,
    q.updated_at
FROM quick_query_info q
JOIN secondary_units s ON q.unit_id = s.unit_id
WHERE s.unit_type = '省级电网公司' AND s.is_active = 1;

-- 录取统计视图
CREATE VIEW v_admission_stats AS
SELECT 
    q.id,
    q.unit_id,
    s.unit_name as province,
    s.org_type,
    q.admission_2025_batch1_count,
    q.admission_2025_batch2_count,
    q.admission_2024_batch1_count,
    q.admission_2024_batch2_count,
    q.admission_2023_batch1_count,
    q.admission_2023_batch2_count,
    q.updated_at
FROM quick_query_info q
JOIN secondary_units s ON q.unit_id = s.unit_id
WHERE s.unit_type = '省级电网公司' AND s.is_active = 1;

-- 完整信息视图
CREATE VIEW v_quick_query_complete AS
SELECT 
    q.*,
    s.unit_name as province,
    s.org_type,
    s.unit_type
FROM quick_query_info q
JOIN secondary_units s ON q.unit_id = s.unit_id
WHERE s.unit_type = '省级电网公司' AND s.is_active = 1;

-- ========================================
-- 创建有用的存储过程
-- ========================================

-- 获取省份完整信息的存储过程
DELIMITER //
CREATE PROCEDURE GetProvinceCompleteInfo(IN province_name VARCHAR(50))
BEGIN
    SELECT 
        q.*,
        s.unit_name as province,
        s.org_type
    FROM quick_query_info q
    JOIN secondary_units s ON q.unit_id = s.unit_id
    WHERE s.unit_name = province_name 
      AND s.unit_type = '省级电网公司' 
      AND s.is_active = 1;
END //
DELIMITER ;

-- 批量更新数据的存储过程
DELIMITER //
CREATE PROCEDURE BatchUpdateQuickQuery()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    -- 批量操作逻辑将在具体使用时实现
    COMMIT;
END //
DELIMITER ;

-- ========================================
-- 插入示例数据用于测试
-- ========================================

-- 为已存在的省份插入一些示例数据
INSERT INTO quick_query_info (unit_id, undergraduate_english, undergraduate_computer, undergraduate_age) 
SELECT 
    unit_id,
    '四级' as undergraduate_english,
    '二级' as undergraduate_computer,
    '35岁以下' as undergraduate_age
FROM secondary_units 
WHERE unit_type = '省级电网公司' AND is_active = 1 
LIMIT 3;
-- 话术库"一问多答"功能数据库扩展
-- 执行日期: 2025-09-14
-- 说明: 在现有scripts表添加JSON字段支持多回复功能

-- 1. 添加新字段
ALTER TABLE scripts 
ADD COLUMN answers JSON COMMENT '多个回复内容(JSON数组)',
ADD COLUMN answer_count INT DEFAULT 1 COMMENT '回复数量',
ADD COLUMN recommended_answer_index INT DEFAULT 0 COMMENT '推荐回复索引(0-based)';

-- 2. 数据迁移：将现有answer字段迁移到answers数组
UPDATE scripts 
SET answers = JSON_ARRAY(answer),
    answer_count = 1,
    recommended_answer_index = 0
WHERE answers IS NULL 
  AND answer IS NOT NULL 
  AND answer != '';

-- 3. 处理空answer的记录
UPDATE scripts 
SET answers = JSON_ARRAY(''),
    answer_count = 1,
    recommended_answer_index = 0
WHERE answers IS NULL 
  AND (answer IS NULL OR answer = '');

-- 4. 创建索引提升查询性能（可选）
-- CREATE INDEX idx_scripts_answer_count ON scripts(answer_count);

-- 5. 验证迁移结果
SELECT 
    id,
    SUBSTRING(question, 1, 50) as question_preview,
    SUBSTRING(answer, 1, 50) as original_answer,
    answers,
    answer_count,
    recommended_answer_index
FROM scripts 
WHERE id IN (
    SELECT id FROM scripts ORDER BY id LIMIT 5
);
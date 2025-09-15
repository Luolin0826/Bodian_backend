-- Scripts表列删除迁移脚本
-- 执行日期: 2025-09-14
-- 说明: 删除scripts表中不再使用的12个字段

-- 备份现有数据（可选，建议在执行前备份整个数据库）
-- CREATE TABLE scripts_backup AS SELECT * FROM scripts;

-- 删除不再使用的字段
ALTER TABLE scripts 
DROP COLUMN IF EXISTS script_type,
DROP COLUMN IF EXISTS data_source,
DROP COLUMN IF EXISTS type,
DROP COLUMN IF EXISTS platform,
DROP COLUMN IF EXISTS customer_info,
DROP COLUMN IF EXISTS script_type_new,
DROP COLUMN IF EXISTS content_type_new,
DROP COLUMN IF EXISTS platform_new,
DROP COLUMN IF EXISTS keywords_new,
DROP COLUMN IF EXISTS classification_meta,
DROP COLUMN IF EXISTS classification_status,
DROP COLUMN IF EXISTS classification_version;

-- 验证删除结果
DESCRIBE scripts;

-- 显示删除后的表结构信息
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() 
AND TABLE_NAME = 'scripts'
ORDER BY ORDINAL_POSITION;
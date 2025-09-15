#!/usr/bin/env python3
"""
手动执行数据库迁移脚本：为 student_feedback_templates 表添加集成化管理字段
"""
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db
from sqlalchemy import text

def migrate_feedback_fields():
    """执行反馈表字段迁移"""
    app = create_app()
    
    with app.app_context():
        try:
            # 连接到数据库
            
            print("🔄 开始执行数据库迁移...")
            
            # 检查字段是否已存在
            result = db.session.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'bdprod' 
                    AND TABLE_NAME = 'student_feedback_templates' 
                    AND COLUMN_NAME IN ('province_name', 'station_name_text', 'recruitment_requirements', 'announcement_url')
            """))
            existing_fields = [row[0] for row in result.fetchall()]
            
            if len(existing_fields) == 4:
                print("✅ 所有新字段已存在，跳过迁移")
                return True
            
            # 添加新字段
            migrations = [
                "ALTER TABLE student_feedback_templates ADD COLUMN province_name VARCHAR(100) COMMENT '省份名称（文本字段）'",
                "ALTER TABLE student_feedback_templates ADD COLUMN station_name_text VARCHAR(200) COMMENT '站点名称（文本字段）'", 
                "ALTER TABLE student_feedback_templates ADD COLUMN recruitment_requirements TEXT COMMENT '招聘要求'",
                "ALTER TABLE student_feedback_templates ADD COLUMN announcement_url VARCHAR(500) COMMENT '公告链接'"
            ]
            
            for sql in migrations:
                field_name = sql.split('ADD COLUMN ')[1].split()[0]
                if field_name not in existing_fields:
                    print(f"📝 添加字段: {field_name}")
                    db.session.execute(text(sql))
                    db.session.commit()
                else:
                    print(f"⏭️  字段已存在: {field_name}")
            
            # 添加索引
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_feedback_province_name ON student_feedback_templates(province_name)",
                "CREATE INDEX IF NOT EXISTS idx_feedback_created_desc ON student_feedback_templates(created_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_feedback_featured ON student_feedback_templates(is_featured)"
            ]
            
            for idx_sql in indexes:
                print(f"📊 创建索引: {idx_sql.split('ON')[0].split()[-1]}")
                try:
                    db.session.execute(text(idx_sql))
                    db.session.commit()
                except Exception as e:
                    if "already exists" in str(e).lower():
                        print(f"⏭️  索引已存在")
                    else:
                        print(f"⚠️  索引创建失败: {e}")
            
            # 数据迁移：填充现有数据的文本字段
            data_migrations = [
                """UPDATE student_feedback_templates sft
                   JOIN advance_batch_provinces abp ON sft.province_plan_id = abp.id
                   SET sft.province_name = abp.province
                   WHERE sft.province_name IS NULL AND sft.province_plan_id IS NOT NULL""",
                
                """UPDATE student_feedback_templates sft
                   JOIN advance_batch_stations abs ON sft.station_id = abs.id
                   SET sft.station_name_text = abs.university_name
                   WHERE sft.station_name_text IS NULL AND sft.station_id IS NOT NULL""",
                
                """UPDATE student_feedback_templates sft
                   JOIN advance_batch_provinces abp ON sft.province_plan_id = abp.id
                   SET sft.recruitment_requirements = abp.other_requirements
                   WHERE sft.recruitment_requirements IS NULL AND abp.other_requirements IS NOT NULL""",
                
                """UPDATE student_feedback_templates sft
                   JOIN advance_batch_provinces abp ON sft.province_plan_id = abp.id
                   SET sft.announcement_url = abp.notice_url
                   WHERE sft.announcement_url IS NULL AND abp.notice_url IS NOT NULL"""
            ]
            
            for data_sql in data_migrations:
                print(f"🔄 执行数据迁移...")
                result = db.session.execute(text(data_sql))
                db.session.commit()
                print(f"   影响行数: {result.rowcount}")
            
            # 验证迁移结果
            result = db.session.execute(text("""
                SELECT 
                    COUNT(*) as total_feedback,
                    COUNT(province_name) as has_province_name,
                    COUNT(station_name_text) as has_station_name,
                    COUNT(recruitment_requirements) as has_requirements,
                    COUNT(announcement_url) as has_announcement_url
                FROM student_feedback_templates
                WHERE is_active = 1
            """))
            
            stats = result.fetchone()
            print(f"\n📊 迁移结果统计:")
            print(f"   总反馈数: {stats[0]}")
            print(f"   有省份名称: {stats[1]}")
            print(f"   有站点名称: {stats[2]}")
            print(f"   有招聘要求: {stats[3]}")
            print(f"   有公告链接: {stats[4]}")
            
            print("✅ 数据库迁移完成！")
            return True
            
        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = migrate_feedback_fields()
    sys.exit(0 if success else 1)
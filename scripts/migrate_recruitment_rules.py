#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移现有recruitment_rules数据到新的三级政策管理系统
将数据迁移到province_policies和company_policies表
"""

import mysql.connector
from mysql.connector import Error
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'database': 'bdprod',
    'user': 'dms_user_9332d9e',
    'password': 'AaBb19990826',
    'charset': 'utf8mb4',
    'autocommit': True,
    'use_unicode': True
}

def get_db_connection():
    """获取数据库连接"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        logger.error(f"数据库连接失败: {e}")
        raise e

def migrate_province_policies():
    """迁移省级政策数据"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        logger.info("开始迁移省级政策数据...")
        
        # 获取所有省级汇总数据
        cursor.execute("""
            SELECT DISTINCT province,
                   cet_requirement, computer_requirement, overage_allowed, 
                   household_priority, non_first_choice_pass, detailed_rules,
                   unwritten_rules, stable_score_range, single_cert_probability,
                   admission_ratio, major_mismatch_allowed, first_batch_fail_second_batch,
                   deferred_graduation_impact, second_choice_available, position_selection_method,
                   early_batch_difference, campus_recruit_then_first_batch
            FROM recruitment_rules 
            WHERE data_level = '省级汇总'
        """)
        
        province_rules = cursor.fetchall()
        logger.info(f"找到 {len(province_rules)} 个省级政策记录")
        
        # 清理现有省级政策数据
        cursor.execute("DELETE FROM province_policies")
        logger.info("清理现有省级政策数据")
        
        for rule in province_rules:
            province = rule['province']
            
            # 获取对应的region_id
            cursor.execute("""
                SELECT region_id FROM administrative_regions 
                WHERE province = %s AND region_level = 'province'
            """, (province,))
            
            region_result = cursor.fetchone()
            if not region_result:
                logger.warning(f"未找到省份 {province} 的区域记录，跳过")
                continue
                
            region_id = region_result['region_id']
            
            # 插入省级政策数据
            insert_query = """
            INSERT INTO province_policies (
                region_id, cet_requirement, computer_requirement, overage_allowed,
                household_priority, non_first_choice_pass, detailed_rules,
                unwritten_rules, stable_score_range, single_cert_probability,
                admission_ratio, major_mismatch_allowed, first_batch_fail_second_batch,
                deferred_graduation_impact, second_choice_available, position_selection_method,
                early_batch_difference, campus_recruit_then_first_batch
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                region_id,
                rule.get('cet_requirement'),
                rule.get('computer_requirement'), 
                rule.get('overage_allowed'),
                rule.get('household_priority'),
                rule.get('non_first_choice_pass'),
                rule.get('detailed_rules'),
                rule.get('unwritten_rules'),
                rule.get('stable_score_range'),
                rule.get('single_cert_probability'),
                rule.get('admission_ratio'),
                rule.get('major_mismatch_allowed'),
                rule.get('first_batch_fail_second_batch'),
                rule.get('deferred_graduation_impact'),
                rule.get('second_choice_available'),
                rule.get('position_selection_method'),
                rule.get('early_batch_difference'),
                rule.get('campus_recruit_then_first_batch')
            ))
            
            logger.info(f"已迁移省级政策: {province} (region_id: {region_id})")
        
        cursor.close()
        connection.close()
        logger.info("省级政策数据迁移完成")
        
    except Exception as e:
        logger.error(f"省级政策迁移失败: {e}")
        raise e

def migrate_company_policies():
    """迁移区县公司级政策数据"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        logger.info("开始迁移区县公司级政策数据...")
        
        # 获取所有区县详情数据
        cursor.execute("""
            SELECT province, city, company,
                   bachelor_985, bachelor_211, bachelor_provincial_double_first,
                   bachelor_external_double_first, bachelor_provincial_non_double,
                   bachelor_external_non_double, bachelor_provincial_second,
                   bachelor_external_second, bachelor_private, bachelor_upgrade,
                   bachelor_college, master_985, master_211, master_provincial_double_first,
                   master_external_double_first, master_provincial_non_double,
                   master_external_non_double, bachelor_salary, bachelor_interview_line,
                   bachelor_comprehensive_score, master_salary, master_interview_line,
                   is_best_value_city, is_best_value_county
            FROM recruitment_rules 
            WHERE data_level = '区县详情' AND company IS NOT NULL
        """)
        
        company_rules = cursor.fetchall()
        logger.info(f"找到 {len(company_rules)} 个区县公司政策记录")
        
        # 清理现有公司政策数据
        cursor.execute("DELETE FROM company_policies")
        logger.info("清理现有公司政策数据")
        
        for rule in company_rules:
            province = rule['province']
            city = rule['city']
            company = rule['company']
            
            # 获取对应的region_id (公司级别)
            cursor.execute("""
                SELECT region_id FROM administrative_regions 
                WHERE province = %s AND city = %s AND company = %s AND region_level = 'company'
            """, (province, city, company))
            
            region_result = cursor.fetchone()
            if not region_result:
                # 如果找不到完全匹配的，尝试只匹配公司名称
                cursor.execute("""
                    SELECT region_id FROM administrative_regions 
                    WHERE province = %s AND company = %s AND region_level = 'company'
                    LIMIT 1
                """, (province, company))
                region_result = cursor.fetchone()
                
                if not region_result:
                    logger.warning(f"未找到公司 {province}-{city}-{company} 的区域记录，跳过")
                    continue
                    
            region_id = region_result['region_id']
            
            # 插入公司政策数据
            insert_query = """
            INSERT INTO company_policies (
                region_id, bachelor_985, bachelor_211, bachelor_provincial_double_first,
                bachelor_external_double_first, bachelor_provincial_non_double,
                bachelor_external_non_double, bachelor_provincial_second,
                bachelor_external_second, bachelor_private, bachelor_upgrade,
                bachelor_college, master_985, master_211, master_provincial_double_first,
                master_external_double_first, master_provincial_non_double,
                master_external_non_double, bachelor_salary, bachelor_interview_line,
                bachelor_comprehensive_score, master_salary, master_interview_line,
                is_best_value_city, is_best_value_county
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                region_id,
                rule.get('bachelor_985'),
                rule.get('bachelor_211'),
                rule.get('bachelor_provincial_double_first'),
                rule.get('bachelor_external_double_first'),
                rule.get('bachelor_provincial_non_double'),
                rule.get('bachelor_external_non_double'),
                rule.get('bachelor_provincial_second'),
                rule.get('bachelor_external_second'),
                rule.get('bachelor_private'),
                rule.get('bachelor_upgrade'),
                rule.get('bachelor_college'),
                rule.get('master_985'),
                rule.get('master_211'),
                rule.get('master_provincial_double_first'),
                rule.get('master_external_double_first'),
                rule.get('master_provincial_non_double'),
                rule.get('master_external_non_double'),
                rule.get('bachelor_salary'),
                rule.get('bachelor_interview_line'),
                rule.get('bachelor_comprehensive_score'),
                rule.get('master_salary'),
                rule.get('master_interview_line'),
                rule.get('is_best_value_city'),
                rule.get('is_best_value_county')
            ))
            
            logger.info(f"已迁移公司政策: {province}-{city}-{company} (region_id: {region_id})")
        
        cursor.close()
        connection.close()
        logger.info("区县公司政策数据迁移完成")
        
    except Exception as e:
        logger.error(f"公司政策迁移失败: {e}")
        raise e

def verify_migration():
    """验证迁移结果"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # 统计迁移结果
        cursor.execute("SELECT COUNT(*) FROM province_policies")
        province_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM company_policies")  
        company_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM recruitment_rules WHERE data_level = '省级汇总'")
        original_province_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM recruitment_rules WHERE data_level = '区县详情'")
        original_company_count = cursor.fetchone()[0]
        
        print("\n=== 数据迁移验证结果 ===")
        print(f"原始省级汇总记录: {original_province_count}")
        print(f"迁移后省级政策记录: {province_count}")
        print(f"原始区县详情记录: {original_company_count}")
        print(f"迁移后公司政策记录: {company_count}")
        
        # 显示样例数据
        cursor.execute("""
            SELECT ar.province, COUNT(*) as policy_count
            FROM province_policies pp
            JOIN administrative_regions ar ON pp.region_id = ar.region_id
            GROUP BY ar.province
            ORDER BY policy_count DESC
            LIMIT 5
        """)
        
        province_samples = cursor.fetchall()
        print("\n=== 省级政策样例 ===")
        for province, count in province_samples:
            print(f"{province}: {count}条政策")
            
        cursor.execute("""
            SELECT ar.province, ar.city, ar.company, COUNT(*) as policy_count
            FROM company_policies cp
            JOIN administrative_regions ar ON cp.region_id = ar.region_id
            GROUP BY ar.province, ar.city, ar.company
            ORDER BY policy_count DESC
            LIMIT 5
        """)
        
        company_samples = cursor.fetchall()
        print("\n=== 公司政策样例 ===")
        for province, city, company, count in company_samples:
            print(f"{province}-{city}-{company}: {count}条政策")
        
        cursor.close()
        connection.close()
        
        return {
            'province_migrated': province_count,
            'company_migrated': company_count,
            'original_province': original_province_count,
            'original_company': original_company_count
        }
        
    except Exception as e:
        logger.error(f"验证迁移结果失败: {e}")
        return {'error': str(e)}

def main():
    """主函数"""
    try:
        logger.info("开始recruitment_rules数据迁移...")
        
        # 步骤1：迁移省级政策
        migrate_province_policies()
        
        # 步骤2：迁移公司政策  
        migrate_company_policies()
        
        # 步骤3：验证迁移结果
        result = verify_migration()
        
        if 'error' not in result:
            logger.info("数据迁移成功完成！")
            print(f"\n迁移成功：省级政策 {result['province_migrated']} 条，公司政策 {result['company_migrated']} 条")
        else:
            logger.error(f"迁移验证失败: {result['error']}")
        
    except Exception as e:
        logger.error(f"数据迁移过程失败: {e}")

if __name__ == "__main__":
    main()
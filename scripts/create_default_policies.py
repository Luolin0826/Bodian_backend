#!/usr/bin/env python3
"""
创建默认政策记录脚本
为所有省份和区县创建基础政策、提前批政策、农网政策的默认记录
"""

import mysql.connector
from mysql.connector import Error
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'database': 'bdprod',
    'user': 'dms_user_9332d9e',
    'password': 'AaBb19990826',
    'charset': 'utf8mb4',
    'autocommit': False,
    'use_unicode': True,
    'consume_results': True
}

def get_db_connection():
    """获取数据库连接"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        logger.error(f"数据库连接失败: {e}")
        raise e

def create_default_basic_policies():
    """为所有单位创建基础政策默认记录"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # 获取所有没有基础政策记录的单位
        cursor.execute("""
            SELECT su.unit_id, su.unit_name, su.unit_type
            FROM secondary_units su
            LEFT JOIN policy_rules_extended pre ON su.unit_id = pre.unit_id
            WHERE pre.unit_id IS NULL
            ORDER BY su.unit_id
        """)
        
        units_without_policies = cursor.fetchall()
        logger.info(f"找到 {len(units_without_policies)} 个单位没有基础政策记录")
        
        # 为每个单位创建默认基础政策记录
        default_values = {
            'recruitment_count': 0,
            'english_requirement': '不限',
            'computer_requirement': '不限',  
            'age_requirement': '不限',
            'written_test_score_line': 60.0,
            'comprehensive_score_line': 60.0,
            'cost_effectiveness_rank': 0,
            'difficulty_rank': 0,
            'application_ratio': '待更新',
            'second_choice_available': 1,
            'household_priority': '不限',
            'major_consistency_required': 0,
            'detailed_admission_rules': '待完善',
            'position_selection_method': '待更新',
            'first_batch_fail_second_ok': 1,
            'deferred_graduation_impact': '无影响',
            'non_first_choice_pass': 1,
            'campus_recruit_then_batch': '支持',
            'single_cert_probability': '待评估',
            'qualification_review_requirements': '待完善',
            'best_value_city_rank': 0,
            'best_value_district_rank': 0,
            'version': 1,
            'custom_data': None
        }
        
        created_count = 0
        for unit in units_without_policies:
            try:
                # 插入基础政策记录
                insert_sql = """
                    INSERT INTO policy_rules_extended (
                        unit_id, recruitment_count, english_requirement, computer_requirement,
                        age_requirement, written_test_score_line, comprehensive_score_line,
                        cost_effectiveness_rank, difficulty_rank, application_ratio,
                        second_choice_available, household_priority, major_consistency_required,
                        detailed_admission_rules, position_selection_method, first_batch_fail_second_ok,
                        deferred_graduation_impact, non_first_choice_pass, campus_recruit_then_batch,
                        single_cert_probability, qualification_review_requirements,
                        best_value_city_rank, best_value_district_rank, version, custom_data,
                        created_at, updated_at
                    ) VALUES (
                        %(unit_id)s, %(recruitment_count)s, %(english_requirement)s, %(computer_requirement)s,
                        %(age_requirement)s, %(written_test_score_line)s, %(comprehensive_score_line)s,
                        %(cost_effectiveness_rank)s, %(difficulty_rank)s, %(application_ratio)s,
                        %(second_choice_available)s, %(household_priority)s, %(major_consistency_required)s,
                        %(detailed_admission_rules)s, %(position_selection_method)s, %(first_batch_fail_second_ok)s,
                        %(deferred_graduation_impact)s, %(non_first_choice_pass)s, %(campus_recruit_then_batch)s,
                        %(single_cert_probability)s, %(qualification_review_requirements)s,
                        %(best_value_city_rank)s, %(best_value_district_rank)s, %(version)s, %(custom_data)s,
                        NOW(), NOW()
                    )
                """
                
                params = default_values.copy()
                params['unit_id'] = unit['unit_id']
                
                cursor.execute(insert_sql, params)
                created_count += 1
                logger.info(f"为 {unit['unit_name']} (ID: {unit['unit_id']}) 创建基础政策记录")
                
            except Error as e:
                logger.error(f"为单位 {unit['unit_name']} 创建基础政策失败: {e}")
        
        connection.commit()
        logger.info(f"成功创建 {created_count} 条基础政策记录")
        
        cursor.close()
        connection.close()
        
        return created_count
        
    except Exception as e:
        if connection:
            connection.rollback()
        logger.error(f"创建基础政策记录失败: {e}")
        raise e

def create_default_early_batch_policies():
    """为所有单位创建提前批政策默认记录"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # 获取所有没有提前批政策记录的单位
        cursor.execute("""
            SELECT su.unit_id, su.unit_name, su.unit_type
            FROM secondary_units su
            LEFT JOIN early_batch_policies_extended ebpe ON su.unit_id = ebpe.unit_id
            WHERE ebpe.unit_id IS NULL
            ORDER BY su.unit_id
        """)
        
        units_without_policies = cursor.fetchall()
        logger.info(f"找到 {len(units_without_policies)} 个单位没有提前批政策记录")
        
        # 默认值
        default_values = {
            'schedule_arrangement': '待更新',
            'education_requirement': '本科及以上',
            'written_test_required': 1,
            'written_test_content': '待更新',
            'admission_factors': '待更新',
            'station_chasing_allowed': 1,
            'unit_admission_status': '待更新',
            'difficulty_ranking': '待评估',
            'position_quality_difference': '待更新',
            'version': 1,
            'custom_data': None
        }
        
        created_count = 0
        for unit in units_without_policies:
            try:
                insert_sql = """
                    INSERT INTO early_batch_policies_extended (
                        unit_id, schedule_arrangement, education_requirement, written_test_required,
                        written_test_content, admission_factors, station_chasing_allowed,
                        unit_admission_status, difficulty_ranking, position_quality_difference,
                        version, custom_data, created_at, updated_at
                    ) VALUES (
                        %(unit_id)s, %(schedule_arrangement)s, %(education_requirement)s, %(written_test_required)s,
                        %(written_test_content)s, %(admission_factors)s, %(station_chasing_allowed)s,
                        %(unit_admission_status)s, %(difficulty_ranking)s, %(position_quality_difference)s,
                        %(version)s, %(custom_data)s, NOW(), NOW()
                    )
                """
                
                params = default_values.copy()
                params['unit_id'] = unit['unit_id']
                
                cursor.execute(insert_sql, params)
                created_count += 1
                logger.info(f"为 {unit['unit_name']} (ID: {unit['unit_id']}) 创建提前批政策记录")
                
            except Error as e:
                logger.error(f"为单位 {unit['unit_name']} 创建提前批政策失败: {e}")
        
        connection.commit()
        logger.info(f"成功创建 {created_count} 条提前批政策记录")
        
        cursor.close()
        connection.close()
        
        return created_count
        
    except Exception as e:
        if connection:
            connection.rollback()
        logger.error(f"创建提前批政策记录失败: {e}")
        raise e

def create_default_rural_grid_policies():
    """为所有单位创建农网政策默认记录"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # 获取所有没有农网政策记录的单位
        cursor.execute("""
            SELECT su.unit_id, su.unit_name, su.unit_type
            FROM secondary_units su
            LEFT JOIN rural_grid_policies_extended rgpe ON su.unit_id = rgpe.unit_id
            WHERE rgpe.unit_id IS NULL
            ORDER BY su.unit_id
        """)
        
        units_without_policies = cursor.fetchall()
        logger.info(f"找到 {len(units_without_policies)} 个单位没有农网政策记录")
        
        # 默认值
        default_values = {
            'salary_benefits': '待更新',
            'exam_schedule': '待更新',
            'age_requirement': '不限',
            'application_status': '开放',
            'online_assessment': '待更新',
            'personality_test': '待更新',
            'qualification_review': '待更新',
            'written_test_content': '待更新',
            'version': 1,
            'custom_data': None
        }
        
        created_count = 0
        for unit in units_without_policies:
            try:
                insert_sql = """
                    INSERT INTO rural_grid_policies_extended (
                        unit_id, salary_benefits, exam_schedule, age_requirement,
                        application_status, online_assessment, personality_test,
                        qualification_review, written_test_content, version, custom_data,
                        created_at, updated_at
                    ) VALUES (
                        %(unit_id)s, %(salary_benefits)s, %(exam_schedule)s, %(age_requirement)s,
                        %(application_status)s, %(online_assessment)s, %(personality_test)s,
                        %(qualification_review)s, %(written_test_content)s, %(version)s, %(custom_data)s,
                        NOW(), NOW()
                    )
                """
                
                params = default_values.copy()
                params['unit_id'] = unit['unit_id']
                
                cursor.execute(insert_sql, params)
                created_count += 1
                logger.info(f"为 {unit['unit_name']} (ID: {unit['unit_id']}) 创建农网政策记录")
                
            except Error as e:
                logger.error(f"为单位 {unit['unit_name']} 创建农网政策失败: {e}")
        
        connection.commit()
        logger.info(f"成功创建 {created_count} 条农网政策记录")
        
        cursor.close()
        connection.close()
        
        return created_count
        
    except Exception as e:
        if connection:
            connection.rollback()
        logger.error(f"创建农网政策记录失败: {e}")
        raise e

def main():
    """主函数"""
    logger.info("开始创建默认政策记录...")
    
    try:
        # 创建基础政策记录
        basic_count = create_default_basic_policies()
        
        # 创建提前批政策记录
        early_batch_count = create_default_early_batch_policies()
        
        # 创建农网政策记录
        rural_grid_count = create_default_rural_grid_policies()
        
        logger.info("=" * 50)
        logger.info("默认政策记录创建完成:")
        logger.info(f"- 基础政策记录: {basic_count} 条")
        logger.info(f"- 提前批政策记录: {early_batch_count} 条")
        logger.info(f"- 农网政策记录: {rural_grid_count} 条")
        logger.info(f"总计创建: {basic_count + early_batch_count + rural_grid_count} 条记录")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"创建默认政策记录失败: {e}")
        raise e

if __name__ == "__main__":
    main()
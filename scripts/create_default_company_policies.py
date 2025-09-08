#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为缺失的区县公司创建默认政策
特别是新增的四川省区县
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

def get_missing_company_policies():
    """获取缺失政策的区县公司"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT ar.region_id, ar.province, ar.city, ar.company
            FROM administrative_regions ar
            LEFT JOIN company_policies cp ON ar.region_id = cp.region_id
            WHERE ar.region_level = 'company' 
              AND ar.is_active = 1
              AND cp.policy_id IS NULL
            ORDER BY ar.province, ar.city, ar.company
        """)
        
        missing_regions = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return missing_regions
        
    except Exception as e:
        logger.error(f"获取缺失政策的区县失败: {e}")
        return []

def create_default_company_policy(region_id, province, city, company):
    """为指定区县创建默认公司政策"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # 默认政策配置
        default_policy = {
            'region_id': region_id,
            'bachelor_985': 0,
            'bachelor_211': 0,
            'bachelor_provincial_double_first': 0,
            'bachelor_external_double_first': 0,
            'bachelor_provincial_non_double': 0,
            'bachelor_external_non_double': 0,
            'bachelor_provincial_second': 0,
            'bachelor_external_second': 0,
            'bachelor_private': 0,
            'bachelor_upgrade': 0,
            'bachelor_college': 0,
            'master_985': 0,
            'master_211': 0,
            'master_provincial_double_first': 0,
            'master_external_double_first': 0,
            'master_provincial_non_double': 0,
            'master_external_non_double': 0,
            'bachelor_salary': 0,
            'bachelor_interview_line': 0,
            'bachelor_comprehensive_score': 0,
            'master_salary': 0,
            'master_interview_line': 0,
            'is_best_value_city': 0,
            'is_best_value_county': 0,
            'created_by': 1  # 系统用户
        }
        
        # 构建插入语句
        fields = list(default_policy.keys())
        placeholders = ', '.join(['%s'] * len(fields))
        field_names = ', '.join(fields)
        values = list(default_policy.values())
        
        insert_query = f"""
        INSERT INTO company_policies ({field_names})
        VALUES ({placeholders})
        """
        
        cursor.execute(insert_query, values)
        policy_id = cursor.lastrowid
        
        cursor.close()
        connection.close()
        
        logger.info(f"为 {province}-{city}-{company} 创建默认政策 (policy_id: {policy_id}, region_id: {region_id})")
        return policy_id
        
    except Exception as e:
        logger.error(f"为 {province}-{city}-{company} 创建政策失败: {e}")
        return None

def create_all_missing_policies():
    """为所有缺失的区县创建默认政策"""
    try:
        # 获取缺失政策的区县
        missing_regions = get_missing_company_policies()
        
        if not missing_regions:
            logger.info("没有发现缺失政策的区县")
            return
        
        logger.info(f"发现 {len(missing_regions)} 个缺失政策的区县")
        
        # 为每个区县创建默认政策
        created_count = 0
        failed_count = 0
        
        for region in missing_regions:
            region_id = region['region_id']
            province = region['province']
            city = region['city']
            company = region['company']
            
            policy_id = create_default_company_policy(region_id, province, city, company)
            
            if policy_id:
                created_count += 1
            else:
                failed_count += 1
        
        logger.info(f"政策创建完成: 成功 {created_count} 个, 失败 {failed_count} 个")
        
        # 打印统计结果
        print_creation_statistics()
        
    except Exception as e:
        logger.error(f"批量创建政策失败: {e}")

def print_creation_statistics():
    """打印创建统计信息"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # 统计各省份的公司政策数量
        cursor.execute("""
            SELECT ar.province, COUNT(*) as policy_count
            FROM company_policies cp
            JOIN administrative_regions ar ON cp.region_id = ar.region_id
            WHERE ar.region_level = 'company'
            GROUP BY ar.province
            ORDER BY ar.province
        """)
        
        province_stats = cursor.fetchall()
        
        print("\n=== 各省份公司政策统计 ===")
        for stat in province_stats:
            print(f"{stat['province']}: {stat['policy_count']}个公司政策")
        
        # 统计四川省的详细信息
        cursor.execute("""
            SELECT ar.city, COUNT(*) as policy_count
            FROM company_policies cp
            JOIN administrative_regions ar ON cp.region_id = ar.region_id
            WHERE ar.region_level = 'company' AND ar.province = '四川'
            GROUP BY ar.city
            ORDER BY ar.city
        """)
        
        sichuan_stats = cursor.fetchall()
        
        print("\n=== 四川省各市公司政策统计 ===")
        for stat in sichuan_stats:
            print(f"{stat['city']}: {stat['policy_count']}个公司政策")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")

def main():
    """主函数"""
    try:
        logger.info("开始为缺失的区县创建默认公司政策...")
        create_all_missing_policies()
        logger.info("任务完成！")
        
    except Exception as e:
        logger.error(f"主程序执行失败: {e}")

if __name__ == "__main__":
    main()
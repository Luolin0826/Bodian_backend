#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为所有省份创建完整的省级政策数据
解决前端请求1-29号政策ID时的404问题
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

def create_full_province_policies():
    """为所有省份创建完整的省级政策数据"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # 获取所有省份区域
        cursor.execute("""
            SELECT region_id, province FROM administrative_regions 
            WHERE region_level = 'province' 
            ORDER BY region_id
        """)
        
        all_provinces = cursor.fetchall()
        logger.info(f"找到 {len(all_provinces)} 个省份区域")
        
        # 获取已存在的政策ID
        cursor.execute("SELECT region_id FROM province_policies")
        existing_regions = {row['region_id'] for row in cursor.fetchall()}
        
        # 默认政策模板
        default_policy = {
            'cet_requirement': '四级优先',
            'computer_requirement': '二级优先', 
            'overage_allowed': '否',
            'household_priority': '是',
            'non_first_choice_pass': '否',
            'detailed_rules': '请参考具体招聘公告，本数据为模板数据',
            'unwritten_rules': '具体政策以最新公告为准',
            'stable_score_range': '待更新',
            'single_cert_probability': '具体情况需咨询招聘单位',
            'admission_ratio': '待统计',
            'major_mismatch_allowed': '否',
            'first_batch_fail_second_batch': '否',
            'deferred_graduation_impact': '有影响',
            'second_choice_available': '否',
            'position_selection_method': '按分数排序选岗',
            'early_batch_difference': '待更新',
            'campus_recruit_then_first_batch': '否'
        }
        
        created_count = 0
        skipped_count = 0
        
        for province in all_provinces:
            region_id = province['region_id']
            province_name = province['province']
            
            if region_id in existing_regions:
                logger.info(f"省份 {province_name} (region_id: {region_id}) 已有政策，跳过")
                skipped_count += 1
                continue
            
            # 创建新的省级政策
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
                default_policy['cet_requirement'],
                default_policy['computer_requirement'],
                default_policy['overage_allowed'],
                default_policy['household_priority'],
                default_policy['non_first_choice_pass'],
                default_policy['detailed_rules'],
                default_policy['unwritten_rules'],
                default_policy['stable_score_range'],
                default_policy['single_cert_probability'],
                default_policy['admission_ratio'],
                default_policy['major_mismatch_allowed'],
                default_policy['first_batch_fail_second_batch'],
                default_policy['deferred_graduation_impact'],
                default_policy['second_choice_available'],
                default_policy['position_selection_method'],
                default_policy['early_batch_difference'],
                default_policy['campus_recruit_then_first_batch']
            ))
            
            policy_id = cursor.lastrowid
            logger.info(f"已创建省级政策: {province_name} (region_id: {region_id}, policy_id: {policy_id})")
            created_count += 1
        
        cursor.close()
        connection.close()
        
        logger.info(f"省级政策创建完成 - 新建: {created_count}, 跳过: {skipped_count}")
        return {'created': created_count, 'skipped': skipped_count}
        
    except Exception as e:
        logger.error(f"创建省级政策失败: {e}")
        raise e

def verify_policy_coverage():
    """验证政策覆盖情况"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # 统计总体情况
        cursor.execute("SELECT COUNT(*) as total FROM administrative_regions WHERE region_level = 'province'")
        total_provinces = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM province_policies")
        total_policies = cursor.fetchone()['total']
        
        # 查看政策ID分布
        cursor.execute("""
            SELECT pp.policy_id, ar.province, pp.created_at
            FROM province_policies pp
            JOIN administrative_regions ar ON pp.region_id = ar.region_id
            ORDER BY pp.policy_id
        """)
        
        policies = cursor.fetchall()
        
        print(f"\n=== 省级政策覆盖验证 ===")
        print(f"总省份数: {total_provinces}")
        print(f"总政策数: {total_policies}")
        print(f"覆盖率: {(total_policies/total_provinces)*100:.1f}%")
        
        print(f"\n=== 政策ID分布 ===")
        policy_ids = [p['policy_id'] for p in policies]
        print(f"最小ID: {min(policy_ids)}")
        print(f"最大ID: {max(policy_ids)}")
        print(f"ID范围: {min(policy_ids)}-{max(policy_ids)}")
        
        # 检查前端常用的1-29范围
        missing_in_range = []
        for i in range(1, 30):
            if i not in policy_ids:
                missing_in_range.append(i)
        
        if missing_in_range:
            print(f"1-29范围内缺失的ID: {missing_in_range}")
        else:
            print("1-29范围内所有ID都有对应政策 ✅")
        
        print(f"\n=== 最新创建的5个政策 ===")
        for policy in policies[-5:]:
            print(f"ID: {policy['policy_id']}, 省份: {policy['province']}, 创建时间: {policy['created_at']}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        logger.error(f"验证失败: {e}")

def main():
    """主函数"""
    try:
        logger.info("开始创建完整的省级政策数据...")
        
        result = create_full_province_policies()
        
        logger.info("验证政策覆盖情况...")
        verify_policy_coverage()
        
        logger.info("✅ 省级政策数据创建完成！")
        print(f"\n总结: 新建 {result['created']} 个政策，跳过 {result['skipped']} 个已存在的政策")
        
    except Exception as e:
        logger.error(f"执行失败: {e}")

if __name__ == "__main__":
    main()
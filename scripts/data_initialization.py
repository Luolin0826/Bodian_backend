#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data-Query优化数据库初始化脚本
用于初始化基础数据和示例政策数据
"""

import mysql.connector
from mysql.connector import Error
import json
import logging
from datetime import datetime, date
import random

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataInitializer:
    """数据初始化器"""
    
    def __init__(self):
        """初始化数据库连接配置"""
        self.db_config = {
            'host': 'rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
            'port': 3306,
            'database': 'data_query_optimized',
            'user': 'dms_user_9332d9e',
            'password': 'AaBb19990826',
            'charset': 'utf8mb4',
            'autocommit': True,
            'use_unicode': True
        }
    
    def get_connection(self):
        """获取数据库连接"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            return connection
        except Error as e:
            logger.error(f"数据库连接失败: {e}")
            raise e
    
    def init_regional_units(self):
        """初始化地区单位数据"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            logger.info("开始初始化地区单位数据...")
            
            # 示例地区单位数据
            regional_units_data = [
                # 国网四川省公司下属单位
                (19, '四川', '成都', '成都天府供电公司', '区县级', '国网四川省电力公司成都天府供电公司', '8-12万', '75-80分', '网申通过率较高', '发达', True),
                (19, '四川', '成都', '成都市区供电公司', '区县级', '国网四川省电力公司成都市区供电公司', '8-12万', '78-82分', '竞争激烈', '发达', True),
                (19, '四川', '绵阳', '绵阳供电公司', '市级', '国网四川省电力公司绵阳供电公司', '7-10万', '72-78分', '网申相对容易', '一般', False),
                (19, '四川', '德阳', '德阳供电公司', '市级', '国网四川省电力公司德阳供电公司', '6-9万', '70-75分', '政策较宽松', '一般', False),
                
                # 国网重庆市公司下属单位
                (20, '重庆', '渝中区', '渝中供电公司', '区县级', '国网重庆市电力公司渝中供电公司', '9-13万', '80-85分', '要求较高', '发达', True),
                (20, '重庆', '江北区', '江北供电公司', '区县级', '国网重庆市电力公司江北供电公司', '8-12万', '75-80分', '网申通过率中等', '发达', True),
                
                # 南网广东省公司下属单位
                (1, '广东', '广州', '广州供电局', '市级', '南方电网广东电网公司广州供电局', '10-15万', '82-88分', '竞争最激烈', '发达', True),
                (1, '广东', '深圳', '深圳供电局', '市级', '南方电网广东电网公司深圳供电局', '12-18万', '85-90分', '要求很高', '发达', True),
                (1, '广东', '佛山', '佛山供电局', '市级', '南方电网广东电网公司佛山供电局', '8-12万', '75-82分', '网申较严格', '发达', True),
                
                # 南网云南省公司下属单位
                (3, '云南', '昆明', '昆明供电局', '市级', '南方电网云南电网公司昆明供电局', '6-9万', '68-75分', '政策相对宽松', '一般', False),
                (3, '云南', '大理', '大理供电局', '市级', '南方电网云南电网公司大理供电局', '5-8万', '65-72分', '网申容易', '欠发达', False),
            ]
            
            # 插入地区单位数据
            insert_query = """
                INSERT INTO regional_units 
                (org_id, province, city, district, unit_level, unit_full_name, 
                 salary_range, estimated_score_range, apply_status, economic_level, is_key_city)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.executemany(insert_query, regional_units_data)
            logger.info(f"成功插入 {len(regional_units_data)} 条地区单位数据")
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            logger.error(f"初始化地区单位数据失败: {e}")
            raise e
    
    def init_policy_rules(self):
        """初始化政策规则数据"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            logger.info("开始初始化政策规则数据...")
            
            # 示例政策规则数据
            policy_rules_data = [
                # 国网四川省公司政策（省级汇总）
                (19, None, 200, '本科学历优先，硕士研究生更有优势；985/211院校毕业生在网申中有明显优势', 
                 '四级425分以上', '计算机二级', '35岁以下', True, '不太看重', True, 65.0, 
                 '综合考虑笔试、面试、学历背景', 75.0, '采用志愿填报+组织分配相结合',
                 True, '延毕1年内可以正常报考，超过1年需要特殊说明', True, '校招和统招不冲突，可以都参加',
                 '四级证书网申通过率约60%，计算机证书约40%', '需要提供三方协议，应届生身份证明', '约8:1',
                 2, 1, 1, 3),
                
                # 国网重庆市公司政策（省级汇总）
                (20, None, 150, '重点关注985/211院校，本硕专业对口要求较严格',
                 '四级必须', '计算机二级必须', '28岁以下', True, '比较看重', False, 70.0,
                 '笔试占40%，面试占35%，学历占25%', 80.0, '按成绩排名选择岗位',
                 False, '延毕影响较大，需要详细说明原因', False, '校招录取后不能参加统招',
                 '双证书网申通过率约80%', '严格审查学历和证书真实性', '约12:1',
                 1, 1, 1, 2),
                
                # 南网广东省公司政策（省级汇总）
                (1, None, 300, '优先985/211，双一流院校；专业对口要求严格',
                 '六级450分以上优先', '计算机二级', '30岁以下', True, '非常看重户籍', False, 75.0,
                 '笔试占50%，面试占30%，综合素质占20%', 82.0, '分专业分岗位择优选择',
                 True, '延毕休学有一定影响，需要提供详细说明', True, '可以参加但优先级较低',
                 '六级+计算机二级通过率约70%', '需要户口本、学历证明、成绩单等', '约15:1',
                 1, 1, 1, 1),
                
                # 南网云南省公司政策（省级汇总）  
                (3, None, 120, '学历要求相对宽松，注重实际能力和稳定性',
                 '四级或同等水平', '计算机一级以上', '35岁以下', True, '不太看重', True, 60.0,
                 '注重综合素质和工作稳定性', 68.0, '双向选择为主',
                 True, '延毕休学影响不大', True, '支持多渠道就业',
                 '有相关证书优先考虑', '资格审查相对宽松', '约6:1',
                 5, 3, 2, 4),
            ]
            
            # 插入政策规则数据
            insert_query = """
                INSERT INTO policy_rules 
                (org_id, unit_id, recruitment_count, unwritten_rules, english_requirement, 
                 computer_requirement, age_requirement, second_choice_available, 
                 household_priority, major_consistency_required, written_test_score_line,
                 detailed_admission_rules, comprehensive_score_line, position_selection_method,
                 first_batch_fail_second_ok, deferred_graduation_impact, non_first_choice_pass, 
                 campus_recruit_then_batch, single_cert_probability, qualification_review_requirements,
                 application_ratio, cost_effectiveness_rank, best_value_city_rank, 
                 best_value_district_rank, difficulty_rank)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.executemany(insert_query, policy_rules_data)
            logger.info(f"成功插入 {len(policy_rules_data)} 条政策规则数据")
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            logger.error(f"初始化政策规则数据失败: {e}")
            raise e
    
    def init_early_batch_policies(self):
        """初始化提前批政策数据"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            logger.info("开始初始化提前批政策数据...")
            
            # 示例提前批政策数据
            early_batch_data = [
                # 国网四川省公司提前批
                (19, '通常在每年9-10月进行，为期3-5天的实地考察和面试',
                 '本科及以上学历，电气工程相关专业', True,
                 '专业知识测试+综合能力测试', True,
                 '学历背景、专业匹配度、综合素质、沟通能力',
                 '各地市局录用情况差异较大，成都地区竞争最激烈',
                 '成都>绵阳>德阳>其他地市', 
                 '提前批岗位相对稳定，发展空间大，但地点选择有限'),
                
                # 国网重庆市公司提前批
                (20, '每年10月中旬，集中在重庆总部进行',
                 '985/211院校本科以上学历', True,
                 '行业知识+管理能力测试', False,
                 '学历层次、专业背景、个人综合能力',
                 '录用标准较高，主要面向管理培训生岗位',
                 '竞争激烈程度：市区>主城区>远郊区县',
                 '提前批多为储备干部岗位，发展前景好'),
                
                # 南网广东省公司提前批
                (1, '分两轮进行，第一轮网上初试，第二轮现场复试',
                 '双一流院校硕士以上学历', True, 
                 '专业技能+英语口语+管理案例分析', True,
                 '学历背景、英语水平、专业技能、领导潜质',
                 '广州、深圳录用门槛最高，其他地市相对宽松',
                 '深圳>广州>佛山>其他地市',
                 '提前批主要为核心技术岗位和管理岗位'),
                
                # 南网云南省公司提前批
                (3, '相对简化，主要在昆明进行集中面试',
                 '本科以上学历，专业不限', False,
                 '基础能力测试', True,
                 '工作稳定性、适应能力、基本素质',
                 '录用相对宽松，主要看个人稳定性',
                 '昆明>大理>其他州市',
                 '提前批和统招岗位质量差异不大'),
            ]
            
            # 插入提前批政策数据
            insert_query = """
                INSERT INTO early_batch_policies 
                (org_id, schedule_arrangement, education_requirement, written_test_required,
                 written_test_content, station_chasing_allowed, admission_factors,
                 unit_admission_status, difficulty_ranking, position_quality_difference)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.executemany(insert_query, early_batch_data)
            logger.info(f"成功插入 {len(early_batch_data)} 条提前批政策数据")
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            logger.error(f"初始化提前批政策数据失败: {e}")
            raise e
    
    def init_rural_grid_policies(self):
        """初始化农网政策数据"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            logger.info("开始初始化农网政策数据...")
            
            # 示例农网政策数据
            rural_grid_data = [
                # 国网四川省公司农网
                (19, '基本工资5-7万，加上各种补贴约6-8万/年',
                 '每年4-5月统一考试', '35岁以下',
                 '网申相对容易，主要看稳定性',
                 '基础能力测试+心理测评', '性格测试重点考察稳定性和抗压能力',
                 '需要提供无犯罪记录证明', '专业基础知识+安全知识'),
                
                # 国网重庆市公司农网
                (20, '基本工资6-8万，综合收入7-10万/年',
                 '每年3-4月集中考试', '30岁以下',
                 '要求具有电气相关背景',
                 '专业知识+综合素质评估', '重点测试工作责任心和团队合作能力',
                 '严格审查学历和专业背景', '电气专业知识+安全规程'),
                
                # 南网广东省公司农网  
                (1, '基本工资7-10万，加各种津贴约8-12万/年',
                 '每年5-6月分批考试', '32岁以下',
                 '网申通过率较高，注重本地化',
                 '线上测评+现场面试', '性格测试注重服务意识和沟通能力', 
                 '需要提供户籍证明和推荐信', '专业技能+客户服务+安全知识'),
                
                # 南网云南省公司农网
                (3, '基本工资4-6万，综合收入5-7万/年',
                 '每年6-7月统一组织', '40岁以下',
                 '门槛相对较低，看重工作态度',
                 '基本素质测评', '主要测试诚信度和责任感',
                 '资格审查相对简单', '基础知识+实操技能'),
            ]
            
            # 插入农网政策数据
            insert_query = """
                INSERT INTO rural_grid_policies
                (org_id, salary_benefits, exam_schedule, age_requirement, application_status,
                 online_assessment, personality_test, qualification_review, written_test_content)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.executemany(insert_query, rural_grid_data)
            logger.info(f"成功插入 {len(rural_grid_data)} 条农网政策数据")
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            logger.error(f"初始化农网政策数据失败: {e}")
            raise e
    
    def init_batch_admission_stats(self):
        """初始化批次录取统计数据"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            logger.info("开始初始化批次录取统计数据...")
            
            # 模拟一些录取统计数据
            admission_stats_data = []
            
            # 为每个组织生成不同批次的统计数据
            org_ids = [19, 20, 1, 3]  # 四川、重庆、广东南网、云南南网
            batch_types = ['一批', '二批', '三批']
            university_ids = list(range(1, 51))  # 假设有50所大学
            years = [2022, 2023, 2024]
            
            for org_id in org_ids:
                for batch_type in batch_types:
                    for year in years:
                        # 每个组织每个批次每年随机选择10-20所学校
                        selected_universities = random.sample(university_ids, random.randint(10, 20))
                        
                        for university_id in selected_universities:
                            admission_count = random.randint(1, 15)
                            application_count = admission_count + random.randint(5, 50)
                            admission_rate = round((admission_count / application_count) * 100, 2)
                            
                            min_score = round(random.uniform(60, 75), 2)
                            max_score = round(min_score + random.uniform(10, 25), 2)
                            avg_score = round((min_score + max_score) / 2, 2)
                            
                            admission_stats_data.append((
                                org_id, batch_type, university_id,
                                admission_count, application_count, admission_rate,
                                min_score, max_score, avg_score, year
                            ))
            
            # 分批插入数据（避免一次插入过多）
            batch_size = 100
            insert_query = """
                INSERT INTO batch_admission_stats
                (org_id, batch_type, university_id, admission_count, application_count,
                 admission_rate, min_score, max_score, avg_score, admission_year)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            for i in range(0, len(admission_stats_data), batch_size):
                batch_data = admission_stats_data[i:i + batch_size]
                cursor.executemany(insert_query, batch_data)
                logger.info(f"已插入 {i + len(batch_data)} / {len(admission_stats_data)} 条录取统计数据")
            
            logger.info(f"成功插入 {len(admission_stats_data)} 条录取统计数据")
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            logger.error(f"初始化录取统计数据失败: {e}")
            raise e
    
    def run_initialization(self):
        """运行完整的数据初始化"""
        try:
            logger.info("=== 开始数据库初始化 ===")
            
            # 1. 初始化地区单位数据
            self.init_regional_units()
            
            # 2. 初始化政策规则数据
            self.init_policy_rules()
            
            # 3. 初始化提前批政策数据
            self.init_early_batch_policies()
            
            # 4. 初始化农网政策数据
            self.init_rural_grid_policies()
            
            # 5. 初始化录取统计数据
            self.init_batch_admission_stats()
            
            logger.info("=== 数据库初始化完成 ===")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise e

def main():
    """主函数"""
    try:
        initializer = DataInitializer()
        initializer.run_initialization()
        print("数据初始化完成！")
        
    except Exception as e:
        print(f"数据初始化失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
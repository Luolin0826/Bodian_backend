#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于现有bdprod数据库的Data-Query政策数据初始化脚本
在现有secondary_units和recruitment_records基础上，添加政策示例数据
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

class BdprodDataInitializer:
    """基于bdprod数据库的数据初始化器"""
    
    def __init__(self):
        """初始化数据库连接配置"""
        self.db_config = {
            'host': 'rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
            'port': 3306,
            'database': 'bdprod',
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
    
    def check_extension_tables_exist(self):
        """检查扩展表是否存在"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            tables_to_check = [
                'policy_rules_extended',
                'early_batch_policies_extended', 
                'rural_grid_policies_extended',
                'display_config_extended'
            ]
            
            existing_tables = []
            for table in tables_to_check:
                cursor.execute("SHOW TABLES LIKE %s", (table,))
                if cursor.fetchone():
                    existing_tables.append(table)
            
            cursor.close()
            connection.close()
            
            logger.info(f"已存在的扩展表: {existing_tables}")
            return existing_tables
            
        except Exception as e:
            logger.error(f"检查扩展表失败: {e}")
            return []
    
    def get_secondary_units_data(self):
        """获取现有的secondary_units数据"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            # 获取所有活跃的单位数据
            cursor.execute("""
                SELECT unit_id, unit_name, unit_type, org_type, region, recruitment_count
                FROM secondary_units 
                WHERE is_active = 1 
                ORDER BY org_type, sort_order, unit_name
            """)
            
            units_data = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            logger.info(f"获取到 {len(units_data)} 个活跃单位数据")
            return units_data
            
        except Exception as e:
            logger.error(f"获取单位数据失败: {e}")
            return []
    
    def init_policy_rules_sample_data(self, units_data):
        """初始化政策规则示例数据"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            logger.info("开始初始化政策规则示例数据...")
            
            # 为部分重要单位添加政策规则示例数据
            sample_units = [
                {'unit_id': 5, 'unit_name': '四川', 'org_type': '国网省公司'},  # 四川
                {'unit_id': 1, 'unit_name': '广东', 'org_type': '南网省公司'},  # 广东 
                {'unit_id': 3, 'unit_name': '山东', 'org_type': '国网省公司'},  # 山东
                {'unit_id': 15, 'unit_name': '广西', 'org_type': '南网省公司'}, # 广西
            ]
            
            policy_templates = {
                '国网省公司': {
                    'recruitment_count': random.randint(150, 300),
                    'unwritten_rules': '985/211院校优先，本硕专业对口要求较严格',
                    'english_requirement': '四级425分以上',
                    'computer_requirement': '计算机二级',
                    'age_requirement': '本科28岁以下，硕士30岁以下',
                    'second_choice_available': True,
                    'household_priority': '一般',
                    'major_consistency_required': False,
                    'written_test_score_line': random.uniform(65, 75),
                    'detailed_admission_rules': '笔试占40%，面试占35%，学历背景占25%',
                    'comprehensive_score_line': random.uniform(75, 85),
                    'position_selection_method': '按成绩排名选择岗位，双向选择',
                    'first_batch_fail_second_ok': True,
                    'deferred_graduation_impact': '延毕1年内可正常报考',
                    'non_first_choice_pass': True,
                    'campus_recruit_then_batch': '校招和统招不冲突',
                    'single_cert_probability': '四级证书网申通过率约60%',
                    'qualification_review_requirements': '学历证明、成绩单、三方协议',
                    'application_ratio': f'{random.randint(6, 12)}:1',
                    'cost_effectiveness_rank': random.randint(1, 10),
                    'best_value_city_rank': random.randint(1, 5),
                    'best_value_district_rank': random.randint(1, 3),
                    'difficulty_rank': random.randint(2, 8)
                },
                '南网省公司': {
                    'recruitment_count': random.randint(100, 250),
                    'unwritten_rules': '双一流院校优先，专业匹配度要求高',
                    'english_requirement': '六级425分以上优先',
                    'computer_requirement': '计算机二级',
                    'age_requirement': '30岁以下',
                    'second_choice_available': True,
                    'household_priority': '较看重',
                    'major_consistency_required': True,
                    'written_test_score_line': random.uniform(70, 80),
                    'detailed_admission_rules': '笔试占50%，面试占30%，综合素质占20%',
                    'comprehensive_score_line': random.uniform(78, 88),
                    'position_selection_method': '分专业分岗位择优录取',
                    'first_batch_fail_second_ok': False,
                    'deferred_graduation_impact': '延毕有一定影响',
                    'non_first_choice_pass': False,
                    'campus_recruit_then_batch': '校招优先级较高',
                    'single_cert_probability': '六级+计算机二级通过率约70%',
                    'qualification_review_requirements': '户口本、学历证明、成绩单等',
                    'application_ratio': f'{random.randint(10, 18)}:1',
                    'cost_effectiveness_rank': random.randint(1, 8),
                    'best_value_city_rank': random.randint(1, 4),
                    'best_value_district_rank': random.randint(1, 2),
                    'difficulty_rank': random.randint(1, 5)
                }
            }
            
            insert_query = """
                INSERT INTO policy_rules_extended 
                (unit_id, recruitment_count, unwritten_rules, english_requirement, 
                 computer_requirement, age_requirement, second_choice_available, 
                 household_priority, major_consistency_required, written_test_score_line,
                 detailed_admission_rules, comprehensive_score_line, position_selection_method,
                 first_batch_fail_second_ok, deferred_graduation_impact, non_first_choice_pass, 
                 campus_recruit_then_batch, single_cert_probability, qualification_review_requirements,
                 application_ratio, cost_effectiveness_rank, best_value_city_rank, 
                 best_value_district_rank, difficulty_rank)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            inserted_count = 0
            for unit in sample_units:
                org_type = unit['org_type']
                if org_type in policy_templates:
                    template = policy_templates[org_type]
                    
                    data = (
                        unit['unit_id'],
                        template['recruitment_count'],
                        template['unwritten_rules'],
                        template['english_requirement'],
                        template['computer_requirement'], 
                        template['age_requirement'],
                        template['second_choice_available'],
                        template['household_priority'],
                        template['major_consistency_required'],
                        template['written_test_score_line'],
                        template['detailed_admission_rules'],
                        template['comprehensive_score_line'],
                        template['position_selection_method'],
                        template['first_batch_fail_second_ok'],
                        template['deferred_graduation_impact'],
                        template['non_first_choice_pass'],
                        template['campus_recruit_then_batch'],
                        template['single_cert_probability'],
                        template['qualification_review_requirements'],
                        template['application_ratio'],
                        template['cost_effectiveness_rank'],
                        template['best_value_city_rank'],
                        template['best_value_district_rank'],
                        template['difficulty_rank']
                    )
                    
                    cursor.execute(insert_query, data)
                    inserted_count += 1
                    logger.info(f"为 {unit['unit_name']} 添加政策规则数据")
            
            cursor.close()
            connection.close()
            
            logger.info(f"成功插入 {inserted_count} 条政策规则示例数据")
            
        except Exception as e:
            logger.error(f"初始化政策规则数据失败: {e}")
            raise e
    
    def init_early_batch_policies_sample_data(self):
        """初始化提前批政策示例数据"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            logger.info("开始初始化提前批政策示例数据...")
            
            early_batch_data = [
                # 国网四川 - unit_id: 5
                (5, '每年10月中旬，为期3天的现场面试和考察', 
                 '本科及以上学历，电气工程相关专业优先', True,
                 '专业知识测试+综合能力评估', True,
                 '学历背景、专业匹配度、综合素质、沟通能力',
                 '成都地区竞争最激烈，其他地市相对宽松',
                 '成都>绵阳>德阳>其他地市',
                 '提前批岗位发展前景好，但地点选择相对有限'),
                
                # 南网广东 - unit_id: 1  
                (1, '分两轮进行，第一轮线上初试，第二轮现场复试',
                 '211院校本科以上学历，硕士优先', True,
                 '专业技能+英语口语+案例分析', True,
                 '学历层次、英语水平、专业能力、管理潜质',
                 '广州深圳录用标准最高，其他地市相对宽松',
                 '深圳>广州>佛山>其他地市',
                 '提前批多为核心技术岗位和储备管理岗位'),
                
                # 国网山东 - unit_id: 3
                (3, '每年9月下旬，集中在济南进行统一面试',
                 '985/211院校本科以上学历', True,
                 '行业知识+综合素质测试', False,
                 '学历背景、专业水平、稳定性、发展潜力',
                 '济南青岛录用人数较多，其他地市机会均等',
                 '济南>青岛>烟台>其他地市',
                 '提前批主要面向技术骨干岗位'),
                
                # 南网广西 - unit_id: 15
                (15, '相对简化，主要在南宁进行集中考核',
                 '本科以上学历，专业要求相对宽松', False,
                 '基础能力测试', True,
                 '工作稳定性、适应能力、基本素质',
                 '南宁地区机会较多，其他地市按需录取',
                 '南宁>柳州>桂林>其他地市',
                 '提前批和统招岗位质量差异不大')
            ]
            
            insert_query = """
                INSERT INTO early_batch_policies_extended 
                (unit_id, schedule_arrangement, education_requirement, written_test_required,
                 written_test_content, station_chasing_allowed, admission_factors,
                 unit_admission_status, difficulty_ranking, position_quality_difference)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.executemany(insert_query, early_batch_data)
            logger.info(f"成功插入 {len(early_batch_data)} 条提前批政策示例数据")
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            logger.error(f"初始化提前批政策数据失败: {e}")
            raise e
    
    def init_rural_grid_policies_sample_data(self):
        """初始化农网政策示例数据"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            logger.info("开始初始化农网政策示例数据...")
            
            rural_grid_data = [
                # 国网四川 - unit_id: 5
                (5, '基本工资5-7万，加上补贴约6-8万/年',
                 '每年4-5月统一考试', '35岁以下',
                 '网申相对容易，主要看稳定性和责任心',
                 '基础能力测试+心理素质评估', 
                 '性格测试重点考察责任心和抗压能力',
                 '需要提供无犯罪记录证明和推荐信', 
                 '电气基础知识+安全规程'),
                
                # 南网广东 - unit_id: 1  
                (1, '基本工资7-9万，综合收入8-11万/年',
                 '每年5-6月分批考试', '32岁以下',
                 '要求本地户籍或有本地工作经验',
                 '线上测评+现场面试相结合', 
                 '注重服务意识和沟通协调能力',
                 '户籍证明、学历认证、体检报告等', 
                 '专业技能+客户服务+安全操作'),
                
                # 国网山东 - unit_id: 3
                (3, '基本工资6-8万，总收入约7-10万/年',
                 '每年3-4月集中招考', '30岁以下',
                 '要求电气相关专业背景',
                 '专业知识+综合素质双重考核', 
                 '重点测试工作责任感和团队协作',
                 '学历证书、专业资格证书等', 
                 '电气专业知识+实操技能'),
                
                # 南网广西 - unit_id: 15
                (15, '基本工资4-6万，综合收入5-7万/年',
                 '每年6-7月统一组织', '40岁以下',
                 '门槛相对较低，重视工作态度',
                 '基本素质测评为主', 
                 '主要测试诚信度和工作责任感',
                 '资格审查相对简单，重点看品德', 
                 '基础知识+实际操作能力')
            ]
            
            insert_query = """
                INSERT INTO rural_grid_policies_extended
                (unit_id, salary_benefits, exam_schedule, age_requirement, application_status,
                 online_assessment, personality_test, qualification_review, written_test_content)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.executemany(insert_query, rural_grid_data)
            logger.info(f"成功插入 {len(rural_grid_data)} 条农网政策示例数据")
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            logger.error(f"初始化农网政策数据失败: {e}")
            raise e
    
    def update_secondary_units_extended_fields(self):
        """更新secondary_units表的扩展字段"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            logger.info("开始更新secondary_units表的扩展字段...")
            
            # 为主要单位添加薪资和分数范围信息
            unit_updates = [
                (5, '6-8万', '70-75分', '网申通过率中等，看重综合素质'),  # 四川
                (1, '8-12万', '75-82分', '竞争激烈，要求较高'), # 广东
                (3, '7-10万', '72-78分', '网申相对容易，政策较稳定'), # 山东
                (15, '5-8万', '65-72分', '政策宽松，机会较多'), # 广西
                (2, '5-7万', '68-73分', '偏远地区，待遇一般'), # 新疆
                (4, '6-9万', '70-76分', '中部地区，发展稳定'), # 河南
                (6, '8-11万', '74-80分', '经济发达，要求较高'), # 江苏
                (7, '7-9万', '72-77分', '中部核心，机会较多'), # 湖北
                (8, '6-8万', '69-74分', '中部地区，政策稳定'), # 湖南
                (9, '8-10万', '73-78分', '经济发达，竞争激烈'), # 浙江
            ]
            
            update_query = """
                UPDATE secondary_units 
                SET salary_range = %s, estimated_score_range = %s, apply_status = %s
                WHERE unit_id = %s
            """
            
            for unit_id, salary, score, status in unit_updates:
                cursor.execute(update_query, (salary, score, status, unit_id))
            
            logger.info(f"成功更新 {len(unit_updates)} 个单位的扩展字段信息")
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            logger.error(f"更新secondary_units扩展字段失败: {e}")
            raise e
    
    def run_initialization(self):
        """运行完整的数据初始化"""
        try:
            logger.info("=== 开始基于bdprod数据库的政策数据初始化 ===")
            
            # 1. 检查扩展表是否存在
            existing_tables = self.check_extension_tables_exist()
            if len(existing_tables) < 4:
                logger.warning("扩展表不完整，请先执行 bdprod_extension_schema.sql 创建扩展表")
                return False
            
            # 2. 获取现有单位数据
            units_data = self.get_secondary_units_data()
            if not units_data:
                logger.error("无法获取单位数据，请检查secondary_units表")
                return False
            
            # 3. 初始化政策规则示例数据
            self.init_policy_rules_sample_data(units_data)
            
            # 4. 初始化提前批政策数据
            self.init_early_batch_policies_sample_data()
            
            # 5. 初始化农网政策数据
            self.init_rural_grid_policies_sample_data()
            
            # 6. 更新secondary_units表的扩展字段
            self.update_secondary_units_extended_fields()
            
            logger.info("=== bdprod数据库政策数据初始化完成 ===")
            return True
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            return False

def main():
    """主函数"""
    try:
        initializer = BdprodDataInitializer()
        success = initializer.run_initialization()
        
        if success:
            print("✅ bdprod数据库政策数据初始化完成！")
            print("现在可以启动Flask应用测试新的API接口：")
            print("- GET /api/v1/policies/filter-options")
            print("- GET /api/v1/policies/unit-details?unit_id=5")  
            print("- GET /api/v1/analytics/schools-by-batch?unit_id=5&batch=一批")
            return 0
        else:
            print("❌ 数据初始化失败，请检查日志信息")
            return 1
        
    except Exception as e:
        print(f"初始化过程出错: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数查一点通 API - Data Search API
为数查一点通功能提供专门的查询接口
"""

from flask import Blueprint, request, jsonify
import mysql.connector
import json
import urllib.parse

class DataSearchAPI:
    def __init__(self):
        """Initialize Data Search API"""
        self.db_config = {
            'host': 'rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
            'port': 3306,
            'database': 'bdprod',
            'user': 'dms_user_9332d9e',
            'password': 'AaBb19990826',
            'charset': 'utf8mb4',
            'autocommit': False,
            'use_unicode': True
        }
    
    def get_mysql_connection(self):
        """Get database connection"""
        return mysql.connector.connect(**self.db_config)
    
    def precise_recruitment_search(self, filters):
        """精准查询接口 - 根据多个筛选条件查询录取数据"""
        try:
            connection = self.get_mysql_connection()
            cursor = connection.cursor()
            
            # 构建查询条件
            conditions = []
            params = []
            
            # 公司类型筛选
            if filters.get('company'):
                conditions.append("rr.company = %s")
                params.append(filters['company'])
            
            # 学校名称筛选
            if filters.get('university_name'):
                conditions.append("u.standard_name LIKE %s")
                params.append(f"%{filters['university_name']}%")
            
            # 二级单位筛选
            if filters.get('secondary_unit'):
                conditions.append("su.unit_name = %s")
                params.append(filters['secondary_unit'])
            
            # 城市筛选 - 这里暂时不过滤，交给政策信息处理
            # if filters.get('city'):
            #     pass  # 城市级别的筛选交给政策信息部分处理
            
            # 区县筛选 - 这里暂时不过滤，交给政策信息处理  
            # if filters.get('county'):
            #     pass  # 区县级别的筛选交给政策信息部分处理
            
            # 批次筛选
            if filters.get('batch'):
                conditions.append("rr.batch = %s") 
                params.append(filters['batch'])
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # 分页参数
            page = filters.get('page', 1)
            limit = filters.get('limit', 50)
            offset = (page - 1) * limit
            
            # 查询总数
            count_query = f"""
                SELECT COUNT(*)
                FROM recruitment_records rr
                JOIN universities u ON rr.university_id = u.university_id
                JOIN secondary_units su ON rr.secondary_unit_id = su.unit_id
                WHERE {where_clause}
            """
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]
            
            # 统计分析
            stats = self._get_search_statistics(cursor, where_clause, params)
            
            # 学校录取统计
            school_stats = self._get_school_recruitment_statistics(cursor, where_clause, params, total_count)
            
            # 二级单位统计 - 修复逻辑：总是返回单位分布数据
            unit_stats = self._get_unit_recruitment_statistics(cursor, where_clause, params, filters, total_count)
            
            cursor.close()
            connection.close()
            
            # 计算分页信息
            total_pages = (total_count + limit - 1) // limit
            
            # 获取网申政策信息 - 调整为省级即可显示政策
            policy_info = None
            should_include_policy = (
                filters.get('company') or  # 新增：有公司信息就可以显示政策
                filters.get('secondary_unit') or 
                filters.get('city') or 
                filters.get('district') or
                filters.get('county') or
                filters.get('education_level')
            )
            
            if should_include_policy:
                policy_info = self._get_recruitment_policy_info(filters)
            
            result = {
                'status': 'success',
                'filters_applied': filters,
                'total_records': total_count,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total_count,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                },
                'statistics': stats,
                'school_statistics': school_stats,
                'unit_statistics': unit_stats,
                'data': []
            }
            
            # 如果有政策信息，添加到结果中
            if policy_info:
                result['policy_info'] = policy_info
                
            return result
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'精准查询失败: {str(e)}'
            }
    
    def _get_search_statistics(self, cursor, where_clause, params):
        """获取搜索结果的统计信息"""
        try:
            stats = {}
            
            # 性别分布
            query = f"""
                SELECT rr.gender, COUNT(*) as count
                FROM recruitment_records rr
                JOIN universities u ON rr.university_id = u.university_id
                JOIN secondary_units su ON rr.secondary_unit_id = su.unit_id
                WHERE {where_clause}
                GROUP BY rr.gender
            """
            cursor.execute(query, params)
            gender_results = cursor.fetchall()
            gender_dist = {k if k is not None else '未知': v for k, v in gender_results}
            stats['gender_distribution'] = gender_dist
            
            # 公司分布
            query = f"""
                SELECT rr.company, COUNT(*) as count
                FROM recruitment_records rr
                JOIN universities u ON rr.university_id = u.university_id
                JOIN secondary_units su ON rr.secondary_unit_id = su.unit_id
                WHERE {where_clause}
                GROUP BY rr.company
            """
            cursor.execute(query, params)
            company_results = cursor.fetchall()
            company_dist = {k if k is not None else '未知': v for k, v in company_results}
            stats['company_distribution'] = company_dist
            
            # 学校层次分布
            query = f"""
                SELECT u.level, COUNT(*) as count
                FROM recruitment_records rr
                JOIN universities u ON rr.university_id = u.university_id
                JOIN secondary_units su ON rr.secondary_unit_id = su.unit_id
                WHERE {where_clause}
                GROUP BY u.level
                ORDER BY count DESC
            """
            cursor.execute(query, params)
            level_results = cursor.fetchall()
            level_dist = {k if k is not None else '未知': v for k, v in level_results}
            stats['university_level_distribution'] = level_dist
            
            # 批次分布
            query = f"""
                SELECT rr.batch, COUNT(*) as count
                FROM recruitment_records rr
                JOIN universities u ON rr.university_id = u.university_id
                JOIN secondary_units su ON rr.secondary_unit_id = su.unit_id
                WHERE {where_clause}
                GROUP BY rr.batch
                ORDER BY count DESC
            """
            cursor.execute(query, params)
            batch_results = cursor.fetchall()
            batch_dist = {k if k is not None else '未知': v for k, v in batch_results}
            stats['batch_distribution'] = batch_dist
            
            return stats
            
        except Exception as e:
            return {'error': f'统计分析失败: {str(e)}'}
    
    def _get_school_recruitment_statistics(self, cursor, where_clause, params, total_count):
        """获取学校录取统计数据"""
        try:
            # 查询学校录取统计：学校名称、学校类型、学校层次、录取人数、占比
            query = f"""
                SELECT 
                    u.standard_name as school_name,
                    u.type as school_type,
                    u.level as school_level,
                    COUNT(*) as recruitment_count
                FROM recruitment_records rr
                JOIN universities u ON rr.university_id = u.university_id
                JOIN secondary_units su ON rr.secondary_unit_id = su.unit_id
                WHERE {where_clause}
                GROUP BY u.university_id, u.standard_name, u.type, u.level
                ORDER BY recruitment_count DESC, u.standard_name
            """
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            school_statistics = []
            for row in results:
                school_name = row[0] if row[0] else '未知学校'
                school_type = row[1] if row[1] else '未知类型'
                school_level = row[2] if row[2] else '未知层次'
                recruitment_count = row[3]
                
                # 计算占比
                percentage = round((recruitment_count / total_count) * 100, 2) if total_count > 0 else 0
                
                school_statistics.append({
                    'school_name': school_name,
                    'school_type': school_type,
                    'school_level': school_level,
                    'recruitment_count': recruitment_count,
                    'percentage': percentage
                })
            
            return {
                'total_schools': len(school_statistics),
                'schools': school_statistics
            }
            
        except Exception as e:
            return {'error': f'学校统计分析失败: {str(e)}'}
    
    def _get_unit_recruitment_statistics(self, cursor, where_clause, params, filters, total_count):
        """获取二级单位录取统计数据 - 修复版本，始终返回数据"""
        try:
            # 查询二级单位录取统计：单位名称、地区、录取人数、占比
            query = f"""
                SELECT 
                    su.unit_name,
                    su.region,
                    COUNT(*) as recruitment_count
                FROM recruitment_records rr
                JOIN universities u ON rr.university_id = u.university_id
                JOIN secondary_units su ON rr.secondary_unit_id = su.unit_id
                WHERE {where_clause}
                GROUP BY su.unit_id, su.unit_name, su.region
                ORDER BY recruitment_count DESC, su.unit_name
            """
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            unit_statistics = []
            for row in results:
                unit_name = row[0] if row[0] else '未知单位'
                region = row[1] if row[1] else '未知地区'
                recruitment_count = row[2]
                
                # 计算占比
                percentage = round((recruitment_count / total_count) * 100, 2) if total_count > 0 else 0
                
                unit_statistics.append({
                    'unit_name': unit_name,
                    'region': region,
                    'recruitment_count': recruitment_count,
                    'percentage': percentage
                })
            
            return {
                'available': True,
                'covered_units': len(unit_statistics),
                'units': unit_statistics
            }
            
        except Exception as e:
            return {
                'available': False,
                'error': f'二级单位统计分析失败: {str(e)}',
                'covered_units': 0,
                'units': []
            }
    
    def search_universities(self, query, limit=10):
        """学校智能搜索 - 支持模糊匹配"""
        try:
            connection = self.get_mysql_connection()
            cursor = connection.cursor()
            
            # 支持学校名称模糊搜索
            search_query = """
                SELECT u.university_id, u.standard_name, u.type, u.level, u.location, u.power_feature,
                       COALESCE(rr_count.total_recruitment, 0) as total_recruitment
                FROM universities u
                LEFT JOIN (
                    SELECT university_id, COUNT(*) as total_recruitment
                    FROM recruitment_records 
                    GROUP BY university_id
                ) rr_count ON u.university_id = rr_count.university_id
                WHERE u.standard_name LIKE %s
                ORDER BY total_recruitment DESC, u.standard_name
                LIMIT %s
            """
            
            search_pattern = f"%{query}%"
            cursor.execute(search_query, (search_pattern, limit))
            results = cursor.fetchall()
            
            universities = []
            for row in results:
                universities.append({
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'level': row[3],
                    'location': row[4],
                    'power_feature': row[5],
                    'total_recruitment': row[6]
                })
            
            cursor.close()
            connection.close()
            
            return {
                'status': 'success',
                'query': query,
                'total_found': len(universities),
                'data': universities
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'学校搜索失败: {str(e)}'
            }
    
    def get_secondary_units_by_company(self, company_type):
        """根据公司类型获取对应的二级单位 - 优化版本"""
        try:
            connection = self.get_mysql_connection()
            cursor = connection.cursor()
            
            # 根据公司类型筛选二级单位，关联recruitment_records表
            query = """
                SELECT su.unit_id, su.unit_name, su.region, su.unit_type,
                       COUNT(*) as recruitment_count,
                       ROUND(COUNT(*) * 100.0 / total.total_count, 2) as percentage
                FROM secondary_units su
                INNER JOIN recruitment_records rr ON su.unit_id = rr.secondary_unit_id 
                CROSS JOIN (
                    SELECT COUNT(*) as total_count 
                    FROM recruitment_records 
                    WHERE company = %s
                ) total
                WHERE rr.company = %s
                GROUP BY su.unit_id, su.unit_name, su.region, su.unit_type, total.total_count
                ORDER BY recruitment_count DESC, su.unit_name
            """
            
            cursor.execute(query, (company_type, company_type))
            results = cursor.fetchall()
            
            secondary_units = []
            region_stats = {}
            
            for row in results:
                unit_data = {
                    'unit_id': row[0],
                    'unit_name': row[1],
                    'region': row[2] or '未分类',
                    'unit_type': row[3] or '未分类',
                    'recruitment_count': row[4],
                    'percentage': float(row[5]),
                    'company_type': company_type
                }
                secondary_units.append(unit_data)
                
                # 统计各地区数据
                region = unit_data['region']
                if region not in region_stats:
                    region_stats[region] = {'count': 0, 'units': 0}
                region_stats[region]['count'] += unit_data['recruitment_count']
                region_stats[region]['units'] += 1
            
            # 转换地区统计为列表格式
            region_list = []
            for region, stats in region_stats.items():
                region_list.append({
                    'region': region,
                    'total_recruitment': stats['count'],
                    'unit_count': stats['units']
                })
            region_list.sort(key=lambda x: x['total_recruitment'], reverse=True)
            
            cursor.close()
            connection.close()
            
            return {
                'status': 'success',
                'company_type': company_type,
                'total_units': len(secondary_units),
                'total_recruitment': sum(unit['recruitment_count'] for unit in secondary_units),
                'region_distribution': region_list,
                'data': secondary_units
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'获取二级单位失败: {str(e)}'
            }
        
    def _safe_float_convert(self, value):
        """安全地转换值为浮点数，处理文本和特殊值"""
        if value is None or value == '':
            return None
        
        # 如果已经是数字类型
        if isinstance(value, (int, float)):
            return float(value)
        
        # 如果是字符串，尝试转换
        if isinstance(value, str):
            # 清理字符串
            cleaned = value.strip()
            if cleaned == '' or cleaned.lower() in ['null', 'none', 'n/a', '无', '无法确定']:
                return None
            
            # 特殊文本值处理
            if cleaned in ['能过网申', '过网申', '可过', '能过']:
                return 1.0  # 表示可以通过
            elif cleaned in ['不能过', '无法过', '过不了']:
                return 0.0  # 表示不能通过
                
            # 尝试直接转换数字
            try:
                return float(cleaned)
            except ValueError:
                # 如果无法转换，返回None
                return None
                
        return None
    
    def _get_min_qualification_threshold(self, policy, degree_level):
        """计算最低学历要求阈值"""
        if degree_level == 'bachelor':
            # 本专科学历从高到低的层次顺序
            bachelor_hierarchy = [
                ('985', 'bachelor_985'),
                ('211', 'bachelor_211'),
                ('省内双一流', 'bachelor_provincial_double_first'),
                ('省外双一流', 'bachelor_external_double_first'),
                ('省内双非一本', 'bachelor_provincial_non_double'),
                ('省外双非一本', 'bachelor_external_non_double'),
                ('省内二本', 'bachelor_provincial_second'),
                ('省外二本', 'bachelor_external_second'),
                ('民办本科', 'bachelor_private'),
                ('专升本', 'bachelor_upgrade'),
                ('专科', 'bachelor_college')
            ]
            
            # 从高到低遍历，找到最后一个有值的项目（真正的最低门槛）
            last_valid_level = None
            for level_name, field_name in bachelor_hierarchy:
                if policy.get(field_name) is not None and policy.get(field_name) != '':
                    last_valid_level = level_name
                else:
                    # 遇到第一个没值的就停止，返回上一个有值的
                    if last_valid_level:
                        return last_valid_level
            # 如果所有级别都有值，返回最后一个（最低的）
            return last_valid_level
            
        elif degree_level == 'master':
            # 硕士学历从高到低的层次顺序
            master_hierarchy = [
                ('985', 'master_985'),
                ('211', 'master_211'),
                ('省内双一流', 'master_provincial_double_first'),
                ('省外双一流', 'master_external_double_first'),
                ('省内双非', 'master_provincial_non_double'),
                ('省外双非', 'master_external_non_double')
            ]
            
            # 从高到低遍历，找到最后一个有值的项目（真正的最低门槛）
            last_valid_level = None
            for level_name, field_name in master_hierarchy:
                if policy.get(field_name) is not None and policy.get(field_name) != '':
                    last_valid_level = level_name
                else:
                    # 遇到第一个没值的就停止，返回上一个有值的
                    if last_valid_level:
                        return last_valid_level
            # 如果所有级别都有值，返回最后一个（最低的）
            return last_valid_level
            
        return None

    def _get_recruitment_policy_info(self, filters):
        """获取网申政策信息 - 用于搜索接口"""
        try:
            connection = self.get_mysql_connection()
            cursor = connection.cursor(dictionary=True)
            
            # 构建查询条件
            conditions = []
            params = []
            
            # 映射搜索条件到政策表字段
            # 根据搜索参数推断地区信息
            province = None
            city = filters.get('city')
            district = None
            
            # 从secondary_unit参数推断省份 - 不依赖company参数
            if filters.get('secondary_unit'):
                # secondary_unit在这里可能是省份名
                if filters['secondary_unit'] in ['四川', '成都', '天府', '绵阳']:
                    province = '四川'
                    if filters['secondary_unit'] in ['成都', '天府', '绵阳']:
                        city = filters['secondary_unit']
                elif filters['secondary_unit'] in ['北京', '上海', '天津', '重庆']:
                    province = filters['secondary_unit']
                    # 对于直辖市，不设置city，让它匹配数据库中city为NULL的记录
                else:
                    # 可能是其他省份
                    province = filters['secondary_unit']
            
            # 从company参数进一步推断（如果有的话）
            if filters.get('company') == '国网' and filters.get('secondary_unit'):
                # 这里可以添加更精确的国网单位映射逻辑
                pass
            
            # 从city参数获取城市信息
            if filters.get('city'):
                city = filters['city']
                # 根据城市推断省份
                if city in ['成都', '天府', '绵阳']:
                    province = '四川'
                elif city in ['北京']:
                    province = '北京'
                elif city in ['上海', '黄浦区']:
                    province = '上海'
                elif city in ['天津']:
                    province = '天津'
                elif city in ['重庆', '渝中区']:
                    province = '重庆'
            
            # 从county参数推断城市和省份信息
            if filters.get('county') and not city:
                county = filters['county']
                # 根据区县推断城市和省份 - 这里可以扩展更多映射
                if county in ['游仙区', '涪城区']:
                    city = '绵阳'
                    province = '四川'
                elif county in ['黄浦区', '浦东新区', '静安区']:
                    city = '上海'
                    province = '上海'
                elif county in ['朝阳区', '海淀区', '西城区']:
                    city = '北京'  
                    province = '北京'
            
            # 构建查询条件
            if province:
                conditions.append("province = %s")
                params.append(province)
            
            if city:
                conditions.append("city = %s")
                params.append(city)
            
            # 如果有district参数，映射到company字段
            if filters.get('district'):
                conditions.append("company = %s")
                params.append(filters['district'])
            
            # 如果有county参数，映射到company字段（区县级筛选）
            if filters.get('county'):
                conditions.append("company = %s")
                params.append(filters['county'])
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # 查询政策信息 - 包含所有学历层次和性价比字段
            query = f"""
                SELECT 
                    id, province, city, company as district, data_level,
                    cet_requirement, bachelor_interview_line, master_interview_line,
                    bachelor_salary, master_salary, detailed_rules,
                    bachelor_985, bachelor_211, master_985, master_211,
                    bachelor_provincial_double_first, bachelor_external_double_first,
                    bachelor_provincial_non_double, bachelor_external_non_double,
                    bachelor_provincial_second, bachelor_external_second,
                    bachelor_private, bachelor_upgrade, bachelor_college,
                    master_provincial_double_first, master_external_double_first,
                    master_provincial_non_double, master_external_non_double,
                    admission_ratio, household_priority, bachelor_comprehensive_score,
                    is_best_value_city, is_best_value_county
                FROM recruitment_rules
                WHERE {where_clause}
                ORDER BY 
                    CASE data_level 
                        WHEN '省级汇总' THEN 1 
                        WHEN '市级汇总' THEN 2 
                        WHEN '区县详情' THEN 3 
                    END,
                    province, city, company
            """
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                cursor.close()
                connection.close()
                return None
            
            # 处理政策信息叠加逻辑：省级 -> 市级 -> 区县级
            policy_hierarchy = {
                '省级汇总': [],
                '市级汇总': [],
                '区县详情': []
            }
            
            for row in results:
                policy_hierarchy[row['data_level']].append(row)
            
            # 选择最合适的政策信息 - 优先显示区县详情（已合并省市级信息）
            final_policies = []
            
            # 如果指定了具体区县，只返回该区县的政策
            if filters.get('county'):
                county_name = filters['county']
                county_policies = [p for p in policy_hierarchy['区县详情'] if p['district'] == county_name]
                if county_policies:
                    final_policies.extend(county_policies)
                else:
                    # 如果没有该区县的具体政策，降级到市级或省级
                    if policy_hierarchy['市级汇总']:
                        final_policies.extend(policy_hierarchy['市级汇总'])
                    elif policy_hierarchy['省级汇总']:
                        final_policies.extend(policy_hierarchy['省级汇总'])
            # 优先显示区县详情政策（已包含完整信息）
            elif policy_hierarchy['区县详情']:
                final_policies.extend(policy_hierarchy['区县详情'])
            # 降级到市级政策
            elif policy_hierarchy['市级汇总']:
                final_policies.extend(policy_hierarchy['市级汇总'])
            # 最后降级到省级政策
            elif policy_hierarchy['省级汇总']:
                final_policies.extend(policy_hierarchy['省级汇总'])
            
            # 格式化政策信息
            policy_info = {
                'available': True,
                'total_policies': len(final_policies),
                'data_source': 'recruitment_rules',
                'policies': []
            }
            
            for policy in final_policies:
                # 根据学历层次过滤信息
                education_level = filters.get('education_level')
                
                # 计算最低学历要求
                bachelor_min_requirement = self._get_min_qualification_threshold(policy, 'bachelor')
                master_min_requirement = self._get_min_qualification_threshold(policy, 'master')
                
                policy_data = {
                    'policy_id': policy['id'],
                    'location': {
                        'province': policy['province'],
                        'city': policy['city'],
                        'district': policy['district']
                    },
                    'data_level': policy['data_level'],
                    'basic_requirements': {
                        'cet_requirement': policy['cet_requirement']
                    },
                    'interview_info': {},
                    'salary_info': {},
                    'school_requirements': {
                        'bachelor_min_requirement': bachelor_min_requirement,
                        'master_min_requirement': master_min_requirement
                    },
                    'additional_info': {
                        'admission_ratio': policy['admission_ratio'],
                        'household_priority': policy['household_priority'],
                        'is_best_value_city': policy['is_best_value_city'],
                        'is_best_value_county': policy['is_best_value_county']
                    }
                }
                
                # 创建教育水平字段映射
                education_field_mapping = {
                    'bachelor_985': 'bachelor_985',
                    'bachelor_211': 'bachelor_211', 
                    'bachelor_provincial_double_first': 'bachelor_provincial_double_first',
                    'bachelor_external_double_first': 'bachelor_external_double_first',
                    'bachelor_provincial_non_double': 'bachelor_provincial_non_double',
                    'bachelor_external_non_double': 'bachelor_external_non_double',
                    'bachelor_provincial_second': 'bachelor_provincial_second',
                    'bachelor_external_second': 'bachelor_external_second',
                    'bachelor_private': 'bachelor_private',
                    'bachelor_upgrade': 'bachelor_upgrade',
                    'bachelor_college': 'bachelor_college',
                    'master_985': 'master_985',
                    'master_211': 'master_211',
                    'master_provincial_double_first': 'master_provincial_double_first',
                    'master_external_double_first': 'master_external_double_first',
                    'master_provincial_non_double': 'master_provincial_non_double',
                    'master_external_non_double': 'master_external_non_double'
                }
                
                # 如果指定了特定的教育水平，返回对应字段的值
                if education_level and education_level in education_field_mapping:
                    field_name = education_field_mapping[education_level]
                    policy_data['education_value'] = policy.get(field_name)
                    policy_data['education_level'] = education_level
                    policy_data['field_name'] = field_name
                
                # 无论是否指定教育水平，都返回基本的薪资和面试信息
                if not education_level or education_level in ['bachelor', 'bachelor_985', 'bachelor_211', 'bachelor_provincial_double_first', 'bachelor_external_double_first', 'bachelor_provincial_non_double', 'bachelor_external_non_double', 'bachelor_provincial_second', 'bachelor_external_second', 'bachelor_private', 'bachelor_upgrade', 'bachelor_college'] or education_level.startswith('bachelor'):
                    policy_data['interview_info']['bachelor_interview_line'] = policy['bachelor_interview_line']
                    policy_data['interview_info']['bachelor_comprehensive_score'] = policy['bachelor_comprehensive_score']
                    policy_data['salary_info']['bachelor_salary'] = policy['bachelor_salary']
                    policy_data['school_requirements']['bachelor_985'] = policy['bachelor_985']
                    policy_data['school_requirements']['bachelor_211'] = policy['bachelor_211']
                
                if not education_level or education_level in ['master', 'master_985', 'master_211', 'master_provincial_double_first', 'master_external_double_first', 'master_provincial_non_double', 'master_external_non_double'] or education_level.startswith('master'):
                    policy_data['interview_info']['master_interview_line'] = policy['master_interview_line']
                    policy_data['salary_info']['master_salary'] = policy['master_salary']  
                    policy_data['school_requirements']['master_985'] = policy['master_985']
                    policy_data['school_requirements']['master_211'] = policy['master_211']
                
                # 添加详细规则（如果存在）
                if policy['detailed_rules']:
                    policy_data['detailed_rules'] = policy['detailed_rules'][:200] + '...' if len(policy['detailed_rules']) > 200 else policy['detailed_rules']
                
                policy_info['policies'].append(policy_data)
            
            cursor.close()
            connection.close()
            
            return policy_info
            
        except Exception as e:
            return {
                'available': False,
                'error': f'政策信息获取失败: {str(e)}',
                'data_source': 'recruitment_rules'
            }
    
    def get_cascade_location_options(self, level='province', province=None, city=None, company=None):
        """省市区县三级级联查询 - 基于 recruitment_rules 表"""
        try:
            connection = self.get_mysql_connection()
            cursor = connection.cursor()
            
            if level == 'province':
                # 获取所有省份，优先从recruitment_rules表获取
                # 使用 COLLATE 确保字符串比较使用一致的排序规则
                query = """
                    SELECT DISTINCT province, COUNT(rr_data.record_count) as total_records
                    FROM recruitment_rules rr
                    LEFT JOIN (
                        SELECT su.unit_name as province_name, COUNT(*) as record_count
                        FROM recruitment_records rec
                        JOIN secondary_units su ON rec.secondary_unit_id = su.unit_id
                        GROUP BY su.unit_name
                    ) rr_data ON CONVERT(rr.province USING utf8mb4) COLLATE utf8mb4_unicode_ci = CONVERT(rr_data.province_name USING utf8mb4) COLLATE utf8mb4_unicode_ci
                    GROUP BY province
                    ORDER BY total_records DESC, province
                """
                cursor.execute(query)
                results = cursor.fetchall()
                
                # 如果recruitment_rules表为空，降级到secondary_units表
                if not results:
                    query = """
                        SELECT DISTINCT su.unit_name as province, COUNT(rr.record_id) as count
                        FROM secondary_units su
                        LEFT JOIN recruitment_records rr ON su.unit_id = rr.secondary_unit_id
                        WHERE su.unit_name IS NOT NULL
                        GROUP BY su.unit_name
                        ORDER BY count DESC, su.unit_name
                    """
                    cursor.execute(query)
                    results = cursor.fetchall()
                    source = 'secondary_units_fallback'
                else:
                    source = 'recruitment_rules'
                
                options = []
                for row in results:
                    options.append({
                        'name': row[0],
                        'count': row[1] if row[1] else 0
                    })
                
                return {
                    'status': 'success',
                    'level': 'province',
                    'data': options,
                    'source': source
                }
                
            elif level == 'city' and province:
                # 基于recruitment_rules表获取城市信息（data_level='市级汇总'）
                # 使用 CONVERT 确保字符串比较使用一致的编码和排序规则
                # 简化查询：先获取所有四川省的数据，不带任何WHERE条件过滤
                query = """
                    SELECT DISTINCT city, COUNT(*) as policy_count
                    FROM recruitment_rules 
                    WHERE province = %s
                        AND city IS NOT NULL AND city != ''
                    GROUP BY city
                    ORDER BY policy_count DESC, city
                """
                cursor.execute(query, (province,))
                results = cursor.fetchall()
                
                # 处理直辖市情况（北京、上海、天津、重庆）
                if not results and province in ['北京', '上海', '天津', '重庆']:
                    # 直辖市的省市名称相同
                    query = """
                        SELECT DISTINCT province as city,
                               COUNT(CASE WHEN data_level IN ('省级汇总', '市级汇总') THEN 1 END) as policy_count,
                               0 as recruitment_count
                        FROM recruitment_rules
                        WHERE province = %s
                        GROUP BY province
                    """
                    cursor.execute(query, (province,))
                    results = cursor.fetchall()
                    source = 'direct_municipality'
                else:
                    source = 'recruitment_rules'
                
                options = [{'name': row[0], 'policy_count': row[1], 'recruitment_count': 0} for row in results]
                
                return {
                    'status': 'success',
                    'level': 'city',
                    'province': province,
                    'data': options,
                    'source': source
                }
                
            elif level == 'district' and province and city:
                # 基于recruitment_rules表获取区县/单位信息，直接查询company字段
                query = """
                    SELECT DISTINCT
                        rr.company as district,
                        COUNT(rec.record_id) as recruitment_count,
                        COUNT(rr.id) as policy_count
                    FROM recruitment_rules rr
                    LEFT JOIN recruitment_records rec ON (
                        CONVERT(rec.company USING utf8mb4) COLLATE utf8mb4_unicode_ci = CONVERT(rr.province USING utf8mb4) COLLATE utf8mb4_unicode_ci OR 
                        CONVERT(rec.company USING utf8mb4) COLLATE utf8mb4_unicode_ci = CONVERT(rr.city USING utf8mb4) COLLATE utf8mb4_unicode_ci OR 
                        CONVERT(rec.company USING utf8mb4) COLLATE utf8mb4_unicode_ci = CONVERT(rr.company USING utf8mb4) COLLATE utf8mb4_unicode_ci
                    )
                    WHERE CONVERT(rr.province USING utf8mb4) COLLATE utf8mb4_unicode_ci = CONVERT(%s USING utf8mb4) COLLATE utf8mb4_unicode_ci
                        AND CONVERT(rr.city USING utf8mb4) COLLATE utf8mb4_unicode_ci = CONVERT(%s USING utf8mb4) COLLATE utf8mb4_unicode_ci
                        AND rr.company IS NOT NULL 
                        AND rr.company != ''
                        AND rr.data_level = '区县详情'
                    GROUP BY rr.company
                    ORDER BY policy_count DESC, recruitment_count DESC, rr.company
                    LIMIT 20
                """
                cursor.execute(query, (province, city))
                results = cursor.fetchall()
                
                options = []
                for row in results:
                    options.append({
                        'name': row[0],
                        'recruitment_count': row[1],
                        'has_policy': bool(row[2])
                    })
                
                return {
                    'status': 'success',
                    'level': 'district',
                    'province': province,
                    'city': city,
                    'data': options,
                    'source': 'secondary_units_with_policy_check'
                }
            
            else:
                return {
                    'status': 'error',
                    'message': '参数不完整或无效'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'级联查询失败: {str(e)}'
            }
        finally:
            try:
                cursor.close()
                connection.close()
            except:
                pass

    def get_detailed_policy_info(self, province, city=None, district=None, education_level=None):
        """获取详细政策信息 - 返回数据库中的所有原始字段"""
        try:
            connection = self.get_mysql_connection()
            cursor = connection.cursor(dictionary=True)
            
            # 构建查询条件 - 与普通政策API保持一致的逻辑
            conditions = []
            params = []
            
            if province:
                conditions.append("province = %s")
                params.append(province)
            
            if city:
                conditions.append("city = %s")
                params.append(city)
            
            if district:
                conditions.append("company = %s")
                params.append(district)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # 查询所有相关政策信息 - 返回所有字段
            query = f"""
                SELECT *
                FROM recruitment_rules
                WHERE {where_clause}
                ORDER BY 
                    CASE data_level 
                        WHEN '省级汇总' THEN 1 
                        WHEN '市级汇总' THEN 2 
                        WHEN '区县详情' THEN 3 
                    END,
                    city, company
            """
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                cursor.close()
                connection.close()
                return {
                    'status': 'error',
                    'message': '没有找到相关政策信息'
                }
            
            # 处理datetime对象，确保JSON序列化
            processed_results = []
            for row in results:
                processed_row = {}
                for key, value in row.items():
                    if hasattr(value, 'isoformat'):
                        # 处理datetime对象
                        processed_row[key] = value.isoformat()
                    else:
                        processed_row[key] = value
                processed_results.append(processed_row)
            
            cursor.close()
            connection.close()
            
            return {
                'status': 'success',
                'query_params': {
                    'province': province,
                    'city': city,
                    'district': district,
                    'education_level': education_level
                },
                'total_records': len(processed_results),
                'data': processed_results
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'获取详细政策失败: {str(e)}'
            }

    def get_recruitment_policies(self, province=None, city=None, district=None, education_level=None, company=None):
        """获取录取政策 - 精简版，用于批量展示"""
        try:
            connection = self.get_mysql_connection()
            cursor = connection.cursor()
            
            # 构建查询条件
            conditions = []
            params = []
            
            if province:
                conditions.append("province = %s")
                params.append(province)
            
            if city:
                conditions.append("city = %s") 
                params.append(city)
                
            if company:
                conditions.append("company = %s")
                params.append(company)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # 查询政策信息 - 精简版
            query = f"""
                SELECT 
                    province, city, company, data_level,
                    cet_requirement, computer_requirement,
                    bachelor_interview_line, bachelor_comprehensive_score, bachelor_salary,
                    master_interview_line, master_salary,
                    bachelor_985, bachelor_211, bachelor_provincial_double_first,
                    master_985, master_211, master_provincial_double_first,
                    admission_ratio, household_priority,
                    is_best_value_city, is_best_value_county
                FROM recruitment_rules
                WHERE {where_clause}
                ORDER BY 
                    CASE data_level 
                        WHEN '省级汇总' THEN 1 
                        WHEN '市级汇总' THEN 2 
                        WHEN '区县详情' THEN 3 
                    END,
                    province, city
            """
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            policies = []
            for row in results:
                policy = {
                    'province': row[0],
                    'city': row[1], 
                    'company': row[2],
                    'data_level': row[3],
                    'requirements': {
                        'cet_requirement': row[4],
                        'computer_requirement': row[5]
                    },
                    'bachelor_info': {
                        'interview_line': row[6],
                        'comprehensive_score': self._safe_float_convert(row[7]),
                        'salary': row[8],
                        'requirements': {
                            'bachelor_985': row[9],
                            'bachelor_211': row[10],
                            'bachelor_provincial_double_first': row[11]
                        }
                    },
                    'master_info': {
                        'interview_line': self._safe_float_convert(row[12]),
                        'salary': row[13],
                        'requirements': {
                            'master_985': row[14],
                            'master_211': row[15],
                            'master_provincial_double_first': row[16]
                        }
                    },
                    'general_info': {
                        'admission_ratio': row[17],
                        'household_priority': row[18],
                        'is_best_value_city': row[19],
                        'is_best_value_county': row[20]
                    }
                }
                
                # 如果指定了学历层次，只返回对应层次的信息
                if education_level == 'bachelor':
                    policy = {
                        'province': policy['province'],
                        'city': policy['city'],
                        'company': policy['company'],
                        'data_level': policy['data_level'],
                        'requirements': policy['requirements'],
                        'education_info': policy['bachelor_info'],
                        'general_info': policy['general_info']
                    }
                elif education_level == 'master':
                    policy = {
                        'province': policy['province'],
                        'city': policy['city'],
                        'company': policy['company'],
                        'data_level': policy['data_level'],
                        'requirements': policy['requirements'],
                        'education_info': policy['master_info'],
                        'general_info': policy['general_info']
                    }
                
                policies.append(policy)
            
            return {
                'status': 'success',
                'total_policies': len(policies),
                'education_level': education_level or 'all',
                'data': policies
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'获取政策信息失败: {str(e)}'
            }
        finally:
            try:
                cursor.close()
                connection.close()
            except:
                pass


# 创建API实例
data_search_api = DataSearchAPI()

# 创建蓝图
data_search_bp = Blueprint('data_search', __name__)

@data_search_bp.route('/locations/cascade', methods=['GET'])
def get_location_cascade():
    """省市区县三级级联查询接口"""
    level = request.args.get('level', 'province')
    province = request.args.get('province')
    city = request.args.get('city')
    company = request.args.get('company')
    
    # URL解码处理中文参数
    if province:
        province = urllib.parse.unquote(province)
    if city:
        city = urllib.parse.unquote(city)
    if company:
        company = urllib.parse.unquote(company)
    
    result = data_search_api.get_cascade_location_options(level, province, city, company)
    return jsonify(result)

@data_search_bp.route('/policies', methods=['GET'])
def get_policies():
    """获取录取政策 - 精简版，用于批量展示"""
    province = request.args.get('province')
    city = request.args.get('city')
    district = request.args.get('district')
    education_level = request.args.get('education_level')  # bachelor, master
    company = request.args.get('company')
    
    # URL解码处理中文参数
    if province:
        province = urllib.parse.unquote(province)
    if city:
        city = urllib.parse.unquote(city)
    if district:
        district = urllib.parse.unquote(district)
    if company:
        company = urllib.parse.unquote(company)
    
    result = data_search_api.get_recruitment_policies(province, city, district, education_level, company)
    return jsonify(result)

@data_search_bp.route('/policies/detail', methods=['GET'])
def get_policy_detail():
    """获取详细政策信息 - 查看详情接口"""
    province = request.args.get('province')
    city = request.args.get('city')
    # 兼容两种参数名：district 和 company
    district = request.args.get('district') or request.args.get('company')
    education_level = request.args.get('education_level')  # bachelor, master
    
    if not province:
        return jsonify({
            'status': 'error',
            'message': '请提供province参数'
        }), 400
    
    # URL解码处理中文参数
    province = urllib.parse.unquote(province)
    if city:
        city = urllib.parse.unquote(city)
    if district:
        district = urllib.parse.unquote(district)
    
    result = data_search_api.get_detailed_policy_info(province, city, district, education_level)
    return jsonify(result)

@data_search_bp.route('/search', methods=['POST'])
def precise_search():
    """精准查询接口"""
    filters = request.get_json() or {}
    result = data_search_api.precise_recruitment_search(filters)
    return jsonify(result)

@data_search_bp.route('/schools/search', methods=['GET'])
def search_schools():
    """学校智能搜索接口"""
    query = request.args.get('query')
    limit = int(request.args.get('limit', 10))
    
    if not query:
        return jsonify({
            'status': 'error',
            'message': '请提供搜索关键词query参数'
        }), 400
    
    # URL解码处理中文参数
    query = urllib.parse.unquote(query)
    
    result = data_search_api.search_universities(query, limit)
    return jsonify(result)

@data_search_bp.route('/secondary-units', methods=['GET'])
def get_secondary_units():
    """根据公司类型获取二级单位"""
    company_type = request.args.get('company_type')
    
    if not company_type:
        return jsonify({
            'status': 'error',
            'message': '请提供company_type参数'
        }), 400
    
    # URL解码处理中文参数
    company_type = urllib.parse.unquote(company_type)
    
    result = data_search_api.get_secondary_units_by_company(company_type)
    return jsonify(result)

# 导出蓝图
__all__ = ['data_search_bp']

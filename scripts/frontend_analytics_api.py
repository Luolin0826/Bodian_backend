#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frontend Analytics API - 前端数据分析专用接口
根据筛选条件提供前端需要的所有分析数据
"""

from flask import Blueprint, request, jsonify
import mysql.connector
import urllib.parse

class FrontendAnalyticsAPI:
    def __init__(self):
        """Initialize analytics API"""
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
    
    def get_frontend_analytics(self, filters=None):
        """
        获取前端数据分析所需的完整信息
        
        Args:
            filters (dict): 筛选条件 {
                'company': '国网',
                'batch': '第一批',
                'region': '华东',
                'university_level': '211工程',
                'university_type': '理工类',
                'secondary_unit': '江苏',
                'gender': '男'
            }
        
        Returns:
            dict: 完整的分析数据
        """
        try:
            connection = self.get_mysql_connection()
            cursor = connection.cursor()
            
            # 构建筛选条件
            conditions = []
            params = []
            
            if filters:
                if filters.get('company'):
                    conditions.append("r.company = %s")
                    params.append(filters['company'])
                
                if filters.get('batch'):
                    conditions.append("r.batch = %s")
                    params.append(filters['batch'])
                
                if filters.get('region'):
                    conditions.append("s.region = %s")
                    params.append(filters['region'])
                
                if filters.get('university_level'):
                    conditions.append("u.level = %s")
                    params.append(filters['university_level'])
                
                if filters.get('university_type'):
                    conditions.append("u.type = %s")
                    params.append(filters['university_type'])
                
                if filters.get('secondary_unit'):
                    conditions.append("s.unit_name = %s")
                    params.append(filters['secondary_unit'])
                
                if filters.get('gender'):
                    conditions.append("r.gender = %s")
                    params.append(filters['gender'])
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            analytics_data = {}
            
            # 1. 总录取人数
            sql = f"""
            SELECT COUNT(*) as total_count
            FROM recruitment_records r
            LEFT JOIN universities u ON r.university_id = u.university_id
            LEFT JOIN secondary_units s ON r.secondary_unit_id = s.unit_id
            {where_clause}
            """
            cursor.execute(sql, params)
            analytics_data['total_count'] = cursor.fetchone()[0]
            
            # 2. 重点学校录取人数（双一流及以上：985工程、211工程、双一流）
            sql = f"""
            SELECT COUNT(*) as key_university_count
            FROM recruitment_records r
            LEFT JOIN universities u ON r.university_id = u.university_id
            LEFT JOIN secondary_units s ON r.secondary_unit_id = s.unit_id
            {where_clause}
            {'AND' if where_clause else 'WHERE'} u.level IN ('985工程', '211工程', '双一流')
            """
            cursor.execute(sql, params)
            key_uni_count = cursor.fetchone()[0]
            analytics_data['key_university_count'] = key_uni_count
            analytics_data['key_university_percentage'] = round((key_uni_count / analytics_data['total_count'] * 100), 2) if analytics_data['total_count'] > 0 else 0
            
            # 3. 男女性别比例
            sql = f"""
            SELECT r.gender, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
            FROM recruitment_records r
            LEFT JOIN universities u ON r.university_id = u.university_id
            LEFT JOIN secondary_units s ON r.secondary_unit_id = s.unit_id
            {where_clause}
            GROUP BY r.gender
            """
            cursor.execute(sql, params)
            gender_data = {}
            for row in cursor.fetchall():
                if row[0]:  # 过滤掉NULL值
                    gender_data[row[0]] = {
                        'count': row[1],
                        'percentage': float(row[2])
                    }
            analytics_data['gender_distribution'] = gender_data
            
            # 4. 覆盖省份数量（通过secondary_units的region统计）
            sql = f"""
            SELECT COUNT(DISTINCT s.region) as province_count
            FROM recruitment_records r
            LEFT JOIN universities u ON r.university_id = u.university_id
            LEFT JOIN secondary_units s ON r.secondary_unit_id = s.unit_id
            {where_clause}
            """
            cursor.execute(sql, params)
            analytics_data['covered_provinces'] = cursor.fetchone()[0]
            
            # 5. 学校类型分布
            sql = f"""
            SELECT u.type, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
            FROM recruitment_records r
            LEFT JOIN universities u ON r.university_id = u.university_id
            LEFT JOIN secondary_units s ON r.secondary_unit_id = s.unit_id
            {where_clause}
            GROUP BY u.type
            ORDER BY count DESC
            """
            cursor.execute(sql, params)
            school_types = []
            for row in cursor.fetchall():
                if row[0]:  # 过滤掉NULL值
                    school_types.append({
                        'type': row[0],
                        'count': row[1],
                        'percentage': float(row[2])
                    })
            analytics_data['school_type_distribution'] = school_types
            
            # 6. 地区录取分布（按二级单位分布）
            sql = f"""
            SELECT s.region, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
            FROM recruitment_records r
            LEFT JOIN universities u ON r.university_id = u.university_id
            LEFT JOIN secondary_units s ON r.secondary_unit_id = s.unit_id
            {where_clause}
            GROUP BY s.region
            ORDER BY count DESC
            """
            cursor.execute(sql, params)
            regional_distribution = []
            for row in cursor.fetchall():
                if row[0]:  # 过滤掉NULL值
                    regional_distribution.append({
                        'region': row[0],
                        'count': row[1],
                        'percentage': float(row[2])
                    })
            analytics_data['regional_distribution'] = regional_distribution
            
            cursor.close()
            connection.close()
            
            return analytics_data
            
        except Exception as e:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
            return {'error': f'前端分析数据获取失败: {str(e)}'}
    
    def get_school_details_list(self, filters=None, page=1, limit=20):
        """
        获取学校详细信息列表：学校名称、学校类型、录取人数、占比
        
        Args:
            filters (dict): 筛选条件
            page (int): 页码
            limit (int): 每页数量
        
        Returns:
            dict: 学校详细信息列表
        """
        try:
            connection = self.get_mysql_connection()
            cursor = connection.cursor()
            
            # 构建筛选条件（与前面相同的逻辑）
            conditions = []
            params = []
            
            if filters:
                if filters.get('company'):
                    conditions.append("r.company = %s")
                    params.append(filters['company'])
                
                if filters.get('batch'):
                    conditions.append("r.batch = %s")
                    params.append(filters['batch'])
                
                if filters.get('region'):
                    conditions.append("s.region = %s")
                    params.append(filters['region'])
                
                if filters.get('university_level'):
                    conditions.append("u.level = %s")
                    params.append(filters['university_level'])
                
                if filters.get('university_type'):
                    conditions.append("u.type = %s")
                    params.append(filters['university_type'])
                
                if filters.get('secondary_unit'):
                    conditions.append("s.unit_name = %s")
                    params.append(filters['secondary_unit'])
                
                if filters.get('gender'):
                    conditions.append("r.gender = %s")
                    params.append(filters['gender'])
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            # 计算偏移量
            offset = (page - 1) * limit
            
            # 获取总数（用于计算占比）
            total_sql = f"""
            SELECT COUNT(*)
            FROM recruitment_records r
            LEFT JOIN universities u ON r.university_id = u.university_id
            LEFT JOIN secondary_units s ON r.secondary_unit_id = s.unit_id
            {where_clause}
            """
            cursor.execute(total_sql, params)
            total_records = cursor.fetchone()[0]
            
            # 获取学校详细列表
            sql = f"""
            SELECT u.university_id, u.standard_name, u.level, u.type, 
                   u.power_feature, u.location, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / %s, 2) as percentage
            FROM recruitment_records r
            LEFT JOIN universities u ON r.university_id = u.university_id
            LEFT JOIN secondary_units s ON r.secondary_unit_id = s.unit_id
            {where_clause}
            GROUP BY u.university_id, u.standard_name, u.level, u.type, u.power_feature, u.location
            ORDER BY count DESC
            LIMIT %s OFFSET %s
            """
            cursor.execute(sql, params + [total_records, limit, offset])
            
            schools = []
            for row in cursor.fetchall():
                schools.append({
                    'university_id': row[0],
                    'school_name': row[1],
                    'school_level': row[2],
                    'school_type': row[3],
                    'power_feature': row[4],
                    'location': row[5],
                    'recruitment_count': row[6],
                    'percentage': float(row[7])
                })
            
            # 获取总的学校数量（用于分页）
            count_sql = f"""
            SELECT COUNT(DISTINCT u.university_id)
            FROM recruitment_records r
            LEFT JOIN universities u ON r.university_id = u.university_id
            LEFT JOIN secondary_units s ON r.secondary_unit_id = s.unit_id
            {where_clause}
            """
            cursor.execute(count_sql, params)
            total_schools = cursor.fetchone()[0]
            
            cursor.close()
            connection.close()
            
            return {
                'schools': schools,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total_schools,
                    'total_pages': (total_schools + limit - 1) // limit
                },
                'total_records': total_records
            }
            
        except Exception as e:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
            return {'error': f'学校详细信息获取失败: {str(e)}'}
    
    def get_university_profile(self, university_id):
        """
        获取指定学校的详细特征信息
        
        Args:
            university_id (int): 学校ID
        
        Returns:
            dict: 学校详细特征
        """
        try:
            connection = self.get_mysql_connection()
            cursor = connection.cursor()
            
            # 获取学校基本信息
            cursor.execute("""
            SELECT university_id, university_code, original_name, standard_name,
                   level, type, power_feature, location, recruitment_count, is_standardized
            FROM universities
            WHERE university_id = %s
            """, (university_id,))
            
            university_row = cursor.fetchone()
            if not university_row:
                return {'error': '未找到该学校信息'}
            
            university_profile = {
                'university_id': university_row[0],
                'university_code': university_row[1],
                'original_name': university_row[2],
                'standard_name': university_row[3],
                'level': university_row[4],
                'type': university_row[5],
                'power_feature': university_row[6],
                'location': university_row[7],
                'total_recruitment_count': university_row[8],
                'is_standardized': university_row[9]
            }
            
            # 获取该学校的招聘统计信息
            cursor.execute("""
            SELECT 
                r.company, COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
            FROM recruitment_records r
            WHERE r.university_id = %s
            GROUP BY r.company
            ORDER BY count DESC
            """, (university_id,))
            
            company_distribution = []
            for row in cursor.fetchall():
                company_distribution.append({
                    'company': row[0],
                    'count': row[1],
                    'percentage': float(row[2])
                })
            university_profile['company_distribution'] = company_distribution
            
            # 获取批次分布
            cursor.execute("""
            SELECT 
                r.batch, COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
            FROM recruitment_records r
            WHERE r.university_id = %s
            GROUP BY r.batch
            ORDER BY count DESC
            """, (university_id,))
            
            batch_distribution = []
            for row in cursor.fetchall():
                batch_distribution.append({
                    'batch': row[0],
                    'count': row[1],
                    'percentage': float(row[2])
                })
            university_profile['batch_distribution'] = batch_distribution
            
            # 获取地区分布（通过secondary_units）
            cursor.execute("""
            SELECT 
                s.region, s.unit_name, COUNT(*) as count
            FROM recruitment_records r
            LEFT JOIN secondary_units s ON r.secondary_unit_id = s.unit_id
            WHERE r.university_id = %s
            GROUP BY s.region, s.unit_name
            ORDER BY count DESC
            LIMIT 10
            """, (university_id,))
            
            regional_distribution = []
            for row in cursor.fetchall():
                if row[0]:  # 过滤NULL值
                    regional_distribution.append({
                        'region': row[0],
                        'unit_name': row[1],
                        'count': row[2]
                    })
            university_profile['regional_distribution'] = regional_distribution
            
            # 获取性别分布
            cursor.execute("""
            SELECT 
                r.gender, COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
            FROM recruitment_records r
            WHERE r.university_id = %s
            GROUP BY r.gender
            """, (university_id,))
            
            gender_distribution = {}
            for row in cursor.fetchall():
                if row[0]:  # 过滤NULL值
                    gender_distribution[row[0]] = {
                        'count': row[1],
                        'percentage': float(row[2])
                    }
            university_profile['gender_distribution'] = gender_distribution
            
            # 获取该学校在同类学校中的排名
            cursor.execute("""
            SELECT 
                ROW_NUMBER() OVER (ORDER BY recruitment_count DESC) as ranking,
                university_id
            FROM universities
            WHERE level = %s
            """, (university_profile['level'],))
            
            ranking_in_level = None
            total_in_level = 0
            for row in cursor.fetchall():
                total_in_level += 1
                if row[1] == university_id:
                    ranking_in_level = row[0]
            
            university_profile['ranking_info'] = {
                'ranking_in_level': ranking_in_level,
                'total_in_level': total_in_level,
                'level': university_profile['level']
            }
            
            cursor.close()
            connection.close()
            
            return university_profile
            
        except Exception as e:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
            return {'error': f'学校详细信息获取失败: {str(e)}'}

# 创建API实例
frontend_analytics_api = FrontendAnalyticsAPI()

# 创建蓝图
frontend_analytics_bp = Blueprint('frontend_analytics', __name__)

@frontend_analytics_bp.route('/analytics/dashboard', methods=['GET'])
def get_dashboard_analytics():
    """
    获取前端Dashboard的完整分析数据
    支持多种筛选条件
    """
    try:
        # 获取筛选参数
        filters = {}
        
        if request.args.get('company'):
            filters['company'] = urllib.parse.unquote(request.args.get('company'))
        if request.args.get('batch'):
            filters['batch'] = urllib.parse.unquote(request.args.get('batch'))
        if request.args.get('region'):
            filters['region'] = urllib.parse.unquote(request.args.get('region'))
        if request.args.get('university_level'):
            filters['university_level'] = urllib.parse.unquote(request.args.get('university_level'))
        if request.args.get('university_type'):
            filters['university_type'] = urllib.parse.unquote(request.args.get('university_type'))
        if request.args.get('secondary_unit'):
            filters['secondary_unit'] = urllib.parse.unquote(request.args.get('secondary_unit'))
        if request.args.get('gender'):
            filters['gender'] = urllib.parse.unquote(request.args.get('gender'))
        
        # 获取分析数据
        analytics_data = frontend_analytics_api.get_frontend_analytics(filters if filters else None)
        
        if 'error' in analytics_data:
            return jsonify({'error': analytics_data['error']}), 500
        
        # 添加筛选条件信息
        analytics_data['filters_applied'] = filters
        
        return jsonify(analytics_data)
        
    except Exception as e:
        return jsonify({'error': f'Dashboard分析数据获取失败: {str(e)}'}), 500

@frontend_analytics_bp.route('/analytics/schools', methods=['GET'])
def get_schools_list():
    """
    获取学校详细信息列表（支持筛选和分页）
    """
    try:
        # 获取筛选参数
        filters = {}
        
        if request.args.get('company'):
            filters['company'] = urllib.parse.unquote(request.args.get('company'))
        if request.args.get('batch'):
            filters['batch'] = urllib.parse.unquote(request.args.get('batch'))
        if request.args.get('region'):
            filters['region'] = urllib.parse.unquote(request.args.get('region'))
        if request.args.get('university_level'):
            filters['university_level'] = urllib.parse.unquote(request.args.get('university_level'))
        if request.args.get('university_type'):
            filters['university_type'] = urllib.parse.unquote(request.args.get('university_type'))
        if request.args.get('secondary_unit'):
            filters['secondary_unit'] = urllib.parse.unquote(request.args.get('secondary_unit'))
        if request.args.get('gender'):
            filters['gender'] = urllib.parse.unquote(request.args.get('gender'))
        
        # 分页参数
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        # 获取学校列表
        schools_data = frontend_analytics_api.get_school_details_list(
            filters if filters else None, page, limit
        )
        
        if 'error' in schools_data:
            return jsonify({'error': schools_data['error']}), 500
        
        # 添加筛选条件信息
        schools_data['filters_applied'] = filters
        
        return jsonify(schools_data)
        
    except Exception as e:
        return jsonify({'error': f'学校列表获取失败: {str(e)}'}), 500

@frontend_analytics_bp.route('/analytics/university/<int:university_id>', methods=['GET'])
def get_university_details(university_id):
    """
    获取指定学校的详细特征信息
    """
    try:
        university_profile = frontend_analytics_api.get_university_profile(university_id)
        
        if 'error' in university_profile:
            return jsonify({'error': university_profile['error']}), 404
        
        return jsonify(university_profile)
        
    except Exception as e:
        return jsonify({'error': f'学校详细信息获取失败: {str(e)}'}), 500

@frontend_analytics_bp.route('/analytics/health', methods=['GET'])
def frontend_analytics_health():
    """前端分析API健康检查"""
    try:
        connection = frontend_analytics_api.get_mysql_connection()
        cursor = connection.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM recruitment_records")
        records_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM universities")
        universities_count = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'healthy',
            'version': 'frontend_analytics_v1.0',
            'features': [
                'dashboard_analytics',
                'schools_list',
                'university_profile'
            ],
            'data_counts': {
                'recruitment_records': records_count,
                'universities': universities_count
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'version': 'frontend_analytics_v1.0'
        }), 500
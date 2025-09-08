#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Updated Recruitment API - 适配新数据库结构
基于新的 universities, secondary_units, recruitment_records 表结构
"""

from flask import Blueprint, request, jsonify
import urllib.parse
import mysql.connector
import os

class UpdatedRecruitmentAPI:
    def __init__(self):
        """Initialize API with new database structure"""
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
    
    def get_recruitment_options(self):
        """获取所有可用的查询选项 - 适配新结构"""
        try:
            connection = self.get_mysql_connection()
            cursor = connection.cursor()
            
            options = {
                'companies': [],
                'batches': [],
                'regions': [],
                'university_levels': [],
                'secondary_unit_types': []
            }
            
            # 获取招聘公司
            cursor.execute("SELECT DISTINCT company FROM recruitment_records WHERE company IS NOT NULL ORDER BY company")
            options['companies'] = [row[0] for row in cursor.fetchall()]
            
            # 获取招聘批次
            cursor.execute("SELECT DISTINCT batch FROM recruitment_records WHERE batch IS NOT NULL ORDER BY batch")
            options['batches'] = [row[0] for row in cursor.fetchall()]
            
            # 获取地区（从secondary_units表）
            cursor.execute("SELECT DISTINCT region FROM secondary_units WHERE region IS NOT NULL ORDER BY region")
            options['regions'] = [row[0] for row in cursor.fetchall()]
            
            # 获取院校层次
            cursor.execute("SELECT DISTINCT level FROM universities WHERE level IS NOT NULL ORDER BY level")
            options['university_levels'] = [row[0] for row in cursor.fetchall()]
            
            # 获取二级单位类型
            cursor.execute("SELECT DISTINCT unit_type FROM secondary_units WHERE unit_type IS NOT NULL ORDER BY unit_type")
            options['secondary_unit_types'] = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            connection.close()
            
            return options
            
        except Exception as e:
            return {'error': str(e)}
    
    def search_universities(self, query, limit=20):
        """学校名称搜索 - 使用新的universities表"""
        try:
            connection = self.get_mysql_connection()
            cursor = connection.cursor()
            
            # 使用universities表和关联查询获取招聘统计
            sql = """
            SELECT u.university_code, u.original_name, u.standard_name, 
                   u.level, u.type, u.power_feature, u.location,
                   COUNT(r.record_id) as recruitment_count
            FROM universities u
            LEFT JOIN recruitment_records r ON u.university_id = r.university_id
            WHERE u.original_name LIKE %s OR u.standard_name LIKE %s
            GROUP BY u.university_id, u.university_code, u.original_name, u.standard_name,
                     u.level, u.type, u.power_feature, u.location
            ORDER BY recruitment_count DESC, u.standard_name
            LIMIT %s
            """
            
            cursor.execute(sql, (f"%{query}%", f"%{query}%", limit))
            
            universities = []
            for row in cursor.fetchall():
                universities.append({
                    'university_code': row[0],
                    'original_name': row[1],
                    'standard_name': row[2],
                    'level': row[3],
                    'type': row[4],
                    'power_feature': row[5],
                    'location': row[6],
                    'recruitment_count': row[7]
                })
            
            cursor.close()
            connection.close()
            
            return {
                'universities': universities,
                'total': len(universities),
                'query': query
            }
            
        except Exception as e:
            return {'error': f'大学搜索失败: {str(e)}'}
    
    def get_recruitment_by_region(self, region=None, unit_type=None, page=1, limit=20):
        """按地区查询招聘情况 - 使用新的secondary_units表"""
        try:
            connection = self.get_mysql_connection()
            cursor = connection.cursor()
            
            conditions = []
            params = []
            
            if region:
                conditions.append("s.region = %s")
                params.append(region)
            
            if unit_type:
                conditions.append("s.unit_type = %s")
                params.append(unit_type)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            # 计算偏移量
            offset = (page - 1) * limit
            params.extend([limit, offset])
            
            # 使用完整信息视图查询
            sql = f"""
            SELECT s.unit_code, s.unit_name, s.unit_type, s.region,
                   COUNT(r.record_id) as recruitment_count,
                   COUNT(DISTINCT r.university_id) as university_count,
                   GROUP_CONCAT(DISTINCT u.level ORDER BY u.level) as university_levels
            FROM secondary_units s
            LEFT JOIN recruitment_records r ON s.unit_id = r.secondary_unit_id
            LEFT JOIN universities u ON r.university_id = u.university_id
            {where_clause}
            GROUP BY s.unit_id, s.unit_code, s.unit_name, s.unit_type, s.region
            ORDER BY recruitment_count DESC
            LIMIT %s OFFSET %s
            """
            
            cursor.execute(sql, params)
            
            units = []
            for row in cursor.fetchall():
                units.append({
                    'unit_code': row[0],
                    'unit_name': row[1],
                    'unit_type': row[2],
                    'region': row[3],
                    'recruitment_count': row[4],
                    'university_count': row[5],
                    'university_levels': row[6].split(',') if row[6] else []
                })
            
            # 获取总数
            count_sql = f"""
            SELECT COUNT(DISTINCT s.unit_id)
            FROM secondary_units s
            LEFT JOIN recruitment_records r ON s.unit_id = r.secondary_unit_id
            {where_clause}
            """
            cursor.execute(count_sql, params[:-2])  # 排除limit和offset参数
            total_count = cursor.fetchone()[0]
            
            cursor.close()
            connection.close()
            
            return {
                'units': units,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total_count,
                    'total_pages': (total_count + limit - 1) // limit
                }
            }
            
        except Exception as e:
            return {'error': f'地区查询失败: {str(e)}'}
    
    def get_recruitment_analytics(self, company=None, batch=None, region=None, university_level=None):
        """招聘数据分析 - 适配新结构"""
        try:
            connection = self.get_mysql_connection()
            cursor = connection.cursor()
            
            # 构建过滤条件
            conditions = []
            params = []
            
            if company:
                conditions.append("r.company = %s")
                params.append(company)
            
            if batch:
                conditions.append("r.batch = %s") 
                params.append(batch)
            
            if region:
                conditions.append("s.region = %s")
                params.append(region)
            
            if university_level:
                conditions.append("u.level = %s")
                params.append(university_level)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            analytics = {
                'total_records': 0,
                'gender_distribution': {},
                'company_distribution': {},
                'batch_distribution': {},
                'university_level_distribution': {},
                'region_distribution': {},
                'top_universities': [],
                'top_secondary_units': []
            }
            
            # 1. 总记录数
            sql = f"""
            SELECT COUNT(*)
            FROM recruitment_records r
            LEFT JOIN universities u ON r.university_id = u.university_id
            LEFT JOIN secondary_units s ON r.secondary_unit_id = s.unit_id
            {where_clause}
            """
            cursor.execute(sql, params)
            analytics['total_records'] = cursor.fetchone()[0]
            
            # 2. 性别分布
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
            analytics['gender_distribution'] = {
                row[0]: {'count': row[1], 'percentage': float(row[2])}
                for row in cursor.fetchall() if row[0]
            }
            
            # 3. 公司分布
            sql = f"""
            SELECT r.company, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
            FROM recruitment_records r
            LEFT JOIN universities u ON r.university_id = u.university_id
            LEFT JOIN secondary_units s ON r.secondary_unit_id = s.unit_id
            {where_clause}
            GROUP BY r.company
            ORDER BY count DESC
            """
            cursor.execute(sql, params)
            analytics['company_distribution'] = [
                {'company': row[0], 'count': row[1], 'percentage': float(row[2])}
                for row in cursor.fetchall()
            ]
            
            # 4. 批次分布
            sql = f"""
            SELECT r.batch, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
            FROM recruitment_records r
            LEFT JOIN universities u ON r.university_id = u.university_id
            LEFT JOIN secondary_units s ON r.secondary_unit_id = s.unit_id
            {where_clause}
            GROUP BY r.batch
            ORDER BY count DESC
            """
            cursor.execute(sql, params)
            analytics['batch_distribution'] = [
                {'batch': row[0], 'count': row[1], 'percentage': float(row[2])}
                for row in cursor.fetchall()
            ]
            
            # 5. 院校层次分布
            sql = f"""
            SELECT u.level, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
            FROM recruitment_records r
            LEFT JOIN universities u ON r.university_id = u.university_id
            LEFT JOIN secondary_units s ON r.secondary_unit_id = s.unit_id
            {where_clause}
            GROUP BY u.level
            ORDER BY count DESC
            """
            cursor.execute(sql, params)
            analytics['university_level_distribution'] = [
                {'level': row[0], 'count': row[1], 'percentage': float(row[2])}
                for row in cursor.fetchall()
            ]
            
            # 6. 地区分布
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
            analytics['region_distribution'] = [
                {'region': row[0], 'count': row[1], 'percentage': float(row[2])}
                for row in cursor.fetchall() if row[0]
            ]
            
            # 7. 热门院校 Top 10
            sql = f"""
            SELECT u.standard_name, u.level, u.type, u.location, COUNT(*) as count
            FROM recruitment_records r
            LEFT JOIN universities u ON r.university_id = u.university_id
            LEFT JOIN secondary_units s ON r.secondary_unit_id = s.unit_id
            {where_clause}
            GROUP BY u.university_id, u.standard_name, u.level, u.type, u.location
            ORDER BY count DESC
            LIMIT 10
            """
            cursor.execute(sql, params)
            analytics['top_universities'] = [
                {
                    'name': row[0],
                    'level': row[1],
                    'type': row[2],
                    'location': row[3],
                    'count': row[4]
                }
                for row in cursor.fetchall()
            ]
            
            # 8. 热门二级单位 Top 10
            sql = f"""
            SELECT s.unit_name, s.unit_type, s.region, COUNT(*) as count
            FROM recruitment_records r
            LEFT JOIN universities u ON r.university_id = u.university_id
            LEFT JOIN secondary_units s ON r.secondary_unit_id = s.unit_id
            {where_clause}
            GROUP BY s.unit_id, s.unit_name, s.unit_type, s.region
            ORDER BY count DESC
            LIMIT 10
            """
            cursor.execute(sql, params)
            analytics['top_secondary_units'] = [
                {
                    'name': row[0],
                    'type': row[1],
                    'region': row[2],
                    'count': row[3]
                }
                for row in cursor.fetchall() if row[0]
            ]
            
            cursor.close()
            connection.close()
            
            return analytics
            
        except Exception as e:
            return {'error': f'数据分析失败: {str(e)}'}
    
    def get_recruitment_statistics_by_university_level(self, level=None):
        """按院校层次统计招聘情况"""
        try:
            connection = self.get_mysql_connection()
            cursor = connection.cursor()
            
            if level:
                where_clause = "WHERE u.level = %s"
                params = [level]
            else:
                where_clause = ""
                params = []
            
            sql = f"""
            SELECT u.level,
                   COUNT(*) as total_count,
                   COUNT(DISTINCT u.university_id) as university_count,
                   COUNT(DISTINCT s.unit_id) as unit_count,
                   ROUND(AVG(CASE WHEN r.gender = '男' THEN 1.0 ELSE 0.0 END) * 100, 2) as male_percentage
            FROM recruitment_records r
            JOIN universities u ON r.university_id = u.university_id
            LEFT JOIN secondary_units s ON r.secondary_unit_id = s.unit_id
            {where_clause}
            GROUP BY u.level
            ORDER BY total_count DESC
            """
            
            cursor.execute(sql, params)
            
            statistics = []
            for row in cursor.fetchall():
                statistics.append({
                    'level': row[0],
                    'total_count': row[1],
                    'university_count': row[2],
                    'unit_count': row[3],
                    'male_percentage': float(row[4]) if row[4] else 0
                })
            
            cursor.close()
            connection.close()
            
            return {'statistics': statistics}
            
        except Exception as e:
            return {'error': f'院校层次统计失败: {str(e)}'}

# 创建API实例
updated_api = UpdatedRecruitmentAPI()

# 创建更新后的蓝图
updated_recruitment_bp = Blueprint('updated_recruitment', __name__)

@updated_recruitment_bp.route('/recruitment/options', methods=['GET'])
def get_updated_recruitment_options():
    """获取所有可用的查询选项 - 新版本"""
    try:
        options = updated_api.get_recruitment_options()
        
        if 'error' in options:
            return jsonify({'error': options['error']}), 500
            
        return jsonify(options)
    except Exception as e:
        return jsonify({'error': f'获取选项失败: {str(e)}'}), 500

@updated_recruitment_bp.route('/recruitment/universities/search', methods=['GET'])
def search_universities():
    """学校搜索 - 新版本"""
    try:
        query = request.args.get('query', '').strip()
        limit = int(request.args.get('limit', 20))
        
        if not query:
            return jsonify({'universities': [], 'total': 0})
        
        result = updated_api.search_universities(query, limit)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 500
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'学校搜索失败: {str(e)}'}), 500

@updated_recruitment_bp.route('/recruitment/regions', methods=['GET'])
def get_recruitment_by_region():
    """按地区查询招聘情况 - 新版本"""
    try:
        region = request.args.get('region')
        unit_type = request.args.get('unit_type')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        result = updated_api.get_recruitment_by_region(region, unit_type, page, limit)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 500
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'地区查询失败: {str(e)}'}), 500

@updated_recruitment_bp.route('/recruitment/analytics', methods=['GET'])
def get_updated_recruitment_analytics():
    """招聘数据分析 - 新版本"""
    try:
        company = request.args.get('company')
        batch = request.args.get('batch')
        region = request.args.get('region')
        university_level = request.args.get('university_level')
        
        analytics = updated_api.get_recruitment_analytics(company, batch, region, university_level)
        
        if 'error' in analytics:
            return jsonify({'error': analytics['error']}), 500
            
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': f'数据分析失败: {str(e)}'}), 500

@updated_recruitment_bp.route('/recruitment/statistics/university-level', methods=['GET'])
def get_university_level_statistics():
    """按院校层次统计 - 新版本"""
    try:
        level = request.args.get('level')
        
        result = updated_api.get_recruitment_statistics_by_university_level(level)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 500
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'院校层次统计失败: {str(e)}'}), 500

@updated_recruitment_bp.route('/recruitment/health/updated', methods=['GET'])
def updated_recruitment_health():
    """更新后API健康检查"""
    try:
        connection = updated_api.get_mysql_connection()
        cursor = connection.cursor()
        
        # 检查各表记录数
        cursor.execute("SELECT COUNT(*) FROM recruitment_records")
        records_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM universities")
        universities_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM secondary_units")
        units_count = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'healthy',
            'version': 'updated_v1.0',
            'database_structure': 'optimized',
            'tables': {
                'recruitment_records': records_count,
                'universities': universities_count,
                'secondary_units': units_count
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'version': 'updated_v1.0'
        }), 500
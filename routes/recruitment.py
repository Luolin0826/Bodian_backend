"""
录取查询相关API路由
"""
from flask import Blueprint, request, jsonify
import sys
import os
import urllib.parse

# 注释掉已删除的模块引用
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# try:
#     from enhanced_recruitment_api import EnhancedRecruitmentAPI
# except ImportError as e:
#     print(f"Warning: Could not import EnhancedRecruitmentAPI: {e}")
#     EnhancedRecruitmentAPI = None

# 已删除enhanced_recruitment_api模块，使用新的API系统
EnhancedRecruitmentAPI = None

# 创建蓝图
recruitment_bp = Blueprint('recruitment', __name__)

# 初始化API实例
api = None
if EnhancedRecruitmentAPI:
    try:
        api = EnhancedRecruitmentAPI()
    except Exception as e:
        print(f"Warning: Could not initialize EnhancedRecruitmentAPI: {e}")
        api = None

@recruitment_bp.route('/recruitment/options', methods=['GET'])
def get_recruitment_options():
    """获取所有可用的查询选项"""
    if not api:
        return jsonify({'error': '录取查询API未初始化'}), 503
        
    try:
        options = api.get_available_options()
        
        # 如果有错误，返回错误信息
        if 'error' in options:
            return jsonify({'error': options['error']}), 500
            
        return jsonify(options)
    except Exception as e:
        return jsonify({'error': f'获取选项失败: {str(e)}'}), 500

@recruitment_bp.route('/recruitment/best-value', methods=['GET'])
def get_best_value_regions():
    """获取性价比地区信息"""
    if not api:
        return jsonify({'error': '录取查询API未初始化'}), 503
        
    try:
        region_level = request.args.get('region_level', 'all')
        
        # 验证参数
        if region_level not in ['city', 'county', 'all']:
            return jsonify({'error': 'region_level参数无效，必须是city、county或all之一'}), 400
            
        result = api.get_best_value_regions(region_level)
        
        # 如果有错误，返回错误信息
        if 'error' in result:
            return jsonify({'error': result['error']}), 500
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'获取性价比地区失败: {str(e)}'}), 500

@recruitment_bp.route('/recruitment/district-policies', methods=['GET'])
def get_district_policies():
    """获取区县级精确录取政策 - 支持8字段筛选"""
    if not api:
        return jsonify({'error': '录取查询API未初始化'}), 503
        
    try:
        # 支持前端的8字段筛选 - 注意URL解码
        company_type = urllib.parse.unquote(request.args.get('company_type', '')) or None
        batch = urllib.parse.unquote(request.args.get('batch', '')) or None
        province = urllib.parse.unquote(request.args.get('province', '')) or None
        city = urllib.parse.unquote(request.args.get('city', '')) or None
        county = urllib.parse.unquote(request.args.get('county', '')) or None
        school_name = urllib.parse.unquote(request.args.get('school_name', '')) or None
        bachelor_level = urllib.parse.unquote(request.args.get('bachelor_level', '')) or None
        master_level = urllib.parse.unquote(request.args.get('master_level', '')) or None
        
        # 分页参数
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        result = get_enhanced_policies_with_filters(
            company_type=company_type,
            batch=batch, 
            province=province,
            city=city,
            county=county,  # county参数映射到company字段
            school_name=school_name,
            bachelor_level=bachelor_level,
            master_level=master_level,
            page=page,
            limit=limit
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'获取政策信息失败: {str(e)}'}), 500

@recruitment_bp.route('/recruitment/admission-by-school-level', methods=['GET'])
def get_admission_by_school_level():
    """按学校层次查询网申通过情况"""
    if not api:
        return jsonify({'error': '录取查询API未初始化'}), 503
        
    try:
        # 获取参数
        school_levels = request.args.getlist('school_levels')
        provinces = request.args.getlist('provinces')
        cities = request.args.getlist('cities')
        education_level = request.args.get('education_level', 'bachelor')
        
        # 如果没有提供学校层次，使用默认值
        if not school_levels:
            school_levels = None
            
        result = api.get_admission_by_school_level(
            school_levels=school_levels,
            provinces=provinces if provinces else None,
            cities=cities if cities else None,
            education_level=education_level
        )
        
        # 如果有错误，返回错误信息
        if 'error' in result:
            return jsonify({'error': result['error']}), 500
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'获取录取情况失败: {str(e)}'}), 500

@recruitment_bp.route('/recruitment/analytics', methods=['GET'])
def get_recruitment_analytics():
    """获取录取情况数据分析"""
    if not api:
        return jsonify({'error': '录取查询API未初始化'}), 503
        
    try:
        analysis_type = request.args.get('analysis_type', 'comprehensive')
        group_by = request.args.getlist('group_by')
        
        # 处理过滤条件
        filters = {}
        if request.args.getlist('provinces'):
            filters['provinces'] = request.args.getlist('provinces')
        if request.args.getlist('school_types'):
            filters['school_types'] = request.args.getlist('school_types')
        if request.args.getlist('years'):
            filters['years'] = [int(year) for year in request.args.getlist('years')]
            
        result = api.get_recruitment_analytics(
            analysis_type=analysis_type,
            group_by=group_by if group_by else None,
            filters=filters if filters else None
        )
        
        # 如果有错误，返回错误信息
        if 'error' in result:
            return jsonify({'error': result['error']}), 500
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'数据分析失败: {str(e)}'}), 500

@recruitment_bp.route('/recruitment/province/<province>', methods=['GET'])
def get_recruitment_by_province(province):
    """按省份查询录取情况（兼容原有接口）"""
    try:
        # 使用原有的recruitment_query_api.py中的功能
        from recruitment_query_api import RecruitmentQueryAPI
        
        original_api = RecruitmentQueryAPI()
        include_school_details = request.args.get('include_school_details', 'true').lower() == 'true'
        
        result = original_api.query_recruitment_by_province(
            province=province,
            include_school_details=include_school_details
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'查询省份录取情况失败: {str(e)}'}), 500

@recruitment_bp.route('/recruitment/policies', methods=['GET'])
def get_recruitment_policies():
    """查询录取政策（兼容原有接口）"""
    try:
        # 使用原有的recruitment_query_api.py中的功能
        from recruitment_query_api import RecruitmentQueryAPI
        
        original_api = RecruitmentQueryAPI()
        province = request.args.get('province')
        city = request.args.get('city')
        
        result = original_api.query_recruitment_policies(province=province, city=city)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'查询录取政策失败: {str(e)}'}), 500

# 健康检查端点
@recruitment_bp.route('/recruitment/cities/<province>', methods=['GET'])
def get_cities_by_province(province):
    """根据省份获取相关城市列表"""
    if not api:
        return jsonify({'error': '录取查询API未初始化'}), 503
        
    try:
        connection = api.get_mysql_connection()
        cursor = connection.cursor()
        
        # 从政策规则表获取城市
        cursor.execute("""
        SELECT DISTINCT city 
        FROM recruitment_rules 
        WHERE province = %s AND city IS NOT NULL
        ORDER BY city
        """, (province,))
        
        rule_cities = [row[0] for row in cursor.fetchall()]
        
        # 从录取记录表获取城市  
        cursor.execute("""
        SELECT DISTINCT city 
        FROM recruitment_records 
        WHERE province = %s AND city IS NOT NULL
        ORDER BY city
        """, (province,))
        
        record_cities = [row[0] for row in cursor.fetchall()]
        
        # 合并去重
        all_cities = list(set(rule_cities + record_cities))
        all_cities.sort()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'province': province,
            'cities': all_cities,
            'count': len(all_cities)
        })
        
    except Exception as e:
        return jsonify({'error': f'获取城市列表失败: {str(e)}'}), 500

@recruitment_bp.route('/recruitment/companies/<province>', methods=['GET'])
def get_companies_by_province(province):
    """根据省份获取相关单位/区县列表"""
    if not api:
        return jsonify({'error': '录取查询API未初始化'}), 503
        
    try:
        city = request.args.get('city')  # 可选的城市过滤
        
        connection = api.get_mysql_connection()
        cursor = connection.cursor()
        
        # 构建查询条件
        where_conditions = ["province = %s"]
        params = [province]
        
        if city:
            where_conditions.append("city = %s")
            params.append(city)
        
        where_clause = " AND ".join(where_conditions)
        
        # 从政策规则表获取单位
        sql = f"""
        SELECT DISTINCT company 
        FROM recruitment_rules 
        WHERE {where_clause} AND company IS NOT NULL
        ORDER BY company
        """
        cursor.execute(sql, params)
        
        rule_companies = [row[0] for row in cursor.fetchall()]
        
        # 从录取记录表获取单位
        sql = f"""
        SELECT DISTINCT company 
        FROM recruitment_records 
        WHERE {where_clause} AND company IS NOT NULL
        ORDER BY company
        """
        cursor.execute(sql, params)
        
        record_companies = [row[0] for row in cursor.fetchall()]
        
        # 合并去重
        all_companies = list(set(rule_companies + record_companies))
        all_companies.sort()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'province': province,
            'city': city,
            'companies': all_companies,
            'count': len(all_companies)
        })
        
    except Exception as e:
        return jsonify({'error': f'获取单位列表失败: {str(e)}'}), 500

@recruitment_bp.route('/recruitment/cities/<province>/<city>/companies', methods=['GET'])  
def get_companies_by_province_city(province, city):
    """根据省份和城市获取具体的单位/区县列表"""
    if not api:
        return jsonify({'error': '录取查询API未初始化'}), 503
        
    try:
        connection = api.get_mysql_connection()
        cursor = connection.cursor()
        
        # 从政策规则表获取单位
        cursor.execute("""
        SELECT DISTINCT company 
        FROM recruitment_rules 
        WHERE province = %s AND city = %s AND company IS NOT NULL
        ORDER BY company
        """, (province, city))
        
        rule_companies = [row[0] for row in cursor.fetchall()]
        
        # 从录取记录表获取单位
        cursor.execute("""
        SELECT DISTINCT company 
        FROM recruitment_records 
        WHERE province = %s AND city = %s AND company IS NOT NULL
        ORDER BY company
        """, (province, city))
        
        record_companies = [row[0] for row in cursor.fetchall()]
        
        # 合并去重
        all_companies = list(set(rule_companies + record_companies))
        all_companies.sort()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'province': province,
            'city': city,
            'companies': all_companies,
            'count': len(all_companies)
        })
        
    except Exception as e:
        return jsonify({'error': f'获取单位列表失败: {str(e)}'}), 500

@recruitment_bp.route('/recruitment/schools/search', methods=['GET'])
def search_schools():
    """学校名称模糊搜索接口"""
    if not api:
        return jsonify({'error': '录取查询API未初始化'}), 503
        
    try:
        query = request.args.get('query', '').strip()
        limit = int(request.args.get('limit', 10))
        
        if not query:
            return jsonify({'schools': [], 'total': 0})
            
        connection = api.get_mysql_connection()
        cursor = connection.cursor()
        
        # 搜索学校名称 - 使用新的数据库结构
        sql = """
        SELECT u.standard_name, u.type, COUNT(rr.record_id) as count
        FROM universities u
        LEFT JOIN recruitment_records rr ON u.university_id = rr.university_id
        WHERE u.standard_name LIKE %s OR u.original_name LIKE %s
        GROUP BY u.university_id, u.standard_name, u.type
        ORDER BY count DESC, u.standard_name
        LIMIT %s
        """
        
        cursor.execute(sql, (f"%{query}%", f"%{query}%", limit))
        
        schools = []
        for row in cursor.fetchall():
            schools.append({
                'school': row[0],
                'school_type': row[1],
                'recruitment_count': row[2]
            })
            
        cursor.close()
        connection.close()
        
        return jsonify({
            'schools': schools,
            'total': len(schools),
            'query': query
        })
        
    except Exception as e:
        return jsonify({'error': f'学校搜索失败: {str(e)}'}), 500

@recruitment_bp.route('/recruitment/detailed-statistics', methods=['GET']) 
def get_detailed_statistics_endpoint():
    """详细统计接口 - 分页显示学校统计数据"""
    if not api:
        return jsonify({'error': '录取查询API未初始化'}), 503
        
    try:
        # 获取筛选条件
        company_type = request.args.get('company_type')
        batch = request.args.get('batch')
        province = request.args.get('province')
        city = request.args.get('city')
        county = request.args.get('county')
        
        # 分页参数
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        connection = api.get_mysql_connection()
        cursor = connection.cursor()
        
        # 构建查询条件
        conditions = []
        params = []
        
        if company_type:
            conditions.append("company_type = %s")
            params.append(company_type)
        if batch:
            batch_mapping = {'一批': '一批', '二批': '二批', '三批': '三批', '南网': '南网', '提前批': '提前批'}
            if batch in batch_mapping:
                conditions.append("batch_type = %s")
                params.append(batch_mapping[batch])
        if province:
            conditions.append("province = %s")
            params.append(province)
        if city:
            conditions.append("city = %s")
            params.append(city)
        if county:
            conditions.append("company LIKE %s")
            params.append(f"%{county}%")
            
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        # 获取详细统计数据
        statistics = get_detailed_statistics(cursor, where_clause, params, page, limit)
        
        # 获取总数 - 使用新的数据库结构
        count_sql = f"""
        SELECT COUNT(DISTINCT u.university_id) 
        FROM universities u
        LEFT JOIN recruitment_records rr ON u.university_id = rr.university_id
        LEFT JOIN secondary_units su ON rr.secondary_unit_id = su.unit_id
        {where_clause}
        """
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'statistics': statistics,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'total_pages': (total_count + limit - 1) // limit
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'详细统计查询失败: {str(e)}'}), 500

@recruitment_bp.route('/recruitment/debug', methods=['GET'])
def debug_province_filter():
    """调试省份筛选问题"""
    if not api:
        return jsonify({'error': '录取查询API未初始化'}), 503
        
    try:
        province = urllib.parse.unquote(request.args.get('province', '')) or None
        connection = api.get_mysql_connection()
        cursor = connection.cursor()
        
        # 测试直接的省份查询
        cursor.execute("SELECT COUNT(*) FROM recruitment_records WHERE province = %s", (province,))
        count_exact = cursor.fetchone()[0]
        
        # 获取所有不同的省份名称来对比
        cursor.execute("SELECT DISTINCT province, COUNT(*) FROM recruitment_records GROUP BY province ORDER BY COUNT(*) DESC LIMIT 10")
        all_provinces = [(row[0], row[1]) for row in cursor.fetchall()]
        
        # 测试like查询
        cursor.execute("SELECT COUNT(*) FROM recruitment_records WHERE province LIKE %s", (f"%{province}%",))
        count_like = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'input_province': province,
            'exact_match_count': count_exact,
            'like_match_count': count_like,
            'all_provinces_sample': all_provinces
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@recruitment_bp.route('/recruitment/cost-effective-recommendations', methods=['GET'])
def get_cost_effective_recommendations():
    """性价比推荐算法 - 基于多维度综合评分"""
    if not api:
        return jsonify({'error': '录取查询API未初始化'}), 503
        
    try:
        # 获取算法参数
        top_n = int(request.args.get('limit', 10))
        region_type = request.args.get('region_type', 'all')  # city, county, all
        
        connection = api.get_mysql_connection()
        cursor = connection.cursor()
        
        # 获取综合数据用于算法分析
        sql = """
        SELECT ru.province, ru.city, ru.company, ru.data_level,
               ru.bachelor_salary, ru.master_salary,
               ru.bachelor_interview_line, ru.master_interview_line,
               ru.cet_requirement, ru.computer_requirement, 
               ru.household_priority, ru.detailed_rules,
               COALESCE(COUNT(rr.id), 0) as recruitment_count
        FROM recruitment_rules ru
        LEFT JOIN recruitment_records rr ON ru.province = rr.province 
            AND (ru.city = rr.city OR ru.city IS NULL)
            AND (ru.company = rr.company OR ru.company IS NULL)
        GROUP BY ru.id, ru.province, ru.city, ru.company, ru.data_level,
                 ru.bachelor_salary, ru.master_salary,
                 ru.bachelor_interview_line, ru.master_interview_line,
                 ru.cet_requirement, ru.computer_requirement,
                 ru.household_priority, ru.detailed_rules
        ORDER BY recruitment_count DESC
        """
        
        cursor.execute(sql)
        regions = []
        
        for row in cursor.fetchall():
            region = {
                'province': row[0],
                'city': row[1],
                'company': row[2], 
                'data_level': row[3],
                'bachelor_salary': row[4],
                'master_salary': row[5],
                'bachelor_interview_line': row[6],
                'master_interview_line': row[7],
                'cet_requirement': row[8],
                'computer_requirement': row[9],
                'household_priority': row[10],
                'detailed_rules': row[11],
                'recruitment_count': row[12]
            }
            
            # 计算性价比得分
            score = calculate_cost_effectiveness_score(region)
            region['cost_effectiveness_score'] = score
            region['recommendation_reasons'] = get_recommendation_reasons(region)
            
            # 根据region_type过滤
            if should_include_region(region, region_type):
                regions.append(region)
        
        # 按性价比得分排序并取前N个
        regions.sort(key=lambda x: x['cost_effectiveness_score'], reverse=True)
        top_regions = regions[:top_n]
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'algorithm_version': 'v1.0',
            'total_analyzed': len(regions),
            'recommendations': top_regions,
            'evaluation_criteria': {
                'factors': ['录取难度', '薪资待遇', '基本要求', '发展潜力'],
                'scoring_method': '多维度加权综合评分'
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'性价比推荐失败: {str(e)}'}), 500

@recruitment_bp.route('/recruitment/health', methods=['GET'])
def recruitment_health():
    """录取查询API健康检查"""
    if not api:
        return jsonify({
            'status': 'unhealthy',
            'error': '录取查询API未初始化',
            'api_version': 'enhanced_v1.0'
        }), 503
        
    try:
        # 测试数据库连接
        connection = api.get_mysql_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM recruitment_records")
        record_count = cursor.fetchone()[0]
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'healthy',
            'recruitment_records': record_count,
            'api_version': 'enhanced_v1.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'api_version': 'enhanced_v1.0'
        }), 500


# ========================================
# 层级展示辅助函数
# ========================================

def get_hierarchy_description(data_level):
    """获取数据层级的描述信息"""
    descriptions = {
        '区县详情': '最具体的录取政策，针对特定区县/单位的详细要求',
        '市级汇总': '市级范围的政策概况，覆盖该市主要录取情况',  
        '省级汇总': '省级政策总览，提供全省录取的基本框架',
        None: '基础录取信息，基于实际录取数据统计'
    }
    return descriptions.get(data_level, '政策信息层级未明确')

def calculate_cost_effectiveness_score(region):
    """
    计算地区性价比得分（0-100分）
    基于多维度加权评分：录取难度40% + 薪资待遇30% + 基本要求20% + 发展潜力10%
    """
    total_score = 0.0
    
    # 1. 录取难度得分 (40%) - 录取人数多表示相对容易
    recruitment_score = min(region.get('recruitment_count', 0) * 2, 40)  # 最高40分
    total_score += recruitment_score
    
    # 2. 薪资待遇得分 (30%)
    salary_score = 0
    bachelor_salary = region.get('bachelor_salary')
    if bachelor_salary and isinstance(bachelor_salary, str) and '万' in bachelor_salary:
        try:
            # 提取薪资数字 (如"8-12万")
            import re
            numbers = re.findall(r'\d+', bachelor_salary)
            if numbers:
                avg_salary = sum(int(n) for n in numbers) / len(numbers)
                # 薪资越高得分越高，最高30分
                salary_score = min(avg_salary * 2.5, 30)
        except:
            salary_score = 10  # 默认分数
    elif bachelor_salary:
        salary_score = 15  # 有薪资信息但解析失败
    total_score += salary_score
    
    # 3. 基本要求得分 (20%) - 要求越宽松得分越高
    requirement_score = 20  # 基础分
    if region.get('cet_requirement') == '必须':
        requirement_score -= 5
    elif region.get('cet_requirement') == '优先':
        requirement_score -= 2
        
    if region.get('computer_requirement') == '必须':
        requirement_score -= 3
    elif region.get('computer_requirement') == '优先':
        requirement_score -= 1
        
    if region.get('household_priority') == '必须':
        requirement_score -= 5
    elif region.get('household_priority') == '是':
        requirement_score -= 2
        
    total_score += max(requirement_score, 0)
    
    # 4. 发展潜力得分 (10%) - 基于地理位置和层级
    development_score = 0
    if region.get('data_level') == '区县详情':
        development_score = 8  # 具体区县，政策明确
    elif region.get('data_level') == '市级汇总':
        development_score = 6  # 市级，发展空间大
    else:
        development_score = 4  # 省级，相对一般
        
    # 核心城市加分
    city = region.get('city', '')
    if city in ['成都', '天府', '重庆', '市区']:
        development_score += 2
        
    total_score += development_score
    
    return round(total_score, 1)

def get_recommendation_reasons(region):
    """生成推荐理由"""
    reasons = []
    
    # 录取难度分析
    count = region.get('recruitment_count', 0)
    if count >= 10:
        reasons.append(f'录取人数较多({count}人)，相对容易进入')
    elif count >= 5:
        reasons.append(f'有一定录取名额({count}人)')
    elif count > 0:
        reasons.append(f'录取名额有限({count}人)，需要充分准备')
    else:
        reasons.append('新设岗位或政策区域，竞争相对较小')
    
    # 薪资分析
    salary = region.get('bachelor_salary')
    if salary and '万' in str(salary):
        reasons.append(f'薪资待遇: {salary}')
    
    # 基本要求分析
    requirements = []
    if region.get('cet_requirement') not in [None, '不要求']:
        requirements.append(f'英语: {region.get("cet_requirement")}')
    if region.get('computer_requirement') not in [None, '不要求']:
        requirements.append(f'计算机: {region.get("computer_requirement")}')
    if region.get('household_priority') not in [None, '否']:
        requirements.append(f'户籍: {region.get("household_priority")}')
    
    if requirements:
        reasons.append('基本要求: ' + ', '.join(requirements))
    else:
        reasons.append('基本要求相对宽松')
    
    # 地理优势
    city = region.get('city', '')
    province = region.get('province', '')
    if city in ['成都', '天府']:
        reasons.append('位于经济发达的成都天府地区')
    elif city == '重庆':
        reasons.append('直辖市，发展前景良好')
    elif province in ['四川', '重庆']:
        reasons.append('西部重点发展区域')
    
    return reasons[:4]  # 返回最多4个理由

def should_include_region(region, region_type):
    """根据类型过滤地区"""
    if region_type == 'all':
        return True
    elif region_type == 'city':
        return region.get('data_level') in ['省级汇总', '市级汇总']
    elif region_type == 'county':
        return region.get('data_level') == '区县详情'
    return True

# ========================================
# 增强版8字段筛选核心函数
# ========================================

def get_enhanced_policies_with_filters(company_type=None, batch=None, province=None, 
                                       city=None, county=None, school_name=None,
                                       bachelor_level=None, master_level=None,
                                       page=1, limit=20):
    """
    8字段筛选的增强版政策查询功能
    
    支持两大模块：
    1. 数据分析模块 - 录取情况统计分析
    2. 录取政策模块 - 政策规则详情展示
    """
    if not api:
        return {'error': '录取查询API未初始化'}
        
    connection = api.get_mysql_connection()
    cursor = connection.cursor()
    
    try:
        # 构建查询条件 - 注意：analysis查询不使用rr别名，policy查询使用
        conditions = []
        params = []
        
        # 基础筛选条件
        if company_type:
            conditions.append("company_type = %s")
            params.append(company_type)
            
        if batch:
            # 批次映射：前端batch -> 后端batch_type
            batch_mapping = {
                '一批': '一批',
                '二批': '二批', 
                '三批': '三批',
                '南网': '南网',
                '提前批': '提前批'
            }
            if batch in batch_mapping:
                conditions.append("batch_type = %s")
                params.append(batch_mapping[batch])
                
        if province:
            conditions.append("province = %s") 
            params.append(province)
            
        if city:
            conditions.append("city = %s")
            params.append(city)
            
        if county:
            conditions.append("company LIKE %s")
            params.append(f"%{county}%")
            
        if school_name:
            conditions.append("u.standard_name LIKE %s")
            params.append(f"%{school_name}%")
            
        # 学历层次筛选 - 使用新的数据库结构
        if bachelor_level:
            conditions.append("u.level IN ('985工程', '211工程', '普通本科')")
                
        if master_level:
            conditions.append("u.level LIKE '%硕士%'")
            
        # 为数据分析和政策分析分别构建WHERE子句
        analysis_where = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        # 政策分析使用原始条件（不添加别名前缀，在政策分析函数中处理）
        policy_where = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        # ===== 数据分析模块 =====
        data_analysis = get_recruitment_analysis(cursor, analysis_where, params)
        
        # ===== 录取政策模块 =====  
        # 注意：政策表没有company_type字段，只按地理位置筛选
        policy_analysis = get_policy_rules_analysis(cursor, None, province, city, page, limit)
        
        cursor.close()
        connection.close()
        
        return {
            'query_params': {
                'company_type': company_type,
                'batch': batch,
                'province': province, 
                'city': city,
                'county': county,
                'school_name': school_name,
                'bachelor_level': bachelor_level,
                'master_level': master_level,
                'page': page,
                'limit': limit
            },
            'data_analysis': data_analysis,
            'policy_analysis': policy_analysis
        }
        
    except Exception as e:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()
        return {'error': str(e)}


def get_recruitment_analysis(cursor, where_clause, params):
    """数据分析模块 - 录取情况统计分析"""
    
    analysis = {
        'total_count': 0,
        'gender_distribution': {},
        'school_type_distribution': {},
        'company_distribution': {},
        'detailed_statistics': []
    }
    
    try:
        # 1. 总录取人数统计
        sql = f"SELECT COUNT(*) FROM recruitment_records {where_clause}"
        cursor.execute(sql, params)
        analysis['total_count'] = cursor.fetchone()[0]
        
        # 2. 男女比例统计
        sql = f"""
        SELECT gender, COUNT(*) as count, 
               ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM recruitment_records {where_clause}
        GROUP BY gender
        """
        cursor.execute(sql, params)
        analysis['gender_distribution'] = {
            row[0]: {'count': row[1], 'percentage': float(row[2])} 
            for row in cursor.fetchall()
        }
        
        # 3. 学校类型分布 (985/211/双一流/普通本科/专科) - 使用新的数据库结构
        sql = f"""
        SELECT 
            CASE 
                WHEN u.level IN ('985工程', '211工程') THEN '重点高校'
                WHEN u.level = '普通本科' THEN '普通本科'
                WHEN u.level = '专科院校' THEN '专科'
                ELSE '其他'
            END as category,
            u.level as school_type,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM recruitment_records rr
        LEFT JOIN universities u ON rr.university_id = u.university_id
        LEFT JOIN secondary_units su ON rr.secondary_unit_id = su.unit_id
        {where_clause}
        GROUP BY u.level
        ORDER BY count DESC
        """
        cursor.execute(sql, params)
        
        school_distribution = {}
        for row in cursor.fetchall():
            category = row[0]
            if category not in school_distribution:
                school_distribution[category] = {'total': 0, 'types': []}
            school_distribution[category]['total'] += row[2]
            school_distribution[category]['types'].append({
                'type': row[1],
                'count': row[2], 
                'percentage': float(row[3])
            })
        
        analysis['school_type_distribution'] = school_distribution
        
        # 4. 地区分布按二级单位展示 - 修复公司名称为null的问题
        sql = f"""
        SELECT COALESCE(company, CONCAT(COALESCE(province, '未知省份'), '-', COALESCE(city, '未知城市'))) as company_name, 
               COUNT(*) as count,
               ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM recruitment_records {where_clause}
        GROUP BY COALESCE(company, CONCAT(COALESCE(province, '未知省份'), '-', COALESCE(city, '未知城市')))
        ORDER BY count DESC
        LIMIT 10
        """
        cursor.execute(sql, params)
        analysis['company_distribution'] = [
            {
                'company': row[0],
                'count': row[1],
                'percentage': float(row[2])
            }
            for row in cursor.fetchall()
        ]
        
        # 5. 详细统计数据 - 添加学校统计信息 - 使用新的数据库结构
        sql = f"""
        SELECT u.standard_name, u.level, COUNT(*) as count,
               ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM recruitment_records rr
        LEFT JOIN universities u ON rr.university_id = u.university_id
        LEFT JOIN secondary_units su ON rr.secondary_unit_id = su.unit_id
        {where_clause}
        GROUP BY u.university_id, u.standard_name, u.level
        ORDER BY count DESC
        LIMIT 50
        """
        cursor.execute(sql, params)
        analysis['detailed_statistics'] = [
            {
                'school_name': row[0],
                'school_type': row[1],
                'count': row[2],
                'percentage': float(row[3])
            }
            for row in cursor.fetchall()
        ]
        
        return analysis
        
    except Exception as e:
        return {'error': f'数据分析失败: {str(e)}'}


def get_policy_rules_analysis(cursor, company_type=None, province=None, city=None, page=1, limit=20):
    """录取政策模块 - 政策规则详情展示（层级展示逻辑）"""
    
    try:
        # 计算分页偏移量
        offset = (page - 1) * limit
        
        # 构建政策规则表的筛选条件
        policy_conditions = []
        policy_params = []
        
        if company_type:
            policy_conditions.append("ru.company_type = %s")
            policy_params.append(company_type)
            
        if province:
            policy_conditions.append("ru.province = %s")
            policy_params.append(province)
            
        if city:
            policy_conditions.append("ru.city = %s")
            policy_params.append(city)
            
        policy_where = "AND " + " AND ".join(policy_conditions) if policy_conditions else ""
        
        sql = f"""
        SELECT DISTINCT ru.province, ru.city, ru.company,
               ru.data_level, ru.detailed_rules, ru.stable_score_range,
               ru.bachelor_salary, ru.master_salary,
               ru.bachelor_interview_line, ru.master_interview_line,
               ru.cet_requirement, ru.computer_requirement,
               ru.household_priority, ru.non_first_choice_pass,
               ru.is_best_value_city, ru.is_best_value_county,
               COALESCE(COUNT(rr.id), 0) as recruitment_count
        FROM recruitment_rules ru
        LEFT JOIN recruitment_records rr ON ru.province = rr.province 
            AND (ru.city = rr.city OR ru.city IS NULL)
            AND (ru.company = rr.company OR ru.company IS NULL)
        WHERE 1=1 {policy_where}
        GROUP BY ru.id, ru.province, ru.city, ru.company, 
                 ru.data_level, ru.detailed_rules, ru.stable_score_range,
                 ru.bachelor_salary, ru.master_salary,
                 ru.bachelor_interview_line, ru.master_interview_line,
                 ru.cet_requirement, ru.computer_requirement,
                 ru.household_priority, ru.non_first_choice_pass,
                 ru.is_best_value_city, ru.is_best_value_county
        ORDER BY 
            CASE 
                WHEN ru.data_level = '区县详情' THEN 1
                WHEN ru.data_level = '市级汇总' THEN 2
                WHEN ru.data_level = '省级汇总' THEN 3
                ELSE 4
            END,
            CASE WHEN ru.detailed_rules IS NOT NULL THEN 1 ELSE 2 END,
            recruitment_count DESC
        LIMIT %s OFFSET %s
        """
        
        cursor.execute(sql, policy_params + [limit, offset])
        
        policies = []
        for row in cursor.fetchall():
            policy = {
                'province': row[0],
                'city': row[1], 
                'company': row[2],
                'data_level': row[3],  # 数据层级 
                'detailed_rules': row[4],  # 详细规则
                'stable_score_range': row[5],  # 稳定分数范围
                'salary_info': {
                    'bachelor_salary': row[6],
                    'master_salary': row[7],
                    'bachelor_interview_line': row[8],
                    'master_interview_line': row[9]
                },
                'basic_requirements': {
                    'cet_requirement': row[10],  # 四六级要求
                    'computer_requirement': row[11],  # 计算机要求  
                    'household_priority': row[12],  # 户口优先
                    'non_first_choice_pass': row[13]  # 非第一志愿通过
                },
                'is_best_value_city': row[14] == '是',
                'is_best_value_county': row[15] == '是',
                'recruitment_count': row[16],
                'is_cost_effective': row[14] == '是' or row[15] == '是',
                'cost_effective_reason': '性价比推荐地区' if (row[14] == '是' or row[15] == '是') else None,
                'hierarchy_level': {
                    'level': row[3] if row[3] else '未分级',
                    'priority': 1 if row[3] == '区县详情' else (2 if row[3] == '市级汇总' else 3),
                    'description': get_hierarchy_description(row[3])
                }
            }
            policies.append(policy)
            
        # 获取总数用于分页 - 基于政策规则表
        count_sql = f"""
        SELECT COUNT(DISTINCT ru.id)
        FROM recruitment_rules ru
        LEFT JOIN recruitment_records rr ON ru.province = rr.province 
            AND (ru.city = rr.city OR ru.city IS NULL)
            AND (ru.company = rr.company OR ru.company IS NULL)
        WHERE 1=1 {policy_where}
        """
        cursor.execute(count_sql, policy_params)
        total_count = cursor.fetchone()[0]
        
        return {
            'policies': policies,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'total_pages': (total_count + limit - 1) // limit
            }
        }
        
    except Exception as e:
        return {'error': f'政策分析失败: {str(e)}'}


def get_detailed_statistics(cursor, where_clause, params, page=1, limit=20):
    """详细统计 - 按学校名称+类型+人数+占比统计"""
    
    try:
        offset = (page - 1) * limit
        
        # 详细统计查询 - 使用新的数据库结构
        sql = f"""
        SELECT u.standard_name, u.level, COUNT(*) as count,
               ROUND(COUNT(*) * 100.0 / (
                   SELECT COUNT(*) FROM recruitment_records rr2
                   LEFT JOIN universities u2 ON rr2.university_id = u2.university_id
                   LEFT JOIN secondary_units su2 ON rr2.secondary_unit_id = su2.unit_id
                   {where_clause}
               ), 2) as percentage
        FROM recruitment_records rr
        LEFT JOIN universities u ON rr.university_id = u.university_id
        LEFT JOIN secondary_units su ON rr.secondary_unit_id = su.unit_id
        {where_clause}
        GROUP BY u.university_id, u.standard_name, u.level
        ORDER BY count DESC
        LIMIT %s OFFSET %s
        """
        
        cursor.execute(sql, params * 2 + [limit, offset])
        
        statistics = []
        for row in cursor.fetchall():
            statistics.append({
                'school': row[0],
                'school_type': row[1], 
                'count': row[2],
                'percentage': float(row[3])
            })
            
        return statistics
        
    except Exception as e:
        return {'error': f'详细统计失败: {str(e)}'}
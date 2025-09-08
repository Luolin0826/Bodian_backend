#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试API流程，看看为什么区县筛选不生效
"""

import mysql.connector

class DebugDataSearchAPI:
    def __init__(self):
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
        return mysql.connector.connect(**self.db_config)
    
    def debug_policy_query(self, filters):
        """调试政策查询过程"""
        print("=== 调试政策查询流程 ===")
        print(f"输入参数: {filters}")
        
        connection = self.get_mysql_connection()
        cursor = connection.cursor(dictionary=True)
        
        # 模拟 _get_recruitment_policy_info 的逻辑
        conditions = []
        params = []
        
        # 1. 推断省份
        province = None
        city = filters.get('city')
        district = None
        
        if filters.get('company') == '国网':
            if filters.get('secondary_unit'):
                if filters['secondary_unit'] in ['四川', '成都', '天府', '绵阳']:
                    province = '四川'
                    if filters['secondary_unit'] in ['成都', '天府', '绵阳']:
                        city = filters['secondary_unit']
                elif filters['secondary_unit'] in ['北京', '上海', '天津', '重庆']:
                    province = filters['secondary_unit']
                    city = filters['secondary_unit']
                else:
                    province = filters['secondary_unit']
        
        print(f"第1步 - 从secondary_unit推断: province={province}, city={city}")
        
        # 2. 从city参数获取城市信息
        if filters.get('city'):
            city = filters['city']
            if city in ['成都', '天府', '绵阳']:
                province = '四川'
            elif city in ['北京']:
                province = '北京'
            # ... 其他城市映射
        
        print(f"第2步 - 从city推断: province={province}, city={city}")
        
        # 3. 从county参数推断城市和省份信息  
        if filters.get('county') and not city:
            county = filters['county']
            if county in ['游仙区', '涪城区']:
                city = '绵阳'
                province = '四川'
            # ... 其他区县映射
        
        print(f"第3步 - 从county推断: province={province}, city={city}")
        
        # 4. 构建查询条件
        if province:
            conditions.append("province = %s")
            params.append(province)
        
        if city:
            conditions.append("city = %s")
            params.append(city)
        
        if filters.get('district'):
            conditions.append("company = %s")
            params.append(filters['district'])
        
        if filters.get('county'):
            conditions.append("company = %s")
            params.append(filters['county'])
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        print(f"第4步 - 查询条件: {where_clause}")
        print(f"第4步 - 查询参数: {params}")
        
        # 5. 执行查询
        query = f"""
            SELECT 
                id, province, city, company as district, data_level
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
        
        print(f"第5步 - SQL查询:")
        print(query)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        print(f"第5步 - 查询结果 ({len(results)} 条):")
        for row in results:
            print(f"  ID:{row['id']} | {row['province']} - {row['city']} - {row['district']} | {row['data_level']}")
        
        # 6. 政策分层处理
        policy_hierarchy = {
            '省级汇总': [],
            '市级汇总': [],
            '区县详情': []
        }
        
        for row in results:
            policy_hierarchy[row['data_level']].append(row)
        
        print(f"第6步 - 政策分层:")
        for level, policies in policy_hierarchy.items():
            print(f"  {level}: {len(policies)} 条")
        
        # 7. 选择最终政策
        final_policies = []
        
        print(f"第7步 - 政策选择逻辑:")
        print(f"  filters.get('county'): {filters.get('county')}")
        
        if filters.get('county'):
            county_name = filters['county']
            print(f"  指定了区县: {county_name}")
            county_policies = [p for p in policy_hierarchy['区县详情'] if p['district'] == county_name]
            print(f"  匹配的区县政策: {len(county_policies)} 条")
            if county_policies:
                final_policies.extend(county_policies)
                print(f"  使用区县政策: {len(county_policies)} 条")
            else:
                final_policies.extend(policy_hierarchy['市级汇总'])
                print(f"  回退到市级政策: {len(policy_hierarchy['市级汇总'])} 条")
        elif policy_hierarchy['区县详情']:
            final_policies.extend(policy_hierarchy['区县详情'])
            print(f"  使用所有区县政策: {len(policy_hierarchy['区县详情'])} 条")
        elif policy_hierarchy['市级汇总']:
            final_policies.extend(policy_hierarchy['市级汇总'])
            print(f"  使用市级政策: {len(policy_hierarchy['市级汇总'])} 条")
        elif policy_hierarchy['省级汇总']:
            final_policies.extend(policy_hierarchy['省级汇总'])
            print(f"  使用省级政策: {len(policy_hierarchy['省级汇总'])} 条")
        
        print(f"第7步 - 最终政策数量: {len(final_policies)}")
        print("最终政策列表:")
        for i, policy in enumerate(final_policies):
            print(f"  {i+1}. {policy['province']} - {policy['city']} - {policy['district']}")
        
        cursor.close()
        connection.close()

# 测试
filters = {
    'company': '国网',
    'secondary_unit': '四川',
    'city': '绵阳',
    'county': '游仙区',
    'university_name': '哈尔滨工业大学',
    'page': 1,
    'limit': 50
}

debug_api = DebugDataSearchAPI()
debug_api.debug_policy_query(filters)
#!/usr/bin/env python3
import mysql.connector

db_config = {
    'host': 'rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'database': 'bdprod',
    'user': 'dms_user_9332d9e',
    'password': 'AaBb19990826',
    'charset': 'utf8mb4'
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor(dictionary=True)

# 模拟搜索条件
filters = {
    'company': '国网',
    'secondary_unit': '四川',
    'city': '绵阳',
    'county': '游仙区',
    'university_name': '哈尔滨工业大学'
}

print("=== 测试政策查询逻辑 ===")
print(f"搜索条件: {filters}")

# 构建查询条件 - 模拟 _get_recruitment_policy_info 方法
conditions = []
params = []

# 省份
province = '四川'  # 从 secondary_unit 推断
if province:
    conditions.append("province = %s")
    params.append(province)
    print(f"添加省份条件: province = {province}")

# 城市
city = filters.get('city')
if city:
    conditions.append("city = %s")
    params.append(city)
    print(f"添加城市条件: city = {city}")

# 区县
county = filters.get('county')
if county:
    conditions.append("company = %s")
    params.append(county)
    print(f"添加区县条件: company = {county}")

where_clause = " AND ".join(conditions)
print(f"\n生成的WHERE子句: {where_clause}")
print(f"查询参数: {params}")

# 执行查询
query = f"""
    SELECT id, province, city, company as district, data_level
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

print(f"\n完整SQL查询:")
print(query)
print(f"参数: {params}")

cursor.execute(query, params)
results = cursor.fetchall()

print(f"\n查询结果 ({len(results)} 条):")
for row in results:
    print(f"ID:{row['id']} | {row['province']} - {row['city']} - {row['district']} | {row['data_level']}")

cursor.close()
conn.close()
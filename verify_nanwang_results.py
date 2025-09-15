#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证南网数据处理结果并补充新增院校信息
"""
import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import datetime

def connect_to_database():
    """连接到数据库"""
    try:
        connection = mysql.connector.connect(
            host='rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
            port=3306,
            database='bdprod',
            user='dms_user_9332d9e',
            password='AaBb19990826',
            charset='utf8mb4'
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def verify_and_update_nanwang():
    """验证南网数据处理结果并补充新增院校信息"""
    print("="*80)
    print("验证南网数据处理结果")
    print("="*80)
    
    connection = connect_to_database()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(buffered=True)
        
        # 1. 读取Excel南网数据
        print("1. 读取Excel数据...")
        df = pd.read_excel("25国网南网录取_updated.xlsx", sheet_name="南网")
        excel_records = len(df)
        print(f"Excel南网记录数: {excel_records}")
        
        # 2. 检查数据库中南网记录
        print("2. 检查数据库中南网记录...")
        cursor.execute("""
            SELECT COUNT(*) FROM recruitment_records 
            WHERE company = '南网'
        """)
        db_nanwang = cursor.fetchone()[0]
        print(f"数据库中南网记录数: {db_nanwang}")
        
        # 3. 检查新增院校信息
        print("3. 检查新增院校...")
        cursor.execute("""
            SELECT university_id, university_code, standard_name, 
                   level, type, power_feature, location
            FROM universities 
            WHERE university_code LIKE 'NWU%'
            ORDER BY university_id
        """)
        new_unis = cursor.fetchall()
        
        if new_unis:
            print(f"新增院校: {len(new_unis)} 个")
            for uni in new_unis:
                uni_id, code, name, level, uni_type, power_feature, location = uni
                print(f"  {uni_id}. {name}")
                print(f"     代码: {code}")
                print(f"     等级: {level or '未设置'}")
                print(f"     类型: {uni_type or '未设置'}")
                print(f"     电力特色: {power_feature or '未设置'}")
                print(f"     地区: {location or '未设置'}")
                print()
            
            # 4. 补充新增院校信息
            print("4. 补充新增院校详细信息...")
            
            # 定义院校详细信息
            universities_info = {
                '华北电力大学': {
                    'level': '211工程',
                    'type': '理工类',
                    'power_feature': '电力特色高校',
                    'location': '北京市'
                },
                '中国矿业大学': {
                    'level': '211工程',
                    'type': '理工类',
                    'power_feature': '普通高校',
                    'location': '江苏省'
                },
                '浙江科技大学': {
                    'level': '普通本科',
                    'type': '理工类',
                    'power_feature': '普通高校',
                    'location': '浙江省'
                },
                '中国石油大学（华东）': {
                    'level': '211工程',
                    'type': '理工类',
                    'power_feature': '普通高校',
                    'location': '山东省'
                },
                '中国石油大学（北京）': {
                    'level': '211工程',
                    'type': '理工类',
                    'power_feature': '普通高校',
                    'location': '北京市'
                },
                '中国矿业大学（北京）': {
                    'level': '211工程',
                    'type': '理工类',
                    'power_feature': '普通高校',
                    'location': '北京市'
                },
                '中国地质大学': {
                    'level': '211工程',
                    'type': '理工类',
                    'power_feature': '普通高校',
                    'location': '北京市'
                }
            }
            
            updated_count = 0
            for uni in new_unis:
                uni_id, code, name = uni[0], uni[1], uni[2]
                
                if name in universities_info:
                    info = universities_info[name]
                    try:
                        cursor.execute("""
                            UPDATE universities 
                            SET level = %s, type = %s, power_feature = %s, location = %s, updated_at = %s
                            WHERE university_id = %s
                        """, (
                            info['level'],
                            info['type'],
                            info['power_feature'],
                            info['location'],
                            datetime.now(),
                            uni_id
                        ))
                        
                        updated_count += 1
                        print(f"✅ 更新成功: {name}")
                        print(f"   等级: {info['level']}")
                        print(f"   类型: {info['type']}")
                        print(f"   电力特色: {info['power_feature']}")
                        print(f"   地区: {info['location']}")
                        print()
                        
                    except Error as e:
                        print(f"❌ 更新失败 {name}: {e}")
                else:
                    print(f"⚠️  未找到院校信息定义: {name}")
            
            print(f"成功更新 {updated_count} 个院校信息")
        
        # 5. 精确匹配验证
        print("\n5. 精确匹配验证...")
        
        # 创建临时表
        cursor.execute("DROP TEMPORARY TABLE IF EXISTS temp_verify_nanwang")
        cursor.execute("""
            CREATE TEMPORARY TABLE temp_verify_nanwang (
                name VARCHAR(50), 
                phone VARCHAR(20)
            )
        """)
        
        # 插入Excel数据
        temp_data = []
        for _, row in df.iterrows():
            if not pd.isna(row['手机号']):
                temp_data.append((row['姓名'], str(row['手机号'])))
        
        if temp_data:
            cursor.executemany("""
                INSERT INTO temp_verify_nanwang (name, phone) 
                VALUES (%s, %s)
            """, temp_data)
        
        # 查询匹配情况
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT CONCAT(tv.name, '|', tv.phone)) as excel_unique,
                COUNT(DISTINCT CONCAT(rr.name, '|', rr.phone)) as db_matched
            FROM temp_verify_nanwang tv
            LEFT JOIN recruitment_records rr ON tv.name = rr.name AND tv.phone = rr.phone
        """)
        result = cursor.fetchone()
        excel_unique = result[0]
        db_matched = result[1]
        
        print(f"Excel中唯一人员: {excel_unique}")
        print(f"数据库中匹配人员: {db_matched}")
        
        # 6. 检查国网南网重叠情况
        print("\n6. 检查国网南网人员重叠情况...")
        cursor.execute("""
            SELECT 
                r1.name, r1.phone, r1.company as company1, r1.batch as batch1,
                r2.company as company2, r2.batch as batch2
            FROM recruitment_records r1
            JOIN recruitment_records r2 ON r1.name = r2.name AND r1.phone = r2.phone
            WHERE r1.company != r2.company AND r1.record_id < r2.record_id
            ORDER BY r1.name
        """)
        overlapping = cursor.fetchall()
        
        if overlapping:
            print(f"发现 {len(overlapping)} 个同时被国网和南网录取的人员:")
            for i, person in enumerate(overlapping[:10], 1):
                name, phone, comp1, batch1, comp2, batch2 = person
                print(f"  {i}. {name} - {comp1}({batch1}) + {comp2}({batch2})")
            if len(overlapping) > 10:
                print(f"  ... 还有 {len(overlapping) - 10} 个重叠人员")
        else:
            print("未发现国网南网重叠录取人员")
        
        # 7. 检查所有公司统计
        print("\n7. 检查所有公司和批次统计...")
        cursor.execute("""
            SELECT company, batch, COUNT(*) as count
            FROM recruitment_records 
            GROUP BY company, batch
            ORDER BY company, 
                CASE batch
                    WHEN '第一批' THEN 1
                    WHEN '第二批' THEN 2  
                    WHEN '第三批' THEN 3
                    WHEN '南网批次' THEN 4
                    ELSE 5
                END
        """)
        all_stats = cursor.fetchall()
        
        company_totals = {}
        print("详细统计:")
        for company, batch, count in all_stats:
            print(f"  {company} - {batch}: {count:,} 人")
            company_totals[company] = company_totals.get(company, 0) + count
        
        print("\n公司总计:")
        total_all = 0
        for company, total in company_totals.items():
            print(f"  {company}: {total:,} 人")
            total_all += total
        print(f"  总计: {total_all:,} 人")
        
        # 8. 检查院校总数
        print("\n8. 检查院校总数...")
        cursor.execute("SELECT COUNT(*) FROM universities")
        total_universities = cursor.fetchone()[0]
        print(f"院校总数: {total_universities} 个")
        
        # 提交更改
        connection.commit()
        
        print("\n" + "="*80)
        print("南网数据验证完成！")
        print("="*80)
        
    except Exception as e:
        print(f"验证过程中出现错误: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    verify_and_update_nanwang()
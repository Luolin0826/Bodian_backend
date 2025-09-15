#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证第三批数据处理结果和补充新增院校信息
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

def verify_and_update_third_batch():
    """验证第三批数据处理结果并补充新增院校信息"""
    print("="*80)
    print("验证第三批数据处理结果")
    print("="*80)
    
    connection = connect_to_database()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(buffered=True)
        
        # 1. 读取Excel第三批数据
        print("1. 读取Excel数据...")
        df = pd.read_excel("25国网南网录取_updated.xlsx", sheet_name="三批")
        excel_records = len(df)
        print(f"Excel第三批记录数: {excel_records}")
        
        # 2. 检查数据库中第三批记录
        print("2. 检查数据库中第三批记录...")
        cursor.execute("""
            SELECT COUNT(*) FROM recruitment_records 
            WHERE batch = '第三批' AND company = '国网'
        """)
        db_third_batch = cursor.fetchone()[0]
        print(f"数据库中第三批记录数: {db_third_batch}")
        
        # 3. 检查新增院校信息
        print("3. 检查新增院校...")
        cursor.execute("""
            SELECT university_id, university_code, standard_name, 
                   level, type, power_feature, location
            FROM universities 
            WHERE university_code LIKE 'B3U%'
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
            
            # 中国地质大学(武汉)的详细信息
            university_info = {
                'level': '211工程',
                'type': '理工类',
                'power_feature': '普通高校',
                'location': '湖北省'
            }
            
            for uni in new_unis:
                uni_id, code, name = uni[0], uni[1], uni[2]
                
                if name == '中国地质大学(武汉)':
                    try:
                        cursor.execute("""
                            UPDATE universities 
                            SET level = %s, type = %s, power_feature = %s, location = %s, updated_at = %s
                            WHERE university_id = %s
                        """, (
                            university_info['level'],
                            university_info['type'],
                            university_info['power_feature'],
                            university_info['location'],
                            datetime.now(),
                            uni_id
                        ))
                        
                        print(f"✅ 更新成功: {name}")
                        print(f"   等级: {university_info['level']}")
                        print(f"   类型: {university_info['type']}")
                        print(f"   电力特色: {university_info['power_feature']}")
                        print(f"   地区: {university_info['location']}")
                        
                    except Error as e:
                        print(f"❌ 更新失败 {name}: {e}")
        
        # 5. 精确匹配验证
        print("\n5. 精确匹配验证...")
        
        # 创建临时表
        cursor.execute("DROP TEMPORARY TABLE IF EXISTS temp_verify_third")
        cursor.execute("""
            CREATE TEMPORARY TABLE temp_verify_third (
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
                INSERT INTO temp_verify_third (name, phone) 
                VALUES (%s, %s)
            """, temp_data)
        
        # 查询匹配情况
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT CONCAT(tv.name, '|', tv.phone)) as excel_unique,
                COUNT(DISTINCT CONCAT(rr.name, '|', rr.phone)) as db_matched
            FROM temp_verify_third tv
            LEFT JOIN recruitment_records rr ON tv.name = rr.name AND tv.phone = rr.phone
        """)
        result = cursor.fetchone()
        excel_unique = result[0]
        db_matched = result[1]
        
        print(f"Excel中唯一人员: {excel_unique}")
        print(f"数据库中匹配人员: {db_matched}")
        
        # 6. 检查所有批次统计
        print("\n6. 检查所有批次统计...")
        cursor.execute("""
            SELECT batch, COUNT(*) as count
            FROM recruitment_records 
            WHERE company = '国网'
            GROUP BY batch
            ORDER BY 
                CASE batch
                    WHEN '第一批' THEN 1
                    WHEN '第二批' THEN 2  
                    WHEN '第三批' THEN 3
                    ELSE 4
                END
        """)
        batch_stats = cursor.fetchall()
        total_count = 0
        print("国网批次统计:")
        for batch, count in batch_stats:
            print(f"  {batch}: {count:,} 人")
            total_count += count
        print(f"  总计: {total_count:,} 人")
        
        # 7. 检查院校总数
        print("\n7. 检查院校总数...")
        cursor.execute("SELECT COUNT(*) FROM universities")
        total_universities = cursor.fetchone()[0]
        print(f"院校总数: {total_universities} 个")
        
        # 提交更改
        connection.commit()
        
        print("\n" + "="*80)
        print("第三批数据验证完成！")
        print("="*80)
        
    except Exception as e:
        print(f"验证过程中出现错误: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    verify_and_update_third_batch()
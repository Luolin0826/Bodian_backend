#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入sanji.xlsx数据到administrative_regions表
处理三级行政区划数据：省份 -> 地级市 -> 区县公司
特别处理直辖市情况
"""

import pandas as pd
import mysql.connector
from mysql.connector import Error
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'database': 'bdprod',
    'user': 'dms_user_9332d9e',
    'password': 'AaBb19990826',
    'charset': 'utf8mb4',
    'autocommit': True,
    'use_unicode': True
}

def get_db_connection():
    """获取数据库连接"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        logger.error(f"数据库连接失败: {e}")
        raise e

def is_municipality(province_name):
    """判断是否为直辖市"""
    municipalities = ['北京', '上海', '天津', '重庆']
    return province_name in municipalities

def clean_data():
    """清理现有数据"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        logger.info("清理现有administrative_regions数据...")
        cursor.execute("DELETE FROM administrative_regions")
        cursor.execute("ALTER TABLE administrative_regions AUTO_INCREMENT = 1")
        
        cursor.close()
        connection.close()
        logger.info("数据清理完成")
        
    except Exception as e:
        logger.error(f"数据清理失败: {e}")
        raise e

def import_regions_data():
    """导入行政区划数据"""
    try:
        # 读取Excel文件
        logger.info("读取sanji.xlsx文件...")
        df = pd.read_excel('/workspace/sanji.xlsx')
        logger.info(f"共读取 {len(df)} 条记录")
        
        # 清理数据
        clean_data()
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # 存储省份ID映射
        province_id_map = {}
        city_id_map = {}
        
        # 第一步：插入所有省份
        logger.info("第一步：插入省份数据...")
        provinces = df['省份 *'].dropna().unique()
        
        for province in provinces:
            is_municip = is_municipality(province)
            
            insert_query = """
            INSERT INTO administrative_regions 
            (province, region_level, is_municipality, is_active, sort_order, region_code) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            # 生成省份编码
            province_code = f"PROV_{province}"
            
            cursor.execute(insert_query, (
                province, 'province', is_municip, 1, 0, province_code
            ))
            
            province_id = cursor.lastrowid
            province_id_map[province] = province_id
            
            logger.info(f"插入省份: {province} (ID: {province_id}, 直辖市: {is_municip})")
        
        # 第二步：插入地级市数据
        logger.info("第二步：插入地级市数据...")
        city_data = df[df['地级市'].notna()][['省份 *', '地级市']].drop_duplicates()
        
        for _, row in city_data.iterrows():
            province = row['省份 *']
            city = row['地级市']
            
            if province in province_id_map:
                parent_id = province_id_map[province]
                
                insert_query = """
                INSERT INTO administrative_regions 
                (province, city, region_level, parent_region_id, is_active, sort_order, region_code) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                
                city_code = f"CITY_{province}_{city}"
                
                cursor.execute(insert_query, (
                    province, city, 'city', parent_id, 1, 0, city_code
                ))
                
                city_id = cursor.lastrowid
                city_key = f"{province}_{city}"
                city_id_map[city_key] = city_id
                
                logger.info(f"插入地级市: {province} -> {city} (ID: {city_id})")
        
        # 第三步：插入区县公司数据
        logger.info("第三步：插入区县公司数据...")
        company_data = df[df['公司'].notna()]
        
        for _, row in company_data.iterrows():
            province = row['省份 *']
            city = row['地级市'] if pd.notna(row['地级市']) else None
            company = row['公司']
            
            # 确定父级ID
            parent_id = None
            if city and f"{province}_{city}" in city_id_map:
                parent_id = city_id_map[f"{province}_{city}"]
            elif province in province_id_map:
                parent_id = province_id_map[province]
            
            if parent_id:
                insert_query = """
                INSERT INTO administrative_regions 
                (province, city, company, region_level, parent_region_id, is_active, sort_order, region_code) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                # 生成唯一的company_code，使用递增ID避免重复
                import time
                import random
                unique_suffix = int(time.time() * 1000000) % 1000000 + random.randint(1000, 9999)
                company_code = f"COMP_{unique_suffix}"
                
                cursor.execute(insert_query, (
                    province, city, company, 'company', parent_id, 1, 0, company_code[:20]  # 限制长度
                ))
                
                company_id = cursor.lastrowid
                logger.info(f"插入区县公司: {province} -> {city} -> {company} (ID: {company_id})")
        
        cursor.close()
        connection.close()
        
        logger.info("行政区划数据导入完成！")
        
        # 统计导入结果
        print_import_statistics()
        
    except Exception as e:
        logger.error(f"数据导入失败: {e}")
        raise e

def print_import_statistics():
    """打印导入统计信息"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # 统计各级别数量
        cursor.execute("""
        SELECT region_level, COUNT(*) as count, 
               SUM(CASE WHEN is_municipality = 1 THEN 1 ELSE 0 END) as municipality_count
        FROM administrative_regions 
        GROUP BY region_level 
        ORDER BY FIELD(region_level, 'province', 'city', 'company')
        """)
        
        results = cursor.fetchall()
        
        print("\n=== 导入统计结果 ===")
        for region_level, count, municipality_count in results:
            level_name = {'province': '省份', 'city': '地级市', 'company': '区县公司'}[region_level]
            if region_level == 'province':
                print(f"{level_name}: {count}个 (其中直辖市: {municipality_count}个)")
            else:
                print(f"{level_name}: {count}个")
        
        # 显示直辖市详情
        cursor.execute("""
        SELECT province, COUNT(*) as total_count
        FROM administrative_regions 
        WHERE is_municipality = 1 OR province IN ('北京', '上海', '天津', '重庆')
        GROUP BY province
        ORDER BY province
        """)
        
        municipality_details = cursor.fetchall()
        
        print("\n=== 直辖市详情 ===")
        for province, count in municipality_details:
            print(f"{province}: {count}条记录")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        logger.error(f"统计信息获取失败: {e}")

def main():
    """主函数"""
    try:
        logger.info("开始导入行政区划数据...")
        import_regions_data()
        logger.info("导入完成！")
        
    except Exception as e:
        logger.error(f"导入过程失败: {e}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充四川省缺失的地市区县数据到administrative_regions表
"""

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

# 四川省缺失的地市区县数据
SICHUAN_DATA = {
    "眉山": ["东坡区", "彭山区", "仁寿县", "洪雅县", "丹棱县"],
    "遂宁": ["安居区", "船山区", "蓬溪县", "大英县", "射洪市"],
    "乐山": ["市中区", "峨眉山", "沐川"],
    "南充": ["高坪区", "顺庆区", "营山县", "蓬安县"],
    "宜宾": ["翠屏区", "南溪区", "江安县"],
    "资阳": ["雁江区", "乐至县"],
    "德阳": ["旌阳区", "罗江区"],
    "内江": ["市中区", "东兴区", "威远县"],
    "巴中": ["巴州区", "平昌县"],
    "攀枝花": ["东区", "西区", "盐边县", "米易县"],
    "三州": ["甘孜", "阿坝", "凉山", "西昌", "理县"]
}

def get_db_connection():
    """获取数据库连接"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        logger.error(f"数据库连接失败: {e}")
        raise e

def get_province_id():
    """获取四川省的ID"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("SELECT region_id FROM administrative_regions WHERE province = '四川' AND region_level = 'province'")
        result = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        if result:
            return result[0]
        else:
            logger.error("未找到四川省记录")
            return None
            
    except Exception as e:
        logger.error(f"获取省份ID失败: {e}")
        return None

def check_city_exists(city_name):
    """检查地级市是否已存在"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("SELECT region_id FROM administrative_regions WHERE province = '四川' AND city = %s AND region_level = 'city'", (city_name,))
        result = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return result[0] if result else None
        
    except Exception as e:
        logger.error(f"检查城市存在性失败: {e}")
        return None

def insert_city(city_name, province_id):
    """插入地级市"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        insert_query = """
        INSERT INTO administrative_regions 
        (province, city, region_level, parent_region_id, is_active, sort_order, region_code) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        city_code = f"CITY_四川_{city_name}"
        
        cursor.execute(insert_query, (
            "四川", city_name, 'city', province_id, 1, 0, city_code[:20]
        ))
        
        city_id = cursor.lastrowid
        
        cursor.close()
        connection.close()
        
        logger.info(f"插入地级市: {city_name} (ID: {city_id})")
        return city_id
        
    except Exception as e:
        logger.error(f"插入城市失败 {city_name}: {e}")
        return None

def check_company_exists(city_name, company_name):
    """检查区县是否已存在"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("SELECT region_id FROM administrative_regions WHERE province = '四川' AND city = %s AND company = %s AND region_level = 'company'", (city_name, company_name))
        result = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return result is not None
        
    except Exception as e:
        logger.error(f"检查区县存在性失败: {e}")
        return False

def insert_company(city_name, company_name, city_id):
    """插入区县"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        insert_query = """
        INSERT INTO administrative_regions 
        (province, city, company, region_level, parent_region_id, is_active, sort_order, region_code) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # 生成唯一的company_code
        import time
        import random
        unique_suffix = int(time.time() * 1000000) % 1000000 + random.randint(1000, 9999)
        company_code = f"COMP_{unique_suffix}"
        
        cursor.execute(insert_query, (
            "四川", city_name, company_name, 'company', city_id, 1, 0, company_code[:20]
        ))
        
        company_id = cursor.lastrowid
        
        cursor.close()
        connection.close()
        
        logger.info(f"插入区县: {city_name} -> {company_name} (ID: {company_id})")
        return company_id
        
    except Exception as e:
        logger.error(f"插入区县失败 {city_name}->{company_name}: {e}")
        return None

def insert_missing_regions():
    """插入缺失的地市区县"""
    try:
        # 获取四川省ID
        province_id = get_province_id()
        if not province_id:
            logger.error("无法获取四川省ID，退出")
            return
        
        logger.info(f"四川省ID: {province_id}")
        
        # 遍历所有缺失的地市
        for city_name, companies in SICHUAN_DATA.items():
            logger.info(f"处理地级市: {city_name}")
            
            # 检查地级市是否已存在
            city_id = check_city_exists(city_name)
            
            # 如果不存在，插入地级市
            if not city_id:
                city_id = insert_city(city_name, province_id)
                if not city_id:
                    logger.error(f"插入地级市失败: {city_name}")
                    continue
            else:
                logger.info(f"地级市 {city_name} 已存在 (ID: {city_id})")
            
            # 插入区县
            for company_name in companies:
                # 检查区县是否已存在
                if not check_company_exists(city_name, company_name):
                    insert_company(city_name, company_name, city_id)
                else:
                    logger.info(f"区县 {city_name}->{company_name} 已存在，跳过")
        
        logger.info("四川省地市区县数据补充完成！")
        
        # 打印最终统计
        print_statistics()
        
    except Exception as e:
        logger.error(f"插入过程失败: {e}")

def print_statistics():
    """打印统计信息"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # 统计四川省数据
        cursor.execute("""
        SELECT region_level, COUNT(*) as count
        FROM administrative_regions 
        WHERE province = '四川'
        GROUP BY region_level 
        ORDER BY FIELD(region_level, 'province', 'city', 'company')
        """)
        
        results = cursor.fetchall()
        
        print("\n=== 四川省数据统计 ===")
        for region_level, count in results:
            level_name = {'province': '省份', 'city': '地级市', 'company': '区县'}[region_level]
            print(f"{level_name}: {count}个")
        
        # 显示所有地级市
        cursor.execute("""
        SELECT city, COUNT(*) as company_count
        FROM administrative_regions 
        WHERE province = '四川' AND region_level = 'company'
        GROUP BY city
        ORDER BY city
        """)
        
        city_details = cursor.fetchall()
        
        print("\n=== 各地级市区县数量 ===")
        for city, count in city_details:
            print(f"{city}: {count}个区县")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        logger.error(f"统计信息获取失败: {e}")

def main():
    """主函数"""
    try:
        logger.info("开始补充四川省地市区县数据...")
        insert_missing_regions()
        logger.info("补充完成！")
        
    except Exception as e:
        logger.error(f"补充过程失败: {e}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
更新quick_query_info表中的display_order和requirement_type字段
"""
import pymysql
from app.config.config import Config

def update_display_order():
    """更新展示顺序和要求类型"""
    
    # 定义省份顺序和类型
    provinces_order = [
        # 明确要求 (1-4)
        ('山东', 1, '明确要求'),
        ('上海', 2, '明确要求'),
        ('江苏', 3, '明确要求'),
        ('安徽', 4, '明确要求'),
        
        # 有限条件 (5-13)
        ('天津', 5, '有限条件'),
        ('山西', 6, '有限条件'),
        ('河北', 7, '有限条件'),
        ('重庆', 8, '有限条件'),
        ('四川', 9, '有限条件'),
        ('辽宁', 10, '有限条件'),
        ('黑龙江', 11, '有限条件'),
        ('新疆', 12, '有限条件'),
        ('甘肃', 13, '有限条件'),
        
        # 无条件 (14-27)
        ('北京', 14, '无条件'),
        ('冀北', 15, '无条件'),
        ('浙江', 16, '无条件'),
        ('福建', 17, '无条件'),
        ('湖北', 18, '无条件'),
        ('湖南', 19, '无条件'),
        ('河南', 20, '无条件'),
        ('江西', 21, '无条件'),
        ('吉林', 22, '无条件'),
        ('蒙东', 23, '无条件'),
        ('陕西', 24, '无条件'),
        ('青海', 25, '无条件'),
        ('宁夏', 26, '无条件'),
        ('西藏', 27, '无条件'),
    ]
    
    config = Config()
    
    # 解析数据库连接字符串
    db_url = config.SQLALCHEMY_DATABASE_URI.replace('mysql+pymysql://', '')
    user_pass, host_db = db_url.split('@')
    user, password = user_pass.split(':')
    host_port, database = host_db.split('/')
    host, port = host_port.split(':')
    # 移除查询参数
    if '?' in database:
        database = database.split('?')[0]
    
    # 连接数据库
    connection = pymysql.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=database,
        charset='utf8mb4'
    )
    
    try:
        with connection.cursor() as cursor:
            # 更新每个省份的展示顺序和要求类型
            for province_name, order, req_type in provinces_order:
                # 首先查找对应的unit_id
                cursor.execute("""
                    SELECT unit_id 
                    FROM secondary_units 
                    WHERE unit_name = %s 
                    AND (unit_type = '省级电网公司' 
                         OR unit_name IN ('冀北', '蒙东', '冀北电网', '蒙东电网'))
                    AND is_active = 1
                    LIMIT 1
                """, (province_name,))
                
                result = cursor.fetchone()
                if result:
                    unit_id = result[0]
                    
                    # 更新quick_query_info表
                    cursor.execute("""
                        UPDATE quick_query_info 
                        SET display_order = %s, 
                            requirement_type = %s 
                        WHERE unit_id = %s
                    """, (order, req_type, unit_id))
                    
                    if cursor.rowcount > 0:
                        print(f"✓ Updated {province_name}: order={order}, type={req_type}")
                    else:
                        print(f"⚠ No record found for {province_name} (unit_id={unit_id})")
                else:
                    print(f"⚠ Province {province_name} not found in secondary_units")
            
            connection.commit()
            print("\n✓ All updates completed successfully!")
            
            # 验证更新结果
            print("\n验证更新结果：")
            cursor.execute("""
                SELECT su.unit_name, qqi.display_order, qqi.requirement_type
                FROM quick_query_info qqi
                JOIN secondary_units su ON qqi.unit_id = su.unit_id
                WHERE qqi.display_order IS NOT NULL
                ORDER BY qqi.display_order
            """)
            
            results = cursor.fetchall()
            for name, order, req_type in results:
                print(f"  {order:2d}. {name:10s} - {req_type}")
            
    except Exception as e:
        print(f"Error: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == '__main__':
    update_display_order()
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复属性错误的单位
"""
import pandas as pd
import pymysql
import re
from app.config.config import Config

def fix_attribute_errors():
    """修复属性错误"""
    config = Config()
    
    # 解析数据库连接信息
    db_url = config.SQLALCHEMY_DATABASE_URI
    pattern = r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)'
    match = re.match(pattern, db_url)
    
    if not match:
        print("无法解析数据库连接字符串")
        return
    
    db_user, db_password, db_host, db_port, db_name = match.groups()
    db_port = int(db_port)
    
    try:
        # 读取Excel文件获取正确的属性
        excel_df = pd.read_excel('/workspace/二级单位表.xlsx')
        excel_dict = {row['unit_name']: row['org_type'] for _, row in excel_df.iterrows()}
        
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            print("=" * 80)
            print("修复属性错误")
            print("=" * 80)
            
            # 需要修复的单位
            units_to_fix = [
                {'name': '冀北博望', 'expected_org_type': '省属产业'},
                {'name': '蒙东电网', 'expected_org_type': '国网省公司'},
                {'name': '冀北电网', 'expected_org_type': '国网省公司'}
            ]
            
            for unit in units_to_fix:
                unit_name = unit['name']
                expected_org_type = unit['expected_org_type']
                
                # 检查Excel文件中的实际值
                if unit_name in excel_dict:
                    correct_org_type = excel_dict[unit_name]
                    print(f"处理单位: {unit_name}")
                    print(f"  Excel中的org_type: {correct_org_type}")
                    
                    # 获取当前数据库中的值
                    cursor.execute("""
                        SELECT unit_id, unit_code, unit_name, unit_type, org_type
                        FROM secondary_units
                        WHERE unit_name = %s
                    """, (unit_name,))
                    
                    current_data = cursor.fetchone()
                    if current_data:
                        print(f"  数据库中的org_type: {current_data[4]}")
                        
                        if current_data[4] != correct_org_type:
                            # 更新org_type
                            cursor.execute("""
                                UPDATE secondary_units
                                SET org_type = %s, updated_at = NOW()
                                WHERE unit_name = %s
                            """, (correct_org_type, unit_name))
                            
                            # 同时更新unit_type
                            if correct_org_type == '省属产业':
                                new_unit_type = '产业单位'
                            elif correct_org_type in ['国网省公司', '南网省公司']:
                                new_unit_type = '省级电网公司'
                            elif correct_org_type in ['国网直属单位', '南网直属单位']:
                                if '电网' in unit_name:
                                    new_unit_type = '省级电网公司'
                                else:
                                    new_unit_type = '其他单位'
                            else:
                                new_unit_type = current_data[3]  # 保持原值
                            
                            cursor.execute("""
                                UPDATE secondary_units
                                SET unit_type = %s
                                WHERE unit_name = %s
                            """, (new_unit_type, unit_name))
                            
                            print(f"  ✓ 已更新: org_type = {correct_org_type}, unit_type = {new_unit_type}")
                        else:
                            print(f"  - 无需更新，属性已正确")
                    else:
                        print(f"  ✗ 在数据库中未找到单位: {unit_name}")
                else:
                    print(f"  ✗ 在Excel中未找到单位: {unit_name}")
            
            # 提交更改
            connection.commit()
            print("\n✓ 所有更改已提交")
            
            # 验证修复结果
            print("\n验证修复结果:")
            for unit in units_to_fix:
                unit_name = unit['name']
                cursor.execute("""
                    SELECT unit_name, unit_type, org_type
                    FROM secondary_units
                    WHERE unit_name = %s
                """, (unit_name,))
                
                result = cursor.fetchone()
                if result:
                    expected_org_type = excel_dict.get(unit_name, '未知')
                    actual_org_type = result[2]
                    status = '✓' if actual_org_type == expected_org_type else '✗'
                    print(f"  {status} {unit_name}: {actual_org_type} (期望: {expected_org_type})")
        
        connection.close()
        
    except Exception as e:
        print(f"修复过程中出现错误: {e}")
        try:
            connection.rollback()
            print("已回滚更改")
        except:
            pass

if __name__ == '__main__':
    fix_attribute_errors()
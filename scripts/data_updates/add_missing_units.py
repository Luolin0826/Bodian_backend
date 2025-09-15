#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
新增缺少的二级单位到数据库
"""
import pandas as pd
import pymysql
import re
from app.config.config import Config
from datetime import datetime

def get_missing_units_from_excel():
    """从Excel文件获取缺少的单位信息"""
    try:
        # 读取Excel文件
        df = pd.read_excel('/workspace/二级单位表.xlsx')
        
        # 获取数据库现有单位
        db_units = get_database_units()
        if db_units is None:
            return None
            
        db_unit_names = {unit['unit_name'] for unit in db_units}
        
        # 找出缺少的单位
        missing_mask = ~df['unit_name'].isin(db_unit_names)
        missing_df = df[missing_mask]
        
        print(f"找到 {len(missing_df)} 个缺少的单位")
        
        return missing_df.to_dict('records')
        
    except Exception as e:
        print(f"获取缺少单位失败: {e}")
        return None

def get_database_units():
    """获取数据库中现有的二级单位"""
    config = Config()
    
    # 解析数据库连接信息
    db_url = config.SQLALCHEMY_DATABASE_URI
    pattern = r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)'
    match = re.match(pattern, db_url)
    
    if not match:
        return None
    
    db_user, db_password, db_host, db_port, db_name = match.groups()
    db_port = int(db_port)
    
    try:
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            charset='utf8mb4'
        )
        
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT unit_id, unit_code, unit_name, unit_type, org_type
                FROM secondary_units
                ORDER BY unit_id
            """)
            return cursor.fetchall()
        
        connection.close()
        
    except Exception as e:
        print(f"获取数据库单位失败: {e}")
        return None

def generate_unit_code(unit_name, existing_codes):
    """生成单位代码"""
    # 获取下一个可用的编号
    max_num = 0
    for code in existing_codes:
        if code and code.startswith('UNIT'):
            try:
                num = int(code[4:])
                max_num = max(max_num, num)
            except:
                pass
    
    next_num = max_num + 1
    return f"UNIT{next_num:04d}"

def determine_unit_type(unit_name, org_type):
    """根据单位名称和组织类型确定单位类型"""
    if org_type in ['国网省公司', '南网省公司']:
        return '省级电网公司'
    elif org_type in ['国网直属单位', '南网直属单位']:
        if '电网' in unit_name:
            return '省级电网公司'
        else:
            return '其他单位'
    elif org_type == '省属产业':
        return '产业单位'
    else:
        return '其他单位'

def add_missing_units():
    """新增缺少的二级单位"""
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
        # 获取缺少的单位
        missing_units = get_missing_units_from_excel()
        if not missing_units:
            print("没有需要添加的单位")
            return
            
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
            print("开始新增缺少的二级单位")
            print("=" * 80)
            
            # 获取现有的unit_code
            cursor.execute("SELECT unit_code FROM secondary_units WHERE unit_code IS NOT NULL")
            existing_codes = [row[0] for row in cursor.fetchall()]
            
            added_count = 0
            
            for unit_data in missing_units:
                unit_name = unit_data['unit_name']
                org_type = unit_data['org_type']
                
                # 生成单位代码
                unit_code = generate_unit_code(unit_name, existing_codes)
                existing_codes.append(unit_code)
                
                # 确定单位类型
                unit_type = determine_unit_type(unit_name, org_type)
                
                # 插入新记录
                insert_sql = """
                    INSERT INTO secondary_units 
                    (unit_code, unit_name, unit_type, org_type, is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                
                now = datetime.now()
                cursor.execute(insert_sql, (
                    unit_code,
                    unit_name,
                    unit_type,
                    org_type,
                    True,
                    now,
                    now
                ))
                
                print(f"✓ 添加单位: {unit_code} | {unit_name} | {unit_type} | {org_type}")
                added_count += 1
            
            # 提交更改
            connection.commit()
            print(f"\n✓ 成功添加 {added_count} 个二级单位")
            
            # 验证结果
            cursor.execute("SELECT COUNT(*) FROM secondary_units")
            total_count = cursor.fetchone()[0]
            print(f"数据库中现有总单位数: {total_count}")
            
            cursor.execute("SELECT COUNT(*) FROM secondary_units WHERE is_active = 1")
            active_count = cursor.fetchone()[0]
            print(f"活跃单位数: {active_count}")
        
        connection.close()
        print("\n新增操作完成！")
        
    except Exception as e:
        print(f"新增过程中出现错误: {e}")
        try:
            connection.rollback()
            print("已回滚更改")
        except:
            pass

def verify_additions():
    """验证新增的单位"""
    config = Config()
    
    # 解析数据库连接信息
    db_url = config.SQLALCHEMY_DATABASE_URI
    pattern = r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)'
    match = re.match(pattern, db_url)
    
    if not match:
        return
    
    db_user, db_password, db_host, db_port, db_name = match.groups()
    db_port = int(db_port)
    
    try:
        # 读取Excel文件
        excel_df = pd.read_excel('/workspace/二级单位表.xlsx')
        excel_units = set(excel_df['unit_name'])
        
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            charset='utf8mb4'
        )
        
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT unit_name, unit_code, unit_type, org_type FROM secondary_units")
            db_units = cursor.fetchall()
            db_unit_names = {unit['unit_name'] for unit in db_units}
            
            print("=" * 80)
            print("验证新增结果")
            print("=" * 80)
            
            print(f"Excel中单位数量: {len(excel_units)}")
            print(f"数据库中单位数量: {len(db_unit_names)}")
            
            # 检查是否还有缺少的单位
            still_missing = excel_units - db_unit_names
            if still_missing:
                print(f"\n仍然缺少的单位 ({len(still_missing)}):")
                for unit in sorted(still_missing):
                    print(f"  - {unit}")
            else:
                print("\n✓ 所有Excel中的单位都已存在于数据库中")
            
            # 显示新添加的单位（最近的25个）
            cursor.execute("""
                SELECT unit_code, unit_name, unit_type, org_type, created_at
                FROM secondary_units
                ORDER BY created_at DESC, unit_id DESC
                LIMIT 30
            """)
            recent_units = cursor.fetchall()
            
            print(f"\n最近添加的单位:")
            for unit in recent_units:
                print(f"  {unit['unit_code']} | {unit['unit_name']} | {unit['unit_type']} | {unit['org_type']}")
        
        connection.close()
        
    except Exception as e:
        print(f"验证过程中出现错误: {e}")

if __name__ == '__main__':
    print("开始新增缺少的二级单位...")
    add_missing_units()
    
    print("\n" + "=" * 80)
    verify_additions()
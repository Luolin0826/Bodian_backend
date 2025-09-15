#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证secondary_units表清理结果
"""
import pymysql
import re
from app.config.config import Config

def verify_cleanup_results():
    """验证清理结果"""
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
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            charset='utf8mb4'
        )
        
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            print("=" * 80)
            print("Secondary Units 表清理结果验证")
            print("=" * 80)
            
            # 1. 检查基本统计
            print("\n1. 基本统计:")
            cursor.execute("SELECT COUNT(*) as total FROM secondary_units")
            total = cursor.fetchone()['total']
            print(f"总记录数: {total}")
            
            cursor.execute("SELECT COUNT(*) as active FROM secondary_units WHERE is_active = 1")
            active = cursor.fetchone()['active']
            print(f"活跃记录数: {active}")
            
            # 2. 检查表结构
            print("\n2. 表结构:")
            cursor.execute("DESCRIBE secondary_units")
            columns = cursor.fetchall()
            print(f"总列数: {len(columns)}")
            print("保留的列:")
            for col in columns:
                print(f"  {col['Field']}: {col['Type']}")
            
            # 3. 检查重复数据
            print("\n3. 重复数据检查:")
            cursor.execute("""
                SELECT unit_name, COUNT(*) as count
                FROM secondary_units
                GROUP BY unit_name
                HAVING COUNT(*) > 1
            """)
            duplicates = cursor.fetchall()
            if duplicates:
                print(f"发现 {len(duplicates)} 个重复的unit_name:")
                for dup in duplicates:
                    print(f"  {dup['unit_name']}: {dup['count']} 条记录")
            else:
                print("✓ 无重复数据")
            
            # 4. 检查特定记录
            print("\n4. 特定记录检查:")
            
            # 检查UNIT0065是否已删除
            cursor.execute("SELECT COUNT(*) as count FROM secondary_units WHERE unit_code = 'UNIT0065'")
            unit0065_count = cursor.fetchone()['count']
            if unit0065_count == 0:
                print("✓ UNIT0065已删除")
            else:
                print(f"✗ UNIT0065仍存在 ({unit0065_count} 条)")
            
            # 检查冀北电网和蒙东电网
            cursor.execute("""
                SELECT unit_id, unit_code, unit_name, is_active
                FROM secondary_units
                WHERE unit_name IN ('冀北电网', '蒙东电网')
                ORDER BY unit_name, unit_id
            """)
            special_units = cursor.fetchall()
            print("冀北电网和蒙东电网记录:")
            for unit in special_units:
                print(f"  ID:{unit['unit_id']} | {unit['unit_code']} | {unit['unit_name']} | Active:{unit['is_active']}")
            
            # 5. 检查已删除的列是否确实不存在
            print("\n5. 已删除列检查:")
            deleted_columns = [
                'economic_level', 'is_key_city', 'version', 'custom_data',
                'salary_range', 'estimated_score_range', 'apply_status'
            ]
            
            existing_column_names = [col['Field'] for col in columns]
            for col_name in deleted_columns:
                if col_name in existing_column_names:
                    print(f"✗ 列 {col_name} 仍然存在")
                else:
                    print(f"✓ 列 {col_name} 已删除")
            
            # 6. 检查省级电网公司数据完整性
            print("\n6. 省级电网公司数据完整性:")
            cursor.execute("""
                SELECT unit_name, unit_type, org_type, is_active
                FROM secondary_units
                WHERE (unit_type = '省级电网公司' OR unit_name IN ('冀北', '蒙东', '冀北电网', '蒙东电网'))
                AND is_active = 1
                ORDER BY unit_name
            """)
            provinces = cursor.fetchall()
            print(f"活跃的省级电网公司: {len(provinces)} 个")
            for province in provinces:
                print(f"  {province['unit_name']} | {province['unit_type']} | {province['org_type']}")
            
            print(f"\n✓ 清理验证完成！")
            print("总结:")
            print(f"  - 总记录数: {total}")
            print(f"  - 活跃记录数: {active}")
            print(f"  - 重复数据: {'无' if not duplicates else len(duplicates)}")
            print(f"  - UNIT0065: {'已删除' if unit0065_count == 0 else '仍存在'}")
            print(f"  - 列数: {len(columns)} (删除了7列)")
        
        connection.close()
        
    except Exception as e:
        print(f"验证过程中出现错误: {e}")

if __name__ == '__main__':
    verify_cleanup_results()
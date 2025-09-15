#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终验证二级单位数据的完整性和正确性
"""
import pandas as pd
import pymysql
import re
from app.config.config import Config

def final_verification():
    """最终验证"""
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
        # 读取Excel文件
        excel_df = pd.read_excel('/workspace/二级单位表.xlsx')
        
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
            print("最终验证报告")
            print("=" * 80)
            
            # 1. 数量对比
            cursor.execute("SELECT COUNT(*) as count FROM secondary_units")
            db_count = cursor.fetchone()['count']
            excel_count = len(excel_df)
            
            print(f"1. 数量对比:")
            print(f"   Excel文件: {excel_count} 个单位")
            print(f"   数据库: {db_count} 个单位")
            print(f"   状态: {'✓' if db_count >= excel_count else '✗'}")
            
            # 2. 完整性检查
            print(f"\n2. 数据完整性检查:")
            excel_units = set(excel_df['unit_name'])
            
            cursor.execute("SELECT unit_name FROM secondary_units")
            db_units = set(row['unit_name'] for row in cursor.fetchall())
            
            missing_in_db = excel_units - db_units
            if missing_in_db:
                print(f"   ✗ 数据库中缺少 {len(missing_in_db)} 个单位:")
                for unit in sorted(missing_in_db):
                    print(f"      - {unit}")
            else:
                print(f"   ✓ 所有Excel单位都在数据库中")
            
            extra_in_db = db_units - excel_units
            if extra_in_db:
                print(f"   数据库中有额外的 {len(extra_in_db)} 个单位 (这是正常的)")
            
            # 3. org_type匹配检查
            print(f"\n3. org_type匹配检查:")
            
            # 获取Excel中的org_type分布
            excel_org_types = excel_df['org_type'].value_counts()
            print("   Excel中的org_type分布:")
            for org_type, count in excel_org_types.items():
                print(f"      {org_type}: {count}个")
            
            # 获取数据库中的org_type分布
            cursor.execute("""
                SELECT org_type, COUNT(*) as count 
                FROM secondary_units 
                WHERE org_type IS NOT NULL 
                GROUP BY org_type 
                ORDER BY count DESC
            """)
            db_org_types = cursor.fetchall()
            print("   数据库中的org_type分布:")
            for row in db_org_types:
                print(f"      {row['org_type']}: {row['count']}个")
            
            # 4. 属性正确性验证
            print(f"\n4. 属性正确性验证:")
            
            # 检查每个Excel单位的属性是否正确
            verification_errors = []
            
            for _, excel_row in excel_df.iterrows():
                unit_name = excel_row['unit_name']
                expected_org_type = excel_row['org_type']
                
                cursor.execute("""
                    SELECT unit_code, unit_name, unit_type, org_type
                    FROM secondary_units
                    WHERE unit_name = %s
                """, (unit_name,))
                
                db_row = cursor.fetchone()
                if db_row:
                    if db_row['org_type'] != expected_org_type:
                        verification_errors.append({
                            'unit_name': unit_name,
                            'expected_org_type': expected_org_type,
                            'actual_org_type': db_row['org_type']
                        })
            
            if verification_errors:
                print(f"   ✗ 发现 {len(verification_errors)} 个属性错误:")
                for error in verification_errors:
                    print(f"      {error['unit_name']}: 期望{error['expected_org_type']}, 实际{error['actual_org_type']}")
            else:
                print(f"   ✓ 所有单位的org_type属性都正确")
            
            # 5. 单位类型分布
            print(f"\n5. 单位类型分布:")
            cursor.execute("""
                SELECT unit_type, COUNT(*) as count
                FROM secondary_units
                WHERE unit_type IS NOT NULL
                GROUP BY unit_type
                ORDER BY count DESC
            """)
            unit_types = cursor.fetchall()
            for row in unit_types:
                print(f"   {row['unit_type']}: {row['count']}个")
            
            # 6. 活跃状态检查
            print(f"\n6. 活跃状态检查:")
            cursor.execute("SELECT COUNT(*) as count FROM secondary_units WHERE is_active = 1")
            active_count = cursor.fetchone()['count']
            cursor.execute("SELECT COUNT(*) as count FROM secondary_units WHERE is_active = 0")
            inactive_count = cursor.fetchone()['count']
            
            print(f"   活跃单位: {active_count}个")
            print(f"   不活跃单位: {inactive_count}个")
            
            # 7. 代码唯一性检查
            print(f"\n7. 代码唯一性检查:")
            cursor.execute("""
                SELECT unit_code, COUNT(*) as count
                FROM secondary_units
                WHERE unit_code IS NOT NULL
                GROUP BY unit_code
                HAVING COUNT(*) > 1
            """)
            duplicate_codes = cursor.fetchall()
            
            if duplicate_codes:
                print(f"   ✗ 发现重复的单位代码:")
                for row in duplicate_codes:
                    print(f"      {row['unit_code']}: {row['count']}次")
            else:
                print(f"   ✓ 所有单位代码都是唯一的")
            
            # 8. 总结
            print(f"\n8. 总结:")
            issues = []
            if db_count < excel_count:
                issues.append("数据库单位数量不足")
            if missing_in_db:
                issues.append(f"缺少{len(missing_in_db)}个单位")
            if verification_errors:
                issues.append(f"{len(verification_errors)}个属性错误")
            if duplicate_codes:
                issues.append("存在重复的单位代码")
            
            if not issues:
                print("   ✅ 所有检查都通过，数据完整且正确！")
            else:
                print("   ⚠️ 发现以下问题:")
                for issue in issues:
                    print(f"      - {issue}")
        
        connection.close()
        
    except Exception as e:
        print(f"验证过程中出现错误: {e}")

if __name__ == '__main__':
    final_verification()
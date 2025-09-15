#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充缺失的7个院校的详细信息
"""
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

def get_current_universities():
    """查询当前新增的7个院校信息"""
    connection = connect_to_database()
    if not connection:
        return
    
    try:
        cursor = connection.cursor()
        
        print("="*80)
        print("查询新增的7个院校当前信息")
        print("="*80)
        
        cursor.execute("""
            SELECT university_id, university_code, original_name, standard_name, 
                   level, type, power_feature, location
            FROM universities 
            WHERE university_code LIKE 'B2U%'
            ORDER BY university_id
        """)
        
        universities = cursor.fetchall()
        
        print(f"找到 {len(universities)} 个新增院校:")
        print("-" * 120)
        print(f"{'ID':<4} {'代码':<8} {'原始名称':<25} {'标准名称':<25} {'等级':<10} {'类型':<10} {'电力特色':<15} {'地区':<10}")
        print("-" * 120)
        
        for uni in universities:
            print(f"{uni[0]:<4} {uni[1]:<8} {uni[2] or '未设置':<25} {uni[3] or '未设置':<25} {uni[4] or '未设置':<10} {uni[5] or '未设置':<10} {uni[6] or '未设置':<15} {uni[7] or '未设置':<10}")
        
        return universities
        
    except Error as e:
        print(f"查询失败: {e}")
    finally:
        cursor.close()
        connection.close()

def update_universities_info():
    """更新院校的详细信息"""
    
    # 定义7个院校的详细信息
    universities_info = {
        '华北电力大学(北京)': {
            'level': '211工程',
            'type': '理工类',
            'power_feature': '电力特色高校',
            'location': '北京市'
        },
        '华北电力大学(保定)': {
            'level': '211工程',
            'type': '理工类', 
            'power_feature': '电力特色高校',
            'location': '河北省'
        },
        '中国矿业大学(北京)': {
            'level': '211工程',
            'type': '理工类',
            'power_feature': '普通高校',
            'location': '北京市'
        },
        '中国石油大学(北京)': {
            'level': '211工程',
            'type': '理工类',
            'power_feature': '普通高校',
            'location': '北京市'
        },
        '哈尔滨工业大学(威海)': {
            'level': '985工程',
            'type': '理工类',
            'power_feature': '普通高校',
            'location': '山东省'
        },
        '中国矿业大学(徐州)': {
            'level': '211工程',
            'type': '理工类',
            'power_feature': '普通高校',
            'location': '江苏省'
        },
        '中国石油大学(华东)': {
            'level': '211工程',
            'type': '理工类',
            'power_feature': '普通高校',
            'location': '山东省'
        }
    }
    
    connection = connect_to_database()
    if not connection:
        return
    
    try:
        cursor = connection.cursor()
        
        print("\n" + "="*80)
        print("更新院校详细信息")
        print("="*80)
        
        # 获取需要更新的院校
        cursor.execute("""
            SELECT university_id, standard_name
            FROM universities 
            WHERE university_code LIKE 'B2U%'
            ORDER BY university_id
        """)
        
        universities = cursor.fetchall()
        updated_count = 0
        
        for uni_id, standard_name in universities:
            if standard_name in universities_info:
                info = universities_info[standard_name]
                
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
                    print(f"✅ 更新成功: {standard_name}")
                    print(f"   等级: {info['level']}")
                    print(f"   类型: {info['type']}")
                    print(f"   电力特色: {info['power_feature']}")
                    print(f"   地区: {info['location']}")
                    print()
                    
                except Error as e:
                    print(f"❌ 更新失败 {standard_name}: {e}")
            else:
                print(f"⚠️  未找到院校信息: {standard_name}")
        
        # 提交更改
        connection.commit()
        
        print("-" * 80)
        print(f"更新完成！成功更新 {updated_count} 个院校的信息")
        print("=" * 80)
        
    except Error as e:
        print(f"更新过程中出现错误: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

def verify_updates():
    """验证更新结果"""
    connection = connect_to_database()
    if not connection:
        return
    
    try:
        cursor = connection.cursor()
        
        print("\n" + "="*80)
        print("验证更新结果")
        print("="*80)
        
        cursor.execute("""
            SELECT university_id, university_code, standard_name, 
                   level, type, power_feature, location
            FROM universities 
            WHERE university_code LIKE 'B2U%'
            ORDER BY university_id
        """)
        
        universities = cursor.fetchall()
        
        print(f"验证 {len(universities)} 个院校的更新结果:")
        print("-" * 120)
        print(f"{'ID':<4} {'代码':<8} {'院校名称':<25} {'等级':<12} {'类型':<10} {'电力特色':<15} {'地区':<10}")
        print("-" * 120)
        
        complete_count = 0
        for uni in universities:
            uni_id, code, name, level, uni_type, power_feature, location = uni
            
            # 检查是否所有字段都已填写
            is_complete = all([level, uni_type, power_feature, location])
            status = "✅" if is_complete else "❌"
            
            if is_complete:
                complete_count += 1
            
            print(f"{uni_id:<4} {code:<8} {name:<25} {level or '未设置':<12} {uni_type or '未设置':<10} {power_feature or '未设置':<15} {location or '未设置':<10} {status}")
        
        print("-" * 120)
        print(f"完整度统计: {complete_count}/{len(universities)} 个院校信息完整")
        
        if complete_count == len(universities):
            print("🎉 所有院校信息更新完成！")
        else:
            print("⚠️  仍有院校信息需要补充")
        
    except Error as e:
        print(f"验证过程中出现错误: {e}")
    finally:
        cursor.close()
        connection.close()

def main():
    """主函数"""
    # 1. 查询当前信息
    print("1. 查询当前院校信息...")
    get_current_universities()
    
    # 2. 更新院校信息
    print("\n2. 更新院校详细信息...")
    update_universities_info()
    
    # 3. 验证更新结果
    print("\n3. 验证更新结果...")
    verify_updates()

if __name__ == "__main__":
    main()
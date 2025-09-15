#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找985和211学校在倒序排列中的具体位置
"""

import requests
import json

def find_all_high_level_schools():
    """查找所有重点学校在倒序排列中的位置"""
    
    base_url = "http://localhost:5000/api/v1/analytics/schools-by-batch"
    
    print("查找985和211学校在倒序排列中的具体位置")
    print("=" * 60)
    
    high_level_schools = []
    page = 1
    
    while True:
        params = {'page': page, 'limit': 100, 'sort_by': 'school_level_desc'}
        
        try:
            response = requests.get(base_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                schools = data['data']['schools']
                
                if not schools:  # 没有更多数据
                    break
                
                # 查找重点学校
                page_high_level = [s for s in schools if s.get('university_type') in ['985工程', '211工程', '双一流']]
                
                if page_high_level:
                    print(f"第{page}页找到{len(page_high_level)}所重点学校:")
                    for i, school in enumerate(page_high_level):
                        position = (page-1) * 100 + schools.index(school) + 1
                        admission_count = school.get('admission_count', 0)
                        level = school.get('university_type')
                        name = school.get('university_name')
                        
                        print(f"  第{position}名: {name} - {level} - {admission_count}人")
                        
                        if admission_count == 0:
                            print(f"    🚨 录取人数为0!")
                        
                        high_level_schools.append({
                            'position': position,
                            'name': name,
                            'level': level,
                            'admission_count': admission_count
                        })
                
                # 如果找到了足够的重点学校样本，就停止
                if len(high_level_schools) >= 20:
                    break
                
                page += 1
                
                if page > 20:  # 防止无限循环
                    break
            else:
                print(f"第{page}页请求失败: {response.status_code}")
                break
        
        except Exception as e:
            print(f"第{page}页测试异常: {e}")
            break
    
    print(f"\n总结:")
    print(f"找到{len(high_level_schools)}所重点学校")
    
    if high_level_schools:
        zero_schools = [s for s in high_level_schools if s['admission_count'] == 0]
        if zero_schools:
            print(f"其中{len(zero_schools)}所学校录取人数为0:")
            for school in zero_schools:
                print(f"  - 第{school['position']}名: {school['name']} ({school['level']})")
        else:
            print("所有重点学校录取人数都正常")

def check_specific_schools():
    """检查特定的知名学校"""
    
    print(f"\n" + "=" * 60)
    print("检查特定知名学校的录取情况")
    print("=" * 60)
    
    base_url = "http://localhost:5000/api/v1/analytics/check-school-admission"
    
    # 测试一些知名的985、211学校
    test_schools = [
        "清华大学", "北京大学", "华北电力大学", "东南大学", 
        "上海交通大学", "西安交通大学", "哈尔滨工业大学"
    ]
    
    for school_name in test_schools:
        params = {'school_name': school_name}
        
        try:
            response = requests.get(base_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if data['success'] and data['data']['found']:
                    schools = data['data']['schools']
                    total_admissions = data['data']['total_batch_admissions']
                    
                    print(f"{school_name}:")
                    print(f"  总体录取数: {total_admissions}")
                    
                    for school in schools:
                        admission_count = school.get('admission_count', 0)
                        level = school.get('school_level', '未知')
                        batch = school.get('batch', '未知')
                        
                        print(f"  - {school.get('university_name')}: {admission_count}人 ({level}) [{batch}]")
                else:
                    print(f"{school_name}: 未找到录取记录")
            else:
                print(f"{school_name}: 查询失败 ({response.status_code})")
        
        except Exception as e:
            print(f"{school_name}: 查询异常 - {e}")

if __name__ == '__main__':
    find_all_high_level_schools()
    check_specific_schools()
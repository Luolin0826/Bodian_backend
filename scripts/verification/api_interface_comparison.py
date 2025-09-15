#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析两个学校查询API接口的区别
"""
import requests
import json

def compare_school_apis():
    """对比两个学校查询API接口"""
    print("="*100)
    print("学校查询API接口对比分析")
    print("="*100)
    
    # API基础URL（注意：用户使用8088端口，但服务器在5000端口）
    base_url = "http://localhost:5000/api/v1/analytics"
    
    print("1. 接口用途分析:")
    print("-" * 60)
    
    # 接口1: schools-by-batch
    print("📊 接口1: /schools-by-batch")
    print("   用途: 获取指定条件下的学校录取统计列表")
    print("   特点: 支持分页、排序、筛选，主要用于展示学校列表")
    print("   参数:")
    print("   - unit_id: 二级单位ID（可选）")
    print("   - batch_code: 批次代码（可选）")
    print("   - quick_filter: 快速筛选（guowang/nanwang）")
    print("   - sort_by: 排序字段")
    print("   - page, limit: 分页参数")
    
    print("\n🔍 接口2: /check-school-admission")
    print("   用途: 根据学校名称查找特定学校的录取记录")
    print("   特点: 支持模糊匹配学校名称，主要用于搜索特定学校")
    print("   参数:")
    print("   - school_name: 学校名称（必需）")
    print("   - unit_id: 二级单位ID（可选）")
    print("   - batch_code: 批次代码（可选）")
    print("   - quick_filter: 快速筛选（可选）")
    
    # 测试两个接口的实际效果
    print(f"\n2. 实际测试对比:")
    print("-" * 60)
    
    # 测试接口1
    print("\n📊 测试接口1: /schools-by-batch")
    try:
        params1 = {
            "unit_id": 5,
            "sort_by": "admission_count",
            "page": 1,
            "limit": 5
        }
        response1 = requests.get(f"{base_url}/schools-by-batch", params=params1, timeout=10)
        
        if response1.status_code == 200:
            data1 = response1.json()
            if data1.get('success'):
                schools1 = data1.get('data', {}).get('schools', [])
                print(f"✅ 返回 {len(schools1)} 所学校")
                print("返回格式示例:")
                if schools1:
                    school = schools1[0]
                    print(f"   university_name: {school.get('university_name')}")
                    print(f"   admission_count: {school.get('admission_count')}")
                    print(f"   batch: {school.get('batch')}")
                    print(f"   org_type: {school.get('org_type')}")
            else:
                print(f"❌ 接口1失败: {data1.get('error')}")
        else:
            print(f"❌ 接口1 HTTP错误: {response1.status_code}")
    except Exception as e:
        print(f"❌ 接口1测试异常: {e}")
    
    # 测试接口2
    print("\n🔍 测试接口2: /check-school-admission")
    try:
        params2 = {
            "school_name": "理工",
            "unit_id": 5,
            "batch_code": "2025GW01"
        }
        response2 = requests.get(f"{base_url}/check-school-admission", params=params2, timeout=10)
        
        if response2.status_code == 200:
            data2 = response2.json()
            if data2.get('success'):
                result2 = data2.get('data', {})
                schools2 = result2.get('schools', [])
                print(f"✅ 找到 {len(schools2)} 所匹配的学校")
                print("返回格式示例:")
                if schools2:
                    school = schools2[0]
                    print(f"   university_name: {school.get('university_name')}")
                    print(f"   admission_count: {school.get('admission_count')}")
                    print(f"   batch: {school.get('batch')}")
                    print(f"   admission_ratio: {school.get('admission_ratio')}%")
                print(f"   search_term: {result2.get('search_term')}")
                print(f"   total_batch_admissions: {result2.get('total_batch_admissions')}")
            else:
                print(f"❌ 接口2失败: {data2.get('error')}")
        else:
            print(f"❌ 接口2 HTTP错误: {response2.status_code}")
    except Exception as e:
        print(f"❌ 接口2测试异常: {e}")
    
    # 分析差异
    print(f"\n3. 接口差异总结:")
    print("-" * 60)
    
    print("📊 /schools-by-batch (学校统计列表接口)")
    print("✓ 适用场景: 展示某个单位/批次的所有学校录取统计")
    print("✓ 支持功能: 分页、多种排序、筛选")
    print("✓ 返回格式: 标准分页列表，包含统计汇总")
    print("✓ 主要用于: 数据展示、报表生成")
    
    print("\n🔍 /check-school-admission (学校搜索接口)")
    print("✓ 适用场景: 按学校名称搜索特定学校")
    print("✓ 支持功能: 模糊匹配、录取占比计算")
    print("✓ 返回格式: 搜索结果列表，包含搜索元信息")
    print("✓ 主要用于: 学校查找、录取情况查询")
    
    # 建议
    print(f"\n4. 使用建议:")
    print("-" * 60)
    
    print("📊 使用 /schools-by-batch 当你需要:")
    print("   • 查看某个单位的所有录取学校")
    print("   • 按录取数量、学校层次等排序")
    print("   • 分页浏览学校列表")
    print("   • 获取统计汇总信息")
    
    print("\n🔍 使用 /check-school-admission 当你需要:")
    print("   • 搜索特定名称的学校（如'理工'）")
    print("   • 查看某个学校的录取占比")
    print("   • 验证某个学校是否在特定批次中有录取")
    print("   • 跨批次搜索学校")
    
    print(f"\n5. 端口提醒:")
    print("-" * 60)
    print("⚠️  注意: 您的请求使用端口8088，但服务器运行在端口5000")
    print("   请将API请求从:")
    print("   http://localhost:8088/api/v1/analytics/...")
    print("   修改为:")
    print("   http://localhost:5000/api/v1/analytics/...")
    
    print("\n" + "="*100)

if __name__ == "__main__":
    compare_school_apis()
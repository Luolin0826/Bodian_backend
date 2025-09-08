#!/usr/bin/env python3
"""
测试API数据格式，诊断前端期望与实际返回的数据差异
"""
import sys
sys.path.append('/workspace')
import json

from app.routes.policy_sections import policy_sections_api

def test_data_formats():
    """测试各种API的数据格式"""
    print("🔍 测试API数据格式差异...\n")
    
    test_unit_id = 44
    
    print("="*60)
    print("1. 基本政策接口数据格式测试")
    print("="*60)
    
    try:
        basic_result = policy_sections_api.get_basic_policy(test_unit_id)
        print("✅ 基本政策API调用成功")
        print(f"📊 返回字段: {list(basic_result.keys())}")
        
        if 'section_data' in basic_result:
            print(f"📄 section_data字段数: {len(basic_result['section_data'])}")
            print("📝 section_data结构示例:")
            for i, (key, value) in enumerate(list(basic_result['section_data'].items())[:3]):
                print(f"   {key}: {json.dumps(value, ensure_ascii=False, indent=2)[:100]}...")
        else:
            print("❌ 缺失 section_data 字段")
            
        # 模拟路由转换后的数据
        print("\n🔄 模拟路由转换后的数据格式:")
        print(json.dumps({
            'success': True,
            'data': basic_result
        }, ensure_ascii=False, indent=2)[:200] + "...")
        
    except Exception as e:
        print(f"❌ 基本政策API异常: {e}")
    
    print("\n" + "="*60)
    print("2. 提前批接口数据格式测试")
    print("="*60)
    
    try:
        early_result = policy_sections_api.get_early_batch_policy(test_unit_id)
        print("✅ 提前批API调用成功")
        print(f"📊 返回字段: {list(early_result.keys())}")
        
        # 模拟路由的数据转换逻辑
        section_data = early_result.get('section_data', {})
        early_batch_info = {}
        display_fields = []
        
        for field_key, field_data in section_data.items():
            early_batch_info[field_key] = {
                'display_name': field_data.get('display_name', ''),
                'type': field_data.get('type', 'text'),
                'value': field_data.get('value', '')
            }
            display_fields.append({
                'field_name': field_key,
                'display_name': field_data.get('display_name', ''),
                'field_type': field_data.get('type', 'text'),
                'display_order': field_data.get('priority', 99)
            })
        
        response_data = {
            'early_batch_info': early_batch_info,
            'display_fields': display_fields,
            'has_data': bool(section_data)
        }
        
        print(f"🔄 转换后的数据结构:")
        print(f"   early_batch_info: {len(early_batch_info)}个字段")
        print(f"   display_fields: {len(display_fields)}个字段")
        print(f"   has_data: {response_data['has_data']}")
        
        if early_batch_info:
            print("📝 early_batch_info示例字段:")
            for key, value in list(early_batch_info.items())[:2]:
                print(f"   {key}: {json.dumps(value, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"❌ 提前批API异常: {e}")
    
    print("\n" + "="*60) 
    print("3. 新添加接口测试")
    print("="*60)
    
    try:
        unit_details_result = policy_sections_api.get_unit_details(test_unit_id)
        print("✅ 单位详情API调用成功")
        print(f"📊 返回字段: {list(unit_details_result.keys())}")
        
        if 'policy_info' in unit_details_result:
            print(f"📄 policy_info字段数: {len(unit_details_result['policy_info'])}")
        
        regional_result = policy_sections_api.get_regional_overview(test_unit_id)
        print("✅ 区域概览API调用成功")
        print(f"📊 返回字段: {list(regional_result.keys())}")
        
    except Exception as e:
        print(f"❌ 新接口异常: {e}")

def analyze_frontend_expectation():
    """分析前端期望的数据格式"""
    print("\n" + "="*60)
    print("📋 前端期望数据格式分析")
    print("="*60)
    
    print("根据控制台日志分析:")
    print("1. UnitPolicyDisplay.vue:758 报错 '基本政策API响应中没有预期的数据字段'")
    print("2. EarlyBatchInfo.vue:563 报错 'API响应中没有预期的数据字段'")
    print("3. 前端期望的结构: {data: {...}, success: true}")
    print("4. 但前端检测逻辑似乎无法找到预期字段")
    
    print("\n可能的原因:")
    print("- 前端期望特定的字段名称或结构")
    print("- 数据嵌套层级不正确")
    print("- 空数据的处理方式不对")
    print("- 字段类型或格式不匹配")

if __name__ == '__main__':
    print("🚀 开始API数据格式诊断...\n")
    
    test_data_formats()
    analyze_frontend_expectation()
    
    print("\n" + "="*60)
    print("🎯 建议修复方案:")
    print("1. 检查前端代码，确认期望的具体字段名称")
    print("2. 对比旧版API的实际返回格式")
    print("3. 修复数据转换逻辑，确保完全兼容")
    print("4. 处理空数据情况，避免返回null")
    print("="*60)
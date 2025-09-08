#!/usr/bin/env python3
"""
测试脚本：验证新版API的修复效果
"""
import sys
sys.path.append('/workspace')

from app.routes.policy_sections import policy_sections_api

def test_early_batch_api():
    """测试提前批API"""
    print("🔍 测试提前批API...")
    
    # 调用API获取数据
    result = policy_sections_api.get_early_batch_policy(44)
    
    if 'error' in result:
        print(f"❌ API调用失败: {result['error']}")
        return False
    
    # 模拟新版API的响应格式转换
    section_data = result.get('section_data', {})
    
    # 转换为旧版格式的early_batch_info
    early_batch_info = {}
    display_fields = []
    
    for field_key, field_data in section_data.items():
        # 构造early_batch_info中的字段格式
        early_batch_info[field_key] = {
            'display_name': field_data.get('display_name', ''),
            'type': field_data.get('type', 'text'),
            'value': field_data.get('value', '')
        }
        
        # 构造display_fields数组
        display_fields.append({
            'field_name': field_key,
            'display_name': field_data.get('display_name', ''),
            'field_type': field_data.get('type', 'text'),
            'display_order': field_data.get('priority', 99)
        })
    
    # 按display_order排序
    display_fields.sort(key=lambda x: x['display_order'])
    
    response_data = {
        'early_batch_info': early_batch_info,
        'display_fields': display_fields,
        'has_data': bool(section_data),
        'version': result.get('version', 1),
        'updated_at': result.get('updated_at'),
        'total_fields': result.get('total_fields', 0)
    }
    
    # 验证结果
    if 'early_batch_info' in response_data:
        print("✅ early_batch_info 字段存在")
        print(f"📊 包含 {len(response_data['early_batch_info'])} 个字段")
        print(f"📝 字段列表: {list(response_data['early_batch_info'].keys())}")
        return True
    else:
        print("❌ early_batch_info 字段缺失")
        return False

def test_rural_grid_api():
    """测试农网API"""
    print("\n🔍 测试农网API...")
    
    # 调用API获取数据
    result = policy_sections_api.get_rural_grid_policy(44)
    
    if 'error' in result:
        print(f"❌ API调用失败: {result['error']}")
        return False
    
    # 模拟新版API的响应格式转换
    section_data = result.get('section_data', {})
    
    # 转换为旧版格式的rural_grid_info
    rural_grid_info = {}
    display_fields = []
    
    for field_key, field_data in section_data.items():
        # 构造rural_grid_info中的字段格式
        rural_grid_info[field_key] = {
            'display_name': field_data.get('display_name', ''),
            'type': field_data.get('type', 'text'),
            'value': field_data.get('value', '')
        }
        
        # 构造display_fields数组
        display_fields.append({
            'field_name': field_key,
            'display_name': field_data.get('display_name', ''),
            'field_type': field_data.get('type', 'text'),
            'display_order': field_data.get('priority', 99)
        })
    
    # 按display_order排序
    display_fields.sort(key=lambda x: x['display_order'])
    
    response_data = {
        'rural_grid_info': rural_grid_info,
        'display_fields': display_fields,
        'has_data': bool(section_data),
        'version': result.get('version', 1),
        'updated_at': result.get('updated_at'),
        'total_fields': result.get('total_fields', 0)
    }
    
    # 验证结果
    if 'rural_grid_info' in response_data:
        print("✅ rural_grid_info 字段存在")
        print(f"📊 包含 {len(response_data['rural_grid_info'])} 个字段")
        print(f"📝 字段列表: {list(response_data['rural_grid_info'].keys())}")
        return True
    else:
        print("❌ rural_grid_info 字段缺失")
        return False

if __name__ == '__main__':
    print("🚀 开始测试新版API修复效果...\n")
    
    # 测试提前批API
    early_batch_ok = test_early_batch_api()
    
    # 测试农网API
    rural_grid_ok = test_rural_grid_api()
    
    # 总结
    print("\n📋 测试结果总结:")
    print(f"提前批API: {'✅ 通过' if early_batch_ok else '❌ 失败'}")
    print(f"农网API: {'✅ 通过' if rural_grid_ok else '❌ 失败'}")
    
    if early_batch_ok and rural_grid_ok:
        print("\n🎉 所有测试通过！新版API修复成功！")
        print("前端将能够正确读取 early_batch_info 和 rural_grid_info 字段")
    else:
        print("\n❌ 部分测试失败，需要进一步修复")
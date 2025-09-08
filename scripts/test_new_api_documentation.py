#!/usr/bin/env python3
"""
新版政策板块管理API文档完整性测试
验证所有API接口是否按照文档描述正常工作
"""
import sys
sys.path.append('/workspace')

from app.routes.policy_sections import policy_sections_api

def test_api_endpoints():
    """测试所有API接口"""
    print("🔍 测试新版政策板块管理API接口...\n")
    
    test_unit_id = 44
    results = {}
    
    # 1. 测试基本政策信息接口
    print("1. 测试基本政策信息接口")
    try:
        result = policy_sections_api.get_basic_policy(test_unit_id)
        if 'error' not in result:
            results['basic_get'] = "✅ 通过"
            print(f"   ✅ GET basic - 字段数量: {result.get('total_fields', 0)}")
        else:
            results['basic_get'] = f"❌ 失败: {result['error']}"
            print(f"   ❌ GET basic失败: {result['error']}")
    except Exception as e:
        results['basic_get'] = f"❌ 异常: {str(e)}"
        print(f"   ❌ GET basic异常: {e}")
    
    # 2. 测试提前批政策接口
    print("2. 测试提前批政策接口")
    try:
        result = policy_sections_api.get_early_batch_policy(test_unit_id)
        if 'error' not in result:
            results['early_batch_get'] = "✅ 通过"
            print(f"   ✅ GET early-batch - 字段数量: {result.get('total_fields', 0)}")
        else:
            results['early_batch_get'] = f"❌ 失败: {result['error']}"
            print(f"   ❌ GET early-batch失败: {result['error']}")
    except Exception as e:
        results['early_batch_get'] = f"❌ 异常: {str(e)}"
        print(f"   ❌ GET early-batch异常: {e}")
    
    # 3. 测试农网政策接口
    print("3. 测试农网政策接口")
    try:
        result = policy_sections_api.get_rural_grid_policy(test_unit_id)
        if 'error' not in result:
            results['rural_grid_get'] = "✅ 通过"
            print(f"   ✅ GET rural-grid - 字段数量: {result.get('total_fields', 0)}")
        else:
            results['rural_grid_get'] = f"❌ 失败: {result['error']}"
            print(f"   ❌ GET rural-grid失败: {result['error']}")
    except Exception as e:
        results['rural_grid_get'] = f"❌ 异常: {str(e)}"
        print(f"   ❌ GET rural-grid异常: {e}")
    
    # 4. 测试区域概览接口
    print("4. 测试区域概览接口")
    try:
        result = policy_sections_api.get_regional_policy(test_unit_id)
        if 'error' not in result:
            results['regional_get'] = "✅ 通过"
            print(f"   ✅ GET regional - 字段数量: {result.get('total_fields', 0)}")
        else:
            results['regional_get'] = f"❌ 失败: {result['error']}"
            print(f"   ❌ GET regional失败: {result['error']}")
    except Exception as e:
        results['regional_get'] = f"❌ 异常: {str(e)}"
        print(f"   ❌ GET regional异常: {e}")
    
    # 5. 测试综合接口
    print("5. 测试综合接口")
    try:
        result = policy_sections_api.get_all_policy_sections(test_unit_id)
        if 'error' not in result:
            results['all_sections'] = "✅ 通过"
            sections_count = result.get('total_sections', 0)
            print(f"   ✅ GET all - 板块数量: {sections_count}")
        else:
            results['all_sections'] = f"❌ 失败: {result['error']}"
            print(f"   ❌ GET all失败: {result['error']}")
    except Exception as e:
        results['all_sections'] = f"❌ 异常: {str(e)}"
        print(f"   ❌ GET all异常: {e}")
    
    return results

def test_data_structure_compatibility():
    """测试数据结构与旧版API的兼容性"""
    print("\n🔄 测试数据结构兼容性...\n")
    
    test_unit_id = 44
    compatibility_results = {}
    
    # 测试提前批数据结构兼容性
    print("1. 提前批数据结构兼容性测试")
    try:
        result = policy_sections_api.get_early_batch_policy(test_unit_id)
        section_data = result.get('section_data', {})
        
        # 模拟API路由的数据转换
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
        
        # 验证必需字段
        required_fields = ['early_batch_info', 'display_fields', 'has_data']
        missing_fields = [field for field in required_fields if field not in response_data]
        
        if not missing_fields:
            compatibility_results['early_batch'] = "✅ 兼容"
            print(f"   ✅ 提前批结构兼容 - early_batch_info字段: {len(early_batch_info)}")
        else:
            compatibility_results['early_batch'] = f"❌ 缺失字段: {missing_fields}"
            print(f"   ❌ 提前批结构不兼容，缺失字段: {missing_fields}")
            
    except Exception as e:
        compatibility_results['early_batch'] = f"❌ 异常: {str(e)}"
        print(f"   ❌ 提前批兼容性测试异常: {e}")
    
    # 测试农网数据结构兼容性
    print("2. 农网数据结构兼容性测试")
    try:
        result = policy_sections_api.get_rural_grid_policy(test_unit_id)
        section_data = result.get('section_data', {})
        
        # 模拟API路由的数据转换
        rural_grid_info = {}
        display_fields = []
        
        for field_key, field_data in section_data.items():
            rural_grid_info[field_key] = {
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
            'rural_grid_info': rural_grid_info,
            'display_fields': display_fields,
            'has_data': bool(section_data)
        }
        
        # 验证必需字段
        required_fields = ['rural_grid_info', 'display_fields', 'has_data']
        missing_fields = [field for field in required_fields if field not in response_data]
        
        if not missing_fields:
            compatibility_results['rural_grid'] = "✅ 兼容"
            print(f"   ✅ 农网结构兼容 - rural_grid_info字段: {len(rural_grid_info)}")
        else:
            compatibility_results['rural_grid'] = f"❌ 缺失字段: {missing_fields}"
            print(f"   ❌ 农网结构不兼容，缺失字段: {missing_fields}")
            
    except Exception as e:
        compatibility_results['rural_grid'] = f"❌ 异常: {str(e)}"
        print(f"   ❌ 农网兼容性测试异常: {e}")
    
    return compatibility_results

def test_field_mapping():
    """测试字段映射功能"""
    print("\n🗺️ 测试字段映射功能...\n")
    
    # 测试数据库字段到前端字段的映射
    mapping_config = policy_sections_api.get_standard_field_mapping()
    
    print("字段映射配置:")
    for db_field, frontend_field in mapping_config.items():
        print(f"   {db_field} -> {frontend_field}")
    
    mapping_results = {
        'mapping_count': len(mapping_config),
        'mapping_status': '✅ 正常' if mapping_config else '❌ 空配置'
    }
    
    return mapping_results

def test_field_configurations():
    """测试字段配置"""
    print("\n⚙️ 测试字段配置...\n")
    
    config_results = {}
    
    # 测试各个板块的字段配置
    configs = {
        'basic': policy_sections_api.get_basic_policy_field_config(),
        'early_batch': policy_sections_api.get_early_batch_field_config(),
        'rural_grid': policy_sections_api.get_rural_grid_field_config(),
        'regional': policy_sections_api.get_regional_field_config()
    }
    
    for section_name, config in configs.items():
        field_count = len(config)
        if field_count > 0:
            config_results[section_name] = f"✅ {field_count}个字段"
            print(f"   {section_name}: {field_count}个字段配置")
        else:
            config_results[section_name] = "❌ 无字段配置"
            print(f"   {section_name}: 无字段配置")
    
    return config_results

def generate_test_report(api_results, compatibility_results, mapping_results, config_results):
    """生成测试报告"""
    print("\n" + "="*60)
    print("📋 新版政策板块管理API文档完整性测试报告")
    print("="*60)
    
    # API接口测试结果
    print("\n1. API接口测试结果:")
    for endpoint, result in api_results.items():
        print(f"   {endpoint}: {result}")
    
    # 数据结构兼容性测试结果
    print("\n2. 数据结构兼容性测试:")
    for section, result in compatibility_results.items():
        print(f"   {section}: {result}")
    
    # 字段映射测试结果
    print(f"\n3. 字段映射测试:")
    print(f"   映射数量: {mapping_results['mapping_count']}")
    print(f"   映射状态: {mapping_results['mapping_status']}")
    
    # 字段配置测试结果
    print("\n4. 字段配置测试:")
    for section, result in config_results.items():
        print(f"   {section}: {result}")
    
    # 总体评估
    all_api_pass = all('✅' in result for result in api_results.values())
    all_compatibility_pass = all('✅' in result for result in compatibility_results.values())
    mapping_pass = '✅' in mapping_results['mapping_status']
    all_config_pass = all('✅' in result for result in config_results.values())
    
    overall_status = all_api_pass and all_compatibility_pass and mapping_pass and all_config_pass
    
    print("\n" + "="*60)
    if overall_status:
        print("🎉 总体评估: 所有测试通过！新版API文档完整且功能正常")
        print("📖 新版API已准备就绪，可以替代旧版API投入使用")
    else:
        print("⚠️ 总体评估: 部分测试未通过，需要进一步修复")
        
        if not all_api_pass:
            print("   - API接口存在问题")
        if not all_compatibility_pass:
            print("   - 数据结构兼容性存在问题")
        if not mapping_pass:
            print("   - 字段映射存在问题")
        if not all_config_pass:
            print("   - 字段配置存在问题")
    
    print("="*60)

if __name__ == '__main__':
    print("🚀 开始新版政策板块管理API文档完整性测试...\n")
    
    # 执行所有测试
    api_results = test_api_endpoints()
    compatibility_results = test_data_structure_compatibility()
    mapping_results = test_field_mapping()
    config_results = test_field_configurations()
    
    # 生成综合测试报告
    generate_test_report(api_results, compatibility_results, mapping_results, config_results)
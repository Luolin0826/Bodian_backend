#!/usr/bin/env python3
"""
完整的API兼容性测试，模拟前端的具体调用场景
"""
import requests
import json

def test_all_apis():
    """测试所有API接口"""
    base_url = "http://localhost:5000"
    test_units = [44, 5, 1]  # 测试多个单位
    
    results = {}
    
    for unit_id in test_units:
        print(f"\n🔍 测试单位 {unit_id}:")
        print("="*50)
        
        unit_results = {}
        
        # 1. 测试基本政策接口
        try:
            response = requests.get(f"{base_url}/api/v1/policy-sections/{unit_id}/basic", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'data' in data:
                    section_data = data['data'].get('section_data', {})
                    unit_results['basic'] = {
                        'status': '✅ 成功',
                        'fields_count': len(section_data),
                        'has_data': bool(section_data)
                    }
                    print(f"   基本政策: ✅ 成功 ({len(section_data)}个字段)")
                else:
                    unit_results['basic'] = {'status': '❌ 数据格式错误', 'response': data}
                    print(f"   基本政策: ❌ 数据格式错误")
            else:
                unit_results['basic'] = {'status': f'❌ HTTP {response.status_code}'}
                print(f"   基本政策: ❌ HTTP {response.status_code}")
        except Exception as e:
            unit_results['basic'] = {'status': f'❌ 异常: {str(e)}'}
            print(f"   基本政策: ❌ 异常: {e}")
        
        # 2. 测试提前批接口
        try:
            response = requests.get(f"{base_url}/api/v1/policy-sections/{unit_id}/early-batch", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'data' in data:
                    early_batch_info = data['data'].get('early_batch_info', {})
                    has_data = data['data'].get('has_data', False)
                    unit_results['early_batch'] = {
                        'status': '✅ 成功',
                        'fields_count': len(early_batch_info),
                        'has_data': has_data,
                        'has_early_batch_info_field': 'early_batch_info' in data['data']
                    }
                    print(f"   提前批: ✅ 成功 ({len(early_batch_info)}个字段, has_data={has_data})")
                else:
                    unit_results['early_batch'] = {'status': '❌ 数据格式错误', 'response': data}
                    print(f"   提前批: ❌ 数据格式错误")
            else:
                unit_results['early_batch'] = {'status': f'❌ HTTP {response.status_code}'}
                print(f"   提前批: ❌ HTTP {response.status_code}")
        except Exception as e:
            unit_results['early_batch'] = {'status': f'❌ 异常: {str(e)}'}
            print(f"   提前批: ❌ 异常: {e}")
        
        # 3. 测试农网接口
        try:
            response = requests.get(f"{base_url}/api/v1/policy-sections/{unit_id}/rural-grid", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'data' in data:
                    rural_grid_info = data['data'].get('rural_grid_info', {})
                    has_data = data['data'].get('has_data', False)
                    unit_results['rural_grid'] = {
                        'status': '✅ 成功',
                        'fields_count': len(rural_grid_info),
                        'has_data': has_data,
                        'has_rural_grid_info_field': 'rural_grid_info' in data['data']
                    }
                    print(f"   农网: ✅ 成功 ({len(rural_grid_info)}个字段, has_data={has_data})")
                else:
                    unit_results['rural_grid'] = {'status': '❌ 数据格式错误', 'response': data}
                    print(f"   农网: ❌ 数据格式错误")
            else:
                unit_results['rural_grid'] = {'status': f'❌ HTTP {response.status_code}'}
                print(f"   农网: ❌ HTTP {response.status_code}")
        except Exception as e:
            unit_results['rural_grid'] = {'status': f'❌ 异常: {str(e)}'}
            print(f"   农网: ❌ 异常: {e}")
        
        # 4. 测试新增接口
        try:
            response = requests.get(f"{base_url}/api/v1/policy-sections/{unit_id}/unit-details", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'data' in data:
                    policy_info = data['data'].get('policy_info', {})
                    unit_info = data['data'].get('unit_info', {})
                    unit_results['unit_details'] = {
                        'status': '✅ 成功',
                        'fields_count': len(policy_info),
                        'unit_name': unit_info.get('unit_name', '未知')
                    }
                    print(f"   单位详情: ✅ 成功 ({unit_info.get('unit_name', '未知')}, {len(policy_info)}个字段)")
                else:
                    unit_results['unit_details'] = {'status': '❌ 数据格式错误'}
                    print(f"   单位详情: ❌ 数据格式错误")
            else:
                unit_results['unit_details'] = {'status': f'❌ HTTP {response.status_code}'}
                print(f"   单位详情: ❌ HTTP {response.status_code}")
        except Exception as e:
            unit_results['unit_details'] = {'status': f'❌ 异常: {str(e)}'}
            print(f"   单位详情: ❌ 异常: {e}")
        
        # 5. 测试区域概览接口
        try:
            response = requests.get(f"{base_url}/api/v1/policy-sections/{unit_id}/regional-overview", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'data' in data:
                    unit_overview = data['data'].get('unit_overview', {})
                    unit_results['regional_overview'] = {
                        'status': '✅ 成功',
                        'unit_name': unit_overview.get('city', '未知')
                    }
                    print(f"   区域概览: ✅ 成功 ({unit_overview.get('city', '未知')})")
                else:
                    unit_results['regional_overview'] = {'status': '❌ 数据格式错误'}
                    print(f"   区域概览: ❌ 数据格式错误")
            else:
                unit_results['regional_overview'] = {'status': f'❌ HTTP {response.status_code}'}
                print(f"   区域概览: ❌ HTTP {response.status_code}")
        except Exception as e:
            unit_results['regional_overview'] = {'status': f'❌ 异常: {str(e)}'}
            print(f"   区域概览: ❌ 异常: {e}")
        
        results[unit_id] = unit_results
    
    return results

def test_filter_options():
    """测试筛选选项接口"""
    print(f"\n🔍 测试筛选选项接口:")
    print("="*50)
    
    try:
        response = requests.get("http://localhost:5000/api/v1/policy-sections/filter-options", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'data' in data:
                filter_data = data['data']
                total_units = filter_data.get('total_units', 0)
                categories = filter_data.get('categories', {})
                print(f"   筛选选项: ✅ 成功 (总共{total_units}个单位)")
                print(f"   分类统计: {categories}")
                return True
            else:
                print(f"   筛选选项: ❌ 数据格式错误")
                return False
        else:
            print(f"   筛选选项: ❌ HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   筛选选项: ❌ 异常: {e}")
        return False

def analyze_results(results):
    """分析测试结果"""
    print(f"\n📊 测试结果分析:")
    print("="*60)
    
    total_tests = len(results) * 5  # 每个单位5个接口
    success_count = 0
    
    for unit_id, unit_results in results.items():
        print(f"\n单位 {unit_id}:")
        for api_name, result in unit_results.items():
            status = result.get('status', '未知')
            if '✅' in status:
                success_count += 1
            print(f"  {api_name}: {status}")
    
    success_rate = (success_count / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"\n总体结果:")
    print(f"成功率: {success_count}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 API兼容性测试大部分通过！")
        if success_rate < 100:
            print("⚠️ 仍有少量问题需要解决")
    else:
        print("❌ API兼容性存在问题，需要进一步修复")
    
    return success_rate >= 80

if __name__ == '__main__':
    print("🚀 开始完整的API兼容性测试...\n")
    
    # 测试所有API接口
    results = test_all_apis()
    
    # 测试筛选选项
    filter_success = test_filter_options()
    
    # 分析结果
    overall_success = analyze_results(results)
    
    if overall_success and filter_success:
        print("\n🎯 结论: 新版API已完全兼容，应该能解决前端的404错误")
        print("建议: 检查前端是否正确调用了新版API路径")
    else:
        print("\n⚠️ 结论: 仍需进一步修复部分接口")
    
    print("\n" + "="*60)
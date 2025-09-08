#!/usr/bin/env python3
"""
测试筛选选项接口
"""
import sys
sys.path.append('/workspace')

from app.routes.policy_sections import policy_sections_api

def test_filter_options():
    """测试筛选选项接口"""
    print("🔍 测试筛选选项接口...\n")
    
    try:
        result = policy_sections_api.get_filter_options()
        
        if 'error' in result:
            print(f"❌ API调用失败: {result['error']}")
            return False
        
        # 检查数据结构
        required_keys = ['gw_provinces', 'gw_direct_units', 'nw_provinces', 'nw_direct_units']
        missing_keys = [key for key in required_keys if key not in result]
        
        if missing_keys:
            print(f"❌ 响应缺失字段: {missing_keys}")
            return False
        
        # 打印统计信息
        print("✅ 筛选选项数据获取成功！")
        print(f"📊 国网省公司: {len(result['gw_provinces'])}个")
        print(f"📊 国网直属单位: {len(result['gw_direct_units'])}个")
        print(f"📊 南网省公司: {len(result['nw_provinces'])}个")
        print(f"📊 南网直属单位: {len(result['nw_direct_units'])}个")
        print(f"📊 总计: {result.get('total_units', 0)}个单位")
        
        # 显示具体单位（前几个作为示例）
        print("\n📋 单位示例:")
        
        if result['gw_provinces']:
            print("🔹 国网省公司:")
            for unit in result['gw_provinces'][:3]:  # 显示前3个
                print(f"   - {unit['unit_name']} (ID: {unit['unit_id']})")
        
        if result['nw_provinces']:
            print("🔹 南网省公司:")
            for unit in result['nw_provinces'][:3]:  # 显示前3个
                print(f"   - {unit['unit_name']} (ID: {unit['unit_id']})")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

if __name__ == '__main__':
    print("🚀 开始测试筛选选项接口...\n")
    
    success = test_filter_options()
    
    print("\n" + "="*50)
    if success:
        print("🎉 筛选选项接口测试成功！")
        print("新版API路由: GET /api/v1/policy-sections/filter-options")
        print("替代旧版路由: GET /api/v1/policies/filter-options")
    else:
        print("❌ 筛选选项接口测试失败")
    print("="*50)
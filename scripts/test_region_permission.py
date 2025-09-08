#!/usr/bin/env python3
"""
测试区域管理权限配置脚本
"""
import requests
import json

# 测试配置
BASE_URL = "http://localhost:5000"
TEST_USER = "admin"  # 或者你的测试用户名
TEST_PASSWORD = "password"  # 替换为实际密码

def test_region_permissions():
    """测试区域管理权限配置"""
    print("🔍 测试区域管理权限配置")
    print("=" * 50)
    
    # 步骤1：登录获取token
    print("1. 尝试登录...")
    login_data = {
        "username": TEST_USER,
        "password": TEST_PASSWORD
    }
    
    try:
        login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get('access_token')
            user_info = login_result.get('user', {})
            print(f"✅ 登录成功！用户: {user_info.get('username')}, 角色: {user_info.get('role')}")
        else:
            print(f"❌ 登录失败: {login_response.status_code}")
            print("请检查用户名和密码，或者数据库中是否有相应用户")
            return False
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return False
    
    # 步骤2：获取用户权限信息
    print("\n2. 检查用户权限...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        me_response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
        if me_response.status_code == 200:
            user_data = me_response.json()
            permissions = user_data.get('permissions', {})
            menu_permissions = permissions.get('menu', [])
            operation_permissions = permissions.get('operation', {})
            
            print(f"✅ 获取权限信息成功！")
            print(f"📋 用户角色: {user_data.get('role')}")
            print(f"📋 菜单权限数量: {len(menu_permissions)}")
            
            # 检查是否包含区域管理权限
            has_region_menu = '/system/region' in menu_permissions
            has_region_operation = 'region_manage' in operation_permissions.get('system', [])
            
            print(f"\n3. 区域管理权限检查:")
            print(f"   菜单权限 (/system/region): {'✅ 存在' if has_region_menu else '❌ 缺失'}")
            print(f"   操作权限 (region_manage): {'✅ 存在' if has_region_operation else '❌ 缺失'}")
            
            if has_region_menu and has_region_operation:
                print("\n🎉 权限配置正确！区域管理功能应该可以正常显示。")
                
                # 显示所有菜单权限
                print(f"\n📜 完整菜单权限列表:")
                for i, menu in enumerate(menu_permissions, 1):
                    status = "🎯" if menu == '/system/region' else "📁"
                    print(f"   {i:2d}. {status} {menu}")
                    
                return True
            else:
                print("\n❌ 权限配置不完整！")
                return False
                
        else:
            print(f"❌ 获取用户信息失败: {me_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 获取权限信息失败: {e}")
        return False

def test_region_api_access():
    """测试区域管理API访问"""
    print("\n" + "=" * 50)
    print("🔧 测试区域管理API访问")
    
    # 首先获取token
    login_data = {"username": TEST_USER, "password": TEST_PASSWORD}
    try:
        login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        if login_response.status_code == 200:
            token = login_response.json().get('access_token')
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试区域管理相关API
            print("4. 测试区域管理API访问...")
            
            # 测试获取省份列表
            regions_response = requests.get(
                f"{BASE_URL}/api/v1/policy-management/regions?region_level=province", 
                headers=headers
            )
            
            if regions_response.status_code == 200:
                regions_data = regions_response.json()
                print(f"✅ 区域API访问成功！")
                print(f"📊 获取到 {len(regions_data.get('data', []))} 个省份")
                return True
            else:
                print(f"❌ 区域API访问失败: {regions_response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ API访问测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 区域管理权限测试工具")
    print("=" * 50)
    
    # 运行权限检查
    permission_ok = test_region_permissions()
    
    # 运行API访问测试
    api_ok = test_region_api_access()
    
    print("\n" + "=" * 50)
    print("📋 测试总结:")
    print(f"   权限配置: {'✅ 通过' if permission_ok else '❌ 失败'}")
    print(f"   API访问: {'✅ 通过' if api_ok else '❌ 失败'}")
    
    if permission_ok and api_ok:
        print("\n🎉 所有测试通过！区域管理功能应该可以正常使用。")
        print("\n💡 建议:")
        print("   1. 清除浏览器缓存并刷新页面")
        print("   2. 重新登录以获取最新权限")
        print("   3. 检查前端是否正确调用了权限验证")
    else:
        print("\n❌ 存在问题，需要进一步检查配置。")
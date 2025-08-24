# app/utils/ip_location.py
"""
IP地理位置查询工具
使用两步查询获取更精确的地址信息：
1. 通过IP获取经纬度
2. 通过经纬度获取详细地址
"""
import requests
import json
from flask import current_app
from typing import Optional, Dict, Any
import time

class IPLocationService:
    """IP地理位置查询服务"""
    
    # IP地理位置查询API (美团)
    IP_GEO_API = "https://apimobile.meituan.com/locate/v2/ip/loc"
    # 经纬度地址查询API (美团)
    LAT_LNG_API = "https://apimobile.meituan.com/group/v1/city/latlng"
    
    TIMEOUT = 10  # 10秒超时
    MAX_RETRIES = 2  # 最大重试次数
    
    @classmethod
    def get_location_by_ip(cls, ip_address: str) -> Optional[Dict[str, Any]]:
        """
        根据IP地址获取地理位置信息（两步查询）
        1. 先通过IP获取经纬度
        2. 再通过经纬度获取详细地址
        
        Args:
            ip_address: IP地址
            
        Returns:
            地理位置信息字典，失败时返回None
        """
        if not ip_address or ip_address in ['127.0.0.1', '::1', 'localhost']:
            return {
                'location_text': '本地',
                'country': '中国',
                'province': '本地',
                'city': '本地',
                'district': '本地',
                'area': '本地',
                'isp': '本地网络',
                'type': '本地网络'
            }
        
        # 第一步：通过IP获取经纬度和基础信息
        ip_geo_data = cls._get_ip_geo_data(ip_address)
        if not ip_geo_data:
            return None
        
        # 提取经纬度（美团API格式）
        latitude = ip_geo_data.get('lat')
        longitude = ip_geo_data.get('lng')
        
        # 第二步：如果有经纬度，通过经纬度获取详细地址
        detailed_address = None
        if latitude and longitude:
            detailed_address = cls._get_address_by_latlng(latitude, longitude)
        
        # 合并结果
        return cls._merge_location_data(ip_geo_data, detailed_address)
    
    @classmethod
    def _get_ip_geo_data(cls, ip_address: str) -> Optional[Dict[str, Any]]:
        """
        通过IP获取地理位置和经纬度信息（美团API）
        """
        for attempt in range(cls.MAX_RETRIES):
            try:
                url = f"{cls.IP_GEO_API}?rgeo=true&ip={ip_address}"
                response = requests.get(url, timeout=cls.TIMEOUT)
                
                if response.status_code == 200:
                    data = response.json()
                    # 美团API返回格式为 {"data": {...}}
                    if data.get('data'):
                        return data['data']
                else:
                    current_app.logger.warning(f"IP地理位置查询失败，状态码: {response.status_code}, IP: {ip_address}, 尝试: {attempt + 1}")
                    
            except requests.RequestException as e:
                current_app.logger.error(f"IP地理位置查询异常: {str(e)}, IP: {ip_address}, 尝试: {attempt + 1}")
            except json.JSONDecodeError as e:
                current_app.logger.error(f"IP地理位置响应解析失败: {str(e)}, IP: {ip_address}, 尝试: {attempt + 1}")
            except Exception as e:
                current_app.logger.error(f"IP地理位置查询未知错误: {str(e)}, IP: {ip_address}, 尝试: {attempt + 1}")
            
            # 重试前等待
            if attempt < cls.MAX_RETRIES - 1:
                time.sleep(1)
        
        return None
    
    @classmethod
    def _get_address_by_latlng(cls, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        通过经纬度获取详细地址信息
        """
        for attempt in range(cls.MAX_RETRIES):
            try:
                url = f"{cls.LAT_LNG_API}/{latitude},{longitude}?tag=0"
                response = requests.get(url, timeout=cls.TIMEOUT)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data'):
                        return data['data']
                else:
                    current_app.logger.warning(f"经纬度地址查询失败，状态码: {response.status_code}, 坐标: {latitude},{longitude}, 尝试: {attempt + 1}")
                    
            except requests.RequestException as e:
                current_app.logger.error(f"经纬度地址查询异常: {str(e)}, 坐标: {latitude},{longitude}, 尝试: {attempt + 1}")
            except json.JSONDecodeError as e:
                current_app.logger.error(f"经纬度地址响应解析失败: {str(e)}, 坐标: {latitude},{longitude}, 尝试: {attempt + 1}")
            except Exception as e:
                current_app.logger.error(f"经纬度地址查询未知错误: {str(e)}, 坐标: {latitude},{longitude}, 尝试: {attempt + 1}")
            
            # 重试前等待
            if attempt < cls.MAX_RETRIES - 1:
                time.sleep(1)
        
        return None
    
    @classmethod
    def _merge_location_data(cls, ip_geo_data: Dict[str, Any], detailed_address: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        合并IP地理位置数据和详细地址数据
        
        Args:
            ip_geo_data: IP地理位置API返回的数据
            detailed_address: 经纬度地址API返回的数据
            
        Returns:
            合并后的位置数据
        """
        try:
            # 从IP地理位置数据提取基础信息（美团API格式）
            rgeo = ip_geo_data.get('rgeo', {})
            country = rgeo.get('country', '未知')
            province_from_ip = rgeo.get('province', '未知')
            city_from_ip = rgeo.get('city', '未知')
            district_from_ip = rgeo.get('district', '')
            
            # 构建regions数组以兼容旧格式
            regions = [province_from_ip, city_from_ip, district_from_ip] if district_from_ip else [province_from_ip, city_from_ip]
            regions = [r for r in regions if r and r != '未知']  # 过滤空值
            
            isp_name = ip_geo_data.get('fromwhere', '未知运营商')
            
            # 如果有详细地址数据，优先使用
            if detailed_address:
                province = detailed_address.get('province', '')
                city = detailed_address.get('city', '')
                district = detailed_address.get('district', '')
                area_name = detailed_address.get('areaName', '')
                detail = detailed_address.get('detail', '')
                
                # 构建详细位置文本
                location_parts = []
                if province and province != city:  # 避免重复，如"北京"和"北京市"
                    location_parts.append(province)
                if city:
                    location_parts.append(city)
                if district:
                    location_parts.append(district)
                if area_name:
                    location_parts.append(area_name)
                
                location_text = ' '.join(location_parts) if location_parts else '未知位置'
                
                # 如果有详细地址，追加到位置文本
                if detail:
                    location_text += f" {detail}"
                
            else:
                # 使用IP地理位置数据
                province = province_from_ip
                city = city_from_ip
                district = district_from_ip
                area_name = ''
                detail = ''
                
                if regions:
                    location_text = ' '.join(regions)
                else:
                    location_text = country
            
            return {
                'ip': ip_geo_data.get('ip'),
                'location_text': location_text,
                'country': country,
                'province': province,
                'city': city,
                'district': district,
                'area': area_name,
                'detail': detail,
                'regions': regions,
                'regions_short': regions,  # 美团API没有单独的短地址
                'type': '宽带',  # 美团API没有网络类型，默认为宽带
                'isp': isp_name,
                'latitude': ip_geo_data.get('lat'),
                'longitude': ip_geo_data.get('lng'),
                'adcode': rgeo.get('adcode', ''),  # 行政区划代码
                'ip_geo_data': ip_geo_data,  # 保存原始IP地理数据
                'detailed_address': detailed_address  # 保存详细地址数据
            }
        except Exception as e:
            current_app.logger.error(f"合并位置数据失败: {str(e)}")
            return {
                'location_text': '未知位置',
                'country': '未知',
                'province': '未知',
                'city': '未知',
                'district': '',
                'area': '',
                'regions': [],
                'type': '未知',
                'ip_geo_data': ip_geo_data,
                'detailed_address': detailed_address
            }
    
    @classmethod
    def get_simple_location_text(cls, ip_address: str) -> str:
        """
        获取简单的位置文本描述
        
        Args:
            ip_address: IP地址
            
        Returns:
            位置文本，如 "北京市 东城区"
        """
        location_data = cls.get_location_by_ip(ip_address)
        if location_data:
            return location_data.get('location_text', '未知位置')
        return '未知位置'

# 便捷函数
def get_ip_location(ip_address: str) -> Optional[Dict[str, Any]]:
    """获取IP地理位置信息的便捷函数"""
    return IPLocationService.get_location_by_ip(ip_address)

def get_ip_location_text(ip_address: str) -> str:
    """获取IP位置文本的便捷函数"""
    return IPLocationService.get_simple_location_text(ip_address)
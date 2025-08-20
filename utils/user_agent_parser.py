# app/utils/user_agent_parser.py
import re
from typing import Dict, Optional

class UserAgentParser:
    """用户代理字符串解析工具"""
    
    # 浏览器检测规则
    BROWSER_RULES = [
        (r'Chrome/(\d+\.?\d*)', 'Chrome'),
        (r'Firefox/(\d+\.?\d*)', 'Firefox'),
        (r'Safari/(\d+\.?\d*)', 'Safari'),
        (r'Edge/(\d+\.?\d*)', 'Edge'),
        (r'Opera/(\d+\.?\d*)', 'Opera'),
        (r'MSIE (\d+\.?\d*)', 'Internet Explorer'),
    ]
    
    # 操作系统检测规则
    OS_RULES = [
        (r'Windows NT 10\.0', 'Windows 10'),
        (r'Windows NT 6\.3', 'Windows 8.1'),
        (r'Windows NT 6\.2', 'Windows 8'),
        (r'Windows NT 6\.1', 'Windows 7'),
        (r'Windows NT 6\.0', 'Windows Vista'),
        (r'Windows NT 5\.1', 'Windows XP'),
        (r'Mac OS X (\d+_\d+)', 'macOS'),
        (r'Linux', 'Linux'),
        (r'Android (\d+\.?\d*)', 'Android'),
        (r'iOS (\d+\.?\d*)', 'iOS'),
        (r'iPhone OS (\d+\.?\d*)', 'iOS'),
    ]
    
    # 设备类型检测规则
    DEVICE_RULES = [
        (r'Mobile|Android|iPhone|iPod', 'Mobile'),
        (r'iPad|Tablet', 'Tablet'),
        (r'Desktop|Windows|Macintosh|Linux', 'Desktop'),
    ]
    
    @classmethod
    def parse(cls, user_agent: str) -> Dict[str, Optional[str]]:
        """
        解析用户代理字符串
        
        Args:
            user_agent: 用户代理字符串
        
        Returns:
            Dict: 解析结果
                - browser: 浏览器名称
                - browser_version: 浏览器版本
                - os: 操作系统
                - os_version: 操作系统版本
                - device_type: 设备类型
        """
        if not user_agent:
            return {
                'browser': 'Unknown',
                'browser_version': None,
                'os': 'Unknown',
                'os_version': None,
                'device_type': 'Unknown'
            }
        
        user_agent_lower = user_agent.lower()
        
        # 解析浏览器
        browser = 'Unknown'
        browser_version = None
        for pattern, name in cls.BROWSER_RULES:
            match = re.search(pattern.lower(), user_agent_lower)
            if match:
                browser = name
                if match.groups():
                    browser_version = match.group(1)
                break
        
        # 解析操作系统
        os_name = 'Unknown'
        os_version = None
        for pattern, name in cls.OS_RULES:
            match = re.search(pattern.lower(), user_agent_lower)
            if match:
                os_name = name
                if match.groups() and '_' not in pattern:
                    os_version = match.group(1)
                elif match.groups() and '_' in pattern:
                    # macOS版本处理
                    os_version = match.group(1).replace('_', '.')
                break
        
        # 解析设备类型
        device_type = 'Desktop'  # 默认桌面设备
        for pattern, dtype in cls.DEVICE_RULES:
            if re.search(pattern.lower(), user_agent_lower):
                device_type = dtype
                break
        
        return {
            'browser': browser,
            'browser_version': browser_version,
            'os': os_name,
            'os_version': os_version,
            'device_type': device_type
        }
    
    @classmethod
    def get_device_fingerprint(cls, user_agent: str, ip_address: str = None) -> str:
        """
        生成设备指纹
        
        Args:
            user_agent: 用户代理字符串
            ip_address: IP地址
        
        Returns:
            str: 设备指纹（MD5哈希）
        """
        import hashlib
        
        # 解析用户代理
        parsed = cls.parse(user_agent)
        
        # 构建指纹数据
        fingerprint_data = f"{parsed['browser']}:{parsed['os']}:{parsed['device_type']}"
        
        if ip_address:
            # 只使用IP的前3段，提供一定的隐私保护
            ip_parts = ip_address.split('.')
            if len(ip_parts) >= 3:
                partial_ip = '.'.join(ip_parts[:3]) + '.x'
                fingerprint_data += f":{partial_ip}"
        
        return hashlib.md5(fingerprint_data.encode()).hexdigest()
    
    @classmethod
    def is_mobile(cls, user_agent: str) -> bool:
        """
        判断是否为移动设备
        
        Args:
            user_agent: 用户代理字符串
        
        Returns:
            bool: 是否为移动设备
        """
        if not user_agent:
            return False
        
        mobile_patterns = [
            r'Mobile', r'Android', r'iPhone', r'iPod',
            r'BlackBerry', r'Windows Phone', r'Opera Mini'
        ]
        
        user_agent_lower = user_agent.lower()
        return any(re.search(pattern.lower(), user_agent_lower) for pattern in mobile_patterns)
    
    @classmethod
    def is_bot(cls, user_agent: str) -> bool:
        """
        判断是否为机器人/爬虫
        
        Args:
            user_agent: 用户代理字符串
        
        Returns:
            bool: 是否为机器人
        """
        if not user_agent:
            return False
        
        bot_patterns = [
            r'bot', r'crawler', r'spider', r'scraper',
            r'googlebot', r'bingbot', r'baiduspider',
            r'yandexbot', r'facebookexternalhit'
        ]
        
        user_agent_lower = user_agent.lower()
        return any(re.search(pattern, user_agent_lower) for pattern in bot_patterns)
    
    @classmethod
    def get_browser_family(cls, user_agent: str) -> str:
        """
        获取浏览器家族（简化分类）
        
        Args:
            user_agent: 用户代理字符串
        
        Returns:
            str: 浏览器家族
        """
        parsed = cls.parse(user_agent)
        browser = parsed['browser']
        
        # 浏览器家族映射
        family_mapping = {
            'Chrome': 'Chromium',
            'Edge': 'Chromium',
            'Opera': 'Chromium',
            'Safari': 'WebKit',
            'Firefox': 'Gecko',
            'Internet Explorer': 'Trident'
        }
        
        return family_mapping.get(browser, 'Unknown')

# 便捷函数
def parse_user_agent(user_agent: str) -> Dict[str, Optional[str]]:
    """解析用户代理字符串的便捷函数"""
    return UserAgentParser.parse(user_agent)

def get_device_info(user_agent: str, ip_address: str = None) -> Dict:
    """获取设备信息的便捷函数"""
    parsed = UserAgentParser.parse(user_agent)
    return {
        **parsed,
        'is_mobile': UserAgentParser.is_mobile(user_agent),
        'is_bot': UserAgentParser.is_bot(user_agent),
        'browser_family': UserAgentParser.get_browser_family(user_agent),
        'device_fingerprint': UserAgentParser.get_device_fingerprint(user_agent, ip_address)
    }
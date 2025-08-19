# app/utils/timezone.py
"""
时区工具模块
"""
from datetime import datetime
import pytz
from flask import current_app

def get_timezone():
    """获取配置的时区"""
    return current_app.config.get('TIMEZONE', pytz.timezone('Asia/Shanghai'))

def now():
    """获取当前时区时间（不带时区信息的naive datetime）"""
    tz = get_timezone()
    return datetime.now(tz).replace(tzinfo=None)

def utcnow():
    """获取当前时区时间（兼容utcnow的命名）"""
    return now()

def localize_datetime(dt):
    """将UTC时间转换为本地时间"""
    if dt is None:
        return None
    
    tz = get_timezone()
    if dt.tzinfo is None:
        # 假设输入是UTC时间
        utc_dt = pytz.utc.localize(dt)
        return utc_dt.astimezone(tz).replace(tzinfo=None)
    
    return dt.astimezone(tz).replace(tzinfo=None)

def format_datetime(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """格式化时间显示"""
    if dt is None:
        return None
    
    # 确保是本地时间
    local_dt = localize_datetime(dt) if dt.tzinfo else dt
    return local_dt.strftime(format_str)

def today():
    """获取当前日期"""
    return now().date()
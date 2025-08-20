# app/services/notification_service.py
from app.models import db, Notification, User
from app.utils.timezone import now
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class NotificationService:
    """通知服务"""
    
    @staticmethod
    def create_notification(user_id: int, title: str, content: str = None, **kwargs) -> Notification:
        """
        创建通知
        
        Args:
            user_id: 用户ID
            title: 通知标题
            content: 通知内容
            **kwargs: 其他参数
                - type: 通知类型 (system/email/push)
                - priority: 优先级 (low/medium/high/urgent)
                - sender: 发送者
                - sender_id: 发送者ID
                - data: 额外数据
                - expires_at: 过期时间
        
        Returns:
            Notification: 创建的通知对象
        """
        notification = Notification.create_notification(
            user_id=user_id,
            title=title,
            content=content,
            **kwargs
        )
        return notification
    
    @staticmethod
    def send_system_notification(user_ids: List[int], title: str, content: str, **kwargs) -> List[Notification]:
        """
        批量发送系统通知
        
        Args:
            user_ids: 用户ID列表
            title: 通知标题
            content: 通知内容
            **kwargs: 其他参数
        
        Returns:
            List[Notification]: 创建的通知列表
        """
        notifications = []
        
        for user_id in user_ids:
            notification = Notification(
                user_id=user_id,
                type='system',
                title=title,
                content=content,
                priority=kwargs.get('priority', 'medium'),
                sender=kwargs.get('sender', '系统'),
                sender_id=kwargs.get('sender_id'),
                data=kwargs.get('data'),
                expires_at=kwargs.get('expires_at')
            )
            notifications.append(notification)
        
        # 批量插入
        db.session.add_all(notifications)
        db.session.commit()
        
        # 这里可以添加实时推送逻辑
        # 例如: WebSocket推送、邮件发送等
        
        return notifications
    
    @staticmethod
    def send_role_notification(role: str, title: str, content: str, **kwargs) -> List[Notification]:
        """
        向特定角色的用户发送通知
        
        Args:
            role: 用户角色
            title: 通知标题
            content: 通知内容
            **kwargs: 其他参数
        
        Returns:
            List[Notification]: 创建的通知列表
        """
        # 获取指定角色的所有活跃用户
        users = User.query.filter_by(role=role, is_active=True).all()
        user_ids = [user.id for user in users]
        
        if not user_ids:
            return []
        
        return NotificationService.send_system_notification(
            user_ids=user_ids,
            title=title,
            content=content,
            **kwargs
        )
    
    @staticmethod
    def send_welcome_notification(user_id: int) -> Notification:
        """
        发送欢迎通知
        
        Args:
            user_id: 用户ID
        
        Returns:
            Notification: 创建的通知对象
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        title = f"欢迎使用系统，{user.real_name or user.username}！"
        content = """
        欢迎加入我们的系统！
        
        您可以通过以下方式开始使用：
        1. 完善您的个人信息
        2. 设置个人偏好
        3. 浏览系统功能
        
        如有任何问题，请联系系统管理员。
        """
        
        return NotificationService.create_notification(
            user_id=user_id,
            title=title,
            content=content,
            type='system',
            priority='medium',
            sender='系统'
        )
    
    @staticmethod
    def send_password_change_notification(user_id: int) -> Notification:
        """
        发送密码修改通知
        
        Args:
            user_id: 用户ID
        
        Returns:
            Notification: 创建的通知对象
        """
        return NotificationService.create_notification(
            user_id=user_id,
            title="密码已修改",
            content=f"您的账户密码已于 {now().strftime('%Y-%m-%d %H:%M:%S')} 成功修改。如果这不是您的操作，请立即联系系统管理员。",
            type='system',
            priority='high',
            sender='安全系统'
        )
    
    @staticmethod
    def send_login_notification(user_id: int, ip_address: str = None, location: str = None) -> Notification:
        """
        发送登录通知（异地登录或可疑登录时）
        
        Args:
            user_id: 用户ID
            ip_address: IP地址
            location: 登录位置
        
        Returns:
            Notification: 创建的通知对象
        """
        title = "新的登录活动"
        content = f"检测到您的账户有新的登录活动：\n"
        content += f"时间：{now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if ip_address:
            content += f"IP地址：{ip_address}\n"
        
        if location:
            content += f"位置：{location}\n"
        
        content += "\n如果这不是您的操作，请立即修改密码并联系系统管理员。"
        
        return NotificationService.create_notification(
            user_id=user_id,
            title=title,
            content=content,
            type='system',
            priority='high',
            sender='安全系统',
            data={
                'ip_address': ip_address,
                'location': location,
                'login_time': now().isoformat()
            }
        )
    
    @staticmethod
    def send_maintenance_notification(title: str, content: str, start_time: datetime, end_time: datetime) -> List[Notification]:
        """
        发送系统维护通知
        
        Args:
            title: 通知标题
            content: 通知内容
            start_time: 维护开始时间
            end_time: 维护结束时间
        
        Returns:
            List[Notification]: 创建的通知列表
        """
        # 获取所有活跃用户
        users = User.query.filter_by(is_active=True).all()
        user_ids = [user.id for user in users]
        
        if not user_ids:
            return []
        
        return NotificationService.send_system_notification(
            user_ids=user_ids,
            title=title,
            content=content,
            type='system',
            priority='urgent',
            sender='系统管理员',
            data={
                'maintenance_start': start_time.isoformat(),
                'maintenance_end': end_time.isoformat()
            },
            expires_at=end_time + timedelta(hours=24)  # 维护结束后24小时过期
        )
    
    @staticmethod
    def cleanup_expired_notifications() -> int:
        """
        清理过期通知
        
        Returns:
            int: 清理的通知数量
        """
        current_time = now()
        
        expired_notifications = Notification.query.filter(
            Notification.expires_at < current_time
        ).all()
        
        count = len(expired_notifications)
        
        for notification in expired_notifications:
            db.session.delete(notification)
        
        db.session.commit()
        
        return count
    
    @staticmethod
    def get_notification_statistics(user_id: int = None) -> Dict:
        """
        获取通知统计信息
        
        Args:
            user_id: 用户ID，如果为None则获取全局统计
        
        Returns:
            Dict: 统计信息
        """
        from sqlalchemy import func
        
        base_query = Notification.query
        if user_id:
            base_query = base_query.filter_by(user_id=user_id)
        
        # 按类型统计
        type_stats = db.session.query(
            Notification.type,
            func.count(Notification.id).label('count'),
            func.sum(func.case((Notification.is_read == False, 1), else_=0)).label('unread')
        ).group_by(Notification.type)
        
        if user_id:
            type_stats = type_stats.filter_by(user_id=user_id)
        
        type_stats = type_stats.all()
        
        # 按优先级统计
        priority_stats = db.session.query(
            Notification.priority,
            func.count(Notification.id).label('count'),
            func.sum(func.case((Notification.is_read == False, 1), else_=0)).label('unread')
        ).group_by(Notification.priority)
        
        if user_id:
            priority_stats = priority_stats.filter_by(user_id=user_id)
        
        priority_stats = priority_stats.all()
        
        # 总体统计
        total_count = base_query.count()
        unread_count = base_query.filter_by(is_read=False).count()
        
        # 最近7天的通知数量
        week_ago = now() - timedelta(days=7)
        recent_count = base_query.filter(Notification.created_at >= week_ago).count()
        
        return {
            'total': total_count,
            'unread': unread_count,
            'recent_week': recent_count,
            'read_rate': ((total_count - unread_count) / total_count * 100) if total_count > 0 else 0,
            'type_stats': {
                type_name: {'total': count, 'unread': unread}
                for type_name, count, unread in type_stats
            },
            'priority_stats': {
                priority: {'total': count, 'unread': unread}
                for priority, count, unread in priority_stats
            }
        }
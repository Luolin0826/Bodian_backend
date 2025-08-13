# app/services/customer_service.py
from app.models import db, Customer
from datetime import datetime

class CustomerService:
    @staticmethod
    def update_status(customer_id, new_status):
        """更新客户状态"""
        customer = Customer.query.get(customer_id)
        if customer:
            customer.status = new_status
            if new_status == '已成交':
                customer.deal_date = datetime.now().date()
            customer.updated_at = datetime.utcnow()
            db.session.commit()
            return customer
        return None
    
    @staticmethod
    def batch_import(data_list):
        """批量导入客户"""
        customers = []
        for data in data_list:
            customer = Customer(**data)
            customers.append(customer)
        
        db.session.bulk_save_objects(customers)
        db.session.commit()
        return len(customers)
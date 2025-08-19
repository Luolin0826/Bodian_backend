# app/utils/employee_utils.py
from datetime import datetime
from sqlalchemy import func
from app.models import db, User, Department

class EmployeeUtils:
    @staticmethod
    def generate_employee_no(department_id, hire_date=None):
        """
        生成员工工号
        格式：{地区缩写}{年份}{月份}{日期}{序号}
        示例：SH202401001
        """
        if hire_date is None:
            hire_date = datetime.now().date()
        
        # 获取部门信息
        department = Department.query.get(department_id)
        if not department:
            raise ValueError("部门不存在")
        
        # 获取地区代码
        region_code = department.get_region_code()
        
        # 格式化日期部分
        year = hire_date.strftime('%Y')
        month = hire_date.strftime('%m')
        day = hire_date.strftime('%d')
        date_prefix = f"{region_code}{year}{month}{day}"
        
        # 查询当天已生成的最大序号
        pattern = f"{date_prefix}%"
        max_employee_no = db.session.query(func.max(User.employee_no)).filter(
            User.employee_no.like(pattern)
        ).scalar()
        
        if max_employee_no:
            # 提取序号部分并加1
            try:
                sequence = int(max_employee_no[-3:]) + 1
            except (ValueError, IndexError):
                sequence = 1
        else:
            sequence = 1
        
        # 生成新的工号
        employee_no = f"{date_prefix}{sequence:03d}"
        
        # 检查是否已存在（防止并发问题）
        existing = User.query.filter_by(employee_no=employee_no).first()
        if existing:
            # 如果存在，递归调用生成下一个号码
            return EmployeeUtils.generate_employee_no(department_id, hire_date)
        
        return employee_no
    
    @staticmethod
    def validate_employee_no(employee_no):
        """验证工号格式是否正确"""
        if not employee_no or len(employee_no) < 11:
            return False
        
        try:
            # 检查地区代码（2位字母）
            region_code = employee_no[:2]
            if not region_code.isalpha():
                return False
            
            # 检查年份（4位数字）
            year = employee_no[2:6]
            if not year.isdigit() or int(year) < 2020:
                return False
            
            # 检查月份（2位数字）
            month = employee_no[6:8]
            if not month.isdigit() or not (1 <= int(month) <= 12):
                return False
            
            # 检查日期（2位数字）
            day = employee_no[8:10]
            if not day.isdigit() or not (1 <= int(day) <= 31):
                return False
            
            # 检查序号（3位数字）
            sequence = employee_no[10:13]
            if not sequence.isdigit():
                return False
            
            return True
        except (ValueError, IndexError):
            return False
    
    @staticmethod
    def parse_employee_no(employee_no):
        """解析工号获取各部分信息"""
        if not EmployeeUtils.validate_employee_no(employee_no):
            return None
        
        return {
            'region_code': employee_no[:2],
            'year': employee_no[2:6],
            'month': employee_no[6:8],
            'day': employee_no[8:10],
            'sequence': employee_no[10:13],
            'hire_date': f"{employee_no[2:6]}-{employee_no[6:8]}-{employee_no[8:10]}"
        }
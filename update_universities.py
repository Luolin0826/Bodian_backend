#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大学数据更新脚本
从Excel文件读取数据并更新数据库中的universities表
"""

import pandas as pd
import sys
import os
sys.path.append('/workspace')

from app import create_app
from app.models.advance_batch import UniversityEmploymentInfo
from app.models import db

def read_excel_data(file_path):
    """读取Excel文件数据"""
    try:
        df = pd.read_excel(file_path)
        print(f"成功读取Excel文件，共 {len(df)} 行数据")
        print(f"列名: {list(df.columns)}")
        return df
    except Exception as e:
        print(f"读取Excel文件失败: {e}")
        return None

def get_database_data():
    """获取数据库中的现有数据"""
    try:
        universities = UniversityEmploymentInfo.query.filter_by(is_active=True).all()
        print(f"数据库中现有 {len(universities)} 条记录")
        return universities
    except Exception as e:
        print(f"获取数据库数据失败: {e}")
        return []

def compare_and_update(excel_df, db_universities):
    """对比并更新数据"""
    updated_count = 0
    created_count = 0
    
    # 将数据库记录转换为字典，便于查找
    db_dict = {}
    for uni in db_universities:
        # 使用大学名称作为主键进行匹配
        db_dict[uni.university_name] = uni
    
    print("\n开始对比数据...")
    
    for index, row in excel_df.iterrows():
        try:
            # 从Excel获取数据，处理NaN值
            excel_data = {}
            for col in excel_df.columns:
                value = row[col]
                # 处理pandas的NaN值
                if pd.isna(value):
                    excel_data[col] = None
                else:
                    excel_data[col] = str(value).strip() if isinstance(value, str) else value
            
            # 打印当前处理的记录 - 修正字段名
            university_name = excel_data.get('university_name') or excel_data.get('standard_name') or excel_data.get('院校名称') or excel_data.get('大学名称')
            if not university_name:
                print(f"第 {index+1} 行: 缺少大学名称，跳过")
                continue
                
            print(f"\n处理第 {index+1} 行: {university_name}")
            
            # 检查是否在数据库中存在
            if university_name in db_dict:
                # 存在，检查是否需要更新
                db_uni = db_dict[university_name]
                needs_update = False
                update_fields = []
                
                # 定义字段映射（Excel列名 -> 数据库字段名）
                field_mapping = {
                    'standard_name': 'university_name',  # Excel中的标准名称映射到数据库的大学名称
                    'university_name': 'university_name',
                    '院校名称': 'university_name', 
                    '大学名称': 'university_name',
                    'university_code': 'university_code',
                    '院校代码': 'university_code',
                    'location': 'address',  # 位置信息映射到地址
                    'employment_website': 'employment_website',
                    '就业网址': 'employment_website',
                    'career_center_name': 'career_center_name',
                    '就业中心名称': 'career_center_name',
                    'contact_person': 'contact_person',
                    '联系人': 'contact_person',
                    'contact_phone': 'contact_phone',
                    '联系电话': 'contact_phone',
                    'contact_email': 'contact_email',
                    '联系邮箱': 'contact_email',
                    'address': 'address',
                    '地址': 'address',
                    'office_hours': 'office_hours',
                    '办公时间': 'office_hours',
                    'remarks': 'remarks',
                    '备注': 'remarks',
                    # 新增字段，将Excel中的附加信息作为备注
                    'level': 'remarks',
                    'type': 'remarks', 
                    'power_feature': 'remarks'
                }
                
                # 检查每个字段是否需要更新
                for excel_col, db_field in field_mapping.items():
                    if excel_col in excel_data:
                        excel_value = excel_data[excel_col]
                        db_value = getattr(db_uni, db_field)
                        
                        # 比较值（处理None和空字符串）
                        excel_str = str(excel_value).strip() if excel_value else ""
                        db_str = str(db_value).strip() if db_value else ""
                        
                        if excel_str != db_str and excel_str:  # 只有Excel中有值且与数据库不同时才更新
                            setattr(db_uni, db_field, excel_value)
                            needs_update = True
                            update_fields.append(f"{db_field}: '{db_str}' -> '{excel_str}'")
                
                if needs_update:
                    print(f"  需要更新的字段:")
                    for field in update_fields:
                        print(f"    {field}")
                    updated_count += 1
                else:
                    print(f"  无需更新")
                    
            else:
                # 不存在，创建新记录
                print(f"  新记录，准备创建")
                new_uni = UniversityEmploymentInfo(
                    university_name=university_name,
                    university_code=excel_data.get('university_code') or excel_data.get('院校代码'),
                    employment_website=excel_data.get('employment_website') or excel_data.get('就业网址'),
                    career_center_name=excel_data.get('career_center_name') or excel_data.get('就业中心名称'),
                    contact_person=excel_data.get('contact_person') or excel_data.get('联系人'),
                    contact_phone=excel_data.get('contact_phone') or excel_data.get('联系电话'),
                    contact_email=excel_data.get('contact_email') or excel_data.get('联系邮箱'),
                    address=excel_data.get('address') or excel_data.get('地址'),
                    office_hours=excel_data.get('office_hours') or excel_data.get('办公时间'),
                    remarks=excel_data.get('remarks') or excel_data.get('备注'),
                    is_active=True
                )
                db.session.add(new_uni)
                created_count += 1
                
        except Exception as e:
            print(f"处理第 {index+1} 行时出错: {e}")
            continue
    
    return updated_count, created_count

def main():
    """主函数"""
    print("=== 大学数据更新工具 ===")
    
    # 创建Flask应用上下文
    app = create_app()
    with app.app_context():
        # 1. 读取Excel文件
        excel_file = '/workspace/unviimport.xlsx'
        if not os.path.exists(excel_file):
            print(f"Excel文件不存在: {excel_file}")
            return
        
        excel_df = read_excel_data(excel_file)
        if excel_df is None:
            return
        
        # 显示Excel文件的前几行
        print("\nExcel文件预览:")
        print(excel_df.head())
        
        # 2. 获取数据库数据
        db_universities = get_database_data()
        
        # 3. 对比和更新
        updated_count, created_count = compare_and_update(excel_df, db_universities)
        
        # 4. 提交更改
        try:
            db.session.commit()
            print(f"\n=== 更新完成 ===")
            print(f"更新了 {updated_count} 条记录")
            print(f"新建了 {created_count} 条记录")
        except Exception as e:
            db.session.rollback()
            print(f"提交数据库更改失败: {e}")

if __name__ == "__main__":
    main()
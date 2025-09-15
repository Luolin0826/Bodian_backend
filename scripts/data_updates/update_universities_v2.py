#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大学数据更新脚本 V2
从Excel文件读取数据并更新数据库中的universities表
"""

import pandas as pd
import sys
import os
sys.path.append('/workspace')

from app import create_app
from app.models.advance_batch import UniversityEmploymentInfo
from app.models import db

def main():
    """主函数"""
    print("=== 大学数据更新工具 V2 ===")
    
    # 创建Flask应用上下文
    app = create_app()
    with app.app_context():
        try:
            # 1. 读取Excel文件
            excel_file = '/workspace/unviimport.xlsx'
            df = pd.read_excel(excel_file)
            print(f"成功读取Excel文件，共 {len(df)} 行数据")
            
            # 2. 获取数据库中现有数据
            existing_universities = UniversityEmploymentInfo.query.filter_by(is_active=True).all()
            existing_dict = {uni.university_name: uni for uni in existing_universities}
            print(f"数据库中现有 {len(existing_universities)} 条记录")
            
            updated_count = 0
            created_count = 0
            
            print("\n开始处理数据...")
            
            for index, row in df.iterrows():
                # 获取Excel数据
                university_name = str(row['standard_name']).strip()
                university_code = str(row['university_code']).strip()
                level = str(row['level']).strip()
                type_info = str(row['type']).strip()  
                power_feature = str(row['power_feature']).strip()
                location = str(row['location']).strip()
                
                # 组合备注信息
                remarks_parts = []
                if level and level != 'nan':
                    remarks_parts.append(f"级别: {level}")
                if type_info and type_info != 'nan':
                    remarks_parts.append(f"类型: {type_info}")
                if power_feature and power_feature != 'nan':
                    remarks_parts.append(f"电力特色: {power_feature}")
                
                remarks = "; ".join(remarks_parts) if remarks_parts else ""
                
                print(f"\n处理第 {index+1} 行: {university_name}")
                
                if university_name in existing_dict:
                    # 更新现有记录
                    uni = existing_dict[university_name]
                    updated_fields = []
                    
                    # 检查university_code
                    if university_code and university_code != 'nan' and uni.university_code != university_code:
                        uni.university_code = university_code
                        updated_fields.append(f"university_code: '{uni.university_code}' -> '{university_code}'")
                    
                    # 检查address (location)
                    if location and location != 'nan' and uni.address != location:
                        uni.address = location
                        updated_fields.append(f"address: '{uni.address}' -> '{location}'")
                    
                    # 检查备注
                    if remarks and uni.remarks != remarks:
                        uni.remarks = remarks
                        updated_fields.append(f"remarks: '{uni.remarks}' -> '{remarks}'")
                    
                    if updated_fields:
                        print(f"  更新字段:")
                        for field in updated_fields:
                            print(f"    {field}")
                        updated_count += 1
                    else:
                        print(f"  无需更新")
                        
                else:
                    # 创建新记录
                    print(f"  新记录，准备创建")
                    new_uni = UniversityEmploymentInfo(
                        university_name=university_name,
                        university_code=university_code if university_code != 'nan' else None,
                        address=location if location != 'nan' else None,
                        remarks=remarks if remarks else None,
                        is_active=True
                    )
                    db.session.add(new_uni)
                    created_count += 1
            
            # 提交更改
            db.session.commit()
            print(f"\n=== 更新完成 ===")
            print(f"更新了 {updated_count} 条记录")
            print(f"新建了 {created_count} 条记录")
            print(f"总共处理了 {len(df)} 行数据")
            
        except Exception as e:
            db.session.rollback()
            print(f"处理失败: {e}")
            import traceback
            print(traceback.format_exc())

if __name__ == "__main__":
    main()
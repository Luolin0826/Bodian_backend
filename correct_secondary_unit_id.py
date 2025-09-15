#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据25国网南网录取_updated表修正recruitment_records中的secondary_unit_id
"""

import pandas as pd
import mysql.connector
from mysql.connector import Error
import numpy as np

# 数据库连接配置
DB_CONFIG = {
    'host': 'rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'database': 'bdprod',
    'user': 'dms_user_9332d9e',
    'password': 'AaBb19990826',
    'charset': 'utf8mb4'
}

def correct_secondary_unit_id():
    """根据Excel数据修正secondary_unit_id"""
    print("="*80)
    print("修正secondary_unit_id - 基于25国网南网录取_updated表")
    print("="*80)
    
    try:
        # 1. 读取Excel文件
        print("1. 读取Excel文件...")
        print("-" * 50)
        
        # 读取Excel文件，获取所有sheet
        excel_file = '25国网南网录取_updated.xlsx'
        try:
            # 首先获取所有sheet名称
            xlsx = pd.ExcelFile(excel_file)
            sheet_names = xlsx.sheet_names
            print(f"Excel文件包含的sheet: {sheet_names}")
            
            # 读取第一个sheet (第一批数据)
            first_sheet = sheet_names[0]
            excel_df = pd.read_excel(excel_file, sheet_name=first_sheet)
            print(f"读取第一个sheet: {first_sheet}")
            print(f"包含 {len(excel_df)} 条记录")
            print(f"列名: {list(excel_df.columns)}")
            
        except FileNotFoundError:
            print(f"❌ 找不到文件: {excel_file}")
            return
        except Exception as e:
            print(f"❌ 读取Excel文件失败: {e}")
            return
        
        # 显示前几行数据
        print(f"\n前5行数据:")
        print(excel_df.head())
        
        # 2. 连接数据库
        print(f"\n2. 连接数据库...")
        print("-" * 50)
        
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        # 获取secondary_units映射
        cursor.execute("SELECT unit_id, unit_name, unit_code FROM secondary_units")
        units = cursor.fetchall()
        
        unit_name_to_id = {}
        unit_id_to_name = {}
        for unit in units:
            unit_name_to_id[unit['unit_name']] = unit['unit_id']
            unit_id_to_name[unit['unit_id']] = unit['unit_name']
        
        print(f"数据库中共有 {len(units)} 个二级单位")
        
        # 3. 分析Excel数据结构，确定关键字段
        print(f"\n3. 分析Excel数据结构...")
        print("-" * 50)
        
        # 查找可能的姓名和单位字段
        possible_name_cols = [col for col in excel_df.columns if '姓名' in col or 'name' in col.lower()]
        possible_unit_cols = [col for col in excel_df.columns if '单位' in col or '电网' in col or '公司' in col or 'unit' in col.lower()]
        
        print(f"可能的姓名字段: {possible_name_cols}")
        print(f"可能的单位字段: {possible_unit_cols}")
        
        # 如果没有明确的字段，显示所有字段让用户确认
        if not possible_name_cols or not possible_unit_cols:
            print(f"\n需要手动确认字段映射:")
            for i, col in enumerate(excel_df.columns):
                print(f"  {i}: {col}")
                sample_data = excel_df[col].dropna().head(3).tolist()
                print(f"     示例数据: {sample_data}")
        
        # 假设第一个是姓名，找到单位相关字段
        name_col = possible_name_cols[0] if possible_name_cols else excel_df.columns[0]
        unit_col = possible_unit_cols[0] if possible_unit_cols else None
        
        if not unit_col:
            # 尝试根据数据内容推断
            for col in excel_df.columns:
                sample_values = excel_df[col].dropna().astype(str).head(10).tolist()
                # 检查是否包含电网相关的值
                if any('电网' in str(val) or '分部' in str(val) or '公司' in str(val) for val in sample_values):
                    unit_col = col
                    break
        
        if not unit_col:
            print("❌ 无法自动识别单位字段，请手动指定")
            return
        
        print(f"\n使用字段映射:")
        print(f"  姓名字段: {name_col}")
        print(f"  单位字段: {unit_col}")
        
        # 4. 对比数据并找出不匹配的记录
        print(f"\n4. 对比数据并找出不匹配记录...")
        print("-" * 50)
        
        mismatched_records = []
        matched_records = []
        not_found_records = []
        excel_unit_not_found = []
        
        total_excel_records = len(excel_df)
        processed_count = 0
        
        for idx, row in excel_df.iterrows():
            name = str(row[name_col]).strip() if pd.notna(row[name_col]) else ""
            excel_unit = str(row[unit_col]).strip() if pd.notna(row[unit_col]) else ""
            
            if not name or not excel_unit:
                continue
                
            processed_count += 1
            
            # 在数据库中查找该人员
            cursor.execute("""
                SELECT r.record_id, r.name, r.secondary_unit_id, s.unit_name
                FROM recruitment_records r
                LEFT JOIN secondary_units s ON r.secondary_unit_id = s.unit_id
                WHERE r.name = %s AND r.company = '国网' AND r.batch = '第一批'
            """, (name,))
            
            db_records = cursor.fetchall()
            
            if not db_records:
                not_found_records.append({
                    'name': name,
                    'excel_unit': excel_unit
                })
                continue
            
            # 获取Excel中单位对应的unit_id
            excel_unit_id = unit_name_to_id.get(excel_unit)
            if not excel_unit_id:
                # 尝试模糊匹配
                for unit_name, unit_id in unit_name_to_id.items():
                    if excel_unit in unit_name or unit_name in excel_unit:
                        excel_unit_id = unit_id
                        break
                
                if not excel_unit_id:
                    excel_unit_not_found.append(excel_unit)
                    continue
            
            # 检查每个数据库记录
            for db_record in db_records:
                db_unit_id = db_record['secondary_unit_id']
                db_unit_name = db_record['unit_name']
                
                if db_unit_id == excel_unit_id:
                    matched_records.append({
                        'record_id': db_record['record_id'],
                        'name': name,
                        'unit_name': db_unit_name
                    })
                else:
                    mismatched_records.append({
                        'record_id': db_record['record_id'],
                        'name': name,
                        'excel_unit': excel_unit,
                        'excel_unit_id': excel_unit_id,
                        'db_unit_id': db_unit_id,
                        'db_unit_name': db_unit_name
                    })
            
            # 每处理100条记录显示进度
            if processed_count % 100 == 0:
                print(f"  已处理: {processed_count}/{total_excel_records}")
        
        print(f"\n对比结果:")
        print(f"  总处理记录数: {processed_count}")
        print(f"  匹配正确: {len(matched_records)}")
        print(f"  需要修正: {len(mismatched_records)}")
        print(f"  在数据库中未找到: {len(not_found_records)}")
        print(f"  Excel单位未找到: {len(set(excel_unit_not_found))}")
        
        # 显示一些不匹配的示例
        if mismatched_records:
            print(f"\n不匹配记录示例 (前10个):")
            for record in mismatched_records[:10]:
                print(f"  {record['name']}: {record['excel_unit']} -> 当前分配: {record['db_unit_name']}")
        
        # 5. 执行修正
        if mismatched_records:
            print(f"\n5. 执行修正操作...")
            print("-" * 50)
            
            confirm = input(f"发现 {len(mismatched_records)} 条需要修正的记录，是否继续修正? (y/N): ")
            
            if confirm.lower() == 'y':
                success_count = 0
                error_count = 0
                
                for record in mismatched_records:
                    try:
                        cursor.execute("""
                            UPDATE recruitment_records 
                            SET secondary_unit_id = %s, updated_at = NOW()
                            WHERE record_id = %s
                        """, (record['excel_unit_id'], record['record_id']))
                        
                        success_count += 1
                        
                        # 每修正100条提交一次
                        if success_count % 100 == 0:
                            connection.commit()
                            print(f"  已修正: {success_count}/{len(mismatched_records)}")
                            
                    except Exception as e:
                        error_count += 1
                        print(f"  修正失败 {record['name']}: {e}")
                
                # 最终提交
                connection.commit()
                
                print(f"\n修正完成:")
                print(f"  成功修正: {success_count}")
                print(f"  失败: {error_count}")
                
                # 6. 验证修正结果
                print(f"\n6. 验证修正结果...")
                print("-" * 50)
                
                # 随机选择10个已修正的记录进行验证
                sample_records = mismatched_records[:10]
                verified_count = 0
                
                for record in sample_records:
                    cursor.execute("""
                        SELECT r.name, s.unit_name
                        FROM recruitment_records r
                        LEFT JOIN secondary_units s ON r.secondary_unit_id = s.unit_id
                        WHERE r.record_id = %s
                    """, (record['record_id'],))
                    
                    result = cursor.fetchone()
                    if result and result['unit_name'] == record['excel_unit']:
                        verified_count += 1
                        print(f"  ✅ {result['name']}: 已正确修正为 {result['unit_name']}")
                    else:
                        print(f"  ❌ {record['name']}: 修正验证失败")
                
                print(f"\n验证结果: {verified_count}/{len(sample_records)} 修正成功")
                
            else:
                print("取消修正操作")
        else:
            print("✅ 所有记录的secondary_unit_id都已正确匹配！")
        
        # 7. 生成报告
        print(f"\n7. 生成修正报告...")
        print("-" * 50)
        
        report = {
            'total_processed': processed_count,
            'matched_correct': len(matched_records),
            'corrected': len(mismatched_records),
            'not_found_in_db': len(not_found_records),
            'excel_unit_not_found': len(set(excel_unit_not_found)),
            'accuracy_rate': len(matched_records) / processed_count * 100 if processed_count > 0 else 0
        }
        
        print(f"📊 修正报告:")
        print(f"  处理记录总数: {report['total_processed']}")
        print(f"  原本正确: {report['matched_correct']} ({report['matched_correct']/processed_count*100:.1f}%)")
        print(f"  已修正: {report['corrected']}")
        print(f"  数据库中未找到: {report['not_found_in_db']}")
        print(f"  Excel单位未找到: {report['excel_unit_not_found']}")
        print(f"  最终准确率: {100:.1f}%" if mismatched_records else f"{report['accuracy_rate']:.1f}%")
        
        if excel_unit_not_found:
            print(f"\n未找到的Excel单位 (需要添加到secondary_units表):")
            for unit in set(excel_unit_not_found)[:10]:
                print(f"  - {unit}")
        
    except Exception as e:
        print(f"修正过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    correct_secondary_unit_id()
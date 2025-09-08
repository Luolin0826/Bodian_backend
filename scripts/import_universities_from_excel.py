#!/usr/bin/env python3
"""导入工作人员修改后的universities Excel数据"""

import mysql.connector
import pandas as pd
from datetime import datetime
import sys
import os

# 数据库配置
db_config = {
    'host': 'rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'database': 'bdprod',
    'user': 'dms_user_9332d9e',
    'password': 'AaBb19990826',
    'charset': 'utf8mb4',
    'autocommit': True,
    'use_unicode': True,
    'consume_results': True
}

def import_universities_from_excel(excel_file_path, preview_only=True):
    """
    导入Excel中修改后的大学数据
    
    Args:
        excel_file_path: Excel文件路径
        preview_only: True=仅预览，False=实际更新数据库
    """
    try:
        print(f"📂 读取Excel文件: {excel_file_path}")
        
        # 读取Excel文件
        if not os.path.exists(excel_file_path):
            print(f"❌ 文件不存在: {excel_file_path}")
            return False
            
        df = pd.read_excel(excel_file_path, sheet_name='大学数据')
        
        print(f"📊 读取到 {len(df)} 条记录")
        
        # 筛选出已修改的记录
        # 检查"已修改标记"列是否有值（是/Y/yes等）
        modified_mask = df['已修改标记'].notna() & (df['已修改标记'].astype(str).str.strip() != '')
        modified_records = df[modified_mask].copy()
        
        if len(modified_records) == 0:
            print("ℹ️  未发现任何标记为已修改的记录")
            return True
            
        print(f"🔍 发现 {len(modified_records)} 条标记为已修改的记录")
        
        # 显示修改预览
        print("\n=== 修改预览 ===")
        for idx, row in modified_records.iterrows():
            print(f"\n📝 记录 {idx + 1}:")
            print(f"   ID: {row['university_id']}")
            print(f"   院校代码: {row['university_code']}")
            print(f"   标准名称: {row['standard_name']}")
            print(f"   层次: {row['level']}")
            print(f"   类型: {row['type']}")
            print(f"   电力特色: {row['power_feature']}")
            print(f"   属地: {row['location']}")
            print(f"   修改标记: {row['已修改标记']}")
            print(f"   修改说明: {row['修改说明']}")
            print(f"   修改时间: {row['修改时间']}")
        
        if preview_only:
            print(f"\n👀 预览模式：发现 {len(modified_records)} 条需要更新的记录")
            print("💡 如需实际更新数据库，请使用 preview_only=False 参数")
            return True
        
        # 实际更新数据库
        print(f"\n🔄 开始更新数据库...")
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        updated_count = 0
        error_count = 0
        
        for idx, row in modified_records.iterrows():
            try:
                # 准备更新SQL
                update_sql = """
                UPDATE universities 
                SET university_code = %s,
                    standard_name = %s,
                    level = %s,
                    type = %s,
                    power_feature = %s,
                    location = %s,
                    updated_at = NOW()
                WHERE university_id = %s
                """
                
                # 处理None值
                values = []
                for field in ['university_code', 'standard_name', 'level', 'type', 'power_feature', 'location']:
                    value = row[field]
                    if pd.isna(value) or value == '' or str(value).lower() == 'none':
                        values.append(None)
                    else:
                        values.append(str(value).strip())
                
                values.append(int(row['university_id']))
                
                cursor.execute(update_sql, values)
                updated_count += 1
                
                print(f"✅ 更新成功: ID {row['university_id']} - {row['standard_name']}")
                
            except Exception as e:
                error_count += 1
                print(f"❌ 更新失败: ID {row['university_id']} - {str(e)}")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print(f"\n📊 更新完成:")
        print(f"   ✅ 成功更新: {updated_count} 条")
        print(f"   ❌ 更新失败: {error_count} 条")
        
        # 生成更新日志
        log_filename = f"import_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(log_filename, 'w', encoding='utf-8') as f:
            f.write(f"Universities数据导入日志\n")
            f.write(f"导入时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"源文件: {excel_file_path}\n")
            f.write(f"总记录数: {len(df)}\n")
            f.write(f"修改记录数: {len(modified_records)}\n")
            f.write(f"成功更新: {updated_count}\n")
            f.write(f"更新失败: {error_count}\n\n")
            
            f.write("=== 修改记录详情 ===\n")
            for idx, row in modified_records.iterrows():
                f.write(f"\nID: {row['university_id']}\n")
                f.write(f"标准名称: {row['standard_name']}\n")
                f.write(f"修改说明: {row['修改说明']}\n")
                f.write(f"修改时间: {row['修改时间']}\n")
        
        print(f"📝 导入日志已保存: {log_filename}")
        
        return updated_count > 0
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print(f"  python3 {sys.argv[0]} <excel文件路径> [--execute]")
        print("")
        print("参数说明:")
        print("  excel文件路径: 工作人员修改后的Excel文件")
        print("  --execute: 实际执行更新（默认为预览模式）")
        print("")
        print("示例:")
        print(f"  python3 {sys.argv[0]} universities_export_20250907_174216.xlsx")
        print(f"  python3 {sys.argv[0]} universities_export_20250907_174216.xlsx --execute")
        return
    
    excel_file = sys.argv[1]
    preview_only = '--execute' not in sys.argv
    
    if preview_only:
        print("🔍 运行在预览模式，不会实际修改数据库")
    else:
        print("⚠️  执行模式：将实际修改数据库")
        confirm = input("确认执行吗？(y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ 操作已取消")
            return
    
    success = import_universities_from_excel(excel_file, preview_only)
    
    if success:
        print("✅ 操作完成")
    else:
        print("❌ 操作失败")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对照数据库universities中level为独立学院的学校与公办院校表.xlsx，
将能找到的学校标记为普通本科
"""

import pandas as pd
import pymysql
from datetime import datetime
import os

def read_public_colleges_excel():
    """读取公办院校表.xlsx文件"""
    try:
        excel_path = '/workspace/公办院校表.xlsx'
        
        if not os.path.exists(excel_path):
            print(f"❌ 文件不存在: {excel_path}")
            return set()
        
        # 尝试读取Excel文件的所有sheet
        excel_file = pd.ExcelFile(excel_path)
        print(f"✅ 成功打开公办院校表.xlsx")
        print(f"   包含工作表: {excel_file.sheet_names}")
        
        public_colleges = set()
        
        # 读取所有工作表
        for sheet_name in excel_file.sheet_names:
            print(f"\n📋 读取工作表: {sheet_name}")
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            print(f"   数据形状: {df.shape}")
            print(f"   列名: {list(df.columns)}")
            
            # 尝试找到包含学校名称的列
            possible_name_columns = ['学校名称', '院校名称', '学校', '院校', 'name', 'school_name', 'university_name']
            name_column = None
            
            for col in df.columns:
                if any(keyword in str(col).lower() for keyword in ['学校', '院校', 'name', 'school', 'university']):
                    name_column = col
                    break
            
            if name_column:
                print(f"   使用列: {name_column}")
                # 清理和标准化学校名称
                school_names = df[name_column].dropna().astype(str).str.strip()
                valid_names = school_names[school_names != ''].tolist()
                public_colleges.update(valid_names)
                print(f"   添加学校: {len(valid_names)} 所")
            else:
                print(f"   ⚠️ 未找到学校名称列，显示前几行数据:")
                print(df.head())
        
        print(f"\n📊 总计公办院校: {len(public_colleges)} 所")
        return public_colleges
        
    except Exception as e:
        print(f"❌ 读取公办院校表.xlsx失败: {e}")
        return set()

def get_independent_colleges_from_db():
    """从数据库获取标记为独立学院的学校"""
    try:
        conn = pymysql.connect(
            host='rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
            port=3306,
            user='dms_user_9332d9e',
            password='AaBb19990826',
            database='bdprod',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # 查询所有独立学院
            query = """
            SELECT university_id, standard_name, original_name, level, type
            FROM universities 
            WHERE level = '独立学院'
            ORDER BY standard_name
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            print(f"✅ 数据库中独立学院数量: {len(results)}")
            return results
            
    except Exception as e:
        print(f"❌ 查询数据库失败: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def find_matches(independent_colleges, public_colleges):
    """找出独立学院中与公办院校表匹配的学校"""
    matches = []
    
    print(f"\n🔍 开始匹配独立学院与公办院校表...")
    
    for college in independent_colleges:
        standard_name = college['standard_name']
        original_name = college['original_name']
        
        # 多种匹配策略
        found_match = False
        match_type = None
        
        # 1. 精确匹配标准名称
        if standard_name in public_colleges:
            found_match = True
            match_type = "标准名称精确匹配"
        
        # 2. 精确匹配原始名称
        elif original_name and original_name in public_colleges:
            found_match = True
            match_type = "原始名称精确匹配"
        
        # 3. 模糊匹配：去除常见后缀
        elif not found_match:
            # 去除独立学院相关后缀
            clean_standard = standard_name
            for suffix in ['独立学院', '学院', '大学']:
                if clean_standard.endswith(suffix):
                    clean_standard = clean_standard[:-len(suffix)]
                    break
            
            # 在公办院校中寻找包含此名称的学校
            for public_college in public_colleges:
                if clean_standard and (clean_standard in public_college or public_college in clean_standard):
                    found_match = True
                    match_type = f"模糊匹配 ({clean_standard} <-> {public_college})"
                    break
        
        if found_match:
            matches.append({
                'college': college,
                'match_type': match_type
            })
            print(f"✅ 找到匹配: {standard_name} - {match_type}")
    
    print(f"\n📊 匹配结果: {len(matches)}/{len(independent_colleges)} 所独立学院在公办院校表中找到")
    return matches

def update_college_levels(matches):
    """更新匹配的学校层次为普通本科"""
    if not matches:
        print("⚠️ 没有找到需要更新的学校")
        return
    
    try:
        conn = pymysql.connect(
            host='rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
            port=3306,
            user='dms_user_9332d9e',
            password='AaBb19990826',
            database='bdprod',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        updated_count = 0
        update_log = []
        
        with conn.cursor() as cursor:
            for match in matches:
                college = match['college']
                university_id = college['university_id']
                old_level = college['level']
                new_level = '普通本科'
                
                try:
                    # 更新学校层次
                    update_query = """
                    UPDATE universities 
                    SET level = %s 
                    WHERE university_id = %s
                    """
                    
                    cursor.execute(update_query, (new_level, university_id))
                    
                    if cursor.rowcount > 0:
                        updated_count += 1
                        log_entry = {
                            'university_id': university_id,
                            'school_name': college['standard_name'],
                            'old_level': old_level,
                            'new_level': new_level,
                            'match_type': match['match_type']
                        }
                        update_log.append(log_entry)
                        print(f"✅ 已更新: {college['standard_name']} ({old_level} → {new_level})")
                    
                except Exception as e:
                    print(f"❌ 更新失败 {college['standard_name']}: {e}")
            
            # 提交事务
            conn.commit()
            print(f"\n✅ 批量更新完成: {updated_count} 所学校")
            
            return update_log
            
    except Exception as e:
        print(f"❌ 数据库更新失败: {e}")
        if 'conn' in locals():
            conn.rollback()
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def generate_report(update_log):
    """生成更新报告"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f'/workspace/独立学院修正报告_{timestamp}.txt'
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("独立学院层次修正报告\n")
            f.write("=" * 50 + "\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"修正学校数量: {len(update_log)}\n\n")
            
            if update_log:
                f.write("修正详情:\n")
                f.write("-" * 30 + "\n")
                
                for i, log in enumerate(update_log, 1):
                    f.write(f"{i}. {log['school_name']}\n")
                    f.write(f"   ID: {log['university_id']}\n")
                    f.write(f"   变更: {log['old_level']} → {log['new_level']}\n")
                    f.write(f"   匹配方式: {log['match_type']}\n\n")
            
            f.write("\n修正说明:\n")
            f.write("- 对照公办院校表.xlsx，将数据库中错误标记为'独立学院'的公办学校修正为'普通本科'\n")
            f.write("- 匹配策略包括精确匹配和模糊匹配\n")
            f.write("- 所有修改已直接应用到数据库\n")
        
        print(f"✅ 报告已生成: {report_file}")
        return report_file
        
    except Exception as e:
        print(f"❌ 生成报告失败: {e}")
        return None

def main():
    """主函数"""
    print("独立学院层次修正工具")
    print("=" * 50)
    
    # 1. 读取公办院校表
    public_colleges = read_public_colleges_excel()
    if not public_colleges:
        print("❌ 无法读取公办院校表，程序退出")
        return
    
    # 2. 查询数据库中的独立学院
    independent_colleges = get_independent_colleges_from_db()
    if not independent_colleges:
        print("❌ 数据库中没有找到独立学院，程序退出")
        return
    
    # 3. 匹配独立学院与公办院校
    matches = find_matches(independent_colleges, public_colleges)
    
    # 4. 更新匹配的学校
    if matches:
        print(f"\n📋 准备更新 {len(matches)} 所学校的层次为'普通本科'")
        print("✅ 自动执行更新...")
        
        update_log = update_college_levels(matches)
        
        # 5. 生成报告
        if update_log:
            generate_report(update_log)
    else:
        print("⚠️ 没有找到需要修正的学校")

if __name__ == '__main__':
    main()
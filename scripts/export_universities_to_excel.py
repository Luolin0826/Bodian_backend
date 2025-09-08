#!/usr/bin/env python3
"""导出universities表数据到Excel，包含修改标记功能"""

import mysql.connector
import pandas as pd
from datetime import datetime
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

def export_universities_to_excel():
    """导出大学数据到Excel文件"""
    try:
        print("🔄 连接数据库...")
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # 查询标准化的大学数据（is_standardized=1）
        print("📊 查询标准化大学数据...")
        query = """
        SELECT 
            university_id,
            university_code,
            standard_name,
            level,
            type,
            power_feature,
            location
        FROM universities 
        WHERE is_standardized = 1
        ORDER BY university_id
        """
        
        cursor.execute(query)
        data = cursor.fetchall()
        
        print(f"📋 获取到 {len(data)} 条记录")
        
        # 转换为DataFrame
        df = pd.DataFrame(data)
        
        # 添加修改标记列
        df['已修改标记'] = ''  # 空值表示未修改
        df['修改说明'] = ''   # 工作人员可以填写修改说明
        df['修改时间'] = ''   # 工作人员可以填写修改时间
        
        # 重新排列列的顺序，把修改相关列放在最前面
        columns_order = [
            '已修改标记', '修改说明', '修改时间',
            'university_id', 'university_code', 'standard_name', 
            'level', 'type', 'power_feature', 'location'
        ]
        df = df[columns_order]
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"universities_export_{timestamp}.xlsx"
        filepath = os.path.join('/workspace', filename)
        
        print("📝 创建Excel文件...")
        
        # 创建Excel写入器
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # 写入数据表
            df.to_excel(writer, sheet_name='大学数据', index=False)
            
            # 创建说明表
            instructions = pd.DataFrame({
                '使用说明': [
                    '1. 这是大学数据人工核对表，请仔细核对每一条记录',
                    '2. 如果需要修改数据，请在对应字段直接修改',
                    '3. 修改后请在"已修改标记"列填写"是"或"Y"',
                    '4. 在"修改说明"列填写修改的内容和原因',
                    '5. 在"修改时间"列填写修改的日期',
                    '6. 核对完成后请将文件发回给系统管理员',
                    '',
                    '字段说明:',
                    'university_id: 大学ID（请勿修改）',
                    'university_code: 院校代码',
                    'standard_name: 标准院校名称',
                    'level: 院校层次（985工程/211工程/双一流/普通本科等）',
                    'type: 院校类型（理工类/综合类/师范类等）',
                    'power_feature: 电力特色（电力特色强校/工程类相关/非电力类等）',
                    'location: 院校属地',
                    '',
                    f'导出时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                    f'总记录数: {len(data)} 条',
                    '数据来源: universities 表'
                ]
            })
            instructions.to_excel(writer, sheet_name='使用说明', index=False)
            
            # 创建数据统计表
            stats_data = []
            
            # 统计层次分布
            level_stats = df['level'].value_counts()
            stats_data.append(['院校层次分布', '', ''])
            for level, count in level_stats.items():
                stats_data.append([level, count, f'{count/len(df)*100:.1f}%'])
            
            stats_data.append(['', '', ''])  # 空行
            
            # 统计类型分布
            type_stats = df['type'].value_counts()
            stats_data.append(['院校类型分布', '', ''])
            for type_name, count in type_stats.items():
                stats_data.append([type_name, count, f'{count/len(df)*100:.1f}%'])
            
            stats_df = pd.DataFrame(stats_data, columns=['分类', '数量', '占比'])
            stats_df.to_excel(writer, sheet_name='数据统计', index=False)
        
        print(f"✅ Excel文件已创建: {filename}")
        print(f"📁 文件路径: {filepath}")
        print(f"📊 包含数据: {len(data)} 条记录")
        
        cursor.close()
        connection.close()
        
        return filepath
        
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        return None

if __name__ == "__main__":
    export_universities_to_excel()
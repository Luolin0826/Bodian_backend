#!/usr/bin/env python3
"""测试大学数据修改工作流程"""

import pandas as pd
import os
from datetime import datetime

def create_test_modified_excel():
    """创建一个测试用的修改后Excel文件"""
    
    # 读取原始导出的Excel
    original_files = [f for f in os.listdir('/workspace') if f.startswith('universities_export_') and f.endswith('.xlsx')]
    
    if not original_files:
        print("❌ 未找到原始导出的Excel文件")
        return None
        
    original_file = sorted(original_files)[-1]  # 获取最新的文件
    print(f"📂 使用原始文件: {original_file}")
    
    # 读取原始数据
    df = pd.read_excel(f'/workspace/{original_file}', sheet_name='大学数据')
    
    # 模拟工作人员的修改
    test_modifications = [
        {
            'row_idx': 0,  # 第一条记录
            'changes': {
                'standard_name': '东南大学(修改测试)',
                'level': '985工程+',
                '已修改标记': '是',
                '修改说明': '测试修改：调整名称和层次',
                '修改时间': '2025-09-07'
            }
        },
        {
            'row_idx': 1,  # 第二条记录
            'changes': {
                'power_feature': '电力特色强校（更新）',
                'location': '河北保定',
                '已修改标记': 'Y',
                '修改说明': '更新电力特色描述和地址信息',
                '修改时间': '2025-09-07'
            }
        },
        {
            'row_idx': 5,  # 第六条记录
            'changes': {
                'type': '综合类（更新）',
                '已修改标记': 'yes',
                '修改说明': '修正院校类型',
                '修改时间': '2025-09-07'
            }
        }
    ]
    
    # 应用修改
    for modification in test_modifications:
        row_idx = modification['row_idx']
        changes = modification['changes']
        
        for column, new_value in changes.items():
            df.at[row_idx, column] = new_value
            
        print(f"✏️  修改记录 {row_idx + 1}: {df.at[row_idx, 'standard_name']}")
    
    # 保存修改后的文件
    test_filename = f"universities_modified_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    test_filepath = f'/workspace/{test_filename}'
    
    with pd.ExcelWriter(test_filepath, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='大学数据', index=False)
        
        # 添加修改说明表
        modification_log = pd.DataFrame([
            ['测试修改日志', ''],
            ['修改时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['修改人员', '系统测试'],
            ['修改记录数', len(test_modifications)],
            ['', ''],
            ['修改详情', ''],
        ] + [
            [f'记录{i+1}', f"ID: {df.at[mod['row_idx'], 'university_id']}, 名称: {df.at[mod['row_idx'], 'standard_name']}, 说明: {mod['changes']['修改说明']}"]
            for i, mod in enumerate(test_modifications)
        ], columns=['项目', '内容'])
        
        modification_log.to_excel(writer, sheet_name='修改日志', index=False)
    
    print(f"✅ 测试修改文件已创建: {test_filename}")
    print(f"📝 包含 {len(test_modifications)} 条修改记录")
    
    return test_filepath

if __name__ == "__main__":
    create_test_modified_excel()
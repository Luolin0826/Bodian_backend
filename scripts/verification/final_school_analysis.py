#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终精确版学校level分类分析
重点标记真正存疑的数据
"""

import pandas as pd
import re
from typing import List, Dict

def load_and_analyze():
    """加载数据并进行精确分析"""
    df = pd.read_excel('/workspace/学校.xlsx')
    
    # 真正的独立学院特征（排除海外院校）
    definitely_independent = []  # 明确的独立学院
    likely_wrong_public = []    # 可能错误标记为普通本科的
    likely_wrong_independent = [] # 可能错误标记为独立学院的
    need_verify = []           # 需要人工核实的
    
    for index, row in df.iterrows():
        school_name = str(row.get('standard_name', ''))
        current_level = str(row.get('level', ''))
        
        if pd.isna(school_name) or school_name == 'nan':
            continue
        
        # 跳过海外高校
        if current_level == '海外高校':
            continue
            
        # 1. 明确的独立学院（某某大学某某学院，且不是海外）
        if re.match(r'.+大学.+学院$', school_name) and '海外' not in current_level:
            if current_level != '独立学院':
                definitely_independent.append({
                    'school_name': school_name,
                    'current_level': current_level,
                    'suggested_level': '独立学院',
                    'confidence': '极高',
                    'reason': '典型独立学院命名格式（某某大学某某学院），应为民办独立学院'
                })
        
        # 2. 可能错误标记为独立学院的公办院校
        elif current_level == '独立学院' and school_name.endswith('学院'):
            # 检查是否有明确的公办特征
            public_indicators = ['师范', '医学', '理工', '科技', '财经', '政法', '外国语', '体育', '艺术', '音乐', '美术']
            has_public_feature = any(indicator in school_name for indicator in public_indicators)
            
            if has_public_feature or school_name in [
                '北京第二外国语学院', '外交学院', '国际关系学院',
                '中央音乐学院', '中央美术学院', '中央戏剧学院',
                '上海海关学院', '中国劳动关系学院', '中华女子学院'
            ]:
                likely_wrong_independent.append({
                    'school_name': school_name,
                    'current_level': current_level,
                    'suggested_level': '普通本科',
                    'confidence': '高',
                    'reason': f'具有公办院校特征，应为公办普通本科而非独立学院'
                })
        
        # 3. 以学院结尾但当前为普通本科，需要核实的
        elif school_name.endswith('学院') and current_level == '普通本科':
            # 排除明确的公办院校
            public_indicators = ['师范', '医学', '理工', '科技', '财经', '政法', '外国语', '体育', '艺术', '音乐', '美术', '交通', '电力', '石油']
            has_public_feature = any(indicator in school_name for indicator in public_indicators)
            
            if not has_public_feature and school_name not in [
                '北京第二外国语学院', '外交学院', '国际关系学院', 
                '中央音乐学院', '中央美术学院', '北京国家会计学院'
            ]:
                need_verify.append({
                    'school_name': school_name,
                    'current_level': current_level,
                    'suggested_level': '需核实',
                    'confidence': '中等',
                    'reason': f'以"学院"结尾且缺乏明显公办特征，建议核实是否为公办还是民办'
                })
    
    return {
        'definitely_independent': definitely_independent,
        'likely_wrong_independent': likely_wrong_independent, 
        'need_verify': need_verify[:50]  # 只显示前50个需要核实的
    }

def generate_summary_report(analysis_results):
    """生成汇总报告"""
    print("=== 学校Level分类问题分析汇总 ===\n")
    
    # 1. 明确需要修改为独立学院的
    definitely_independent = analysis_results['definitely_independent']
    if definitely_independent:
        print(f"🔴 明确应修改为'独立学院'的院校 ({len(definitely_independent)}所):")
        print("这些院校采用'某某大学某某学院'命名格式，是典型的民办独立学院\n")
        
        for i, item in enumerate(definitely_independent[:20], 1):  # 显示前20个
            print(f"{i:2d}. {item['school_name']}")
            print(f"    当前分类: {item['current_level']} → 建议: {item['suggested_level']}")
            print()
        
        if len(definitely_independent) > 20:
            print(f"... 还有{len(definitely_independent) - 20}所类似院校\n")
    
    # 2. 可能错误标记为独立学院的公办院校
    likely_wrong_independent = analysis_results['likely_wrong_independent']
    if likely_wrong_independent:
        print(f"🟡 可能错误标记为'独立学院'的公办院校 ({len(likely_wrong_independent)}所):")
        print("这些院校具有公办特征，可能应该是普通本科\n")
        
        for i, item in enumerate(likely_wrong_independent, 1):
            print(f"{i:2d}. {item['school_name']}")
            print(f"    当前分类: {item['current_level']} → 建议: {item['suggested_level']}")
            print(f"    原因: {item['reason']}")
            print()
    
    # 3. 需要人工核实的
    need_verify = analysis_results['need_verify']
    if need_verify:
        print(f"⚠️  需要人工核实的院校 ({len(need_verify)}所，显示前20所):")
        print("这些院校以'学院'结尾但缺乏明显的公办/民办特征\n")
        
        for i, item in enumerate(need_verify[:20], 1):
            print(f"{i:2d}. {item['school_name']} (当前: {item['current_level']})")
        
        print(f"\n建议核实方法:")
        print("1. 查看学校官网 - 查看办学性质说明")
        print("2. 查看教育部门网站 - 确认是否为公办")
        print("3. 查看学费标准 - 民办院校学费通常较高")
    
    # 保存详细数据到Excel
    all_issues = []
    for item in definitely_independent:
        all_issues.append({**item, 'issue_type': '明确独立学院'})
    for item in likely_wrong_independent:
        all_issues.append({**item, 'issue_type': '可能误判为独立学院'})
    for item in need_verify:
        all_issues.append({**item, 'issue_type': '需人工核实'})
    
    if all_issues:
        df_issues = pd.DataFrame(all_issues)
        df_issues.to_excel('/workspace/学校分类问题汇总.xlsx', index=False, engine='openpyxl')
        print(f"\n📊 详细数据已保存到: /workspace/学校分类问题汇总.xlsx")
        print(f"   总计发现 {len(all_issues)} 个需要关注的分类问题")

def main():
    results = load_and_analyze()
    generate_summary_report(results)

if __name__ == '__main__':
    main()
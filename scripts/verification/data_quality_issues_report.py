#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大学数据质量问题分析和修正建议
"""

import pandas as pd
import sys
sys.path.append('/workspace')

from app import create_app
from app.models.advance_batch import UniversityEmploymentInfo
from app.models import db

def identify_data_issues():
    """识别数据质量问题"""
    print("=== 大学数据质量问题分析 ===")
    
    app = create_app()
    with app.app_context():
        try:
            universities = UniversityEmploymentInfo.query.filter_by(is_active=True).all()
            print(f"正在分析 {len(universities)} 条大学记录...")
            
            issues = []
            
            # 1. 检查华北电力大学缺失备注问题
            hbdl_main = UniversityEmploymentInfo.query.filter_by(
                university_name="华北电力大学", is_active=True
            ).first()
            
            if hbdl_main and not hbdl_main.remarks:
                issues.append({
                    'type': '关键院校缺失备注',
                    'university': '华北电力大学',
                    'issue': '华北电力大学作为中国电力行业顶级院校，缺失层次和电力特色标识',
                    'suggestion': '应标记为"级别: 211工程; 类型: 理工类; 电力特色: 电力部直属"',
                    'severity': '高'
                })
            
            # 2. 检查985院校的电力特色分类是否合理
            suspicious_985_power = []
            for uni in universities:
                if uni.remarks and '985工程' in uni.remarks and '电力特色强校' in uni.remarks:
                    # 检查是否真的是电力特色强校
                    non_power_985 = ['北京大学', '复旦大学', '中国人民大学', '南开大学', '南京大学']
                    if any(name in uni.university_name for name in non_power_985):
                        suspicious_985_power.append(uni.university_name)
            
            for uni_name in suspicious_985_power:
                issues.append({
                    'type': '985院校电力特色分类争议',
                    'university': uni_name,
                    'issue': '该985院校被标记为电力特色强校，但主要不是以电力学科见长',
                    'suggestion': '建议重新评估是否应标记为电力特色强校',
                    'severity': '中'
                })
            
            # 3. 检查电力院校层次不一致问题
            power_universities_levels = []
            power_unis = ['华北电力大学', '上海电力大学', '东北电力大学', '南京工程学院', '沈阳工程学院']
            
            for power_uni in power_unis:
                uni = UniversityEmploymentInfo.query.filter(
                    UniversityEmploymentInfo.university_name.like(f'%{power_uni}%'),
                    UniversityEmploymentInfo.is_active == True
                ).first()
                
                if uni and uni.remarks:
                    import re
                    level_match = re.search(r'级别:\s*([^;]+)', uni.remarks)
                    if level_match:
                        level = level_match.group(1).strip()
                        power_universities_levels.append((uni.university_name, level))
            
            # 华北电力大学应该是211工程，但主校区标记可能不一致
            for uni_name, level in power_universities_levels:
                if '华北电力大学' in uni_name and level == '电力部直属':
                    issues.append({
                        'type': '电力院校层次标记不一致',
                        'university': uni_name,
                        'issue': '华北电力大学应该是211工程院校，不仅仅是电力部直属',
                        'suggestion': '建议统一标记为"级别: 211工程; 类型: 理工类; 电力特色: 电力部直属"',
                        'severity': '中'
                    })
            
            # 4. 检查没有备注的重要院校
            important_unis_without_remarks = []
            for uni in universities:
                if not uni.remarks and uni.university_name:
                    # 检查是否是重要院校（简单判断：包含知名关键词）
                    important_keywords = ['交通大学', '理工大学', '科技大学', '工业大学', '电力大学', '师范大学']
                    if any(keyword in uni.university_name for keyword in important_keywords):
                        important_unis_without_remarks.append(uni.university_name)
            
            for uni_name in important_unis_without_remarks[:10]:  # 只显示前10个
                issues.append({
                    'type': '重要院校缺失备注',
                    'university': uni_name,
                    'issue': '重要院校缺失层次、类型和电力特色标识',
                    'suggestion': '需要补充完整的院校信息',
                    'severity': '中'
                })
            
            # 5. 检查电力特色分类的一致性
            power_feature_inconsistencies = []
            
            # 检查明显的电力院校是否标记正确
            obvious_power_schools = ['华北电力', '上海电力', '东北电力', '电力']
            for uni in universities:
                if uni.remarks:
                    has_power_name = any(keyword in uni.university_name for keyword in obvious_power_schools)
                    has_power_feature = '电力' in uni.remarks and ('电力特色强校' in uni.remarks or '电力部直属' in uni.remarks)
                    
                    if has_power_name and not has_power_feature:
                        power_feature_inconsistencies.append(uni.university_name)
            
            for uni_name in power_feature_inconsistencies:
                issues.append({
                    'type': '电力特色标记不一致',
                    'university': uni_name,
                    'issue': '院校名称显示为电力相关，但电力特色标记不明确',
                    'suggestion': '检查并修正电力特色标记',
                    'severity': '低'
                })
            
            # 6. 统计报告
            print(f"\n=== 发现的问题统计 ===")
            issue_types = {}
            severity_count = {'高': 0, '中': 0, '低': 0}
            
            for issue in issues:
                issue_type = issue['type']
                severity = issue['severity']
                
                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
                severity_count[severity] += 1
            
            print(f"总共发现 {len(issues)} 个问题")
            print(f"严重程度分布: 高={severity_count['高']}, 中={severity_count['中']}, 低={severity_count['低']}")
            
            print(f"\n问题类型分布:")
            for issue_type, count in issue_types.items():
                print(f"  {issue_type}: {count} 个")
            
            # 7. 详细问题报告
            print(f"\n=== 详细问题列表 ===")
            for i, issue in enumerate(issues, 1):
                print(f"\n{i}. {issue['type']} ({issue['severity']}严重程度)")
                print(f"   院校: {issue['university']}")
                print(f"   问题: {issue['issue']}")
                print(f"   建议: {issue['suggestion']}")
            
            # 8. 生成修正建议CSV
            df_issues = pd.DataFrame(issues)
            df_issues.to_csv('/workspace/data_quality_issues.csv', index=False, encoding='utf-8')
            print(f"\n问题报告已保存至: /workspace/data_quality_issues.csv")
            
            return issues
            
        except Exception as e:
            print(f"分析失败: {e}")
            import traceback
            print(traceback.format_exc())
            return []

if __name__ == "__main__":
    identify_data_issues()
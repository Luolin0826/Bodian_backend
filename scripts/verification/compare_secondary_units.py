#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
对比二级单位表.xlsx文件与数据库，新增缺少的单位
"""
import pandas as pd
import pymysql
import re
from app.config.config import Config

def read_excel_file():
    """读取二级单位表.xlsx文件"""
    try:
        # 读取Excel文件
        df = pd.read_excel('/workspace/二级单位表.xlsx')
        print(f"Excel文件读取成功，共 {len(df)} 条记录")
        print(f"列名: {list(df.columns)}")
        
        # 显示前几行数据
        print("\n前5行数据预览:")
        print(df.head().to_string())
        
        return df
    except Exception as e:
        print(f"读取Excel文件失败: {e}")
        return None

def get_database_units():
    """获取数据库中现有的二级单位"""
    config = Config()
    
    # 解析数据库连接信息
    db_url = config.SQLALCHEMY_DATABASE_URI
    pattern = r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)'
    match = re.match(pattern, db_url)
    
    if not match:
        print("无法解析数据库连接字符串")
        return None
    
    db_user, db_password, db_host, db_port, db_name = match.groups()
    db_port = int(db_port)
    
    try:
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            charset='utf8mb4'
        )
        
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT unit_id, unit_code, unit_name, unit_type, org_type, 
                       sort_order, region, recruitment_count, is_active
                FROM secondary_units
                ORDER BY unit_id
            """)
            db_units = cursor.fetchall()
            
            print(f"数据库中现有 {len(db_units)} 个二级单位")
            return db_units
        
        connection.close()
        
    except Exception as e:
        print(f"获取数据库单位失败: {e}")
        return None

def compare_and_identify_missing(excel_df, db_units):
    """对比并识别缺少的单位"""
    if excel_df is None or db_units is None:
        return None, None
    
    # 获取数据库中的单位名称集合
    db_unit_names = {unit['unit_name'] for unit in db_units}
    print(f"数据库中的单位数量: {len(db_unit_names)}")
    
    # 获取Excel中的单位名称（需要确定Excel中单位名称的列名）
    # 先检查可能的列名
    print("\nExcel列名分析:")
    for col in excel_df.columns:
        print(f"  {col}: {excel_df[col].dtype}")
    
    # 尝试找到单位名称列
    name_column = None
    possible_name_columns = ['单位名称', 'unit_name', '名称', '单位']
    
    for col in possible_name_columns:
        if col in excel_df.columns:
            name_column = col
            break
    
    if not name_column:
        # 如果没有找到标准列名，使用第一个字符串类型的列
        for col in excel_df.columns:
            if excel_df[col].dtype == 'object':
                name_column = col
                print(f"使用列 '{col}' 作为单位名称列")
                break
    
    if not name_column:
        print("无法找到单位名称列")
        return None, None
    
    excel_unit_names = set(excel_df[name_column].dropna().astype(str))
    print(f"Excel中的单位数量: {len(excel_unit_names)}")
    
    # 找出缺少的单位
    missing_units = excel_unit_names - db_unit_names
    print(f"\n缺少的单位数量: {len(missing_units)}")
    
    if missing_units:
        print("缺少的单位:")
        for unit in sorted(missing_units):
            print(f"  - {unit}")
    
    # 找出Excel中对应的完整记录
    missing_records = []
    if missing_units:
        missing_mask = excel_df[name_column].isin(missing_units)
        missing_records = excel_df[missing_mask].to_dict('records')
    
    return missing_units, missing_records

def analyze_excel_structure(excel_df):
    """分析Excel文件结构，确定字段映射"""
    print("\n=" * 60)
    print("Excel文件结构分析")
    print("=" * 60)
    
    for col in excel_df.columns:
        print(f"\n列名: {col}")
        print(f"数据类型: {excel_df[col].dtype}")
        print(f"非空值数量: {excel_df[col].notna().sum()}")
        print(f"唯一值数量: {excel_df[col].nunique()}")
        
        # 显示前几个非空值
        non_null_values = excel_df[col].dropna().head(5)
        if len(non_null_values) > 0:
            print("前5个值:", list(non_null_values))

def create_mapping_strategy(excel_df, db_units):
    """创建字段映射策略"""
    print("\n=" * 60)
    print("字段映射分析")
    print("=" * 60)
    
    # 数据库字段
    db_fields = ['unit_code', 'unit_name', 'unit_type', 'org_type', 'sort_order', 'region', 'recruitment_count']
    
    # Excel列名
    excel_columns = list(excel_df.columns)
    
    # 尝试自动映射
    mapping = {}
    
    # 常见映射规则
    mapping_rules = {
        'unit_name': ['单位名称', 'unit_name', '名称', '单位'],
        'unit_code': ['单位代码', 'unit_code', '代码', '编码'],
        'unit_type': ['单位类型', 'unit_type', '类型'],
        'org_type': ['组织类型', 'org_type', '组织', '归属'],
        'region': ['地区', 'region', '省份', '区域'],
        'sort_order': ['排序', 'sort_order', '序号', '顺序'],
        'recruitment_count': ['招聘人数', 'recruitment_count', '人数']
    }
    
    for db_field, possible_excel_cols in mapping_rules.items():
        for excel_col in possible_excel_cols:
            if excel_col in excel_columns:
                mapping[db_field] = excel_col
                break
    
    print("自动映射结果:")
    for db_field, excel_col in mapping.items():
        print(f"  {db_field} -> {excel_col}")
    
    return mapping

def main():
    print("开始对比二级单位表...")
    
    # 1. 读取Excel文件
    excel_df = read_excel_file()
    if excel_df is None:
        return
    
    # 2. 分析Excel结构
    analyze_excel_structure(excel_df)
    
    # 3. 获取数据库现有单位
    db_units = get_database_units()
    if db_units is None:
        return
    
    # 4. 创建字段映射
    mapping = create_mapping_strategy(excel_df, db_units)
    
    # 5. 对比并找出缺少的单位
    missing_units, missing_records = compare_and_identify_missing(excel_df, db_units)
    
    if missing_units:
        print(f"\n找到 {len(missing_units)} 个缺少的单位")
        return excel_df, db_units, mapping, missing_records
    else:
        print("\n未发现缺少的单位")
        return excel_df, db_units, mapping, []

if __name__ == '__main__':
    main()
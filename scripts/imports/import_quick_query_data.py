#!/usr/bin/env python3
"""
快捷查询数据导入脚本
从Excel文件导入本科、硕士信息和录取统计数据到数据库
"""

import pandas as pd
import mysql.connector
from mysql.connector import Error
import logging
import sys
import os
from datetime import datetime
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('quick_query_import.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class QuickQueryImporter:
    """快捷查询数据导入器"""
    
    def __init__(self):
        """初始化数据库连接配置"""
        self.db_config = {
            'host': 'rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
            'port': 3306,
            'database': 'bdprod',
            'user': 'dms_user_9332d9e',
            'password': 'AaBb19990826',
            'charset': 'utf8mb4',
            'autocommit': False,
            'use_unicode': True
        }
        
        # Excel字段映射到数据库字段
        self.field_mapping = {
            # 基本信息
            '省份': 'province_name',
            
            # 本科信息
            '本科英语': 'undergraduate_english',
            '本科计算机': 'undergraduate_computer',
            '资格审查': 'undergraduate_qualification',  # 假设这是本科的
            '本科年龄': 'undergraduate_age',
            
            # 本科分数线
            '25年一批本科录取分数': 'undergrad_2025_batch1_score',
            '25年二批本科录取分数': 'undergrad_2025_batch2_score', 
            '24年一批本科录取分数线': 'undergrad_2024_batch1_score',
            '24年二批本科录取分数': 'undergrad_2024_batch2_score',
            '23年一批本科分数线': 'undergrad_2023_batch1_score',
            '23年二批本科分数线': 'undergrad_2023_batch2_score',
            
            # 硕士信息
            '硕士英语': 'graduate_english',
            '硕士计算机': 'graduate_computer',
            '资格审查.1': 'graduate_qualification',  # 硕士的资格审查
            '硕士年龄': 'graduate_age',
            
            # 硕士分数线
            '25年一批硕士录取分数': 'graduate_2025_batch1_score',
            '25年二批硕士录取分数': 'graduate_2025_batch2_score',
            '24年一批硕士录取分数线': 'graduate_2024_batch1_score',
            '24年二批硕士录取分数': 'graduate_2024_batch2_score',
            '23年一批硕士分数线': 'graduate_2023_batch1_score',
            '23年二批硕士分数线': 'graduate_2023_batch2_score',
            
            # 录取人数统计
            '25一批录取人数': 'admission_2025_batch1_count',
            '25二批录取人数': 'admission_2025_batch2_count',
            '24年一批录取人数': 'admission_2024_batch1_count',
            '24年二批录取人数': 'admission_2024_batch2_count',
            '23年一批录取人数': 'admission_2023_batch1_count',
            '23年二批录取人数': 'admission_2023_batch2_count'
        }
        
        # 数字字段（需要转换为整数）
        self.numeric_fields = {
            'admission_2025_batch1_count', 'admission_2025_batch2_count',
            'admission_2024_batch1_count', 'admission_2024_batch2_count',
            'admission_2023_batch1_count', 'admission_2023_batch2_count'
        }
    
    def get_mysql_connection(self):
        """获取数据库连接"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            return connection
        except Error as e:
            logger.error(f"数据库连接失败: {e}")
            raise e
    
    def get_unit_id_mapping(self):
        """获取省份名称到unit_id的映射"""
        try:
            connection = self.get_mysql_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT unit_id, unit_name 
                FROM secondary_units 
                WHERE (unit_type = '省级电网公司' OR unit_name IN ('冀北', '蒙东', '冀北电网', '蒙东电网')) 
                AND is_active = 1
            """)
            
            results = cursor.fetchall()
            cursor.close()
            connection.close()
            
            # 创建映射字典
            mapping = {}
            for row in results:
                mapping[row['unit_name']] = row['unit_id']
                
            logger.info(f"获取到 {len(mapping)} 个省份的unit_id映射")
            return mapping
            
        except Exception as e:
            logger.error(f"获取unit_id映射失败: {e}")
            raise e
    
    def clean_value(self, value, field_name):
        """清理字段值"""
        if pd.isna(value) or value == '' or str(value).strip() == '':
            return None
            
        # 转换为字符串并去除空白
        cleaned = str(value).strip()
        
        # 处理数字字段
        if field_name in self.numeric_fields:
            try:
                # 尝试转换为整数
                if cleaned.lower() in ['nan', 'null', '无数据', '-', '']:
                    return None
                # 移除可能的小数点
                if '.' in cleaned:
                    cleaned = cleaned.split('.')[0]
                return int(cleaned)
            except (ValueError, TypeError):
                logger.warning(f"无法转换 '{cleaned}' 为整数，字段: {field_name}")
                return None
        
        # 处理文本字段
        if cleaned.lower() in ['nan', 'null', '无数据', '无', '-']:
            return None
        
        # 截断过长的文本（数据库字段限制为VARCHAR(100)或VARCHAR(50)）
        max_length = 50  # 分数字段限制为50字符
        if len(cleaned) > max_length:
            logger.warning(f"字段 {field_name} 数据过长，已截断: {cleaned[:max_length]}...")
            cleaned = cleaned[:max_length]
            
        return cleaned
    
    def create_table_if_not_exists(self):
        """创建表（如果不存在）"""
        try:
            connection = self.get_mysql_connection()
            cursor = connection.cursor()
            
            # 读取SQL脚本
            script_path = '/workspace/quick_query_schema.sql'
            if os.path.exists(script_path):
                with open(script_path, 'r', encoding='utf-8') as f:
                    sql_script = f.read()
                
                # 分割SQL语句
                statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
                
                for statement in statements:
                    if statement.upper().startswith('CREATE TABLE') and 'quick_query_info' in statement:
                        try:
                            cursor.execute(statement)
                            logger.info("快捷查询表创建成功")
                        except mysql.connector.Error as e:
                            if 'already exists' in str(e):
                                logger.info("快捷查询表已存在")
                            else:
                                logger.warning(f"创建表时出现警告: {e}")
                
                connection.commit()
            else:
                logger.warning(f"SQL脚本文件不存在: {script_path}")
                
            cursor.close()
            connection.close()
            
        except Exception as e:
            logger.error(f"创建表失败: {e}")
            raise e
    
    def import_from_excel(self, excel_file_path, sheet_name='Sheet1'):
        """从Excel文件导入数据"""
        try:
            logger.info(f"开始导入Excel文件: {excel_file_path}")
            
            # 创建表
            self.create_table_if_not_exists()
            
            # 读取Excel文件
            df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
            logger.info(f"读取到 {len(df)} 行数据，列: {list(df.columns)}")
            
            # 获取unit_id映射
            unit_mapping = self.get_unit_id_mapping()
            
            # 处理数据
            success_count = 0
            error_count = 0
            errors = []
            
            connection = self.get_mysql_connection()
            cursor = connection.cursor()
            
            for index, row in df.iterrows():
                try:
                    # 获取省份名称
                    province_name = self.clean_value(row.get('省份'), 'province_name')
                    if not province_name:
                        error_msg = f"第{index+2}行: 省份名称为空"
                        errors.append(error_msg)
                        error_count += 1
                        continue
                    
                    # 获取unit_id
                    unit_id = unit_mapping.get(province_name)
                    if not unit_id:
                        error_msg = f"第{index+2}行: 找不到省份 '{province_name}' 对应的unit_id"
                        errors.append(error_msg)
                        error_count += 1
                        continue
                    
                    # 检查是否已存在
                    cursor.execute("SELECT id FROM quick_query_info WHERE unit_id = %s", (unit_id,))
                    existing = cursor.fetchone()
                    
                    # 准备数据
                    data = {'unit_id': unit_id}
                    
                    # 映射Excel列到数据库字段
                    for excel_col, db_field in self.field_mapping.items():
                        if db_field == 'province_name':  # 跳过省份名称，已处理
                            continue
                            
                        if excel_col in row.index:
                            cleaned_value = self.clean_value(row[excel_col], db_field)
                            data[db_field] = cleaned_value
                    
                    if existing:
                        # 更新现有记录
                        update_fields = []
                        update_values = []
                        
                        for field, value in data.items():
                            if field != 'unit_id':  # 不更新unit_id
                                update_fields.append(f"{field} = %s")
                                update_values.append(value)
                        
                        if update_fields:
                            update_values.append(unit_id)
                            update_sql = f"""
                                UPDATE quick_query_info 
                                SET {', '.join(update_fields)}, updated_at = NOW()
                                WHERE unit_id = %s
                            """
                            cursor.execute(update_sql, update_values)
                            logger.info(f"更新省份 '{province_name}' 的数据")
                    else:
                        # 插入新记录
                        fields = list(data.keys())
                        values = list(data.values())
                        placeholders = ', '.join(['%s'] * len(fields))
                        
                        insert_sql = f"""
                            INSERT INTO quick_query_info ({', '.join(fields)})
                            VALUES ({placeholders})
                        """
                        cursor.execute(insert_sql, values)
                        logger.info(f"插入省份 '{province_name}' 的数据")
                    
                    success_count += 1
                    
                except Exception as e:
                    error_msg = f"第{index+2}行处理失败: {str(e)}"
                    errors.append(error_msg)
                    error_count += 1
                    logger.error(error_msg)
                    logger.error(traceback.format_exc())
            
            # 提交事务
            connection.commit()
            cursor.close()
            connection.close()
            
            # 输出结果
            logger.info(f"导入完成:")
            logger.info(f"  成功: {success_count} 条")
            logger.info(f"  失败: {error_count} 条")
            
            if errors:
                logger.info("错误详情:")
                for error in errors[:10]:  # 只显示前10个错误
                    logger.info(f"  - {error}")
                if len(errors) > 10:
                    logger.info(f"  ... 还有 {len(errors) - 10} 个错误")
            
            return {
                'success_count': success_count,
                'error_count': error_count,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"导入失败: {e}")
            logger.error(traceback.format_exc())
            raise e

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python import_quick_query_data.py <excel_file_path> [sheet_name]")
        print("示例: python import_quick_query_data.py /workspace/各省份要求，快捷查询表.xlsx Sheet1")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    sheet_name = sys.argv[2] if len(sys.argv) > 2 else 'Sheet1'
    
    if not os.path.exists(excel_file):
        logger.error(f"Excel文件不存在: {excel_file}")
        sys.exit(1)
    
    try:
        importer = QuickQueryImporter()
        result = importer.import_from_excel(excel_file, sheet_name)
        
        print(f"\n✓ 导入完成!")
        print(f"  成功导入: {result['success_count']} 条")
        print(f"  导入失败: {result['error_count']} 条")
        
        if result['error_count'] > 0:
            print(f"  详细错误请查看日志文件: quick_query_import.log")
        
    except Exception as e:
        logger.error(f"导入过程中发生错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
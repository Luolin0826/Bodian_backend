#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回滚错误的大学合并操作
恢复被错误删除的大学记录和招聘记录关联
"""

import mysql.connector
import json
from datetime import datetime

class MergeRollback:
    def __init__(self):
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
    
    def get_connection(self):
        return mysql.connector.connect(**self.db_config)
    
    def backup_current_state(self):
        """备份当前状态，以防回滚失败"""
        print("=== 备份当前状态 ===")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 备份当前大学表
        cursor.execute("SELECT university_id, standard_name FROM universities ORDER BY university_id")
        current_universities = cursor.fetchall()
        
        # 备份招聘记录的university_id分布
        cursor.execute("""
            SELECT university_id, COUNT(*) as count 
            FROM recruitment_records 
            GROUP BY university_id 
            ORDER BY university_id
        """)
        current_records = cursor.fetchall()
        
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'universities': current_universities,
            'recruitment_counts': current_records
        }
        
        # 保存备份
        with open('/workspace/merge_backup.json', 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"当前状态已备份到 merge_backup.json")
        print(f"大学数量: {len(current_universities)}")
        print(f"有记录的大学: {len(current_records)}")
        
        cursor.close()
        conn.close()
    
    def create_rollback_plan(self):
        """创建回滚计划 - 重建被错误删除的大学记录"""
        
        # 根据第一次合并的操作，需要恢复这些被删除的记录
        # 这些是从原始分析中获得的信息，需要重建
        
        rollback_operations = [
            # 华北电力大学 - 恢复保定校区等被误删的记录
            {
                'restore_universities': [
                    {'id': 2, 'name': '华北电力大学 (保定)', 'type': '理工类', 'level': '211工程'},
                    {'id': 291, 'name': '华北电力大学', 'type': '理工类', 'level': '211工程'},
                ],
                'from_primary': 14,  # 从这个ID分离出记录
                'reason': '恢复华北电力大学保定校区等重要分校区'
            },
            
            # 其他可能的错误合并 - 先检查再决定是否回滚
        ]
        
        return rollback_operations
    
    def analyze_merge_damage(self):
        """分析合并造成的损失"""
        print("=== 分析合并损失 ===")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 检查当前华北电力大学的记录数
        cursor.execute("""
            SELECT COUNT(*) FROM recruitment_records 
            WHERE university_id = 14
        """)
        current_count = cursor.fetchone()[0]
        print(f"华北电力大学 (北京) 当前招聘记录数: {current_count}")
        
        # 检查universities表中是否还有original_name信息
        cursor.execute("""
            SELECT university_id, original_name, standard_name
            FROM universities 
            WHERE university_id = 14
        """)
        main_record = cursor.fetchone()
        if main_record:
            print(f"主记录信息:")
            print(f"  ID: {main_record[0]}")
            print(f"  原始名称: {main_record[1]}")
            print(f"  标准名称: {main_record[2]}")
        
        # 检查是否还有其他华北电力相关记录
        cursor.execute("""
            SELECT university_id, original_name, standard_name, recruitment_count
            FROM universities 
            WHERE standard_name LIKE '%华北电力%' OR original_name LIKE '%华北电力%'
            ORDER BY university_id
        """)
        
        all_records = cursor.fetchall()
        print(f"\n所有华北电力相关记录:")
        for uid, orig_name, std_name, rec_count in all_records:
            print(f"  ID {uid}: {orig_name} -> {std_name} ({rec_count} 条)")
        
        print(f"\n*** 严重问题 ***")
        print(f"由于recruitment_records表只存储university_id，没有原始大学名称")
        print(f"一旦合并后，无法从数据本身恢复分校区信息")
        print(f"需要从备份或者外部数据源恢复")
        
        cursor.close()
        conn.close()
        
        return current_count
    
    def execute_rollback(self, dry_run=True):
        """执行回滚操作"""
        if dry_run:
            print("=== 干运行模式 - 模拟回滚 ===")
        else:
            print("=== 执行回滚操作 ===")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 第一步：重新创建华北电力大学保定校区
            if not dry_run:
                # 检查ID 2是否存在
                cursor.execute("SELECT university_id FROM universities WHERE university_id = 2")
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO universities (university_id, standard_name, type, level)
                        VALUES (2, '华北电力大学 (保定)', '理工类', '211工程')
                    """)
                    print("✓ 重建华北电力大学 (保定) 记录")
            else:
                print("[干运行] 将重建华北电力大学 (保定) 记录")
            
            # 第二步：尝试将部分招聘记录重新分配给保定校区
            # 基于原始大学名称或地点信息
            if not dry_run:
                cursor.execute("""
                    UPDATE recruitment_records 
                    SET university_id = 2 
                    WHERE university_id = 14 
                    AND (university_name LIKE '%保定%' 
                         OR location LIKE '%保定%'
                         OR (university_name LIKE '%华北电力%' 
                             AND university_name NOT LIKE '%北京%'
                             AND university_name NOT LIKE '%(北京)%'))
                """)
                
                affected_rows = cursor.rowcount
                print(f"✓ 重新分配了 {affected_rows} 条记录到保定校区")
            else:
                # 预览将要移动的记录数
                cursor.execute("""
                    SELECT COUNT(*) FROM recruitment_records 
                    WHERE university_id = 14 
                    AND (university_name LIKE '%保定%' 
                         OR location LIKE '%保定%'
                         OR (university_name LIKE '%华北电力%' 
                             AND university_name NOT LIKE '%北京%'
                             AND university_name NOT LIKE '%(北京)%'))
                """)
                preview_count = cursor.fetchone()[0]
                print(f"[干运行] 将重新分配 {preview_count} 条记录到保定校区")
            
            if not dry_run:
                conn.commit()
                print("回滚操作完成")
            else:
                print("干运行完成")
                
        except Exception as e:
            conn.rollback()
            print(f"回滚失败: {str(e)}")
            
        finally:
            cursor.close()
            conn.close()
    
    def verify_rollback(self):
        """验证回滚结果"""
        print("=== 验证回滚结果 ===")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 检查华北电力大学的分布
        cursor.execute("""
            SELECT u.university_id, u.standard_name, COUNT(rr.record_id) as count
            FROM universities u
            LEFT JOIN recruitment_records rr ON u.university_id = rr.university_id
            WHERE u.standard_name LIKE '%华北电力%'
            GROUP BY u.university_id, u.standard_name
            ORDER BY count DESC
        """)
        
        results = cursor.fetchall()
        print("华北电力大学分布:")
        for uid, name, count in results:
            print(f"  ID {uid}: {name} - {count} 条记录")
        
        cursor.close()
        conn.close()

def main():
    import sys
    
    rollback = MergeRollback()
    
    print("大学合并回滚工具")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'analyze':
            rollback.analyze_merge_damage()
            return
        elif sys.argv[1] == 'backup':
            rollback.backup_current_state()
            return
        elif sys.argv[1] == 'preview':
            rollback.backup_current_state()
            rollback.analyze_merge_damage()
            rollback.execute_rollback(dry_run=True)
            return
        elif sys.argv[1] == 'execute':
            rollback.backup_current_state()
            rollback.execute_rollback(dry_run=False)
            rollback.verify_rollback()
            return
    
    # 默认执行分析和预览
    rollback.backup_current_state()
    rollback.analyze_merge_damage()
    rollback.execute_rollback(dry_run=True)

if __name__ == "__main__":
    main()
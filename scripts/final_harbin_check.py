#!/usr/bin/env python3
import mysql.connector

db_config = {
    'host': 'rm-uf6f40gg0d576z607jo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'database': 'bdprod',
    'user': 'dms_user_9332d9e',
    'password': 'AaBb19990826',
    'charset': 'utf8mb4'
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

print("=== 哈尔滨工业大学最终状态检查 ===")

cursor.execute("""
    SELECT university_id, standard_name, recruitment_count
    FROM universities 
    WHERE standard_name LIKE '%哈尔滨工业大学%'
    ORDER BY recruitment_count DESC
""")

harbin_records = cursor.fetchall()
print(f"哈尔滨工业大学相关记录:")
for uid, name, count in harbin_records:
    # 检查格式规范性
    format_issues = []
    if '（' in name or '）' in name:
        format_issues.append("中文括号")
    if '(' in name and ' (' not in name:
        format_issues.append("缺少空格")
    
    status = " ⚠️ " + ", ".join(format_issues) if format_issues else " ✓"
    print(f"  ID {uid}: {name} - {count} 条{status}")

cursor.close()
conn.close()
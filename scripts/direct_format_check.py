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

print("=== 直接检查具体问题记录 ===")

# 检查之前发现的问题记录
problem_ids = [262, 256, 922, 923, 247, 375, 784]

for uid in problem_ids:
    cursor.execute("SELECT university_id, standard_name, recruitment_count FROM universities WHERE university_id = %s", (uid,))
    record = cursor.fetchone()
    if record:
        print(f"ID {record[0]}: '{record[1]}' ({record[2]} 条)")
        
        # 检查字符
        name = record[1]
        has_chinese_bracket = '（' in name or '）' in name
        has_english_bracket = '(' in name or ')' in name
        print(f"  中文括号: {has_chinese_bracket}, 英文括号: {has_english_bracket}")

print("\n=== 查找所有中文括号记录 ===")
cursor.execute("SELECT university_id, standard_name, recruitment_count FROM universities WHERE standard_name LIKE '%（%' OR standard_name LIKE '%）%'")

chinese_bracket_records = cursor.fetchall()
if chinese_bracket_records:
    print(f"发现 {len(chinese_bracket_records)} 条使用中文括号的记录:")
    for uid, name, count in chinese_bracket_records:
        print(f"  ID {uid}: {name} ({count} 条)")
else:
    print("没有发现中文括号记录")

cursor.close()
conn.close()
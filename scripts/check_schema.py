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

print("=== recruitment_records表结构 ===")
cursor.execute("DESCRIBE recruitment_records")
for row in cursor.fetchall():
    print(f"  {row[0]} | {row[1]} | {row[2]} | {row[3]}")

print("\n=== universities表结构 ===")
cursor.execute("DESCRIBE universities")
for row in cursor.fetchall():
    print(f"  {row[0]} | {row[1]} | {row[2]} | {row[3]}")

cursor.close()
conn.close()
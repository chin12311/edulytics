import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='eval_user',
    password='!eETXiuo4LHxeu6M4#sz',
    database='evaluation'
)

cursor = conn.cursor()
cursor.execute("SHOW TABLES LIKE 'main_evaluation%'")
print("✅ Evaluation-related tables in MySQL:")
for row in cursor.fetchall():
    print(f"  - {row[0]}")

conn.close()
print("\n✅ All evaluation tables verified!")

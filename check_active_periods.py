import pymysql
from datetime import datetime

conn = pymysql.connect(
    host='13.211.104.201',
    user='eval_user',
    password='eval_password',
    database='evaluation',
    port=3306,
    connect_timeout=10
)

cursor = conn.cursor()

print("=== Evaluation Periods (Student) ===\n")
cursor.execute("""
    SELECT id, name, is_active, start_date, end_date, created_at
    FROM main_evaluationperiod 
    WHERE evaluation_type = 'student'
    ORDER BY created_at DESC
    LIMIT 5
""")
periods = cursor.fetchall()
for p in periods:
    print(f"Period: {p[1]}")
    print(f"  ID: {p[0]}")
    print(f"  Active: {p[2]}")
    print(f"  Start: {p[3]}")
    print(f"  End: {p[4]}")
    print(f"  Created: {p[5]}")
    
    # Count responses
    cursor.execute("SELECT COUNT(*) FROM main_evaluationresponse WHERE evaluation_period_id = %s", (p[0],))
    count = cursor.fetchone()[0]
    print(f"  Responses: {count}")
    
    if count > 0:
        cursor.execute("""
            SELECT u1.username, u2.username 
            FROM main_evaluationresponse er
            JOIN auth_user u1 ON er.evaluator_id = u1.id
            JOIN auth_user u2 ON er.evaluatee_id = u2.id
            WHERE er.evaluation_period_id = %s
            LIMIT 3
        """, (p[0],))
        responses = cursor.fetchall()
        for r in responses:
            print(f"    - {r[0]} -> {r[1]}")
    print()

# Check active periods
print("\n=== Active Student Periods ===")
cursor.execute("""
    SELECT id, name 
    FROM main_evaluationperiod 
    WHERE is_active = 1 AND evaluation_type = 'student'
""")
active = cursor.fetchall()
print(f"Count: {len(active)}")
for p in active:
    print(f"  - {p[1]} (ID: {p[0]})")

conn.close()

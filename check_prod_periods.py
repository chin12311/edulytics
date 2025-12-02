import pymysql
from datetime import datetime

conn = pymysql.connect(
    host='localhost',
    user='eval_user',
    password='eval_password',
    database='evaluation',
    port=3306
)

cursor = conn.cursor()

print("=" * 80)
print("PRODUCTION DATABASE - EVALUATION PERIODS")
print("=" * 80)

# Check student periods
print("\n📚 STUDENT EVALUATION PERIODS:")
cursor.execute("""
    SELECT id, name, is_active, start_date, end_date, created_at
    FROM main_evaluationperiod 
    WHERE evaluation_type = 'student'
    ORDER BY created_at DESC
""")
student_periods = cursor.fetchall()
for p in student_periods:
    print(f"\n  Period: {p[1]}")
    print(f"  ID: {p[0]}")
    print(f"  Active: {p[2]}")
    print(f"  Start: {p[3]}")
    print(f"  End: {p[4]}")
    print(f"  Created: {p[5]}")

# Check peer periods
print("\n\n👥 PEER EVALUATION PERIODS:")
cursor.execute("""
    SELECT id, name, is_active, start_date, end_date, created_at
    FROM main_evaluationperiod 
    WHERE evaluation_type = 'peer'
    ORDER BY created_at DESC
""")
peer_periods = cursor.fetchall()
for p in peer_periods:
    print(f"\n  Period: {p[1]}")
    print(f"  ID: {p[0]}")
    print(f"  Active: {p[2]}")
    print(f"  Start: {p[3]}")
    print(f"  End: {p[4]}")
    print(f"  Created: {p[5]}")

conn.close()
print("\n")

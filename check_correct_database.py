import pymysql

# Connect to the evaluation database (the one edulytics.uk actually uses)
connection = pymysql.connect(
    host='localhost',
    user='eval_user',
    password='eval_password',
    database='evaluation',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

print("=== Checking 'evaluation' database (the one edulytics.uk uses) ===\n")

with connection.cursor() as cursor:
    # Count evaluations
    cursor.execute("SELECT COUNT(*) as count FROM main_evaluationresponse")
    regular_count = cursor.fetchone()['count']
    print(f"Regular Evaluations: {regular_count}")
    
    cursor.execute("SELECT COUNT(*) as count FROM main_irregularevaluation")
    irregular_count = cursor.fetchone()['count']
    print(f"Irregular Evaluations: {irregular_count}")
    
    # Get recent evaluations
    if regular_count > 0:
        print(f"\n=== Regular Evaluations ===")
        cursor.execute("""
            SELECT r.id, u1.username as evaluator, u2.username as evaluatee, r.submitted_at
            FROM main_evaluationresponse r
            JOIN auth_user u1 ON r.evaluator_id = u1.id
            JOIN auth_user u2 ON r.evaluatee_id = u2.id
            ORDER BY r.submitted_at DESC
            LIMIT 10
        """)
        for row in cursor.fetchall():
            print(f"  ID {row['id']}: {row['evaluator']} -> {row['evaluatee']} ({row['submitted_at']})")
    
    if irregular_count > 0:
        print(f"\n=== Irregular Evaluations ===")
        cursor.execute("""
            SELECT i.id, u.username as evaluator, i.evaluatee_name, i.submitted_at
            FROM main_irregularevaluation i
            JOIN auth_user u ON i.evaluator_id = u.id
            ORDER BY i.submitted_at DESC
            LIMIT 10
        """)
        for row in cursor.fetchall():
            print(f"  ID {row['id']}: {row['evaluator']} -> {row['evaluatee_name']} ({row['submitted_at']})")

connection.close()
print("\n✓ Found the correct database!")

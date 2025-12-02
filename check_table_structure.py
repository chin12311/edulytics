from django.db import connection

print("=== Database Table Structure Check ===\n")

with connection.cursor() as cursor:
    print("--- main_irregularevaluation table structure ---")
    cursor.execute("DESCRIBE main_irregularevaluation")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[0]}: {col[1]} (Null: {col[2]}, Key: {col[3]})")
    
    print("\n--- main_evaluationresponse table structure ---")
    cursor.execute("DESCRIBE main_evaluationresponse")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[0]}: {col[1]} (Null: {col[2]}, Key: {col[3]})")

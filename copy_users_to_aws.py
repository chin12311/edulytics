import mysql.connector
import sys

try:
    # Connect to LOCAL MySQL
    print("Connecting to LOCAL MySQL...")
    local_db = mysql.connector.connect(
        host="localhost",
        user="eval_user",
        password="eval_password",
        database="evaluation"
    )
    local_cursor = local_db.cursor(dictionary=True)
    
    # Connect to AWS MySQL
    print("Connecting to AWS MySQL...")
    aws_db = mysql.connector.connect(
        host="54.66.185.78",
        user="eval_user",
        password="eval_password",
        database="evaluation",
        port=3306
    )
    aws_cursor = aws_db.cursor()
    
    # Copy users
    local_cursor.execute("SELECT * FROM auth_user WHERE username != 'admin'")
    users = local_cursor.fetchall()
    print(f"Found {len(users)} users locally")
    
    for user in users:
        sql = """INSERT INTO auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        aws_cursor.execute(sql, (user['id'], user['password'], user['last_login'], user['is_superuser'], 
                                 user['username'], user['first_name'], user['last_name'], user['email'], 
                                 user['is_staff'], user['is_active'], user['date_joined']))
    
    aws_db.commit()
    print(f"✓ Successfully copied {len(users)} users to AWS!")
    
    local_db.close()
    aws_db.close()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

#!/usr/bin/env python3
import pymysql

print("=== PRODUCTION DATABASE CHECK (evaluation db) ===\n")

conn = pymysql.connect(
    host='localhost',
    user='eval_user',
    password='eval_password',
    database='evaluation'
)

cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM main_evaluationresponse')
print(f'Regular Evaluations: {cur.fetchone()[0]}')

cur.execute('SELECT COUNT(*) FROM main_irregularevaluation')
print(f'Irregular Evaluations: {cur.fetchone()[0]}')

cur.execute('''
    SELECT r.id, u1.username, u2.username, r.submitted_at
    FROM main_evaluationresponse r
    JOIN auth_user u1 ON r.evaluator_id=u1.id
    JOIN auth_user u2 ON r.evaluatee_id=u2.id
    ORDER BY r.submitted_at DESC
    LIMIT 5
''')

print('\nRecent submissions:')
rows = cur.fetchall()
if rows:
    for row in rows:
        print(f'  ID {row[0]}: {row[1]} -> {row[2]} at {row[3]}')
else:
    print('  None')

conn.close()

import os
import sys

# Check 1: Database Configuration
print("=== CHECK 1: Database Configuration ===")
from django.conf import settings
print(f"Database Engine: {settings.DATABASES['default']['ENGINE']}")
print(f"Database Name: {settings.DATABASES['default']['NAME']}")
print(f"Database Host: {settings.DATABASES['default']['HOST']}")
print(f"Database Port: {settings.DATABASES['default']['PORT']}")
print(f"Database User: {settings.DATABASES['default']['USER']}")

# Check 2: Model Inspection
print("\n=== CHECK 2: Model Field Names ===")
from main.models import EvaluationResponse, IrregularEvaluation
print(f"EvaluationResponse fields: {[f.name for f in EvaluationResponse._meta.get_fields()]}")
print(f"IrregularEvaluation fields: {[f.name for f in IrregularEvaluation._meta.get_fields()]}")

# Check 3: Database Router
print("\n=== CHECK 3: Database Router ===")
if hasattr(settings, 'DATABASE_ROUTERS'):
    print(f"Database routers: {settings.DATABASE_ROUTERS}")
else:
    print("No database routers configured")

# Check 4: Direct SQL Query
print("\n=== CHECK 4: Raw SQL Query ===")
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT DATABASE()")
    print(f"Current database: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM main_evaluationresponse")
    print(f"main_evaluationresponse count: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM main_irregularevaluation")
    print(f"main_irregularevaluation count: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM auth_user")
    print(f"auth_user count: {cursor.fetchone()[0]}")
    
    # Check if specific users exist
    cursor.execute("SELECT id, username FROM auth_user WHERE username IN ('jadepuno', 'zyrahmastelero', 'aeroncaligagan')")
    users = cursor.fetchall()
    print(f"\nUsers from screenshot:")
    if users:
        for user_id, username in users:
            print(f"  - {username} (ID: {user_id})")
    else:
        print("  - NONE FOUND")
    
    # Get all evaluation responses
    cursor.execute("SELECT id, evaluator_id, evaluatee_id FROM main_evaluationresponse LIMIT 5")
    responses = cursor.fetchall()
    print(f"\nFirst 5 evaluation responses:")
    if responses:
        for resp_id, eval_or, eval_ee in responses:
            cursor.execute("SELECT username FROM auth_user WHERE id = %s", [eval_or])
            evaluator = cursor.fetchone()
            cursor.execute("SELECT username FROM auth_user WHERE id = %s", [eval_ee])
            evaluatee = cursor.fetchone()
            print(f"  - ID {resp_id}: {evaluator[0] if evaluator else 'UNKNOWN'} -> {evaluatee[0] if evaluatee else 'UNKNOWN'}")
    else:
        print("  - NONE FOUND")
    
    # Get all irregular evaluations
    cursor.execute("SELECT id, evaluator_id, evaluatee_name FROM main_irregularevaluation LIMIT 5")
    irregulars = cursor.fetchall()
    print(f"\nFirst 5 irregular evaluations:")
    if irregulars:
        for irreg_id, eval_or, eval_name in irregulars:
            cursor.execute("SELECT username FROM auth_user WHERE id = %s", [eval_or])
            evaluator = cursor.fetchone()
            print(f"  - ID {irreg_id}: {evaluator[0] if evaluator else 'UNKNOWN'} -> {eval_name}")
    else:
        print("  - NONE FOUND")

# Check 5: Admin Configuration
print("\n=== CHECK 5: Admin Site ===")
from django.contrib import admin
from main.models import EvaluationResponse, IrregularEvaluation
print(f"EvaluationResponse registered in admin: {EvaluationResponse in admin.site._registry}")
print(f"IrregularEvaluation registered in admin: {IrregularEvaluation in admin.site._registry}")

if EvaluationResponse in admin.site._registry:
    admin_class = admin.site._registry[EvaluationResponse]
    print(f"EvaluationResponse admin queryset uses: {admin_class.get_queryset.__module__}")
    
if IrregularEvaluation in admin.site._registry:
    admin_class = admin.site._registry[IrregularEvaluation]
    print(f"IrregularEvaluation admin queryset uses: {admin_class.get_queryset.__module__}")

print("\n=== DIAGNOSIS COMPLETE ===")

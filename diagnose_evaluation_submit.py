#!/usr/bin/env python
"""
Diagnostic script to check evaluation submission issue
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
sys.path.insert(0, os.getcwd())
django.setup()

from main.models import Evaluation, EvaluationPeriod, EvaluationResponse
from django.contrib.auth.models import User

print("=" * 60)
print("EVALUATION SUBMISSION DIAGNOSTICS")
print("=" * 60)

# Check 1: Evaluation periods
print("\n1. EVALUATION PERIODS:")
periods = EvaluationPeriod.objects.all()
if periods.exists():
    for period in periods:
        print(f"   - {period.name}")
        print(f"     Type: {period.evaluation_type}")
        print(f"     Active: {period.is_active}")
        print(f"     Start: {period.start_date}")
        print(f"     End: {period.end_date}")
else:
    print("   ❌ NO EVALUATION PERIODS FOUND")

# Check 2: Evaluation forms
print("\n2. EVALUATION FORMS:")
evals = Evaluation.objects.all()
if evals.exists():
    for eval in evals:
        print(f"   - {eval.name}")
        print(f"     Type: {eval.evaluation_type}")
        print(f"     Released: {eval.is_released}")
        print(f"     Period: {eval.evaluation_period}")
else:
    print("   ❌ NO EVALUATION FORMS FOUND")

# Check 3: Check if period is active
print("\n3. ACTIVE EVALUATION PERIOD CHECK:")
is_active = Evaluation.is_evaluation_period_active('student')
print(f"   Is student evaluation period active? {is_active}")

# Check 4: Evaluation responses
print("\n4. EVALUATION RESPONSES:")
responses = EvaluationResponse.objects.all()
print(f"   Total submitted: {responses.count()}")

# Check 5: Users who can evaluate
print("\n5. USERS IN SYSTEM:")
print(f"   Total users: {User.objects.count()}")

print("\n" + "=" * 60)
print("TO FIX EVALUATION SUBMISSION:")
print("=" * 60)
print("""
Option 1: Via Django Shell
  python manage.py shell
  from main.models import Evaluation
  eval = Evaluation.objects.filter(evaluation_type='student').first()
  eval.is_released = True
  eval.save()
  print('Evaluation released!')

Option 2: Via Django Admin
  python manage.py runserver
  Go to: http://localhost:8000/admin/
  Login and edit Evaluation > is_released to True

Option 3: Create/Fix Evaluation Period & Form
  Check if EvaluationPeriod and Evaluation exist and are configured
""")

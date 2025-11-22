#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
sys.path.insert(0, os.getcwd())
django.setup()

from main.models import EvaluationPeriod, Evaluation

print("=" * 60)
print("ENABLING EVALUATION SUBMISSIONS")
print("=" * 60)

# Find student evaluation period for current month
period = EvaluationPeriod.objects.filter(
    evaluation_type='student',
    name__icontains='November 2025'
).first()

if period:
    print(f"\nFound: {period.name}")
    print(f"  Current is_active: {period.is_active}")
    
    # Enable it
    period.is_active = True
    period.save()
    print(f"  Updated is_active: {period.is_active}")
    print("\n[SUCCESS] Student evaluation period is now ACTIVE!")
else:
    print("\n[ERROR] Could not find November 2025 student evaluation period")

# Also release the evaluation form
eval_form = Evaluation.objects.filter(evaluation_type='student').first()
if eval_form:
    print(f"\nEvaluation Form:")
    print(f"  Current is_released: {eval_form.is_released}")
    eval_form.is_released = True
    eval_form.save()
    print(f"  Updated is_released: {eval_form.is_released}")
    print("\n[SUCCESS] Evaluation form is now RELEASED!")

print("\n" + "=" * 60)
print("STUDENTS CAN NOW SUBMIT EVALUATIONS!")
print("=" * 60)

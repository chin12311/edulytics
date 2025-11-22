#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
sys.path.insert(0, os.getcwd())
django.setup()

from main.models import Evaluation, EvaluationResponse, EvaluationPeriod

print("=" * 60)
print("EVALUATION SUBMISSION STATUS")
print("=" * 60)

# Check evaluation periods
periods = EvaluationPeriod.objects.all()
print(f"\nEvaluation Periods: {periods.count()}")
for p in periods:
    print(f"  - {p.name} (type: {p.evaluation_type}, active: {p.is_active})")

# Check evaluations
evals = Evaluation.objects.all()
print(f"\nEvaluation Forms: {evals.count()}")
for e in evals:
    print(f"  - {e.name} (type: {e.evaluation_type}, released: {e.is_released})")

# Check evaluation responses
responses = EvaluationResponse.objects.all()
print(f"\nSubmitted Evaluations: {responses.count()}")
if responses.exists():
    latest = responses.last()
    print(f"  Latest submission: {latest.evaluator} → {latest.evaluatee} on {latest.submitted_at}")

# Check if period is active
is_active = Evaluation.is_evaluation_period_active('student')
print(f"\nStudent Evaluation Period Active: {is_active}")

print("\n" + "=" * 60)
print("TO ENABLE EVALUATIONS (if needed):")
print("=" * 60)
print("""
If is_released = False, run:
  eval = Evaluation.objects.filter(evaluation_type='student').first()
  if eval:
      eval.is_released = True
      eval.save()
      print('✓ Evaluation form released!')
""")

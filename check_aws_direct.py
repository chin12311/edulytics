#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluation.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import EvaluationResponse, IrregularEvaluation, EvaluationResult

print("=== Direct AWS Database Check ===\n")

print(f"Total Users: {User.objects.count()}")

print("\n--- Checking users from screenshot ---")
users_to_check = ["jowardclaudio", "jadepuno", "zyrahmastelero", "aeroncaligagan"]
for username in users_to_check:
    exists = User.objects.filter(username=username).exists()
    if exists:
        user = User.objects.get(username=username)
        print(f"✓ {username}: EXISTS (ID: {user.id})")
    else:
        print(f"✗ {username}: NOT FOUND")

print(f"\nEvaluationResponse count: {EvaluationResponse.objects.count()}")
print(f"IrregularEvaluation count: {IrregularEvaluation.objects.count()}")
print(f"EvaluationResult count: {EvaluationResult.objects.count()}")

# Show actual data if exists
responses = EvaluationResponse.objects.all()
if responses.exists():
    print("\n--- Regular Responses ---")
    for r in responses[:10]:
        print(f"  {r.evaluator.username} -> {r.evaluatee.username} (Period: {r.period.name})")
else:
    print("\n--- No Regular Responses ---")

irregulars = IrregularEvaluation.objects.all()
if irregulars.exists():
    print("\n--- Irregular Evaluations ---")
    for i in irregulars[:10]:
        print(f"  {i.evaluator.username} -> {i.evaluatee_name} (Period: {i.period.name})")
else:
    print("\n--- No Irregular Evaluations ---")

results = EvaluationResult.objects.all()
if results.exists():
    print("\n--- Evaluation Results ---")
    for r in results[:10]:
        print(f"  {r.user.username}: {r.average_score:.2f} (Section: {r.section})")
else:
    print("\n--- No Evaluation Results ---")

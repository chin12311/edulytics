#!/usr/bin/env python3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import Evaluation
from main.utils import can_view_evaluation_results

print("=" * 60)
print("EVALUATION RELEASE STATUS")
print("=" * 60)

evals = Evaluation.objects.filter(evaluation_type='student').order_by('-id')
for e in evals[:3]:
    print(f"\nEvaluation ID {e.id}:")
    print(f"  Type: {e.evaluation_type}")
    print(f"  Is Released: {e.is_released}")

print("\n" + "=" * 60)
print(f"can_view_evaluation_results('student'): {can_view_evaluation_results('student')}")
print("=" * 60)

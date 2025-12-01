#!/usr/bin/env python3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import EvaluationPeriod

print("=" * 60)
print("EVALUATION PERIOD STATUS")
print("=" * 60)

periods = EvaluationPeriod.objects.filter(evaluation_type='student').order_by('-start_date')

for p in periods[:3]:
    print(f"\nPeriod: {p.name}")
    print(f"  - Active: {p.is_active}")
    print(f"  - Results Released: {p.results_released}")
    print(f"  - Start Date: {p.start_date}")
    print(f"  - End Date: {p.end_date}")
    
print("\n" + "=" * 60)

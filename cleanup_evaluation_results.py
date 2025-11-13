#!/usr/bin/env python
"""
Script to find and delete old evaluation results that are lingering
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from main.models import EvaluationResult, EvaluationPeriod
from django.contrib.auth.models import User

print("=" * 80)
print("EVALUATION RESULTS CLEANUP")
print("=" * 80)

# List all evaluation results
print("\n📊 ALL EVALUATION RESULTS IN DATABASE:")
print("-" * 80)

all_results = EvaluationResult.objects.all().select_related('user', 'evaluation_period', 'section')
print(f"Total results: {all_results.count()}\n")

for result in all_results:
    period_status = "ACTIVE" if result.evaluation_period.is_active else "ARCHIVED"
    section_name = result.section.code if result.section else "N/A"
    print(f"User: {result.user.username:20} | Period: {result.evaluation_period.name:30} | Status: {period_status:10} | Section: {section_name:10} | Score: {result.total_percentage}% | Responses: {result.total_responses}")

# List all evaluation periods
print("\n" + "=" * 80)
print("📅 ALL EVALUATION PERIODS IN DATABASE:")
print("-" * 80)

all_periods = EvaluationPeriod.objects.all().order_by('-start_date')
print(f"Total periods: {all_periods.count()}\n")

for period in all_periods:
    status = "ACTIVE (is_active=True)" if period.is_active else "ARCHIVED (is_active=False)"
    results_count = EvaluationResult.objects.filter(evaluation_period=period).count()
    print(f"Period: {period.name:30} | Type: {period.evaluation_type:10} | Status: {status:35} | Results: {results_count}")

print("\n" + "=" * 80)
print("💡 TO DELETE SPECIFIC RESULTS:")
print("-" * 80)
print("""
Option 1: Delete all results from archived periods
    from main.models import EvaluationResult, EvaluationPeriod
    archived_periods = EvaluationPeriod.objects.filter(is_active=False)
    EvaluationResult.objects.filter(evaluation_period__in=archived_periods).delete()

Option 2: Delete all evaluation results (WARNING: deletes everything)
    from main.models import EvaluationResult
    count = EvaluationResult.objects.count()
    EvaluationResult.objects.all().delete()
    print(f"Deleted {count} results")

Option 3: Delete results for specific user
    from main.models import EvaluationResult
    from django.contrib.auth.models import User
    user = User.objects.get(username='dr_smith')  # Change to actual username
    count = EvaluationResult.objects.filter(user=user).count()
    EvaluationResult.objects.filter(user=user).delete()
    print(f"Deleted {count} results for {user.username}")

Option 4: Delete specific period results
    from main.models import EvaluationResult, EvaluationPeriod
    period = EvaluationPeriod.objects.get(name='Student Evaluation November 2025')
    count = EvaluationResult.objects.filter(evaluation_period=period).count()
    EvaluationResult.objects.filter(evaluation_period=period).delete()
    print(f"Deleted {count} results from {period.name}")
""")

print("=" * 80)

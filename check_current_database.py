#!/usr/bin/env python
"""
Check actual current evaluation responses in detail
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import EvaluationResponse, EvaluationResult, EvaluationPeriod, IrregularEvaluation
from django.utils import timezone

print("="*70)
print("CURRENT DATABASE STATE - DETAILED CHECK")
print("="*70)

# Check all evaluation responses
print("\n📋 EVALUATION RESPONSES (Regular):")
responses = EvaluationResponse.objects.all().select_related('evaluator', 'evaluatee', 'evaluation_period')
print(f"Total count: {responses.count()}")

if responses.exists():
    for r in responses:
        period_name = r.evaluation_period.name if r.evaluation_period else "No Period"
        print(f"\n  Response ID: {r.id}")
        print(f"  Evaluator: {r.evaluator.username} ({r.evaluator.userprofile.role if hasattr(r.evaluator, 'userprofile') else 'No Profile'})")
        print(f"  Evaluatee: {r.evaluatee.username}")
        print(f"  Section: {r.student_section}")
        print(f"  Period: {period_name}")
        print(f"  Submitted: {r.submitted_at}")

# Check irregular evaluations
print("\n\n📋 IRREGULAR EVALUATIONS:")
irregular = IrregularEvaluation.objects.all().select_related('evaluator', 'evaluatee', 'evaluation_period')
print(f"Total count: {irregular.count()}")

if irregular.exists():
    for r in irregular:
        period_name = r.evaluation_period.name if r.evaluation_period else "No Period"
        print(f"\n  Irregular ID: {r.id}")
        print(f"  Evaluator: {r.evaluator.username}")
        print(f"  Evaluatee: {r.evaluatee.username}")
        print(f"  Student #: {r.student_number}")
        print(f"  Period: {period_name}")
        print(f"  Submitted: {r.submitted_at}")

# Check evaluation results
print("\n\n📊 EVALUATION RESULTS:")
results = EvaluationResult.objects.all().select_related('user', 'section', 'evaluation_period')
print(f"Total count: {results.count()}")

if results.exists():
    for r in results:
        section_name = r.section.code if r.section else "No Section"
        period_name = r.evaluation_period.name if r.evaluation_period else "No Period"
        print(f"\n  Result ID: {r.id}")
        print(f"  User: {r.user.username}")
        print(f"  Section: {section_name}")
        print(f"  Period: {period_name}")
        print(f"  Total %: {r.total_percentage:.2f}%")
        print(f"  Responses: {r.total_responses}")

# Check evaluation periods
print("\n\n📅 EVALUATION PERIODS:")
periods = EvaluationPeriod.objects.filter(evaluation_type='student').order_by('-end_date')
for p in periods[:3]:
    status = "ACTIVE" if p.is_active else "INACTIVE"
    print(f"\n  {status}: {p.name} (ID: {p.id})")
    print(f"  End: {p.end_date}")
    print(f"  Now: {timezone.now()}")
    print(f"  Is Past: {p.end_date <= timezone.now()}")

# Summary
print("\n\n" + "="*70)
print("SUMMARY:")
print("="*70)
regular_count = EvaluationResponse.objects.count()
irregular_count = IrregularEvaluation.objects.count()
result_count = EvaluationResult.objects.count()

print(f"\nRegular responses: {regular_count}")
print(f"Irregular evaluations: {irregular_count}")
print(f"Total evaluations: {regular_count + irregular_count}")
print(f"Evaluation results: {result_count}")

if (regular_count + irregular_count) > result_count:
    print(f"\n⚠️ {(regular_count + irregular_count) - result_count} evaluations not yet processed to results")
    print("   These evaluations exist but won't show in profile settings until processed")

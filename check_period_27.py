import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import EvaluationPeriod, EvaluationResponse, IrregularEvaluation
from django.contrib.auth.models import User

# Check period 27
period = EvaluationPeriod.objects.get(id=27)
print(f"Period 27: {period.name}")
print(f"Active: {period.is_active}")
print(f"Created: {period.created_at}")
print(f"Start: {period.start_date}")
print(f"End: {period.end_date}")

print("\n" + "=" * 80)
print("RESPONSES IN PERIOD 27")
print("=" * 80)

# Check all responses in this period
regular = EvaluationResponse.objects.filter(evaluation_period=period).select_related('evaluator', 'evaluatee')
print(f"\nRegular responses: {regular.count()}")
for r in regular:
    evaluator_name = r.evaluator.username if r.evaluator else "NULL"
    evaluatee_name = r.evaluatee.username if r.evaluatee else "NULL"
    print(f"  {evaluator_name} → {evaluatee_name} (Submitted: {r.submitted_at})")

irregular = IrregularEvaluation.objects.filter(evaluation_period=period).select_related('evaluator', 'evaluatee')
print(f"\nIrregular responses: {irregular.count()}")
for r in irregular:
    evaluator_name = r.evaluator.username if r.evaluator else "NULL"
    evaluatee_name = r.evaluatee.username if r.evaluatee else "NULL"
    print(f"  {evaluator_name} → {evaluatee_name} (Submitted: {r.submitted_at})")

print("\n" + "=" * 80)
print("ALL ACTIVE PERIODS")
print("=" * 80)

active_periods = EvaluationPeriod.objects.filter(is_active=True)
print(f"\nTotal active periods: {active_periods.count()}")
for p in active_periods:
    print(f"  {p.name} (ID: {p.id}, Type: {p.evaluation_type})")

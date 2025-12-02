import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import EvaluationPeriod, EvaluationResponse, IrregularEvaluation, Evaluation
from django.utils import timezone

print("=" * 80)
print("CLEANING UP OLD DATA")
print("=" * 80)

# 1. Deactivate ALL active periods
print("\n1. Deactivating all active periods...")
active_periods = EvaluationPeriod.objects.filter(is_active=True)
print(f"   Found {active_periods.count()} active periods")
for p in active_periods:
    print(f"   - Deactivating: {p.name} (ID: {p.id})")
    p.is_active = False
    p.end_date = timezone.now()
    p.save()
print("   ✅ All periods deactivated")

# 2. Check Evaluation objects
print("\n2. Checking Evaluation template objects...")
evaluations = Evaluation.objects.all()
print(f"   Found {evaluations.count()} Evaluation objects")
for ev in evaluations:
    print(f"   - Type: {ev.evaluation_type}, Released: {ev.is_released}, Evaluator: {ev.evaluator}")
    # Set all to unreleased so we can release again
    ev.is_released = False
    ev.save()
print("   ✅ All evaluations set to unreleased")

print("\n" + "=" * 80)
print("CLEANUP COMPLETE!")
print("=" * 80)
print("\nNow you can:")
print("1. Go to edulytics.uk admin dashboard")
print("2. Click 'Release' button")
print("3. This will create a NEW period with timestamp")
print("4. Evaluate as a student")
print("5. Unrelease and Release again to test the cycle")
print("\n")

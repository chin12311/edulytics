import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluation.settings')
django.setup()

from main.models import Evaluation, EvaluationPeriod

print("\n🔍 CHECKING FOR ORPHANED EVALUATIONS...")
print("-" * 50)

# Find evaluations without periods
orphaned = Evaluation.objects.filter(evaluation_period__isnull=True)
print(f"Found {orphaned.count()} orphaned Evaluation records (without EvaluationPeriod)")

for eval_obj in orphaned:
    print(f"  - ID: {eval_obj.id} | Type: {eval_obj.evaluation_type} | Released: {eval_obj.is_released}")

# Find evaluations with is_released=True but no active period
inconsistent = []
for eval_obj in Evaluation.objects.filter(is_released=True):
    if eval_obj.evaluation_period:
        if not eval_obj.evaluation_period.is_active:
            inconsistent.append(eval_obj)
    else:
        inconsistent.append(eval_obj)

print(f"\nFound {len(inconsistent)} evaluations marked as released without active periods")
for eval_obj in inconsistent:
    period_info = f"Period ID: {eval_obj.evaluation_period.id}" if eval_obj.evaluation_period else "No period"
    print(f"  - ID: {eval_obj.id} | Type: {eval_obj.evaluation_type} | {period_info}")

print("\n" + "=" * 50)
print("🗑️  CLEANING UP ORPHANED RECORDS...")
print("=" * 50)

# Delete orphaned evaluations
deleted_count = orphaned.count()
if deleted_count > 0:
    orphaned.delete()
    print(f"✅ Deleted {deleted_count} orphaned Evaluation records")
else:
    print("✅ No orphaned records to delete")

# Fix inconsistent is_released flags
for eval_obj in inconsistent:
    if eval_obj.evaluation_period and not eval_obj.evaluation_period.is_active:
        eval_obj.is_released = False
        eval_obj.save()
        print(f"✅ Fixed Evaluation ID {eval_obj.id} - set is_released=False")

print("\n" + "=" * 50)
print("🔍 VERIFICATION - Current State:")
print("=" * 50)

all_evals = Evaluation.objects.all()
print(f"Total Evaluations: {all_evals.count()}")
for eval_obj in all_evals:
    period_info = f"Period: {eval_obj.evaluation_period.id if eval_obj.evaluation_period else 'None'}"
    print(f"  - ID: {eval_obj.id} | Type: {eval_obj.evaluation_type} | Released: {eval_obj.is_released} | {period_info}")

all_periods = EvaluationPeriod.objects.all()
print(f"\nTotal EvaluationPeriods: {all_periods.count()}")
for period in all_periods:
    print(f"  - ID: {period.id} | Type: {period.evaluation_type} | Active: {period.is_active} | Name: {period.period_name}")

print("\n✅ CLEANUP COMPLETE!\n")

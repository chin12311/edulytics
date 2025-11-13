"""
Script to delete all evaluation results from the database
Run this to clean up the old 40% results
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluation.settings')
django.setup()

from main.models import EvaluationResult, EvaluationPeriod, EvaluationResponse

print("=" * 80)
print("EVALUATION RESULTS CLEANUP")
print("=" * 80)

# Show current state
print("\n📊 BEFORE:")
print("-" * 80)
all_results = EvaluationResult.objects.all()
print(f"Total EvaluationResult records: {all_results.count()}")
for result in all_results:
    print(f"  • {result.user.username}: {result.total_percentage}%")

# Delete all results
print("\n🗑️  DELETING ALL EVALUATION RESULTS...")
count = EvaluationResult.objects.count()
EvaluationResult.objects.all().delete()
print(f"✅ Deleted {count} records")

# Show after state
print("\n✅ AFTER:")
print("-" * 80)
remaining = EvaluationResult.objects.count()
print(f"Total EvaluationResult records: {remaining}")
if remaining == 0:
    print("✅ All results cleared! Database is clean.")

print("\n" + "=" * 80)
print("Next steps:")
print("1. Release a new evaluation")
print("2. Submit fresh evaluation responses")
print("3. Results will be stored fresh with no old data")
print("=" * 80)

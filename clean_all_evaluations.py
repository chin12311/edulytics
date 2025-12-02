"""
CLEAN ALL EVALUATION DATA - Deletes all responses, irregular evaluations, and results
USE WITH CAUTION - This will permanently delete all evaluation data!
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import EvaluationResponse, IrregularEvaluation, EvaluationResult

print("\n" + "=" * 80)
print("DELETING ALL EVALUATION DATA")
print("=" * 80)

# Count before deletion
response_count = EvaluationResponse.objects.all().count()
irregular_count = IrregularEvaluation.objects.all().count()
result_count = EvaluationResult.objects.all().count()

print(f"\n📊 BEFORE DELETION:")
print(f"   - EvaluationResponse: {response_count}")
print(f"   - IrregularEvaluation: {irregular_count}")
print(f"   - EvaluationResult: {result_count}")
print(f"   - TOTAL: {response_count + irregular_count + result_count}")

# Delete all
print(f"\n🗑️ DELETING...")
EvaluationResponse.objects.all().delete()
IrregularEvaluation.objects.all().delete()
EvaluationResult.objects.all().delete()

# Count after deletion
response_count_after = EvaluationResponse.objects.all().count()
irregular_count_after = IrregularEvaluation.objects.all().count()
result_count_after = EvaluationResult.objects.all().count()

print(f"\n📊 AFTER DELETION:")
print(f"   - EvaluationResponse: {response_count_after}")
print(f"   - IrregularEvaluation: {irregular_count_after}")
print(f"   - EvaluationResult: {result_count_after}")
print(f"   - TOTAL: {response_count_after + irregular_count_after + result_count_after}")

if response_count_after == 0 and irregular_count_after == 0 and result_count_after == 0:
    print("\n✅ SUCCESS - All evaluation data has been deleted!")
    print("   Database is now clean and ready for new evaluations.")
else:
    print("\n⚠️ WARNING - Some records still remain!")

print("=" * 80 + "\n")

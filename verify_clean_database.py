"""
Verify that all evaluation responses have been deleted from the database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import EvaluationResponse, IrregularEvaluation, EvaluationResult
from django.utils import timezone

print("\n" + "=" * 80)
print("DATABASE CLEANUP VERIFICATION")
print("=" * 80)

# Check EvaluationResponse
response_count = EvaluationResponse.objects.all().count()
print(f"\n📊 EvaluationResponse table: {response_count} records")
if response_count > 0:
    print("   ⚠️ WARNING: Still has responses!")
    responses = EvaluationResponse.objects.all()[:5]
    for resp in responses:
        print(f"   - ID {resp.id}: {resp.evaluator.username} → {resp.evaluatee.username}")
else:
    print("   ✅ CLEAN - No responses")

# Check IrregularEvaluation
irregular_count = IrregularEvaluation.objects.all().count()
print(f"\n📊 IrregularEvaluation table: {irregular_count} records")
if irregular_count > 0:
    print("   ⚠️ WARNING: Still has irregular evaluations!")
    irregulars = IrregularEvaluation.objects.all()[:5]
    for irreg in irregulars:
        print(f"   - ID {irreg.id}: {irreg.evaluator.username} → {irreg.evaluatee.username}")
else:
    print("   ✅ CLEAN - No irregular evaluations")

# Check EvaluationResult
result_count = EvaluationResult.objects.all().count()
print(f"\n📊 EvaluationResult table: {result_count} records")
if result_count > 0:
    print("   ⚠️ WARNING: Still has results!")
    results = EvaluationResult.objects.all()[:5]
    for result in results:
        print(f"   - ID {result.id}: {result.user.username}, Section {result.section_id}, {result.total_percentage}%")
else:
    print("   ✅ CLEAN - No results")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

total = response_count + irregular_count + result_count
if total == 0:
    print("✅ DATABASE IS CLEAN - Ready for new evaluations")
else:
    print(f"⚠️ DATABASE STILL HAS {total} TOTAL RECORDS")
    print(f"   - {response_count} EvaluationResponse")
    print(f"   - {irregular_count} IrregularEvaluation")
    print(f"   - {result_count} EvaluationResult")
    
print("=" * 80 + "\n")

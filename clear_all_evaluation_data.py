from main.models import (EvaluationResponse, IrregularEvaluation, EvaluationResult, 
                         EvaluationPeriod, EvaluationHistory, Evaluation)

print("=" * 80)
print("CLEARING ALL EVALUATION DATA")
print("=" * 80)

# Count before deletion
eval_responses = EvaluationResponse.objects.all().count()
irregular_evals = IrregularEvaluation.objects.all().count()
eval_results = EvaluationResult.objects.all().count()
eval_history = EvaluationHistory.objects.all().count()
eval_periods = EvaluationPeriod.objects.all().count()
evaluations = Evaluation.objects.all().count()

print(f"\n📊 CURRENT DATA:")
print(f"  EvaluationResponse: {eval_responses}")
print(f"  IrregularEvaluation: {irregular_evals}")
print(f"  EvaluationResult: {eval_results}")
print(f"  EvaluationHistory: {eval_history}")
print(f"  EvaluationPeriod: {eval_periods}")
print(f"  Evaluation: {evaluations}")

print(f"\n🗑️  DELETING ALL RECORDS...")

# Delete all records
EvaluationResponse.objects.all().delete()
IrregularEvaluation.objects.all().delete()
EvaluationResult.objects.all().delete()
EvaluationHistory.objects.all().delete()
EvaluationPeriod.objects.all().delete()
Evaluation.objects.all().delete()

print(f"\n✅ DELETION COMPLETE!")
print(f"  ✓ Deleted {eval_responses} evaluation responses")
print(f"  ✓ Deleted {irregular_evals} irregular evaluations")
print(f"  ✓ Deleted {eval_results} evaluation results")
print(f"  ✓ Deleted {eval_history} evaluation history records")
print(f"  ✓ Deleted {eval_periods} evaluation periods")
print(f"  ✓ Deleted {evaluations} evaluation records")

print(f"\n📊 VERIFICATION:")
print(f"  EvaluationResponse: {EvaluationResponse.objects.all().count()}")
print(f"  IrregularEvaluation: {IrregularEvaluation.objects.all().count()}")
print(f"  EvaluationResult: {EvaluationResult.objects.all().count()}")
print(f"  EvaluationHistory: {EvaluationHistory.objects.all().count()}")
print(f"  EvaluationPeriod: {EvaluationPeriod.objects.all().count()}")
print(f"  Evaluation: {Evaluation.objects.all().count()}")

print("\n" + "=" * 80)
print("🎉 ALL EVALUATION DATA CLEARED - READY FOR FRESH START")
print("=" * 80)

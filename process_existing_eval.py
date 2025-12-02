from main.models import EvaluationResponse, EvaluationPeriod, EvaluationResult
from main.views import process_evaluation_period_to_results

print("=== MANUALLY PROCESSING UNPROCESSED EVALUATIONS ===\n")

# Find the December 2025 period
period = EvaluationPeriod.objects.get(name="Student Evaluation December 2025", evaluation_type='student')
print(f"Period: {period.name}")
print(f"Active: {period.is_active}")
print(f"Responses in period: {EvaluationResponse.objects.filter(evaluation_period=period).count()}")
print(f"Existing results: {EvaluationResult.objects.filter(evaluation_period=period).count()}")

print("\n=== Processing results ===")
processed_count = process_evaluation_period_to_results(period)
print(f"✓ Processed {processed_count} results")

print("\n=== After Processing ===")
results = EvaluationResult.objects.filter(evaluation_period=period)
print(f"Total results: {results.count()}")
for result in results:
    print(f"  {result.user.username} - Section {result.section.code}: {result.average_score:.2f}")

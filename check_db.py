from main.models import EvaluationResult, EvaluationPeriod, EvaluationResponse
from django.contrib.auth.models import User

print("=" * 80)
print("EVALUATION RESULTS IN DATABASE")
print("=" * 80)

# List all evaluation results
all_results = EvaluationResult.objects.all().select_related('user', 'evaluation_period', 'section')
print(f"\nTotal evaluation results: {all_results.count()}\n")

if all_results.count() == 0:
    print("✅ No evaluation results found in database!")
else:
    print("Results found:")
    for result in all_results:
        period_status = "ACTIVE" if result.evaluation_period.is_active else "ARCHIVED"
        section_name = result.section.code if result.section else "All Sections"
        print(f"  • {result.user.username:20} | Period: {result.evaluation_period.name:30} | {period_status:10} | {result.total_percentage}% | {result.total_responses} responses")

print("\n" + "=" * 80)
print("EVALUATION PERIODS IN DATABASE")
print("=" * 80)

all_periods = EvaluationPeriod.objects.all().order_by('-start_date')
print(f"\nTotal periods: {all_periods.count()}\n")

for period in all_periods:
    status = "ACTIVE" if period.is_active else "ARCHIVED"
    results_count = EvaluationResult.objects.filter(evaluation_period=period).count()
    print(f"  • {period.name:30} ({period.evaluation_type:10}) | {status:10} | {results_count} results")

print("\n" + "=" * 80)
print("EVALUATION RESPONSES IN DATABASE")
print("=" * 80)

all_responses = EvaluationResponse.objects.all()
print(f"\nTotal responses: {all_responses.count()}\n")

if all_responses.count() > 0:
    for response in all_responses[:10]:  # Show first 10
        print(f"  • {response.evaluatee.username} <- evaluated by {response.evaluator.username if response.evaluator else 'System'} at {response.submitted_at}")
    if all_responses.count() > 10:
        print(f"  ... and {all_responses.count() - 10} more")

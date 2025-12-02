from main.models import EvaluationPeriod, EvaluationResponse
from django.utils import timezone

print("=== Current Evaluation Periods ===\n")
periods = EvaluationPeriod.objects.filter(evaluation_type='student').order_by('-start_date')[:5]
for p in periods:
    print(f"Period: {p.name}")
    print(f"  ID: {p.id}")
    print(f"  Active: {p.is_active}")
    print(f"  Start: {p.start_date}")
    print(f"  End: {p.end_date}")
    responses = EvaluationResponse.objects.filter(evaluation_period=p)
    print(f"  Responses: {responses.count()}")
    if responses.exists():
        for r in responses[:3]:
            print(f"    - {r.evaluator.username} -> {r.evaluatee.username}")
    print()

# Check for active periods
active = EvaluationPeriod.objects.filter(is_active=True, evaluation_type='student')
print(f"Active student periods: {active.count()}")
for p in active:
    print(f"  - {p.name} (ID: {p.id})")

from django.contrib.auth.models import User
from main.models import EvaluationResponse, IrregularEvaluation, EvaluationResult, EvaluationPeriod

print("=== Complete Database Dump ===\n")

# Check all users
print(f"Total Users: {User.objects.count()}")
print("\nAll usernames:")
for user in User.objects.all().order_by('username'):
    print(f"  - {user.username} (ID: {user.id})")

# Check periods
print(f"\n=== Evaluation Periods ===")
periods = EvaluationPeriod.objects.all()
print(f"Total periods: {periods.count()}")
for p in periods:
    print(f"  Period {p.id}: {p.name}")
    print(f"    Active: {p.is_active}, Start: {p.start_date}, End: {p.end_date}")
    print(f"    Responses in this period: {EvaluationResponse.objects.filter(evaluation_period=p).count()}")
    print(f"    Irregular in this period: {IrregularEvaluation.objects.filter(evaluation_period=p).count()}")

# Raw count - NO FILTERS
print(f"\n=== Raw Counts (No Filters) ===")
print(f"EvaluationResponse.objects.all().count(): {EvaluationResponse.objects.all().count()}")
print(f"IrregularEvaluation.objects.all().count(): {IrregularEvaluation.objects.all().count()}")
print(f"EvaluationResult.objects.all().count(): {EvaluationResult.objects.all().count()}")

# Show ALL responses
print(f"\n=== ALL Evaluation Responses ===")
for r in EvaluationResponse.objects.all():
    print(f"  ID {r.id}: {r.evaluator.username} -> {r.evaluatee.username}")
    print(f"    Period: {r.evaluation_period.name}, Submitted: {r.submitted_at}")

# Show ALL irregular
print(f"\n=== ALL Irregular Evaluations ===")
for i in IrregularEvaluation.objects.all():
    print(f"  ID {i.id}: {i.evaluator.username} -> {i.evaluatee_name}")
    print(f"    Period: {i.evaluation_period.name}, Submitted: {i.submitted_at}")

# Show ALL results
print(f"\n=== ALL Evaluation Results ===")
for r in EvaluationResult.objects.all():
    print(f"  ID {r.id}: {r.user.username} - Score: {r.average_score}")
    print(f"    Period: {r.evaluation_period.name}, Section: {r.section}")

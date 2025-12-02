from main.models import EvaluationResponse, IrregularEvaluation, EvaluationResult, EvaluationPeriod
from django.contrib.auth.models import User

print("=== CURRENT DATABASE STATE ===\n")

# Check periods
print("=== Active Periods ===")
active_periods = EvaluationPeriod.objects.filter(is_active=True)
for p in active_periods:
    print(f"  {p.name} ({p.evaluation_type}) - Active: {p.is_active}")

print("\n=== Recent Periods ===")
recent_periods = EvaluationPeriod.objects.all().order_by('-start_date')[:3]
for p in recent_periods:
    print(f"  {p.name} ({p.evaluation_type}) - Active: {p.is_active}, End: {p.end_date}")

# Check evaluations
regular_count = EvaluationResponse.objects.count()
irregular_count = IrregularEvaluation.objects.count()
print(f"\n=== Evaluations ===")
print(f"Regular: {regular_count}")
print(f"Irregular: {irregular_count}")

if regular_count > 0:
    print("\n--- Regular Evaluations ---")
    for r in EvaluationResponse.objects.all().order_by('-submitted_at'):
        print(f"  {r.evaluator.username} -> {r.evaluatee.username}")
        print(f"    Period: {r.evaluation_period.name if r.evaluation_period else 'None'}")
        print(f"    Section: {r.student_section}")
        print(f"    Evaluator role: {r.evaluator.userprofile.role}")
        print(f"    Evaluatee role: {r.evaluatee.userprofile.role}")
        print(f"    Submitted: {r.submitted_at}")
        print()

if irregular_count > 0:
    print("--- Irregular Evaluations ---")
    for i in IrregularEvaluation.objects.all().order_by('-submitted_at'):
        print(f"  {i.evaluator.username} -> {i.evaluatee.username}")
        print(f"    Period: {i.evaluation_period.name if i.evaluation_period else 'None'}")
        print(f"    Student number: {i.student_number}")
        print(f"    Submitted: {i.submitted_at}")
        print()

# Check results
results = EvaluationResult.objects.all()
print(f"=== Evaluation Results: {results.count()} ===")
for result in results:
    print(f"\n  User: {result.user.username}")
    print(f"  Period: {result.evaluation_period.name}")
    print(f"  Section: {result.section.code if result.section else 'None'}")
    print(f"  Score: {result.total_percentage:.2f}%")
    print(f"  Responses: {result.total_responses}")

# Check specific section C405
print("\n=== C405 Analysis ===")
c405_responses = EvaluationResponse.objects.filter(student_section='C405')
print(f"C405 Regular responses: {c405_responses.count()}")
for r in c405_responses:
    print(f"  {r.evaluator.username} -> {r.evaluatee.username} (Period: {r.evaluation_period.name if r.evaluation_period else 'None'})")

c405_results = EvaluationResult.objects.filter(section__code='C405')
print(f"\nC405 Results: {c405_results.count()}")
for r in c405_results:
    print(f"  {r.user.username}: {r.total_percentage:.2f}%")

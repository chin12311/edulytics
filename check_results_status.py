from main.models import EvaluationResponse, IrregularEvaluation, EvaluationResult, EvaluationPeriod
from django.contrib.auth.models import User

print("=== PRODUCTION DATABASE STATUS ===\n")

# Check evaluations
regular = EvaluationResponse.objects.count()
irregular = IrregularEvaluation.objects.count()
results = EvaluationResult.objects.count()

print(f"Regular Evaluations: {regular}")
print(f"Irregular Evaluations: {irregular}")
print(f"Evaluation Results: {results}")

# Check periods
print("\n=== Evaluation Periods ===")
periods = EvaluationPeriod.objects.all().order_by('-start_date')
for p in periods:
    print(f"\nPeriod: {p.name}")
    print(f"  Type: {p.evaluation_type}")
    print(f"  Active: {p.is_active}")
    print(f"  Start: {p.start_date}")
    print(f"  End: {p.end_date}")

# Check the evaluation details
if regular > 0:
    print("\n=== Evaluation Details ===")
    for r in EvaluationResponse.objects.all():
        print(f"\nEvaluation ID {r.id}:")
        print(f"  Evaluator: {r.evaluator.username}")
        print(f"  Evaluatee: {r.evaluatee.username}")
        print(f"  Period: {r.evaluation_period.name if r.evaluation_period else 'None'}")
        print(f"  Section: {r.student_section}")
        print(f"  Submitted: {r.submitted_at}")

# Check if aeroncaligagan has results
print("\n=== Checking aeroncaligagan Results ===")
try:
    aeron = User.objects.get(username='aeroncaligagan')
    aeron_results = EvaluationResult.objects.filter(user=aeron)
    print(f"Results for aeroncaligagan: {aeron_results.count()}")
    for result in aeron_results:
        print(f"  Period: {result.evaluation_period.name}")
        print(f"  Section: {result.section}")
        print(f"  Score: {result.average_score:.2f}")
except User.DoesNotExist:
    print("User aeroncaligagan not found")

# Check profile settings data
print("\n=== Profile Data Check ===")
try:
    aeron = User.objects.get(username='aeroncaligagan')
    profile = aeron.userprofile
    print(f"Role: {profile.role}")
    print(f"Section: {profile.section}")
    
    # Check assigned sections
    from main.models import SectionAssignment
    assignments = SectionAssignment.objects.filter(user=aeron)
    print(f"Section Assignments: {assignments.count()}")
    for assignment in assignments:
        print(f"  - {assignment.section.code}")
except Exception as e:
    print(f"Error: {e}")

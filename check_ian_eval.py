from main.models import EvaluationResponse, IrregularEvaluation
from django.contrib.auth.models import User

print("=== Checking for Ian Ilao's Evaluation ===\n")

# Check if user exists
try:
    ian = User.objects.get(username='ianilao')
    print(f"✓ User 'ianilao' found (ID: {ian.id})")
except User.DoesNotExist:
    print("✗ User 'ianilao' NOT FOUND")
    ian = None

if ian:
    # Check regular evaluations
    regular_evals = EvaluationResponse.objects.filter(evaluator=ian)
    print(f"\nRegular Evaluations by ianilao: {regular_evals.count()}")
    for eval in regular_evals:
        print(f"  - Evaluating: {eval.evaluatee.username}")
        print(f"    Period: {eval.evaluation_period.name}")
        print(f"    Section: {eval.student_section}")
        print(f"    Submitted: {eval.submitted_at}")
    
    # Check irregular evaluations
    irregular_evals = IrregularEvaluation.objects.filter(evaluator=ian)
    print(f"\nIrregular Evaluations by ianilao: {irregular_evals.count()}")
    for eval in irregular_evals:
        print(f"  - Evaluating: {eval.evaluatee.username}")
        print(f"    Period: {eval.evaluation_period.name}")
        print(f"    Submitted: {eval.submitted_at}")

# Check all recent evaluations
print(f"\n=== All Recent Evaluations (Last 10) ===")
all_evals = EvaluationResponse.objects.all().order_by('-submitted_at')[:10]
print(f"Total evaluations in DB: {EvaluationResponse.objects.count()}")
for eval in all_evals:
    print(f"  - {eval.evaluator.username} -> {eval.evaluatee.username} (at {eval.submitted_at})")

all_irregular = IrregularEvaluation.objects.all().order_by('-submitted_at')[:10]
print(f"\nTotal irregular in DB: {IrregularEvaluation.objects.count()}")
for eval in all_irregular:
    print(f"  - {eval.evaluator.username} -> {eval.evaluatee.username} (at {eval.submitted_at})")

from main.models import EvaluationResponse, IrregularEvaluation, EvaluationResult

print("=== PRODUCTION DATABASE (evaluation) ===\n")

regular = EvaluationResponse.objects.count()
irregular = IrregularEvaluation.objects.count()
results = EvaluationResult.objects.count()

print(f"Regular Evaluations: {regular}")
print(f"Irregular Evaluations: {irregular}")
print(f"Evaluation Results: {results}")

if regular > 0:
    print("\n=== Recent Regular Evaluations ===")
    for r in EvaluationResponse.objects.all().order_by('-submitted_at')[:5]:
        print(f"  ID {r.id}: {r.evaluator.username} -> {r.evaluatee.username} at {r.submitted_at}")

if irregular > 0:
    print("\n=== Recent Irregular Evaluations ===")
    for i in IrregularEvaluation.objects.all().order_by('-submitted_at')[:5]:
        print(f"  ID {i.id}: {i.evaluator.username} -> {i.evaluatee_name} at {i.submitted_at}")

if results > 0:
    print("\n=== Recent Results ===")
    for r in EvaluationResult.objects.all().order_by('-id')[:5]:
        print(f"  {r.user.username}: {r.average_score:.2f}")

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import Evaluation, EvaluationPeriod, EvaluationResponse, IrregularEvaluation
from django.contrib.auth.models import User

print("=" * 80)
print("CHECKING EVALUATION OBJECTS")
print("=" * 80)

# Check all Evaluation objects
evaluations = Evaluation.objects.all().order_by('-created_at')
print(f"\nTotal Evaluation objects: {evaluations.count()}")
for ev in evaluations[:10]:
    print(f"\n  ID: {ev.id}")
    print(f"  Evaluator: {ev.evaluator if ev.evaluator else 'Unknown/NULL'}")
    print(f"  Type: {ev.evaluation_type}")
    print(f"  Is Released: {ev.is_released}")
    print(f"  Created: {ev.created_at}")
    if ev.evaluation_period:
        print(f"  Period: {ev.evaluation_period.name} (Active: {ev.evaluation_period.is_active})")
    else:
        print(f"  Period: None")

print("\n" + "=" * 80)
print("CHECKING EVALUATION PERIODS")
print("=" * 80)

# Check student periods
student_periods = EvaluationPeriod.objects.filter(evaluation_type='student').order_by('-created_at')[:3]
print(f"\nRecent Student Periods:")
for p in student_periods:
    print(f"\n  {p.name} (ID: {p.id})")
    print(f"  Active: {p.is_active}")
    print(f"  Created: {p.created_at}")
    
    # Count evaluations linked to this period
    eval_count = Evaluation.objects.filter(evaluation_period=p).count()
    print(f"  Evaluation objects: {eval_count}")
    
    # Count responses in this period
    response_count = EvaluationResponse.objects.filter(evaluation_period=p).count()
    irregular_count = IrregularEvaluation.objects.filter(evaluation_period=p).count()
    print(f"  Responses: {response_count} regular, {irregular_count} irregular")

print("\n" + "=" * 80)
print("CHECKING AERONCALIGAGAN'S SUBMISSIONS")
print("=" * 80)

try:
    aeron = User.objects.get(username='aeroncaligagan')
    
    # Check regular responses
    responses = EvaluationResponse.objects.filter(evaluator=aeron).select_related('evaluation_period', 'evaluatee')
    print(f"\nRegular responses by {aeron.username}: {responses.count()}")
    for r in responses:
        print(f"  → {r.evaluatee.username} | Period: {r.evaluation_period.name if r.evaluation_period else 'NO PERIOD'} (Active: {r.evaluation_period.is_active if r.evaluation_period else 'N/A'})")
    
    # Check irregular responses
    irregular = IrregularEvaluation.objects.filter(evaluator=aeron).select_related('evaluation_period', 'evaluatee')
    print(f"\nIrregular responses by {aeron.username}: {irregular.count()}")
    for r in irregular:
        print(f"  → {r.evaluatee.username} | Period: {r.evaluation_period.name if r.evaluation_period else 'NO PERIOD'} (Active: {r.evaluation_period.is_active if r.evaluation_period else 'N/A'})")
        
except User.DoesNotExist:
    print("User not found")

print("\n")

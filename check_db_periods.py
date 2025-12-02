import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import EvaluationPeriod, EvaluationResponse, IrregularEvaluation
from django.contrib.auth.models import User

print("=" * 80)
print("EVALUATION PERIODS")
print("=" * 80)

# Check student periods
print("\n📚 STUDENT EVALUATION PERIODS:")
student_periods = EvaluationPeriod.objects.filter(evaluation_type='student').order_by('-created_at')
for p in student_periods:
    print(f"\n  Period: {p.name}")
    print(f"  ID: {p.id}")
    print(f"  Active: {p.is_active}")
    print(f"  Start: {p.start_date}")
    print(f"  End: {p.end_date}")
    print(f"  Created: {p.created_at}")
    
    # Count responses in this period
    regular_count = EvaluationResponse.objects.filter(evaluation_period=p).count()
    irregular_count = IrregularEvaluation.objects.filter(evaluation_period=p).count()
    print(f"  Regular Responses: {regular_count}")
    print(f"  Irregular Responses: {irregular_count}")

# Check peer periods
print("\n\n👥 PEER EVALUATION PERIODS:")
peer_periods = EvaluationPeriod.objects.filter(evaluation_type='peer').order_by('-created_at')
for p in peer_periods:
    print(f"\n  Period: {p.name}")
    print(f"  ID: {p.id}")
    print(f"  Active: {p.is_active}")
    print(f"  Start: {p.start_date}")
    print(f"  End: {p.end_date}")
    print(f"  Created: {p.created_at}")
    
    # Count responses in this period
    response_count = EvaluationResponse.objects.filter(evaluation_period=p).count()
    print(f"  Responses: {response_count}")

print("\n" + "=" * 80)
print("CHECKING SPECIFIC USER EVALUATIONS")
print("=" * 80)

# Check aeroncaligagan's evaluations
try:
    aeron = User.objects.get(username='aeroncaligagan')
    print(f"\n🔍 Evaluations by {aeron.username}:")
    
    regular_evals = EvaluationResponse.objects.filter(evaluator=aeron).select_related('evaluatee', 'evaluation_period')
    for ev in regular_evals:
        print(f"  → {ev.evaluatee.username} in period '{ev.evaluation_period.name}' (ID: {ev.evaluation_period.id}, Active: {ev.evaluation_period.is_active})")
    
    irregular_evals = IrregularEvaluation.objects.filter(evaluator=aeron).select_related('evaluatee', 'evaluation_period')
    for ev in irregular_evals:
        print(f"  → [IRREGULAR] {ev.evaluatee.username} in period '{ev.evaluation_period.name}' (ID: {ev.evaluation_period.id}, Active: {ev.evaluation_period.is_active})")
    
    if not regular_evals.exists() and not irregular_evals.exists():
        print("  No evaluations found")
        
except User.DoesNotExist:
    print("  User 'aeroncaligagan' not found")

print("\n")

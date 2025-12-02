import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import EvaluationHistory, EvaluationResult, EvaluationPeriod
from django.contrib.auth.models import User

print("=" * 80)
print("EVALUATION HISTORY RECORDS IN DATABASE")
print("=" * 80)

histories = EvaluationHistory.objects.all().select_related('user', 'evaluation_period')
print(f"\nTotal EvaluationHistory records: {histories.count()}")
for h in histories:
    print(f"\n  ID: {h.id}")
    print(f"  User: {h.user.username if h.user else 'NULL'}")
    print(f"  Period: {h.evaluation_period.name if h.evaluation_period else 'NULL'}")
    print(f"  Overall Score: {h.overall_score}")
    print(f"  Section: {h.section.code if h.section else 'N/A'}")
    print(f"  Created: {h.created_at}")

print("\n" + "=" * 80)
print("CURRENT EVALUATION RESULTS")
print("=" * 80)

results = EvaluationResult.objects.all().select_related('user', 'evaluation_period', 'section')
print(f"\nTotal EvaluationResult records: {results.count()}")
for r in results:
    print(f"\n  ID: {r.id}")
    print(f"  User: {r.user.username if r.user else 'NULL'}")
    print(f"  Period: {r.evaluation_period.name if r.evaluation_period else 'NULL'}")
    print(f"  Overall Score: {r.overall_score}")
    print(f"  Section: {r.section.code if r.section else 'N/A'}")
    print(f"  Created: {r.created_at}")

print("\n" + "=" * 80)
print("CHECK FOR SPECIFIC USER (aeroncaligagan)")
print("=" * 80)

try:
    user = User.objects.get(username='aeroncaligagan')
    
    print(f"\nHistory records for {user.username}:")
    user_histories = EvaluationHistory.objects.filter(user=user).select_related('evaluation_period', 'section')
    print(f"Count: {user_histories.count()}")
    for h in user_histories:
        print(f"  - Period: {h.evaluation_period.name}, Score: {h.overall_score}, Section: {h.section.code if h.section else 'N/A'}")
    
    print(f"\nCurrent results for {user.username}:")
    user_results = EvaluationResult.objects.filter(user=user).select_related('evaluation_period', 'section')
    print(f"Count: {user_results.count()}")
    for r in user_results:
        print(f"  - Period: {r.evaluation_period.name}, Score: {r.overall_score}, Section: {r.section.code if r.section else 'N/A'}")
        
except User.DoesNotExist:
    print("User not found")

print("\n")

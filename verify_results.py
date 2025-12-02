from main.models import EvaluationResult
from django.contrib.auth.models import User

print("=== CHECKING RESULTS ===\n")

results = EvaluationResult.objects.all()
print(f"Total Results: {results.count()}")

for result in results:
    print(f"\nUser: {result.user.username}")
    print(f"Period: {result.evaluation_period.name}")
    print(f"Section: {result.section.code if result.section else 'No section'}")
    print(f"Total Percentage: {result.total_percentage:.2f}%")
    print(f"Responses: {result.total_responses}")

# Check aeroncaligagan specifically
print("\n=== aeroncaligagan Profile Check ===")
aeron = User.objects.get(username='aeroncaligagan')
aeron_results = EvaluationResult.objects.filter(user=aeron)
print(f"Results: {aeron_results.count()}")
for r in aeron_results:
    print(f"  Period: {r.evaluation_period.name}")
    print(f"  Section: {r.section.code}")
    print(f"  Score: {r.total_percentage:.2f}%")

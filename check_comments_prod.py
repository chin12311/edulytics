from main.models import EvaluationResponse, User
from django.contrib.auth.models import User

# Check total evaluations
total = EvaluationResponse.objects.count()
with_comments = EvaluationResponse.objects.filter(comments__isnull=False).exclude(comments='').count()

print(f"Total evaluations: {total}")
print(f"With comments: {with_comments}")
print(f"Percentage: {(with_comments/total*100) if total > 0 else 0:.1f}%")

# Check comments for a specific faculty
try:
    user = User.objects.filter(first_name__icontains='Jannette').first()
    if user:
        print(f"\nChecking {user.get_full_name()}...")
        responses = EvaluationResponse.objects.filter(
            evaluatee=user,
            comments__isnull=False
        ).exclude(comments='')
        print(f"  Has {responses.count()} evaluations with comments")
        if responses.count() > 0:
            for resp in responses[:3]:
                print(f"  - {resp.comments[:100]}")
except Exception as e:
    print(f"Error: {e}")

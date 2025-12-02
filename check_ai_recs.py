from main.models import AiRecommendation, EvaluationPeriod, User

# Get the user (aeroncaligagan)
user = User.objects.get(username='aeroncaligagan')

# Get all periods
periods = EvaluationPeriod.objects.filter(is_active=False).order_by('-created_at')[:5]

print(f"Checking AI recommendations for user: {user.username}")
print(f"\nTotal inactive periods: {periods.count()}")

for period in periods:
    print(f"\nPeriod: {period.name} (ID: {period.id})")
    recs = AiRecommendation.objects.filter(user=user, evaluation_period=period)
    print(f"  AI Recommendations: {recs.count()}")
    for rec in recs:
        print(f"    - {rec.title if rec.title else 'No title'}: {rec.recommendation[:100] if rec.recommendation else 'No recommendation'}...")

# Check all AI recommendations for this user
all_recs = AiRecommendation.objects.filter(user=user)
print(f"\n\nTotal AI recommendations for {user.username}: {all_recs.count()}")
for rec in all_recs:
    period_name = rec.evaluation_period.name if rec.evaluation_period else "No period"
    print(f"  Period: {period_name} (ID: {rec.evaluation_period.id if rec.evaluation_period else 'N/A'})")
    print(f"    Title: {rec.title}")
    print(f"    Has recommendation: {bool(rec.recommendation)}")
    print()

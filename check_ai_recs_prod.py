from main.models import AiRecommendation

recs = AiRecommendation.objects.all()
print(f"Total cached recommendations: {recs.count()}")

if recs.count() > 0:
    rec = recs.first()
    print(f"\nFirst recommendation:")
    print(f"Title: {rec.title}")
    print(f"Priority: {rec.priority}")
    print(f"\nDescription (first 800 chars):")
    print(rec.description[:800])
    print("...")
else:
    print("No cached recommendations - they will be generated on first view")

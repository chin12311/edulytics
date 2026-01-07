from main.models import AiRecommendation
AiRecommendation.objects.all().delete()
print("Cache cleared successfully!")

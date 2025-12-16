from main.models import AiRecommendation

count = AiRecommendation.objects.all().count()
print(f'Found {count} cached AI recommendations')

AiRecommendation.objects.all().delete()
print('All cached AI recommendations cleared!')
print('They will regenerate with the new scoring context on next view')

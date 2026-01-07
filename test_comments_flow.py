from django.contrib.auth.models import User
from main.models import EvaluationResponse, EvaluationPeriod, Section, SectionAssignment
from main.ai_service import TeachingAIRecommendationService
import json

# Get Jannette Zapata or first faculty with comments
user = User.objects.filter(first_name__icontains='Jannette').first()
if not user:
    users_with_comments = EvaluationResponse.objects.filter(
        comments__isnull=False
    ).exclude(comments='').values_list('evaluatee', flat=True).distinct()
    if users_with_comments:
        user = User.objects.get(id=users_with_comments[0])

if user:
    print(f"Testing for user: {user.get_full_name()} ({user.username})")
    
    # Get their assigned section
    assignments = SectionAssignment.objects.filter(user=user)
    if assignments.exists():
        section = assignments.first().section
        section_code = section.code
        print(f"Section: {section_code}")
        
        # Get latest period
        period = EvaluationPeriod.objects.filter(
            evaluation_type='student',
            is_active=False
        ).order_by('-end_date').first()
        
        if period:
            print(f"Period: {period}")
            
            # Get comments
            comments = EvaluationResponse.objects.filter(
                evaluatee=user,
                student_section=section_code,
                evaluation_period=period,
                comments__isnull=False
            ).exclude(comments='').values_list('comments', flat=True)
            
            print(f"\nComments found: {comments.count()}")
            for i, comment in enumerate(comments, 1):
                print(f"{i}. {comment}")
            
            # Categorize
            positive = []
            negative = []
            mixed = []
            
            for comment in comments:
                sentiment = TeachingAIRecommendationService.analyze_comment_sentiment(comment)
                if sentiment == 'positive':
                    positive.append(comment)
                elif sentiment == 'negative':
                    negative.append(comment)
                elif sentiment == 'mixed':
                    mixed.append(comment)
            
            print(f"\nCategorized:")
            print(f"Positive: {len(positive)}")
            print(f"Negative: {len(negative)}")
            print(f"Mixed: {len(mixed)}")
            
            # Create section_data like the view does
            section_data = {
                'has_data': True,
                'category_scores': [26.6, 23.2, 16.0, 16.7],
                'total_percentage': 82.5,
                'evaluation_count': 2,
                'positive_comments': positive,
                'negative_comments': negative,
                'mixed_comments': mixed
            }
            
            print(f"\nSection data: {json.dumps({k: len(v) if isinstance(v, list) else v for k, v in section_data.items()}, indent=2)}")
            
            # Test AI service
            print("\n" + "="*60)
            print("Testing AI Service...")
            print("="*60)
            
            ai_service = TeachingAIRecommendationService()
            context = ai_service._prepare_ai_context(user, section_data, section_code, "Faculty", "student")
            
            print("\nContext sent to AI:")
            print(context[:2000])  # First 2000 chars
            
        else:
            print("No period found")
    else:
        print("No section assignments")
else:
    print("No user found")

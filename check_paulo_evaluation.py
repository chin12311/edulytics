import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import UserProfile, DeanEvaluationResponse

# Find Paulo Madrigal
try:
    paulo_user = User.objects.filter(first_name__icontains='paulo', last_name__icontains='madrigal').first()
    if not paulo_user:
        paulo_user = User.objects.filter(username__icontains='paulo').first()
    
    if paulo_user:
        print(f"Found user: {paulo_user.get_full_name()} (ID: {paulo_user.id})")
        print(f"Username: {paulo_user.username}")
        print(f"Email: {paulo_user.email}")
        
        # Get profile
        try:
            profile = UserProfile.objects.get(user=paulo_user)
            print(f"Role: {profile.role}")
            print(f"Institute: {profile.institute}")
        except:
            print("No profile found")
        
        print("\n" + "="*60)
        print("DEAN EVALUATION RESPONSES (Faculty → Paulo):")
        print("="*60)
        
        # Get all dean evaluations where Paulo is the evaluatee
        dean_responses = DeanEvaluationResponse.objects.filter(evaluatee=paulo_user)
        
        if dean_responses.exists():
            print(f"\nTotal evaluations received: {dean_responses.count()}\n")
            
            # Rating mapping
            rating_to_numeric = {
                'Poor': 1,
                'Unsatisfactory': 2,
                'Satisfactory': 3,
                'Very Satisfactory': 4,
                'Outstanding': 5
            }
            
            for idx, response in enumerate(dean_responses, 1):
                print(f"\nEvaluation #{idx}:")
                print(f"  Evaluator: {response.evaluator.get_full_name()}")
                print(f"  Submitted: {response.submitted_at}")
                print(f"  Period: {response.evaluation_period}")
                
                # Show all questions and ratings
                total_score = 0
                print("\n  Individual Question Ratings:")
                for i in range(1, 16):
                    question_field = f'question{i}'
                    rating = getattr(response, question_field)
                    numeric_score = rating_to_numeric.get(rating, 1)
                    total_score += numeric_score
                    print(f"    Q{i:2d}: {rating:20s} = {numeric_score}")
                
                # Calculate percentage
                max_possible = 15 * 5  # 15 questions, max 5 points each = 75
                percentage = (total_score / max_possible) * 100
                
                print(f"\n  Total Score: {total_score}/{max_possible}")
                print(f"  Percentage: {percentage:.2f}%")
                
                if response.comments:
                    print(f"  Comments: {response.comments}")
            
            # Calculate overall average
            print("\n" + "="*60)
            print("OVERALL CALCULATION:")
            print("="*60)
            
            grand_total = 0
            for response in dean_responses:
                response_total = 0
                for i in range(1, 16):
                    question_field = f'question{i}'
                    rating = getattr(response, question_field)
                    score = rating_to_numeric.get(rating, 1)
                    response_total += score
                grand_total += response_total
            
            avg_total_score = grand_total / dean_responses.count()
            overall_percentage = (avg_total_score / 75) * 100
            
            print(f"\nTotal raw score across all evaluations: {grand_total}")
            print(f"Average total score: {avg_total_score:.2f}")
            print(f"Overall Percentage: {overall_percentage:.2f}%")
            
        else:
            print("\nNo dean evaluation responses found for Paulo Madrigal")
        
    else:
        print("Paulo Madrigal not found in the database")
        print("\nSearching all users with 'paulo' in name:")
        users = User.objects.filter(first_name__icontains='paulo')
        for u in users:
            print(f"  - {u.get_full_name()} ({u.username})")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

"""
Test compute_peer_scores function directly
"""
import os
import sys
import django

sys.path.append('/home/ubuntu/edulytics')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import EvaluationPeriod, EvaluationResponse, User
from main.views import compute_peer_scores

def main():
    # Get peer period
    peer_period = EvaluationPeriod.objects.filter(evaluation_type='peer').first()
    print(f"Peer Period: {peer_period.name} (ID: {peer_period.id})")
    print()
    
    # Get jadepuno
    user = User.objects.get(username='jadepuno')
    print(f"Testing for user: {user.username}")
    print()
    
    # Check responses manually
    print("=== MANUAL CHECK ===")
    responses = EvaluationResponse.objects.filter(
        evaluatee=user,
        evaluation_period=peer_period
    )
    print(f"Responses for jadepuno in peer period: {responses.count()}")
    
    if responses.exists():
        for r in responses:
            print(f"  Response ID {r.id}:")
            print(f"    Evaluator: {r.evaluator.username}")
            print(f"    Questions 1-5: {r.question1}, {r.question2}, {r.question3}, {r.question4}, {r.question5}")
            print()
        
        # Calculate manually
        rating_to_numeric = {
            'Poor': 1,
            'Unsatisfactory': 2,
            'Satisfactory': 3,
            'Very Satisfactory': 4,
            'Outstanding': 5
        }
        
        total_score = 0
        total_questions = 0
        
        for response in responses:
            for i in range(1, 16):  # 15 questions
                question_key = f'question{i}'
                rating_text = getattr(response, question_key, 'Poor')
                score = rating_to_numeric.get(rating_text, 1)
                total_score += score
                total_questions += 1
                print(f"  Q{i}: {rating_text} = {score}")
        
        print()
        print(f"Total score: {total_score}")
        print(f"Total questions: {total_questions}")
        average_score = total_score / total_questions
        print(f"Average score (out of 5): {average_score}")
        total_percentage = (average_score / 5) * 100
        print(f"Percentage: {total_percentage}%")
    
    print()
    print("=== FUNCTION RESULT ===")
    result = compute_peer_scores(user, evaluation_period=peer_period)
    print(f"compute_peer_scores result: {result}")
    print(f"Total percentage (index 4): {result[4]}")

if __name__ == '__main__':
    main()

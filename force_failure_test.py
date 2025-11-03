# force_failure_test.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import User, UserProfile, EvaluationFailureLog
from main.services.evaluation_service import EvaluationService
from django.utils import timezone

def force_failure_test():
    print("🔧 FORCING FAILURE SCENARIO TEST")
    
    instructor = User.objects.filter(username='albertoreyes').first()
    if not instructor:
        print("❌ Instructor not found")
        return
    
    print(f"Instructor: {instructor.username}")
    
    # Manually set failure count to 1 (simulate first failure)
    profile, created = UserProfile.objects.get_or_create(
        user=instructor,
        defaults={'role': 'Faculty', 'institute': 'CCA'}
    )
    profile.evaluation_failure_count = 1
    profile.save()
    
    print(f"Manually set failure count to: {profile.evaluation_failure_count}")
    
    # Manually add a failure log
    EvaluationFailureLog.objects.create(
        user=instructor,
        score=65.0,
        passing_score=70.0
    )
    
    # Now process results with a failing score
    print("Processing with failing score...")
    
    # We need to simulate a failing overall score
    # Let's check what the actual score is first
    from main.views import compute_category_scores
    scores = compute_category_scores(instructor)
    actual_score = scores[4] if scores and len(scores) > 4 else 0
    print(f"Actual calculated score: {actual_score}%")
    
    # If the score is actually passing, we need to understand why
    if actual_score >= 70.0:
        print("❌ PROBLEM IDENTIFIED: The evaluations are actually scoring ABOVE 70%")
        print("   Even with 'low' scores, the averaging might be pushing it above 70%")
        print("   Let's check individual evaluation scores...")
        
        # Check individual evaluation scores
        from main.models import EvaluationResponse
        evaluations = EvaluationResponse.objects.filter(evaluatee=instructor)
        for eval in evaluations:
            print(f"   Evaluation from {eval.evaluator.username}:")
            # Calculate score for this single evaluation
            rating_values = {
                'Poor': 1, 'Unsatisfactory': 2, 'Satisfactory': 3, 
                'Very Satisfactory': 4, 'Outstanding': 5
            }
            total_score = 0
            for i in range(1, 16):
                question_key = f'question{i}'
                rating = getattr(eval, question_key, 'Poor')
                total_score += rating_values.get(rating, 1)
            
            single_score_percentage = (total_score / (15 * 5)) * 100
            print(f"     Single evaluation score: {single_score_percentage:.2f}%")
    
    # Force process with a failing score
    print("\nForcing failure processing with 65% score...")
    EvaluationService._handle_evaluation_failure(instructor, 65.0)
    
    # Check final status
    final_profile = UserProfile.objects.get(user=instructor)
    print(f"Final failure count: {final_profile.evaluation_failure_count}")
    print(f"Alert sent: {final_profile.failure_alert_sent}")

if __name__ == "__main__":
    force_failure_test()
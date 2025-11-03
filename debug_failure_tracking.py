import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import Evaluation, User, EvaluationResponse, UserProfile
from main.services.evaluation_service import EvaluationService

def debug_failure_tracking():
    print("🔍 DEBUGGING FAILURE TRACKING ACROSS PERIODS")
    
    # Find the instructor you evaluated
    instructor = User.objects.filter(username='albertoreyes').first()
    if not instructor:
        print("❌ Instructor not found")
        return
    
    print(f"Testing instructor: {instructor.username}")
    
    # Check current failure status
    stats = EvaluationService.get_user_failure_stats(instructor)
    print(f"Current status: {stats['failure_count']} failures, Score: {stats['overall_score']}%")
    
    # Check how many evaluations they have
    evaluation_count = EvaluationResponse.objects.filter(evaluatee=instructor).count()
    print(f"Total evaluations: {evaluation_count}")
    
    # Show all evaluations
    print("All evaluations:")
    for eval in EvaluationResponse.objects.filter(evaluatee=instructor):
        print(f"  - From: {eval.evaluator.username}, Section: {eval.student_section}")
    
    # Manually calculate score to verify
    from main.views import compute_category_scores
    manual_scores = compute_category_scores(instructor)
    print(f"Manual score calculation: {manual_scores}")
    
    # Check if score is below passing (70%)
    if manual_scores and len(manual_scores) > 4:
        overall_score = manual_scores[4]
        print(f"Overall score: {overall_score}%")
        print(f"Below 70%: {overall_score < 70.0}")
    
    # Process results manually to see what happens
    print("\nProcessing results...")
    success, results = EvaluationService.process_evaluation_results()
    
    for result in results:
        if instructor.username in result:
            print(f"Result: {result}")
    
    # Check final status
    final_stats = EvaluationService.get_user_failure_stats(instructor)
    print(f"Final status: {final_stats['failure_count']} failures")

if __name__ == "__main__":
    debug_failure_tracking()
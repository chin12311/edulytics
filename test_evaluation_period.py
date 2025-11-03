import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import Evaluation
from main.services.evaluation_service import EvaluationService

def test_evaluation_period_behavior():
    # Get a test user
    user = User.objects.filter(userprofile__role='Faculty').first()
    if not user:
        print("No faculty user found.")
        return
    
    print(f"Testing with user: {user.username}")
    
    # Test 1: When evaluation period is active (form released)
    print("\n1. Testing when evaluation period is ACTIVE:")
    Evaluation.objects.filter(evaluation_type='student').update(is_released=True)
    print("   Evaluation form: RELEASED")
    
    success, message = EvaluationService.process_evaluation_result(user, 55.0)
    print(f"   Result: {success} - {message}")
    
    # Test 2: When evaluation period has ended (form unreleased)
    print("\n2. Testing when evaluation period has ENDED:")
    Evaluation.objects.filter(evaluation_type='student').update(is_released=False)
    print("   Evaluation form: UNRELEASED")
    
    success, message = EvaluationService.process_evaluation_result(user, 55.0)
    print(f"   Result: {success} - {message}")
    
    # Show current status
    print(f"\nCurrent Evaluation Status:")
    print(f"  Period Active: {Evaluation.is_evaluation_period_active()}")
    print(f"  Can Send Alerts: {EvaluationService.can_send_failure_alerts()}")

if __name__ == "__main__":
    test_evaluation_period_behavior()
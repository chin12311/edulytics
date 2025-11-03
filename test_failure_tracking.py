# test_failure_tracking.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from main.services.evaluation_service import EvaluationService

def test_failure_tracking():
    # Get a faculty user to test with
    try:
        user = User.objects.filter(userprofile__role='Faculty').first()
        if not user:
            user = User.objects.first()
    except:
        user = User.objects.first()
    
    if not user:
        print("No users found in database.")
        return
    
    print(f"Testing failure tracking with user: {user.username}")
    
    # Test failure scenarios
    print("\n1. Testing first failure (55% score):")
    success, message = EvaluationService.process_evaluation_result(user, 55.0)
    print(f"   Result: {success} - {message}")
    
    print("\n2. Testing second failure (60% score):")
    success, message = EvaluationService.process_evaluation_result(user, 60.0)
    print(f"   Result: {success} - {message}")
    
    # Show failure stats
    stats = EvaluationService.get_user_failure_stats(user)
    print(f"\nFailure Statistics:")
    print(f"  Failure Count: {stats['failure_count']}")
    print(f"  Alert Sent: {stats['alert_sent']}")
    print(f"  Recent Failures: {stats['recent_failures'].count()}")

if __name__ == "__main__":
    test_failure_tracking()
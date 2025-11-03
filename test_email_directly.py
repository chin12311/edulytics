# test_email_directly.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.services.email_service import EvaluationEmailService
from django.contrib.auth.models import User

def test_email_directly():
    print("📧 TESTING EMAIL SERVICE DIRECTLY")
    
    # Test with a real instructor
    instructor = User.objects.filter(username='albertoreyes').first()
    if not instructor:
        print("❌ Instructor not found")
        return
    
    print(f"Testing emails for: {instructor.username}")
    
    # Test 1: Warning email to instructor
    print("1. Testing warning email to instructor...")
    warning_success = EvaluationEmailService.send_warning_to_user(instructor, 65.0, 1)
    print(f"   Warning email: {'✅ SENT' if warning_success else '❌ FAILED'}")
    
    # Test 2: Alert email to school head
    print("2. Testing alert email to school head...")
    alert_success = EvaluationEmailService.send_failure_alert_to_school_head(instructor, 60.0, 2)
    print(f"   Alert email: {'✅ SENT' if alert_success else '❌ FAILED'}")

if __name__ == "__main__":
    test_email_directly()
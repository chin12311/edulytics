#!/usr/bin/env python
"""
Troubleshoot email sending issues
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.conf import settings
from django.contrib.auth.models import User
from main.models import UserProfile, Evaluation

print("\n" + "="*80)
print("EMAIL NOTIFICATION TROUBLESHOOTER")
print("="*80)

# Test 1: Check Email Settings
print("\n1️⃣  EMAIL CONFIGURATION:")
print("-" * 80)

email_settings = {
    'EMAIL_BACKEND': settings.EMAIL_BACKEND,
    'EMAIL_HOST': settings.EMAIL_HOST,
    'EMAIL_PORT': settings.EMAIL_PORT,
    'EMAIL_USE_TLS': settings.EMAIL_USE_TLS,
    'EMAIL_HOST_USER': settings.EMAIL_HOST_USER,
    'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
}

all_set = True
for key, value in email_settings.items():
    if value:
        print(f"✅ {key:25} = {str(value)[:50]}")
    else:
        print(f"❌ {key:25} = NOT SET")
        all_set = False

if not all_set:
    print("\n⚠️  Some email settings are missing! Check your .env file.")
    sys.exit(1)

# Test 2: Check the account you just created
print("\n2️⃣  CHECKING YOUR NEW ACCOUNT:")
print("-" * 80)

try:
    user = User.objects.get(email='cibituonon@cca.edu.ph')
    profile = user.userprofile
    
    print(f"✅ User found: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   Active: {user.is_active}")
    print(f"   Role: {profile.role}")
    print(f"   Created: {user.date_joined}")
    
    if not user.is_active:
        print("\n⚠️  WARNING: This user is NOT ACTIVE!")
        print("   Inactive users don't get emails.")
        print("   Make sure is_active=True in database")
        
except User.DoesNotExist:
    print("❌ User with email cibituonon@cca.edu.ph not found!")
    sys.exit(1)

# Test 3: Check Evaluations Released
print("\n3️⃣  CHECKING RELEASED EVALUATIONS:")
print("-" * 80)

released_evals = Evaluation.objects.filter(is_released=True, evaluation_type='student')
print(f"Released student evaluations: {released_evals.count()}")

if released_evals.count() == 0:
    print("⚠️  No student evaluations are released!")
    print("   Email notifications are only sent when you release an evaluation")
    print("   Try releasing an evaluation again")

unreleased = Evaluation.objects.filter(is_released=False, evaluation_type='student')
print(f"Unreleased student evaluations: {unreleased.count()}")

# Test 4: Check all active users
print("\n4️⃣  CHECKING ALL ACTIVE USERS:")
print("-" * 80)

active_users = User.objects.filter(is_active=True).exclude(email='')
print(f"Total active users with email: {active_users.count()}")

if active_users.count() == 0:
    print("❌ No active users found!")
    print("   Email would have nowhere to send")
else:
    print("\nFirst 10 active users:")
    for i, user in enumerate(active_users[:10], 1):
        status = "✅ WILL GET EMAIL" if user.is_active else "❌ INACTIVE"
        print(f"  {i}. {user.email:35} {status}")

# Test 5: Test email connection
print("\n5️⃣  TESTING EMAIL CONNECTION:")
print("-" * 80)

try:
    from django.core.mail import get_connection
    connection = get_connection()
    connection.open()
    connection.close()
    print("✅ Successfully connected to Gmail SMTP")
except Exception as e:
    print(f"❌ Failed to connect to Gmail SMTP:")
    print(f"   Error: {e}")
    print("\n   Solutions:")
    print("   1. Check EMAIL_HOST_USER in .env")
    print("   2. Check EMAIL_HOST_PASSWORD in .env")
    print("   3. Make sure 2FA is enabled on Gmail")
    print("   4. Regenerate app password at: https://myaccount.google.com/apppasswords")
    sys.exit(1)

# Test 6: Send test email
print("\n6️⃣  SENDING TEST EMAIL:")
print("-" * 80)

recipient = 'cibituonon@cca.edu.ph'
print(f"Attempting to send test email to: {recipient}")

try:
    from django.core.mail import send_mail
    result = send_mail(
        subject='🎓 Edulytics Test Email - Check This',
        message='This is a test email from Edulytics. If you got this, emails are working!',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        fail_silently=False,
    )
    print(f"✅ Test email sent successfully!")
    print(f"   Recipient: {recipient}")
    print(f"   Check your inbox within 1-2 minutes")
except Exception as e:
    print(f"❌ Failed to send test email:")
    print(f"   Error: {e}")
    print("\n   This is likely why evaluation emails aren't sending!")
    sys.exit(1)

# Test 7: Test the email service
print("\n7️⃣  TESTING EMAIL SERVICE:")
print("-" * 80)

try:
    from main.email_service import EvaluationEmailService
    
    print("Testing EvaluationEmailService.send_evaluation_released_notification()...")
    result = EvaluationEmailService.send_evaluation_released_notification('student')
    
    print(f"\n✅ Email service executed!")
    print(f"   Success: {result['success']}")
    print(f"   Sent: {result['sent_count']}")
    print(f"   Failed: {len(result['failed_emails'])}")
    print(f"   Message: {result['message']}")
    
    if result['failed_emails']:
        print(f"\n   Failed addresses:")
        for email in result['failed_emails']:
            print(f"     - {email}")
            
except Exception as e:
    print(f"❌ Email service error:")
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "="*80)
print("TROUBLESHOOTING SUMMARY")
print("="*80)

print("""
✅ Configuration looks correct
✅ Gmail connection successful
✅ Test email sent

IF YOU DIDN'T GET EMAILS:

1. Check your spam/junk folder
   - Gmail sometimes puts system emails in spam
   - Mark as "Not spam" if it's there

2. Check the email address
   - Verify cibituonon@cca.edu.ph is correct
   - Check that the user account is ACTIVE in database

3. Check if evaluation was actually released
   - Go to admin panel
   - Release evaluation again
   - Check the response for email status

4. Look at Django logs
   - tail -f logs/django.log | grep -i email
   - This will show if emails were attempted

5. If still not working, run this script again
   - It will try to send another test email
   - This will help identify the issue
""")

print("="*80 + "\n")

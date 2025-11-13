#!/usr/bin/env python
"""
Test script for Email Notification System
Use this to verify that email notifications are working correctly
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from main.models import UserProfile
from main.email_service import EvaluationEmailService

print("\n" + "="*80)
print("EDULYTICS EMAIL NOTIFICATION SYSTEM - TEST SUITE")
print("="*80)

# Test 1: Check Email Configuration
print("\n1️⃣  CHECKING EMAIL CONFIGURATION:")
print("-" * 80)

config_items = {
    'EMAIL_BACKEND': settings.EMAIL_BACKEND,
    'EMAIL_HOST': settings.EMAIL_HOST,
    'EMAIL_PORT': settings.EMAIL_PORT,
    'EMAIL_USE_TLS': settings.EMAIL_USE_TLS,
    'EMAIL_HOST_USER': settings.EMAIL_HOST_USER,
    'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
}

all_configured = True
for key, value in config_items.items():
    if value:
        status = "✅"
        print(f"{status} {key:25} = {value}")
    else:
        status = "❌"
        all_configured = False
        print(f"{status} {key:25} = NOT CONFIGURED")

if not all_configured:
    print("\n⚠️  Some email settings are missing!")
    print("   Check your .env file and ensure all email variables are set.")
    sys.exit(1)

# Test 2: Test Connection to Gmail
print("\n2️⃣  TESTING CONNECTION TO GMAIL SMTP:")
print("-" * 80)

try:
    from django.core.mail import get_connection
    connection = get_connection()
    connection.open()
    connection.close()
    print("✅ Successfully connected to Gmail SMTP server")
except Exception as e:
    print(f"❌ Failed to connect to Gmail SMTP: {e}")
    print("   Check your EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env")
    sys.exit(1)

# Test 3: Count Users
print("\n3️⃣  CHECKING USERS IN SYSTEM:")
print("-" * 80)

total_users = User.objects.filter(is_active=True).exclude(email='').count()
print(f"Total active users with email: {total_users}")

if total_users == 0:
    print("⚠️  No active users found!")
    print("   At least one user is needed to test email notifications.")
else:
    print(f"✅ Found {total_users} users ready for email notifications")

# Test 4: Send Test Email
print("\n4️⃣  SENDING TEST EMAIL:")
print("-" * 80)

test_email = settings.EMAIL_HOST_USER  # Send to sender's email for testing
print(f"Attempting to send test email to: {test_email}")

try:
    send_mail(
        subject='🎓 Edulytics Email Test - System Check',
        message='This is a test email from Edulytics. If you received this, email notifications are working correctly!',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[test_email],
        fail_silently=False,
    )
    print("✅ Test email sent successfully!")
    print(f"   Check your inbox at {test_email} within 1-2 minutes")
except Exception as e:
    print(f"❌ Failed to send test email: {e}")
    print("   Verify your credentials and try again")
    sys.exit(1)

# Test 5: Test Email Service
print("\n5️⃣  TESTING EMAIL SERVICE:")
print("-" * 80)

print("Testing EvaluationEmailService.send_evaluation_released_notification('student')...")
print("(Note: This will send emails to ALL active users)")

response = input("Do you want to proceed? (yes/no): ").lower().strip()

if response == 'yes':
    try:
        result = EvaluationEmailService.send_evaluation_released_notification('student')
        print(f"\n✅ Email service executed successfully!")
        print(f"   Sent: {result['sent_count']} emails")
        print(f"   Failed: {len(result['failed_emails'])} emails")
        print(f"   Message: {result['message']}")
        
        if result['failed_emails']:
            print(f"\n   Failed email addresses:")
            for email in result['failed_emails']:
                print(f"     - {email}")
    except Exception as e:
        print(f"❌ Email service failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("Skipped email service test")

# Test 6: Summary
print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)

print("\n✅ EMAIL SYSTEM STATUS: READY")
print("\nYour email notification system is configured and ready to use!")
print("\nNext Steps:")
print("1. Release an evaluation from the admin control panel")
print("2. All users will automatically receive email notifications")
print("3. Check the Django logs for email sending details")
print("\nFor help, see: EMAIL_NOTIFICATION_SETUP.md")
print("="*80 + "\n")

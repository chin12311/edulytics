#!/usr/bin/env python
"""
Send a test email through Django to verify everything works end-to-end
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("\n" + "="*80)
print("SENDING TEST EMAIL THROUGH DJANGO")
print("="*80)

recipient = 'cibituonon@cca.edu.ph'

print(f"\n📧 From: {settings.DEFAULT_FROM_EMAIL}")
print(f"📧 To: {recipient}")
print(f"📧 Host: {settings.EMAIL_HOST}")

try:
    send_mail(
        subject='✅ Edulytics Email System - Test Successful!',
        message='This is a test email from your Edulytics system.\n\nIf you received this, the email system is working correctly!\n\nYou will now receive notifications when evaluations are released.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        fail_silently=False,
    )
    print("\n✅ Test email sent successfully!")
    print("\n" + "="*80)
    print("✅ EMAIL SYSTEM IS FULLY OPERATIONAL")
    print("="*80)
    print("\nNext steps:")
    print("1. Check your inbox at cibituonon@cca.edu.ph (in 1-2 minutes)")
    print("2. Release an evaluation in your admin panel")
    print("3. All 58 system users should receive an email")
    print("="*80 + "\n")
    
except Exception as e:
    print(f"\n❌ Failed to send test email:")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

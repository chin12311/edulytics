# test_email_detailed.py
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("Testing email with real content...")
print(f"From: {settings.DEFAULT_FROM_EMAIL}")
print(f"To: cibituonon@cca.edu.ph")

try:
    send_mail(
        subject='🚨 TEST: Evaluation Failure Alert - Test User',
        message='This is a plain text test message. If you see this, email is working.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['cibituonon@cca.edu.ph'],
        html_message='<h1>HTML Test</h1><p>This is an HTML test message.</p>',
        fail_silently=False,
    )
    print("✅ Test email sent successfully!")
    print("📧 Please check inbox AND spam folder at cibituonon@cca.edu.ph")
except Exception as e:
    print(f"❌ Email failed: {e}")
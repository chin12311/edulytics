from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from ..models import Evaluation

class EvaluationEmailService:
    @staticmethod
    def send_failure_alert_to_school_head(user, evaluation_score, failure_count):
        """Send alert to school head when user fails evaluation twice - ONLY when period ended"""
        # ✅ ADDED: Check if we can send alerts
        if Evaluation.is_evaluation_period_active():
            print("⏸️  Evaluation period active - skipping alert to school head")
            return False
            
        subject = f"🚨 Evaluation Failure Alert - {user.get_full_name() or user.username}"
        
        # Get user profile info
        user_profile = user.userprofile
        
        context = {
            'user_name': user.get_full_name() or user.username,
            'user_type': user_profile.get_role_display(),
            'evaluation_score': evaluation_score,
            'passing_score': getattr(settings, 'EVALUATION_PASSING_SCORE', 70.0),
            'failure_count': failure_count,
            'institute': user_profile.institute or 'CCA',
            'date': timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        html_message = render_to_string('emails/evaluation_failure_alert.html', context)
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.SCHOOL_HEAD_EMAIL],
                html_message=html_message,
                fail_silently=False,
            )
            print(f"✅ Failure alert sent to school head for {user.username}")
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    @staticmethod
    def send_warning_to_user(user, evaluation_score, failure_count):
        """Send warning email to user after first failure - ONLY when period ended"""
        # ✅ ADDED: Check if we can send alerts
        if Evaluation.is_evaluation_period_active():
            print("⏸️  Evaluation period active - skipping warning to user")
            return False
            
        subject = f"⚠️ Evaluation Warning - {user.get_full_name() or user.username}"
        
        context = {
            'user_name': user.get_full_name() or user.username,
            'evaluation_score': evaluation_score,
            'passing_score': getattr(settings, 'EVALUATION_PASSING_SCORE', 70.0),
            'failure_count': failure_count,
            'next_attempt_allowed': True,
        }
        
        html_message = render_to_string('emails/evaluation_warning.html', context)
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            print(f"✅ Warning email sent to {user.username}")
            return True
        except Exception as e:
            print(f"Failed to send warning email: {e}")
            return False
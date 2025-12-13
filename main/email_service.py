"""
Email Service for Edulytics
Handles sending email notifications to users
"""

import logging
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth.models import User
from .models import UserProfile, Role

logger = logging.getLogger(__name__)


class EvaluationEmailService:
    """Service for sending evaluation-related emails"""
    
    @staticmethod
    def send_evaluation_released_notification(evaluation_type='student'):
        """
        Send email notification to users that an evaluation has been released
        
        Args:
            evaluation_type (str): Type of evaluation ('student', 'peer', or 'upward')
        
        Returns:
            dict: {
                'success': bool,
                'sent_count': int,
                'failed_emails': list,
                'message': str
            }
        
        Email Recipients by Evaluation Type:
        - student: Students only
        - peer: Dean, Coordinator, Faculty (NOT Students)
        - upward: Faculty only
        """
        try:
            # Get all active users with valid email addresses
            # Exclude the school head admin account (cibituonon@cca.edu.ph)
            base_users = User.objects.filter(is_active=True).exclude(email='').exclude(email='cibituonon@cca.edu.ph')
            
            # Filter users based on evaluation type
            if evaluation_type == 'student':
                # Only send to Students
                users = base_users.filter(userprofile__role='Student')
            elif evaluation_type == 'peer':
                # Send to Dean, Coordinator, and Faculty (NOT Students)
                users = base_users.filter(userprofile__role__in=['Dean', 'Coordinator', 'Faculty'])
            elif evaluation_type == 'upward':
                # Only send to Faculty
                users = base_users.filter(userprofile__role='Faculty')
            else:
                # Default: all users (shouldn't happen)
                users = base_users
            
            if not users.exists():
                logger.warning(f"No active users to notify about {evaluation_type} evaluation release")
                return {
                    'success': False,
                    'sent_count': 0,
                    'failed_emails': [],
                    'message': 'No active users found to notify'
                }
            
            logger.info(f"Sending {evaluation_type} evaluation release notification to {users.count()} users")
            
            sent_count = 0
            failed_emails = []
            
            # Prepare email content
            subject = EvaluationEmailService._get_release_subject(evaluation_type)
            html_content = EvaluationEmailService._get_release_html_content(evaluation_type)
            text_content = EvaluationEmailService._get_release_text_content(evaluation_type)
            
            # Send email to each user
            for user in users:
                try:
                    email = EvaluationEmailService._send_release_email(
                        recipient_email=user.email,
                        recipient_name=user.first_name or user.username,
                        subject=subject,
                        html_content=html_content,
                        text_content=text_content,
                        evaluation_type=evaluation_type
                    )
                    sent_count += 1
                    logger.debug(f"Successfully sent {evaluation_type} evaluation release email to {user.email}")
                    
                except Exception as e:
                    logger.error(f"Failed to send email to {user.email}: {str(e)}")
                    failed_emails.append(user.email)
            
            logger.info(f"Sent {evaluation_type} evaluation release notification: "
                       f"{sent_count} successful, {len(failed_emails)} failed")
            
            return {
                'success': True,
                'sent_count': sent_count,
                'failed_emails': failed_emails,
                'message': f'Successfully sent {evaluation_type} evaluation release notification to {sent_count} users'
            }
            
        except Exception as e:
            logger.error(f"Exception in send_evaluation_released_notification: {str(e)}", exc_info=True)
            return {
                'success': False,
                'sent_count': 0,
                'failed_emails': [],
                'message': f'Error sending notifications: {str(e)}'
            }
    
    @staticmethod
    def send_evaluation_unreleased_notification(evaluation_type='student'):
        """
        Send email notification to users that an evaluation has been unreleased/closed
        
        Args:
            evaluation_type (str): Type of evaluation ('student', 'peer', or 'upward')
        
        Returns:
            dict: {
                'success': bool,
                'sent_count': int,
                'failed_emails': list,
                'message': str
            }
        
        Email Recipients by Evaluation Type:
        - student: Students only
        - peer: Dean, Coordinator, Faculty (NOT Students)
        - upward: Faculty only
        """
        try:
            base_users = User.objects.filter(is_active=True).exclude(email='').exclude(email='cibituonon@cca.edu.ph')
            
            # Filter users based on evaluation type
            if evaluation_type == 'student':
                # Only send to Students
                users = base_users.filter(userprofile__role='Student')
            elif evaluation_type == 'peer':
                # Send to Dean, Coordinator, and Faculty (NOT Students)
                users = base_users.filter(userprofile__role__in=['Dean', 'Coordinator', 'Faculty'])
            elif evaluation_type == 'upward':
                # Only send to Faculty
                users = base_users.filter(userprofile__role='Faculty')
            else:
                # Default: all users (shouldn't happen)
                users = base_users
            
            if not users.exists():
                logger.warning(f"No active users to notify about {evaluation_type} evaluation close")
                return {
                    'success': False,
                    'sent_count': 0,
                    'failed_emails': [],
                    'message': 'No active users found to notify'
                }
            
            logger.info(f"Sending {evaluation_type} evaluation close notification to {users.count()} users")
            
            sent_count = 0
            failed_emails = []
            
            subject = EvaluationEmailService._get_unreleased_subject(evaluation_type)
            html_content = EvaluationEmailService._get_unreleased_html_content(evaluation_type)
            text_content = EvaluationEmailService._get_unreleased_text_content(evaluation_type)
            
            for user in users:
                try:
                    EvaluationEmailService._send_unreleased_email(
                        recipient_email=user.email,
                        recipient_name=user.first_name or user.username,
                        subject=subject,
                        html_content=html_content,
                        text_content=text_content,
                        evaluation_type=evaluation_type
                    )
                    sent_count += 1
                    logger.debug(f"Successfully sent {evaluation_type} evaluation close email to {user.email}")
                    
                except Exception as e:
                    logger.error(f"Failed to send close email to {user.email}: {str(e)}")
                    failed_emails.append(user.email)
            
            logger.info(f"Sent {evaluation_type} evaluation close notification: "
                       f"{sent_count} successful, {len(failed_emails)} failed")
            
            return {
                'success': True,
                'sent_count': sent_count,
                'failed_emails': failed_emails,
                'message': f'Successfully sent {evaluation_type} evaluation close notification to {sent_count} users'
            }
            
        except Exception as e:
            logger.error(f"Exception in send_evaluation_unreleased_notification: {str(e)}", exc_info=True)
            return {
                'success': False,
                'sent_count': 0,
                'failed_emails': [],
                'message': f'Error sending notifications: {str(e)}'
            }
    
    @staticmethod
    def _send_release_email(recipient_email, recipient_name, subject, html_content, text_content, evaluation_type):
        """Send individual release email"""
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email]
        )
        msg.attach_alternative(html_content, "text/html")
        result = msg.send()
        
        if result == 0:
            raise Exception(f"Email send failed for {recipient_email}")
        
        return recipient_email
    
    @staticmethod
    def _send_unreleased_email(recipient_email, recipient_name, subject, html_content, text_content, evaluation_type):
        """Send individual unreleased/close email"""
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email]
        )
        msg.attach_alternative(html_content, "text/html")
        result = msg.send()
        
        if result == 0:
            raise Exception(f"Email send failed for {recipient_email}")
        
        return recipient_email
    
    @staticmethod
    def _get_release_subject(evaluation_type):
        """Get email subject for evaluation release"""
        if evaluation_type == 'peer':
            return "🎓 Peer Evaluation Form Released - Action Required"
        elif evaluation_type == 'upward':
            return "🎓 Upward Evaluation Form Released - Action Required"
        else:
            return "🎓 Student Evaluation Form Released - Action Required"
    
    @staticmethod
    def _get_unreleased_subject(evaluation_type):
        """Get email subject for evaluation unreleased"""
        if evaluation_type == 'peer':
            return "📋 Peer Evaluation Period Closed"
        elif evaluation_type == 'upward':
            return "📋 Upward Evaluation Period Closed"
        else:
            return "📋 Student Evaluation Period Closed"
    
    @staticmethod
    def _get_release_html_content(evaluation_type):
        """Generate HTML content for release email"""
        if evaluation_type == 'peer':
            eval_name = "Peer Evaluation Form"
        elif evaluation_type == 'upward':
            eval_name = "Upward Evaluation Form"
        else:
            eval_name = "Student Evaluation Form"
        
        # Get site URL from settings or environment
        site_url = getattr(settings, 'SITE_URL', 'http://13.211.104.201')
        
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #f9f9f9; padding: 20px; border-radius: 8px;">
                    
                    <!-- Header -->
                    <div style="background-color: #576d2e; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">🎓 {eval_name} Released</h1>
                    </div>
                    
                    <!-- Content -->
                    <div style="background-color: white; padding: 30px; border-radius: 0 0 8px 8px;">
                        <p style="font-size: 16px; margin-bottom: 20px;">
                            Dear User,
                        </p>
                        
                        <p style="font-size: 14px; margin-bottom: 15px;">
                            The <strong>{eval_name}</strong> has been officially released and is now <span style="color: #28a745; font-weight: bold;">ACTIVE</span>.
                        </p>
                        
                        <div style="background-color: #e7f3ff; border-left: 4px solid #2196F3; padding: 15px; margin: 20px 0; border-radius: 4px;">
                            <p style="margin: 0; font-size: 14px;">
                                <strong>ℹ️ What's Next?</strong><br>
                                Please log in to the Edulytics system and complete your evaluation forms. 
                                Your feedback is valuable to our institution's continuous improvement.
                            </p>
                        </div>
                        
                        <p style="font-size: 14px; margin: 20px 0;">
                            <strong>Key Details:</strong>
                        </p>
                        <ul style="font-size: 14px; margin: 10px 0;">
                            <li>Evaluation Type: <strong>{eval_name}</strong></li>
                            <li>Status: <span style="color: #28a745; font-weight: bold;">Active</span></li>
                            <li>Action Required: Please complete your evaluation</li>
                        </ul>
                        
                        <div style="background-color: #f0f8ff; border: 1px solid #b3d9ff; padding: 15px; margin: 20px 0; border-radius: 4px;">
                            <p style="margin: 0; font-size: 13px; color: #555;">
                                <strong>Access Your Evaluation:</strong><br>
                                Log in to <a href="{site_url}" style="color: #576d2e; text-decoration: none;">Edulytics System</a>
                            </p>
                        </div>
                        
                        <p style="font-size: 13px; color: #666; margin-top: 25px;">
                            If you have any questions or experience technical difficulties, 
                            please contact the administration office.
                        </p>
                        
                    </div>
                    
                    <!-- Footer -->
                    <div style="background-color: #f0f0f0; padding: 15px; text-align: center; border-radius: 0 0 8px 8px; font-size: 12px; color: #666;">
                        <p style="margin: 0;">
                            City College of Angeles - Edulytics Evaluation System<br>
                            This is an automated notification. Please do not reply to this email.
                        </p>
                    </div>
                    
                </div>
            </body>
        </html>
        """
        return html
    
    @staticmethod
    def _get_release_text_content(evaluation_type):
        """Generate plain text content for release email"""
        if evaluation_type == 'peer':
            eval_name = "Peer Evaluation Form"
        elif evaluation_type == 'upward':
            eval_name = "Upward Evaluation Form"
        else:
            eval_name = "Student Evaluation Form"
        
        # Get site URL from settings or environment
        site_url = getattr(settings, 'SITE_URL', 'http://13.211.104.201')
        
        text = f"""
The {eval_name} has been officially released and is now ACTIVE.

WHAT'S NEXT?
Please log in to the Edulytics system and complete your evaluation forms.
Your feedback is valuable to our institution's continuous improvement.

KEY DETAILS:
- Evaluation Type: {eval_name}
- Status: Active
- Action Required: Please complete your evaluation

ACCESS YOUR EVALUATION:
Log in to the Edulytics System at {site_url}

If you have any questions or experience technical difficulties,
please contact the administration office.

---
City College of Angeles - Edulytics Evaluation System
This is an automated notification. Please do not reply to this email.
        """
        return text.strip()
    
    @staticmethod
    def _get_unreleased_html_content(evaluation_type):
        """Generate HTML content for unreleased/close email"""
        if evaluation_type == 'peer':
            eval_name = "Peer Evaluation Form"
        elif evaluation_type == 'upward':
            eval_name = "Upward Evaluation Form"
        else:
            eval_name = "Student Evaluation Form"
        
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #f9f9f9; padding: 20px; border-radius: 8px;">
                    
                    <!-- Header -->
                    <div style="background-color: #f39c12; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">📋 {eval_name} Period Closed</h1>
                    </div>
                    
                    <!-- Content -->
                    <div style="background-color: white; padding: 30px; border-radius: 0 0 8px 8px;">
                        <p style="font-size: 16px; margin-bottom: 20px;">
                            Dear User,
                        </p>
                        
                        <p style="font-size: 14px; margin-bottom: 15px;">
                            The <strong>{eval_name}</strong> evaluation period has ended and is now <span style="color: #e74c3c; font-weight: bold;">CLOSED</span>.
                        </p>
                        
                        <div style="background-color: #ffe7e7; border-left: 4px solid #e74c3c; padding: 15px; margin: 20px 0; border-radius: 4px;">
                            <p style="margin: 0; font-size: 14px;">
                                <strong>⚠️ Important Notice</strong><br>
                                No further evaluations can be submitted. The evaluation period has officially closed.
                            </p>
                        </div>
                        
                        <p style="font-size: 14px; margin: 20px 0;">
                            <strong>Summary:</strong>
                        </p>
                        <ul style="font-size: 14px; margin: 10px 0;">
                            <li>Evaluation Type: <strong>{eval_name}</strong></li>
                            <li>Status: <span style="color: #e74c3c; font-weight: bold;">Closed</span></li>
                            <li>Submissions: No longer accepted</li>
                        </ul>
                        
                        <p style="font-size: 13px; color: #666; margin-top: 25px;">
                            Thank you for your participation. Your feedback has been valuable to our institution's evaluation process.
                        </p>
                        
                    </div>
                    
                    <!-- Footer -->
                    <div style="background-color: #f0f0f0; padding: 15px; text-align: center; border-radius: 0 0 8px 8px; font-size: 12px; color: #666;">
                        <p style="margin: 0;">
                            City College of Angeles - Edulytics Evaluation System<br>
                            This is an automated notification. Please do not reply to this email.
                        </p>
                    </div>
                    
                </div>
            </body>
        </html>
        """
        return html
    
    @staticmethod
    def _get_unreleased_text_content(evaluation_type):
        """Generate plain text content for unreleased/close email"""
        if evaluation_type == 'peer':
            eval_name = "Peer Evaluation Form"
        elif evaluation_type == 'upward':
            eval_name = "Upward Evaluation Form"
        else:
            eval_name = "Student Evaluation Form"
        
        text = f"""
The {eval_name} evaluation period has ended and is now CLOSED.

IMPORTANT NOTICE:
No further evaluations can be submitted. The evaluation period has officially closed.

SUMMARY:
- Evaluation Type: {eval_name}
- Status: Closed
- Submissions: No longer accepted

Thank you for your participation. Your feedback has been valuable to our institution's evaluation process.

---
City College of Angeles - Edulytics Evaluation System
This is an automated notification. Please do not reply to this email.
        """
        return text.strip()

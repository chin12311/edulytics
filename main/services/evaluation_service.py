from django.conf import settings
from django.utils import timezone
from ..models import UserProfile, EvaluationFailureLog, Evaluation, EvaluationResponse, Role
from .email_service import EvaluationEmailService

class EvaluationService:
    @staticmethod
    def process_evaluation_results(evaluation_type="student"):
        """
        Process evaluation results when period ends (form unreleased)
        This should be called when admin unreleases the evaluation form
        """
        # Check if we can view results (evaluation period ended)
        if Evaluation.is_evaluation_period_active(evaluation_type):
            print("⏸️  Evaluation period still active - cannot process results yet")
            return False, ["Evaluation period is still active"]
        
        print("🔄 Processing evaluation results after period ended...")
        
        # ✅ FIXED: Use the correct role values from your Role class
        staff_users = UserProfile.objects.filter(
            role__in=[Role.FACULTY, Role.COORDINATOR, Role.DEAN]  # Use the actual enum values
        )
        
        results = []
        processed_count = 0
        
        for staff_profile in staff_users:
            user = staff_profile.user
            overall_score = EvaluationService.calculate_overall_score(user, evaluation_type)
            
            print(f"📊 {user.username} ({staff_profile.role}): Overall Score = {overall_score}%")
            
            # Only process failures if score is below passing and they have evaluations
            if overall_score > 0:  # Only if they have evaluations
                processed_count += 1
                if overall_score < getattr(settings, 'EVALUATION_PASSING_SCORE', 70.0):
                    result = EvaluationService._handle_evaluation_failure(user, overall_score)
                    results.append(f"{user.username} ({staff_profile.role}): Failed ({overall_score}%) - {result}")
                else:
                    # Reset failure count if they passed this period
                    reset_result = EvaluationService._reset_failure_count(user)
                    results.append(f"{user.username} ({staff_profile.role}): Passed ({overall_score}%) - Reset failures")
            else:
                results.append(f"{user.username} ({staff_profile.role}): No evaluations - Skipped")
        
        if processed_count == 0:
            results.append("No staff members with evaluations found.")
        
        print(f"✅ Processed {processed_count} staff members")
        return True, results
    
    @staticmethod
    def _handle_evaluation_failure(user, overall_score):
        """Handle evaluation failure - tracks across multiple periods"""
        user_profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': Role.FACULTY, 'institute': 'CCA'}
        )
        
        # Log this period's failure
        failure_log = EvaluationFailureLog.objects.create(
            user=user,
            score=overall_score,
            passing_score=getattr(settings, 'EVALUATION_PASSING_SCORE', 70.0)
        )
        
        # Increment persistent failure count
        old_failure_count = user_profile.evaluation_failure_count
        user_profile.evaluation_failure_count += 1
        user_profile.last_evaluation_failure_date = timezone.now()
        
        print(f"📝 {user.username}: Failure count {old_failure_count} → {user_profile.evaluation_failure_count}")
        
        result_message = f"Failure count: {user_profile.evaluation_failure_count}"
        
        # FIRST FAILURE: Send warning to user
        if user_profile.evaluation_failure_count == 1:
            if EvaluationEmailService.send_warning_to_user(user, overall_score, 1):
                result_message += " - Warning email sent"
            else:
                result_message += " - Warning email failed"
            user_profile.save()
        
        # SECOND OR MORE FAILURES: Always send alert to school head
        elif user_profile.evaluation_failure_count >= getattr(settings, 'MAX_FAILURE_ATTEMPTS', 2):
            # ✅ REMOVED: The failure_alert_sent check - send alert every time after threshold
            if EvaluationEmailService.send_failure_alert_to_school_head(
                user, overall_score, user_profile.evaluation_failure_count
            ):
                user_profile.failure_alert_sent = True  # Keep for tracking first alert
                result_message += " - Alert email sent to school head"
            else:
                result_message += " - Alert email failed"
            user_profile.save()
        
        else:
            user_profile.save()
        
        return result_message

    @staticmethod
    def _reset_failure_count(user):
        """Reset failure count for a user who passed this period"""
        try:
            user_profile = UserProfile.objects.get(user=user)
            if user_profile.evaluation_failure_count > 0:
                print(f"🔄 Resetting failure count for {user.username}: {user_profile.evaluation_failure_count} → 0")
                user_profile.evaluation_failure_count = 0
                user_profile.failure_alert_sent = False
                user_profile.last_evaluation_failure_date = None
                user_profile.save()
                return "Failures reset"
            return "No failures to reset"
        except UserProfile.DoesNotExist:
            return "No user profile found"
    
    @staticmethod
    def get_user_failure_stats(user):
        """Get failure statistics for a user"""
        try:
            user_profile = UserProfile.objects.get(user=user)
            failures = EvaluationFailureLog.objects.filter(user=user).order_by('-evaluation_date')
            
            overall_score = EvaluationService.calculate_overall_score(user)
            has_evaluations = EvaluationResponse.objects.filter(evaluatee=user).exists()
            
            return {
                'failure_count': user_profile.evaluation_failure_count,
                'last_failure_date': user_profile.last_evaluation_failure_date,
                'recent_failures': failures[:5],
                'alert_sent': user_profile.failure_alert_sent,
                'overall_score': overall_score,
                'has_evaluations': has_evaluations,
                'role': user_profile.role,  # Add role to see what it actually is
            }
        except UserProfile.DoesNotExist:
            return {
                'failure_count': 0,
                'last_failure_date': None,
                'recent_failures': [],
                'alert_sent': False,
                'overall_score': 0,
                'has_evaluations': False,
                'role': 'None',
            }
    
    @staticmethod
    def reset_all_failures():
        """Reset all failure counts (useful for starting fresh)"""
        try:
            # Reset UserProfile failure counts
            UserProfile.objects.update(
                evaluation_failure_count=0,
                failure_alert_sent=False,
                last_evaluation_failure_date=None
            )
            
            # Clear all failure logs
            EvaluationFailureLog.objects.all().delete()
            
            print("✅ All failure counts and logs reset")
            return True
            
        except Exception as e:
            print(f"❌ Error resetting failures: {e}")
            return False
        
    @staticmethod
    def reset_selected_failures(user_ids):
        """Reset failure counts for specific users"""
        try:
            # Reset UserProfile failure counts for selected users
            reset_count = UserProfile.objects.filter(user_id__in=user_ids).update(
                evaluation_failure_count=0,
                failure_alert_sent=False,
                last_evaluation_failure_date=None
            )
            
            # Clear failure logs for selected users
            EvaluationFailureLog.objects.filter(user_id__in=user_ids).delete()
            
            print(f"✅ Reset failure counts for {reset_count} selected users")
            return True, reset_count
            
        except Exception as e:
            print(f"❌ Error resetting selected failures: {e}")
            return False, 0

    @staticmethod
    def calculate_overall_score(user, evaluation_type="student"):
        """
        Calculate overall average score for an instructor across all evaluations
        """
        try:
            # Check if user has any evaluations
            has_evaluations = EvaluationResponse.objects.filter(evaluatee=user).exists()
            if not has_evaluations:
                return 0.0  # No evaluations yet
            
            from ..views import compute_category_scores
            scores = compute_category_scores(user)
            
            if scores and len(scores) > 4:
                overall_score = scores[4]  # Total percentage
                return overall_score
            else:
                return 0.0
                
        except Exception as e:
            print(f"❌ Error calculating overall score for {user.username}: {e}")
            return 0.0
    
    @staticmethod
    def get_evaluation_status(evaluation_type="student"):
        """
        Get current evaluation status for admin panel
        """
        try:
            is_active = Evaluation.is_evaluation_period_active(evaluation_type)
            is_released = Evaluation.objects.filter(
                evaluation_type=evaluation_type, 
                is_released=True
            ).exists()
            
            return {
                'is_active': is_active,
                'is_released': is_released,
                'evaluation_type': evaluation_type,
            }
            
        except Exception as e:
            print(f"❌ Error getting evaluation status: {e}")
            return {
                'is_active': False,
                'is_released': False,
                'evaluation_type': evaluation_type,
                'error': str(e)
            }


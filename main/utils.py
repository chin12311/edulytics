from .models import Evaluation, AdminActivityLog

def can_view_evaluation_results(evaluation_type='student'):
    """
    Check if users can view evaluation results
    Users can only see results when evaluations are UNRELEASED
    """
    try:
        is_released = Evaluation.objects.filter(
            is_released=True, 
            evaluation_type=evaluation_type
        ).exists()
        return not is_released  # Can view results when NOT released
    except Exception:
        # If there's any error, default to allowing view (safe fallback)
        return True

def is_evaluation_period_active(evaluation_type='student'):
    """
    Check if evaluation period is currently active
    Evaluation period is active when forms are RELEASED
    """
    try:
        return Evaluation.objects.filter(
            is_released=True, 
            evaluation_type=evaluation_type
        ).exists()
    except Exception:
        # If there's any error, default to inactive (safe fallback)
        return False

def log_admin_activity(request, action, description, target_user=None, target_section=None):
    """
    Log admin activities for audit trail
    
    Args:
        request: Django request object
        action: Action type (must be in AdminActivityLog.ACTION_CHOICES)
        description: Detailed description of the action
        target_user: User affected by the action (optional)
        target_section: Section affected by the action (optional)
    """
    try:
        # Get IP address from request
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Create log entry
        AdminActivityLog.objects.create(
            admin=request.user if request.user.is_authenticated else None,
            action=action,
            target_user=target_user,
            target_section=target_section,
            description=description,
            ip_address=ip_address
        )
    except Exception as e:
        # Silent fail - don't break the app if logging fails
        print(f"Failed to log admin activity: {e}")
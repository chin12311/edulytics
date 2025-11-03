# decorators.py
from django.shortcuts import render

from main.models import Evaluation
from .utils import can_view_evaluation_results

def evaluation_results_required(view_func):
    """
    Decorator to check if evaluation period has ended before showing results
    But allow profile settings access
    """
    def wrapped_view(request, *args, **kwargs):
        # Check if this is a profile settings page
        if 'profile-settings' in request.path:
            # Always allow access to profile settings
            return view_func(request, *args, **kwargs)
        
        # For other pages, check evaluation period
        if not Evaluation.can_view_results('student'):
            return render(request, 'main/evaluation_period_active.html', {
                'message': 'Evaluation period is still active. Results will be available after the evaluation period ends.'
            })
        return view_func(request, *args, **kwargs)
    return wrapped_view

def profile_settings_allowed(view_func):
    """
    Decorator that allows access to profile settings but restricts evaluation results
    """
    def wrapped_view(request, *args, **kwargs):
        # Always allow access to profile settings
        # The template will handle showing/hiding evaluation results based on evaluation_period_ended
        return view_func(request, *args, **kwargs)
    return wrapped_view
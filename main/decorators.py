# decorators.py
from django.shortcuts import render
from django.http import HttpResponseForbidden
from django.core.cache import cache
import time
import logging

from main.models import Evaluation
from .utils import can_view_evaluation_results

logger = logging.getLogger(__name__)

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

def rate_limit(max_attempts=5, window_seconds=300):
    """
    Rate limiting decorator to prevent brute force attacks.
    Args:
        max_attempts: Maximum number of attempts allowed in the time window
        window_seconds: Time window in seconds (default 5 minutes = 300 seconds)
    
    Example usage:
        @rate_limit(max_attempts=5, window_seconds=300)  # 5 attempts per 5 minutes
        def login_view(request):
            ...
    """
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            # Get client IP address
            client_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
            if ',' in client_ip:  # X-Forwarded-For can contain multiple IPs
                client_ip = client_ip.split(',')[0].strip()
            
            # Create cache key for this IP and view
            cache_key = f"rate_limit:{view_func.__name__}:{client_ip}"
            
            # Get current attempt count
            attempt_count = cache.get(cache_key, 0)
            
            # Check if limit exceeded
            if attempt_count >= max_attempts:
                logger.warning(f"Rate limit exceeded for IP {client_ip} on {view_func.__name__} - attempt {attempt_count + 1}")
                return HttpResponseForbidden("Too many attempts. Please try again later.")
            
            # Increment attempt count
            cache.set(cache_key, attempt_count + 1, window_seconds)
            
            try:
                response = view_func(request, *args, **kwargs)
                # On successful completion (2xx status), reset the counter
                if hasattr(response, 'status_code') and 200 <= response.status_code < 300:
                    cache.delete(cache_key)
                    logger.debug(f"Rate limit counter reset for IP {client_ip} on {view_func.__name__} after successful request")
                return response
            except Exception as e:
                logger.error(f"Error in rate-limited view {view_func.__name__}: {str(e)}", exc_info=True)
                raise
        
        wrapped_view.__name__ = view_func.__name__
        wrapped_view.__doc__ = view_func.__doc__
        return wrapped_view
    return decorator
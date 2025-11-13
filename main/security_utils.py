# =============================================================================
# SECURITY UTILITIES
# =============================================================================
# Helper functions for common security operations

from urllib.parse import urlparse, urljoin
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def is_safe_redirect_url(url):
    """
    Validate that a URL is safe for redirect (prevents open redirect attacks).
    
    Only allows:
    - Relative URLs (starting with /)
    - Same-origin URLs (same domain as request)
    
    Args:
        url: URL string to validate
        
    Returns:
        bool: True if URL is safe for redirect, False otherwise
    """
    if not url:
        return False
    
    # Strip whitespace
    url = url.strip()
    
    # Only allow relative URLs or same-origin URLs
    if url.startswith('/'):
        # Relative URL - safe
        return True
    
    # Check for protocol-relative URL (//example.com)
    if url.startswith('//'):
        return False
    
    # Parse absolute URLs
    try:
        parsed_url = urlparse(url)
        
        # Only allow http and https
        if parsed_url.scheme not in ('http', 'https', ''):
            return False
        
        # If URL has a domain, check if it matches allowed hosts
        if parsed_url.netloc:
            allowed_hosts = settings.ALLOWED_HOSTS
            # Check if netloc is in allowed hosts (simple check)
            for host in allowed_hosts:
                if host == '*' or parsed_url.netloc == host or parsed_url.netloc.endswith(host):
                    return True
            return False
        
        return True
        
    except Exception as e:
        logger.warning(f"Error parsing redirect URL: {str(e)}")
        return False


def get_safe_next_url(request, default_url='/'):
    """
    Get a safe 'next' URL from request parameters.
    
    Args:
        request: Django request object
        default_url: Default URL if 'next' parameter is invalid or missing
        
    Returns:
        str: Safe URL for redirect
    """
    # Try GET parameter first, then POST
    next_url = request.GET.get('next') or request.POST.get('next', '')
    
    if is_safe_redirect_url(next_url):
        return next_url
    
    logger.warning(f"Invalid redirect URL attempted: {next_url}")
    return default_url

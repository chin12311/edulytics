from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.urls import reverse

class NoCacheMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if request.user.is_authenticated:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response


class RestrictAdminMiddleware(MiddlewareMixin):
    """
    Restrict access to Django admin panel - only allow superusers
    """
    def process_request(self, request):
        # Check if the request is for the admin site
        if request.path.startswith('/admin/'):
            # Allow superusers to access admin
            if request.user.is_authenticated and request.user.is_superuser:
                return None
            
            # Redirect authenticated users to their respective dashboard
            if request.user.is_authenticated:
                try:
                    user_role = request.user.userprofile.role
                    
                    # Redirect based on role
                    if user_role == 'Student':
                        return redirect('main:index')  # Student dashboard
                    elif user_role == 'Dean':
                        return redirect('main:dean')  # Dean dashboard
                    elif user_role == 'Faculty':
                        return redirect('main:faculty')  # Faculty dashboard
                    elif user_role == 'Coordinator':
                        return redirect('main:coordinator')  # Coordinator dashboard
                    else:
                        return redirect('main:index')  # Default to index
                        
                except Exception:
                    # If no profile exists, redirect to index
                    return redirect('main:index')
            
            # Redirect unauthenticated users to login page
            return redirect('/login/')
        
        return None

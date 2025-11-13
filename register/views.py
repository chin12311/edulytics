from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.views import View
from django.contrib.auth.models import User
from django.db import transaction
import logging
from main.models import UserProfile
from main.security_utils import get_safe_next_url
from main.decorators import rate_limit
from .forms import RegisterForm, LoginForm
from main.models import Section
from main.utils import log_admin_activity

logger = logging.getLogger(__name__)


class RegisterView(View):
    def get(self, request):
        next_url = get_safe_next_url(request, request.META.get('HTTP_REFERER', '/'))
        form = RegisterForm()
        return render(request, 'register/register.html', {'form': form, 'next_url': next_url})

    def post(self, request):
        form = RegisterForm(request.POST)
        next_url = get_safe_next_url(request, request.META.get('HTTP_REFERER', '/'))

        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()  # This now calls our custom save method
                    
                    # Log admin activity for account creation
                    log_admin_activity(
                        request=request,
                        action='create_account',
                        description=f"Created new account: {user.username} ({user.email}) - Role: {user.userprofile.role}",
                        target_user=user
                    )
                    
                # Add success parameter to URL
                separator = '&' if '?' in next_url else '?'
                success_url = f"{next_url}{separator}account_added=success"
                return redirect(success_url)

            except Exception as e:
                logger.error(f"Error creating account: {str(e)}", exc_info=True)
                form.add_error(None, f"Error creating account: {e}")
                return render(request, 'register/register.html', {'form': form, 'next_url': next_url})

        return render(request, 'register/register.html', {'form': form, 'next_url': next_url})


@rate_limit(max_attempts=5, window_seconds=300)  # 5 login attempts per 5 minutes
def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                # Try to find the user by email (case-insensitive)
                user = User.objects.get(email__iexact=email)
                # Authenticate using the username (not email)
                authenticated_user = authenticate(request, username=user.username, password=password)

                if authenticated_user is not None:
                    login(request, authenticated_user)
                    logger.info(f"Successful login for user: {user.username} ({email})")
                    return redirect('main:index')
                else:
                    # Invalid password
                    logger.warning(f"Failed login attempt for {email} - invalid password")
                    form.add_error(None, "Invalid email or password.")
            except User.DoesNotExist:
                logger.info(f"Login attempt with non-existent email: {email}")
                form.add_error(None, "Invalid email or password.")
            except Exception as e:
                logger.error(f"Error during login for {email}: {str(e)}", exc_info=True)
                form.add_error(None, "An error occurred during login. Please try again.")
        else:
            logger.warning(f"Login form invalid: {form.errors}")
    else:
        form = LoginForm()

    return render(request, 'registration/login.html', {'form': form})
    
    





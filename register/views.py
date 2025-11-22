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
        # Get next URL but default to register page path without query params
        next_url = get_safe_next_url(request, '/register/')
        # Strip query parameters from next_url to avoid CSRF token in redirect
        if '?' in next_url:
            next_url = next_url.split('?')[0]
        form = RegisterForm()
        return render(request, 'register/register.html', {'form': form, 'next_url': next_url})

    def post(self, request):
        # Diagnostic logging for 500 error investigation
        logger.info("[RegisterView.post] Incoming Add Account request")
        logger.info(f"[RegisterView.post] Raw POST keys: {list(request.POST.keys())}")
        logger.info(f"[RegisterView.post] POST sample values: display_name={request.POST.get('display_name')}, email={request.POST.get('email')}, role={request.POST.get('role')}")
        form = RegisterForm(request.POST)
        next_url = get_safe_next_url(request, '/register/')
        # Strip query parameters from next_url to avoid CSRF token in redirect
        if '?' in next_url:
            next_url = next_url.split('?')[0]

        logger.info(f"[RegisterView.post] Form valid? {form.is_valid()}")
        if not form.is_valid():
            logger.warning(f"[RegisterView.post] Form errors: {form.errors}")

        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()  # This now calls our custom save method
                    logger.info(f"[RegisterView.post] User object created id={user.id} username={user.username}")
                    
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
                logger.info(f"[RegisterView.post] Redirecting to {success_url}")
                return redirect(success_url)

            except Exception as e:
                logger.error(f"[RegisterView.post] Exception during account creation: {str(e)}", exc_info=True)
                form.add_error(None, f"Error creating account: {e}")
                return render(request, 'register/register.html', {'form': form, 'next_url': next_url})

        return render(request, 'register/register.html', {'form': form, 'next_url': next_url})


@rate_limit(max_attempts=5, window_seconds=300)  # 5 login attempts per 5 minutes
def login_view(request):
    # Get client IP for debugging
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', 'UNKNOWN'))
    if ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()
    
    if request.method == "POST":
        form = LoginForm(request.POST)
        logger.warning(f"🔐 LOGIN ATTEMPT from IP: {client_ip} - Form valid: {form.is_valid()}")
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            logger.warning(f"   Email (cleaned): '{email}'")
            logger.warning(f"   Password length: {len(password) if password else 0}")
            logger.warning(f"   Password first 5 chars: '{password[:5] if password else 'EMPTY'}'")
            logger.warning(f"   Client IP: {client_ip}")
            try:
                # Try to find the user by email (case-insensitive)
                user = User.objects.get(email__iexact=email)
                logger.warning(f"   ✅ User found: {user.username}")
                logger.warning(f"   User is_active: {user.is_active}")
                logger.warning(f"   Password hash from DB: {user.password[:50]}...")
                
                # Check password directly first
                password_valid = user.check_password(password)
                logger.warning(f"   check_password() result: {password_valid}")
                
                # Authenticate using the username (not email)
                authenticated_user = authenticate(request, username=user.username, password=password)
                logger.warning(f"   authenticate() result: {authenticated_user}")

                if authenticated_user is not None:
                    login(request, authenticated_user)
                    logger.info(f"✅ Successful login for user: {user.username} ({email})")
                    return redirect('main:index')
                else:
                    # Invalid password
                    logger.warning(f"❌ Failed login attempt for {email}")
                    logger.warning(f"   - authenticate() returned None")
                    logger.warning(f"   - check_password() was: {password_valid}")
                    form.add_error(None, "Invalid email or password.")
            except User.DoesNotExist:
                logger.warning(f"❌ Login attempt with non-existent email: {email}")
                form.add_error(None, "Invalid email or password.")
            except Exception as e:
                logger.error(f"❌ Error during login for {email}: {str(e)}", exc_info=True)
                form.add_error(None, "An error occurred during login. Please try again.")
        else:
            logger.warning(f"❌ Login form invalid: {form.errors}")
    else:
        form = LoginForm()

    return render(request, 'registration/login.html', {'form': form})
    
    





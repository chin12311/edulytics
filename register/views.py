from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.views import View
from django.contrib.auth.models import User
from django.db import transaction
from main.models import UserProfile
from .forms import RegisterForm, LoginForm
from main.models import Section
from main.utils import log_admin_activity

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.views import View
from django.contrib.auth.models import User
from django.db import transaction
from main.models import UserProfile
from .forms import RegisterForm, LoginForm



class RegisterView(View):
    def get(self, request):
        next_url = request.GET.get('next', request.META.get('HTTP_REFERER', '/'))
        form = RegisterForm()
        return render(request, 'register/register.html', {'form': form, 'next_url': next_url})

    def post(self, request):
        form = RegisterForm(request.POST)
        next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))

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
                    
                return redirect(next_url)

            except Exception as e:
                form.add_error(None, f"Error creating account: {e}")
                return render(request, 'register/register.html', {'form': form, 'next_url': next_url})

        return render(request, 'register/register.html', {'form': form, 'next_url': next_url})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            # login(request, form.user)  # authenticated user
            # return redirect(next_url)
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)

                if user is not None:
                    login(request, user)
                    return redirect('main:index')
                else:
                    form = LoginForm()
            except User.DoesNotExist:
                pass # put a condition if the user does not exist.
    else:
        form = LoginForm()

    return render(request, 'registration/login.html', {'form': form})
    
    





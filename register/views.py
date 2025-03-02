from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from .forms import RegisterForm


# Create your views here.
class RegisterView(View):
    def get(self, request):
        form = RegisterForm()
        return render(request, 'register/register.html', {'form' : form})
    
    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
        return redirect('index')
from django.shortcuts import render, HttpResponse, redirect
from django.views import View
from .models import Teacher, UserProfile, Role
from django.core.exceptions import ObjectDoesNotExist
from .forms import CreateNewRating
from django.http import HttpResponseForbidden
# Create your views here.

class IndexView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return render(request, 'main/home.html')
        else:
            return redirect('/login')
    
class RatingView(View):
    def get(self, request):
        if request.user.is_authenticated:
            try:
                teachers = Teacher.objects.all()
                return render(request, 'main/index.html', {'teachers' : teachers})
            except ObjectDoesNotExist:
                return HttpResponse('TodoList does not exist', status = 404)
        else:
            return redirect('/login')
        
class CreateView(View):
    def get(self, request):
        if request.user.is_authenticated:
            form = CreateNewRating()
            return render(request, 'main/create.html', {'form' : form})
        else:
            return redirect('/login')
    
    def post(self, request):
        if request.user.is_authenticated:
            form = CreateNewRating(request.POST)

            if form.is_valid():
                n = form.cleaned_data['name']
                t = Teacher(name = n)
                t.save()
                return redirect('/')
        else:
            return redirect('/login')
        
class StudentsOnlyView(View):
    def get(self, request):
        if request.user.is_authenticated:
            try:
                user_profile = UserProfile.objects.get(user = request.user)
                if user_profile.role != Role.ADMIN:
                    return HttpResponseForbidden("Only an Admin are allowed to access this page.")
            except UserProfile.DoesNotExist:
                return redirect('/login')
            
            return render(request, 'main/students.html')
        else:
            return redirect('/login')
class DeanOnlyView(View):
    def get(self, request):
        if request.user.is_authenticated:
            try:
                user_profile = UserProfile.objects.get(user = request.user)
                if user_profile.role != Role.ADMIN:
                    return HttpResponseForbidden("Only an Admin are allowed to access this page.")
            except UserProfile.DoesNotExist:
                return redirect('/login')
            
            return render(request, 'main/students.html')
        else:
            return redirect('/login')
    
class CoordinatorOnlyView(View):
    def get(self, request):
        if request.user.is_authenticated:
            try:
                user_profile = UserProfile.objects.get(user = request.user)
                if user_profile.role != Role.ADMIN:
                    return HttpResponseForbidden("Only an Admin are allowed to access this page.")
            except UserProfile.DoesNotExist:
                return redirect('/login')
            
            return render(request, 'main/students.html')
        else:
            return redirect('/login')
    
class FacultyOnlyView(View):
    def get(self, request):
        if request.user.is_authenticated:
            try:
                user_profile = UserProfile.objects.get(user = request.user)
                if user_profile.role != Role.ADMIN:
                    return HttpResponseForbidden("Only an Admin are allowed to access this page.")
            except UserProfile.DoesNotExist:
                return redirect('/login')
            
            return render(request, 'main/students.html')
        else:
            return redirect('/login')
    

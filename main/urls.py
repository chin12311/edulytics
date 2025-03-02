from django.urls import path
from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('rating/', views.RatingView.as_view(), name='rating'),
    path('create/', views.CreateView.as_view(), name='creatrating'),
    path('students/', views.StudentsOnlyView.as_view(), name='students'),
    path('dean/', views.DeanOnlyView.as_view(), name='dean'),
    path('coordinator/', views.CoordinatorOnlyView.as_view(), name='coordinator'),
    path('faculty/', views.FacultyOnlyView.as_view(), name='faculty'),
]
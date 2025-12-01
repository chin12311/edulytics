from django.urls import path
from . import views

app_name = "register"
urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.login_view, name="login"),
    path("get-courses/<int:institute_id>/", views.get_courses_by_institute, name="get_courses"),
]
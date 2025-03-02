from django.contrib import admin
from .models import Teacher, UserProfile, Rating

# Register your models here.
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject')

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)

class RatingAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'score', 'review', 'created_at')

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'course')  # Display user and course in the list view
    list_filter = ('course',)  # Enable filtering by course
    search_fields = ('user__username', 'course')  # Allow searching by username and course

admin.site.register(Teacher, TeacherAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Rating, RatingAdmin)


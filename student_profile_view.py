# Student Profile Settings View
@method_decorator(cache_control(no_store=True, no_cache=True, must_revalidate=True), name='dispatch')
class StudentProfileSettingsView(View):
    
    def get(self, request):
        user = request.user
        if user.is_authenticated:
            try:
                user_profile = UserProfile.objects.get(user=user)
                
                if user_profile.role != Role.STUDENT:
                    return redirect('main:index')
                
                try:
                    index_url = reverse('main:index')
                except:
                    index_url = '/'
                
                next_url = request.GET.get('next', request.META.get('HTTP_REFERER', index_url))
                
                # Add timestamp for cache busting
                import time
                timestamp = int(time.time())
                
                return render(request, 'main/student_profile_settings.html', {
                    'user': user,
                    'user_profile': user_profile,
                    'next_url': next_url,
                    'timestamp': timestamp
                })
            except UserProfile.DoesNotExist:
                return redirect('/login')
        return redirect('/login')
    
    def post(self, request):
        user = request.user
        if user.is_authenticated:
            try:
                user_profile = UserProfile.objects.get(user=user)
                
                if user_profile.role != Role.STUDENT:
                    return redirect('main:index')
                
                try:
                    index_url = reverse('main:index')
                except:
                    index_url = '/'
                
                next_url = request.POST.get('next', request.META.get('HTTP_REFERER', index_url))
                
                username = request.POST.get("username")
                email = request.POST.get("email")
                new_password = request.POST.get("new_password1")
                confirm_password = request.POST.get("new_password2")
                
                # Email validation for students - must be @cca.edu.ph
                if not email.endswith("@cca.edu.ph"):
                    return render(request, 'main/student_profile_settings.html', {
                        'user': user,
                        'user_profile': user_profile,
                        'next_url': next_url,
                        'error': 'Students must use a @cca.edu.ph email address.'
                    })
                
                # Password validation
                if new_password and new_password != confirm_password:
                    return render(request, 'main/student_profile_settings.html', {
                        'user': user,
                        'user_profile': user_profile,
                        'next_url': next_url,
                        'error': 'Passwords do not match.'
                    })
                
                # Handle profile picture upload
                if 'profile_picture' in request.FILES:
                    user_profile.profile_picture = request.FILES['profile_picture']
                    user_profile.save()
                
                # Update user information
                user.username = username
                user.email = email
                
                if new_password:
                    user.set_password(new_password)
                    update_session_auth_hash(request, user)
                
                user.save()
                
                messages.success(request, "Profile updated successfully.")
                
                # Add success parameter to URL
                if "?" in next_url:
                    next_url += "&updated=true"
                else:
                    next_url += "?updated=true"
                
                return redirect(next_url)
                
            except UserProfile.DoesNotExist:
                return redirect('/login')
        return redirect('/login')

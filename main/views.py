from datetime import timezone
from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.views import View
from django.db import transaction
from django.core.paginator import Paginator
import openai
from .models import EvaluationComment, EvaluationPeriod, EvaluationResult, UserProfile, Role, AiRecommendation, EvaluationHistory
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .models import Evaluation, EvaluationResponse, IrregularEvaluation, Section, SectionAssignment, EvaluationFailureLog, AdminActivityLog
from django.urls import reverse
import re
from django.contrib.auth import logout, update_session_auth_hash
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required
from openai import OpenAI
import google.generativeai as genai
from django.conf import settings
import json
import logging
import time
from .ai_service import TeachingAIRecommendationService
from .decorators import evaluation_results_required, profile_settings_allowed
from .utils import log_admin_activity, can_view_evaluation_results
from main.services.evaluation_service import EvaluationService
from .validation_utils import AccountValidator
from .email_service import EvaluationEmailService

# Setup logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client only if API key is available
try:
    client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
except Exception as e:
    logger.warning(f"Failed to initialize OpenAI client: {e}")
    client = None


    
@method_decorator(cache_control(no_store=True, no_cache=True, must_revalidate=True), name='dispatch')
@method_decorator(login_required(login_url='login'), name='dispatch')
class IndexView(View):
    def get(self, request):
        try:
            # Fetch the user's profile
            user_profile = UserProfile.objects.get(user=request.user)

            # Admin view
            if user_profile.role == Role.ADMIN:
                # Use select_related to prevent N+1 queries on User lookups
                # Order by ID descending to show newest accounts first
                students_list = UserProfile.objects.filter(role=Role.STUDENT).select_related('user').order_by('-id')

                # Add pagination (25 items per page)
                paginator = Paginator(students_list, 25)
                page_number = request.GET.get('page', 1)
                students = paginator.get_page(page_number)

                # Distinct list of student courses - get course codes
                course_names = students_list.values_list('course', flat=True).distinct()
                # Get course codes from Course model
                from main.models import Course
                course_codes = set()
                for course_name in course_names:
                    if course_name:
                        course_obj = Course.objects.filter(name=course_name).first()
                        if course_obj and course_obj.code:
                            course_codes.add(course_obj.code)
                        else:
                            course_codes.add(course_name)
                course = sorted(course_codes)

                # Retrieve the selected user from the session (if any)
                selected_user_id = request.session.get('selected_user')
                selected_user = UserProfile.objects.get(id=selected_user_id) if selected_user_id else None

                context = {
                    'user_profile': user_profile,
                    'students': students,
                    'paginator': paginator,
                    'course': course,
                    'selected_user': selected_user,
                }
                response = render(request, 'main/index.html', context)

            elif user_profile.role == Role.COORDINATOR:
                return redirect('main:faculty')

            elif user_profile.role == Role.DEAN:
                return redirect('main:coordinators')

            # If the user is a Student or Faculty, redirect them to the evaluation page
            elif user_profile.role in [Role.STUDENT, Role.FACULTY]:
                return redirect('main:evaluation')  # Redirecting student and faculty to the evaluation page

            else:
                return HttpResponseForbidden("You do not have permission to access this page.")

            # Prevent caching
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response

        except UserProfile.DoesNotExist:
            return redirect('/login')

        return HttpResponse("Unhandled case.")

from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth.models import User
from .models import UserProfile, Role, Section, SectionAssignment

class UpdateUser(View):
        
        def get(self, request, user_Id):        
            try:
                user = get_object_or_404(User, id=user_Id)
                profile = user.userprofile

                # Get all sections
                sections = Section.objects.all()

                # For students, get their current section from profile
                student_current_section = None
                if profile.role == Role.STUDENT:
                    if profile.section:
                        student_current_section = profile.section.id
                        section_display = f"{profile.section.code} ({profile.section.get_year_level_display()})"
                        logger.debug(f"Student {user.username} - current section: {student_current_section} ({section_display})")
                    else:
                        logger.debug(f"Student {user.username} - no current section")

                # For staff, get assigned sections (prevent N+1 queries)
                assigned_sections = None
                currently_assigned_ids = []
                if profile.role in [Role.DEAN, Role.COORDINATOR, Role.FACULTY]:
                    assigned_sections = SectionAssignment.objects.filter(user=user).select_related('section')
                    currently_assigned_ids = assigned_sections.values_list('section_id', flat=True)

                # Capture the previous page or fallback to index
                next_url = request.GET.get('next', '')
                if not next_url:
                    try:
                        next_url = reverse('main:index')
                    except Exception as e:
                        logger.warning(f"Error generating reverse URL for main:index: {str(e)}")
                        next_url = '/'

                # Check for success message
                updated = request.GET.get('updated')
                success_message = "Profile updated successfully!" if updated else None

                context = {
                    'user': user,
                    'sections': sections,
                    'years': list(Section.objects.values_list("year_level", flat=True).distinct()),
                    'next_url': next_url,
                    'student_current_section': student_current_section,
                    'success': success_message,
                }

                # Only add staff-specific context for staff users
                if profile.role in [Role.DEAN, Role.COORDINATOR, Role.FACULTY]:
                    context.update({
                        'assigned_sections': assigned_sections,
                        'currently_assigned_ids': list(currently_assigned_ids),
                    })

                return render(request, 'main/update.html', context)

            except Exception as e:
                import traceback
                traceback.print_exc()
                return HttpResponse(f"Error loading page: {str(e)}", status=500)

        @transaction.atomic
        def post(self, request, user_Id):
       
            try:
                user = get_object_or_404(User, id=user_Id)
                profile = get_object_or_404(UserProfile, user=user)

                # Track changes for logging
                changes = []
                old_username = user.username
                old_email = user.email

                # Get form data
                new_username = request.POST.get("username", "").strip()
                new_email = request.POST.get("email", "").strip()
                new_password = request.POST.get("password", "").strip()
                confirm_password = request.POST.get("confirm_password", "").strip()
                section_id = request.POST.get("section")

                # Build validation data
                validation_data = {}
                if new_username:
                    validation_data['username'] = new_username
                if new_email:
                    validation_data['email'] = new_email
                if new_password:
                    validation_data['password'] = new_password
                    validation_data['confirm_password'] = confirm_password

                # Comprehensive validation using AccountValidator
                validation_result = AccountValidator.validate_account_update(
                    validation_data,
                    exclude_user_id=user.id
                )

                if not validation_result['valid']:
                    # Render form with validation errors
                    error_messages = " | ".join(validation_result['errors'].values())
                    context = {
                        'user': user,
                        'sections': Section.objects.all(),
                        'years': list(Section.objects.values_list("year_level", flat=True).distinct()),
                        'next_url': request.POST.get('next', '/'),
                        'error': error_messages,
                    }
                    
                    # Add staff-specific context if needed
                    if profile.role in [Role.DEAN, Role.COORDINATOR, Role.FACULTY]:
                        assigned_sections = SectionAssignment.objects.filter(user=user).select_related('section')
                        currently_assigned_ids = assigned_sections.values_list('section_id', flat=True)
                        context.update({
                            'assigned_sections': assigned_sections,
                            'currently_assigned_ids': list(currently_assigned_ids),
                        })
                    elif profile.role == Role.STUDENT:
                        if profile.section:
                            context['student_current_section'] = profile.section.id
                    
                    return render(request, 'main/update.html', context)


                # Store old section for comparison
                old_section = profile.section
                old_section_code = old_section.code if old_section else None


                # Update user details - USE THE NEW VARIABLE NAMES
                if old_username != new_username:
                    changes.append(f"Username: '{old_username}' → '{new_username}'")
                    user.username = new_username
                
                if old_email != new_email:
                    changes.append(f"Email: '{old_email}' → '{new_email}'")
                    user.email = new_email
                
                if new_password:
                    changes.append("Password: Updated")
                    user.set_password(new_password)
                
                user.save()


                # Handle student section update
                if profile.role == "Student":
                    # Handle irregular status toggle
                    is_irregular = request.POST.get("is_irregular") == "on"
                    if profile.is_irregular != is_irregular:
                        old_status = "Irregular" if profile.is_irregular else "Regular"
                        new_status = "Irregular" if is_irregular else "Regular"
                        changes.append(f"Student Status: '{old_status}' → '{new_status}'")
                        profile.is_irregular = is_irregular
                        profile.save()
                
                    if section_id:
                        try:
                            section = get_object_or_404(Section, id=section_id)
                        
                            # Check if section is actually changing
                            if old_section != section:
                                changes.append(f"Section: '{old_section.code if old_section else 'None'}' → '{section.code}'")
                            
                                # DELETE EVALUATION RESPONSES if section is changing
                                if old_section:
                                    
                                
                                    # Delete evaluations where this student is the EVALUATOR (submitted evaluations)
                                    evaluations_as_evaluator = EvaluationResponse.objects.filter(
                                        evaluator=user
                                    )
                                    evaluator_count = evaluations_as_evaluator.count()
                                
                                    # Delete evaluations where this student is the EVALUATEE (evaluations about them)
                                    evaluations_as_evaluatee = EvaluationResponse.objects.filter(
                                        evaluatee=user
                                    )
                                    evaluatee_count = evaluations_as_evaluatee.count()
                                
                                    # Delete all evaluations
                                    total_deleted = evaluator_count + evaluatee_count
                                    evaluations_as_evaluator.delete()
                                    evaluations_as_evaluatee.delete()
                                
                                    
                                else:
                                    logger.debug("No old section, no evaluations to delete")
                            
                                # Update the section
                                profile.section = section
                                profile.save()
                                
                            else:
                                
                                profile.section = section
                                profile.save()
                        
                            # Verify the save worked
                            profile.refresh_from_db()
                            current_section = str(profile.section) if profile.section else "None"
                            
                        
                        except Exception as e:
                            
                            import traceback
                            traceback.print_exc()
                    else:
                        
                        # Track section removal
                        if old_section:
                            changes.append(f"Section: '{old_section.code}' → 'None' (removed)")
                        
                        # Delete evaluations if clearing section and there was an old section
                        if old_section:
                            # Delete all evaluations for this student
                            evaluations_as_evaluator = EvaluationResponse.objects.filter(evaluator=user)
                            evaluator_count = evaluations_as_evaluator.count()
                        
                            evaluations_as_evaluatee = EvaluationResponse.objects.filter(evaluatee=user)
                            evaluatee_count = evaluations_as_evaluatee.count()
                        
                            total_deleted = evaluator_count + evaluatee_count
                            evaluations_as_evaluator.delete()
                            evaluations_as_evaluatee.delete()
                        
                            
                    
                        profile.section = None
                        profile.save()
                    
                    # Handle student number update for students
                    student_number = request.POST.get("studentnumber", "")
                    if student_number and profile.studentnumber != student_number:
                        changes.append(f"Student Number: '{profile.studentnumber}' → '{student_number}'")
                        profile.studentnumber = student_number
                        profile.save()
                

                elif profile.role in ["Dean", "Coordinator", "Faculty"]:
                    
                    selected_section_ids = request.POST.getlist("sections")
                    
                
                    # Properly handle section IDs - convert to integers and filter empty values
                    processed_section_ids = []
                    for section_id in selected_section_ids:
                        if section_id and section_id.strip():  # Check if not empty
                            try:
                                processed_section_ids.append(int(section_id))
                            except ValueError:
                                
                                continue
                
                    
                
                    # Get current assignments with related section data (prevent N+1 queries)
                    current_assignments = SectionAssignment.objects.filter(user=user).select_related('section')
                    current_section_ids = list(current_assignments.values_list('section_id', flat=True))
                    
                    # Track section changes for staff
                    old_sections = [assignment.section.code for assignment in current_assignments]
                
                    # Handle removal of all sections
                    if not processed_section_ids:
                        
                        # Track removal of all sections
                        if old_sections:
                            changes.append(f"Removed all section assignments: {', '.join(old_sections)}")
                    
                        # ✅ DELETE EVALUATION RESPONSES for all sections being removed
                        total_evaluations_deleted = 0
                        for assignment in current_assignments:
                            section_code = assignment.section.code
                        
                            # Delete evaluations where this staff is the EVALUATEE in this section
                            evaluations_as_evaluatee = EvaluationResponse.objects.filter(
                                evaluatee=user,
                                student_section=section_code
                            )
                            evaluatee_count = evaluations_as_evaluatee.count()
                            evaluations_as_evaluatee.delete()
                        
                            # Delete evaluations where this staff is the EVALUATOR in this section
                            evaluations_as_evaluator = EvaluationResponse.objects.filter(
                                evaluator=user,
                                student_section=section_code
                            )
                            evaluator_count = evaluations_as_evaluator.count()
                            evaluations_as_evaluator.delete()
                        
                            total_evaluations_deleted += evaluatee_count + evaluator_count
                            
                    
                        deleted_count, _ = current_assignments.delete()
                        
                    
                    else:
                        # Remove sections that are no longer selected
                        sections_to_remove = set(current_section_ids) - set(processed_section_ids)
                        if sections_to_remove:
                            # Track removed sections
                            removed_section_objects = Section.objects.filter(id__in=sections_to_remove)
                            removed_section_codes = [s.code for s in removed_section_objects]
                            changes.append(f"Removed sections: {', '.join(removed_section_codes)}")
                            
                            total_evaluations_deleted = 0
                        
                            # Get the assignments to be removed
                            assignments_to_remove = SectionAssignment.objects.filter(
                                user=user,
                                section_id__in=sections_to_remove
                            )
                        
                            # ✅ DELETE EVALUATION RESPONSES for each section being removed
                            for assignment in assignments_to_remove:
                                section_code = assignment.section.code
                            
                                # Delete evaluations where this staff is the EVALUATEE in this section
                                evaluations_as_evaluatee = EvaluationResponse.objects.filter(
                                    evaluatee=user,
                                    student_section=section_code
                                )
                                evaluatee_count = evaluations_as_evaluatee.count()
                                evaluations_as_evaluatee.delete()
                            
                                # Delete evaluations where this staff is the EVALUATOR in this section
                                evaluations_as_evaluator = EvaluationResponse.objects.filter(
                                    evaluator=user,
                                    student_section=section_code
                                )
                                evaluator_count = evaluations_as_evaluator.count()
                                evaluations_as_evaluator.delete()
                            
                                total_evaluations_deleted += evaluatee_count + evaluator_count
                                
                        
                            deleted_count = assignments_to_remove.delete()[0]
                            
                        # Add new sections that aren't already assigned
                        sections_to_add = set(processed_section_ids) - set(current_section_ids)
                        added_section_codes = []
                        for section_id in sections_to_add:
                            try:
                                section = Section.objects.get(id=section_id)
                                assignment, created = SectionAssignment.objects.get_or_create(
                                    user=user,
                                    section=section,
                                    defaults={'role': profile.role.lower()}
                                )
                                if created:
                                    added_section_codes.append(section.code)
                                    logger.debug(f"Created new assignment for section: {section.code}")
                                else:
                                    logger.debug(f"Assignment already exists for section: {section.code}")
                            except Section.DoesNotExist:
                                logger.warning(f"Section with ID {section_id} does not exist")
                            except Exception as e:
                                logger.error(f"ERROR creating assignment for section {section_id}: {str(e)}")
                        
                        # Track added sections
                        if added_section_codes:
                            changes.append(f"Added sections: {', '.join(added_section_codes)}")


                # Log admin activity with detailed changes
                if changes:
                    changes_text = " | ".join(changes)
                    description = f"Updated account for {user.username} ({user.email}) - Role: {profile.role}\nChanges: {changes_text}"
                else:
                    description = f"Viewed/accessed account settings for {user.username} ({user.email}) - Role: {profile.role} (No changes made)"
                
                log_admin_activity(
                    request=request,
                    action='update_account',
                    description=description,
                    target_user=user
                )

                # Redirect back to the update page to show changes
                next_url = request.POST.get('next', '')
                if not next_url:
                    try:
                        next_url = reverse('main:update-user', args=[user_Id])
                    except Exception as e:
                        logger.warning(f"Error generating update-user URL: {str(e)}")
                        next_url = f'/update-user/{user_Id}/'


                return redirect(next_url + ("&" if "?" in next_url else "?") + "updated=true")


            except Exception as e:
                logger.error(f"ERROR in UpdateUser POST: {str(e)}", exc_info=True)
                return HttpResponse(f"Error updating profile: {str(e)}", status=500)

    
class SelectStudentView(View):
    def get(self, request, student_id):
        try:
            # Get the selected student
            student = UserProfile.objects.get(id=student_id, role=Role.STUDENT)
            # Store the selected user in the session
            request.session['selected_user'] = student.id
            return redirect('index')  # Redirect back to the admin dashboard
        except UserProfile.DoesNotExist:
            return redirect('index')  # Handle the case where the student doesn't exist

    def delete(self, request, user_Id):
        user = get_object_or_404(User, id=user_Id)

        # Deleting the user account
        user.delete()

        # Redirect after deletion with a deleted flag in the URL
        next_url = request.META.get('HTTP_REFERER', reverse('index'))

        if "?" in next_url:
            next_url += "&deleted=true"
        else:
            next_url += "?deleted=true"

        return redirect(next_url)
    
@method_decorator(cache_control(no_store=True, no_cache=True, must_revalidate=True), name='dispatch')
class DeanOnlyView(View):
    def get(self, request):
        logger.debug(f"DeanOnlyView accessed by user: {request.user}")
        logger.debug(f"User authenticated: {request.user.is_authenticated}")
        
        if not request.user.is_authenticated:
            logger.info("User not authenticated, redirecting to login")
            return redirect('/login')

        try:
            user_profile = UserProfile.objects.get(user=request.user)
            logger.debug(f"User role: {user_profile.role}")
            logger.debug(f"User institute: {user_profile.institute}")

            # ✅ Allow Admin AND Dean to access dean management
            if user_profile.role in [Role.ADMIN, Role.DEAN]:
                logger.debug("User has permission to access Dean page")
                # Use select_related to prevent N+1 queries
                deans_list = UserProfile.objects.filter(role=Role.DEAN).select_related('user')
                
                # Add pagination (25 items per page)
                paginator = Paginator(deans_list, 25)
                page_number = request.GET.get('page', 1)
                deans = paginator.get_page(page_number)
                
                # ✅ Get distinct institutes from dean list - convert to codes
                institute_names = deans_list.values_list('institute', flat=True).distinct()
                from main.models import Institute
                institute_codes = set()
                for institute_name in institute_names:
                    if institute_name:
                        institute_obj = Institute.objects.filter(name=institute_name).first()
                        if institute_obj and institute_obj.code:
                            institute_codes.add(institute_obj.code)
                        else:
                            institute_codes.add(institute_name)
                institutes = sorted(institute_codes)

                context = {
                    'user_profile': user_profile,
                    'deans': deans,
                    'paginator': paginator,
                    'institutes': institutes
                }
                return render(request, 'main/dean.html', context)
            else:
                logger.warning(f"User role '{user_profile.role}' not allowed to access Dean page")
                return HttpResponseForbidden("You do not have permission to access this page.")

        except UserProfile.DoesNotExist:
            logger.warning("UserProfile does not exist")
            return redirect('/login')
        
@method_decorator(cache_control(no_store=True, no_cache=True, must_revalidate=True), name='dispatch')        
class FacultyOnlyView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('/login')

        try:
            user_profile = UserProfile.objects.get(user=request.user)

            # 🔥 Filter by institute for Dean and Coordinator
            if user_profile.role in [Role.COORDINATOR, Role.DEAN]:
                faculties_list = UserProfile.objects.filter(role=Role.FACULTY, institute=user_profile.institute).select_related('user')
                coordinators_list = UserProfile.objects.filter(role=Role.COORDINATOR, institute=user_profile.institute).select_related('user')

            # 🔥 Admin can see all faculties and coordinators
            elif user_profile.role == Role.ADMIN:
                faculties_list = UserProfile.objects.filter(role=Role.FACULTY).select_related('user')
                coordinators_list = UserProfile.objects.filter(role=Role.COORDINATOR).select_related('user')

            else:
                return HttpResponseForbidden("You do not have permission to access this page.")
            
            # Add pagination (25 items per page)
            faculties_paginator = Paginator(faculties_list, 25)
            coordinators_paginator = Paginator(coordinators_list, 25)
            page_number = request.GET.get('page', 1)
            faculties = faculties_paginator.get_page(page_number)
            coordinators = coordinators_paginator.get_page(page_number)
            
            # Get distinct institutes - convert to codes
            institute_names = coordinators_list.values_list('institute', flat=True).distinct()
            from main.models import Institute
            institute_codes = set()
            for institute_name in institute_names:
                if institute_name:
                    institute_obj = Institute.objects.filter(name=institute_name).first()
                    if institute_obj and institute_obj.code:
                        institute_codes.add(institute_obj.code)
                    else:
                        institute_codes.add(institute_name)
            institutes = sorted(institute_codes)

            context = {
                'user_profile': user_profile,
                'faculties': faculties,
                'coordinators': coordinators,
                'faculties_paginator': faculties_paginator,
                'coordinators_paginator': coordinators_paginator,
                'institutes': institutes,
            }
            return render(request, 'main/faculty.html', context)

        except UserProfile.DoesNotExist:
            return redirect('/login')
          
@method_decorator(cache_control(no_store=True, no_cache=True, must_revalidate=True), name='dispatch')    
class CoordinatorOnlyView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('/login')

        try:
            user_profile = UserProfile.objects.get(user=request.user)

            # 🔥 Dean should see ALL coordinators in their institute
            if user_profile.role == Role.DEAN:
                coordinators_list = UserProfile.objects.filter(
                    role=Role.COORDINATOR, 
                    institute=user_profile.institute
                ).select_related('user')

            # 🔥 Coordinator should see only themselves (or other logic as needed)
            elif user_profile.role == Role.COORDINATOR:
                coordinators_list = UserProfile.objects.filter(
                    role=Role.COORDINATOR, 
                    user=request.user  # Or adjust based on your requirements
                ).select_related('user')

            # 🔥 Admin sees all coordinators
            elif user_profile.role == Role.ADMIN:
                coordinators_list = UserProfile.objects.filter(
                    role=Role.COORDINATOR
                ).select_related('user')

            else:
                return HttpResponseForbidden("You do not have permission to access this page.")

            # Add pagination (25 items per page)
            paginator = Paginator(coordinators_list, 25)
            page_number = request.GET.get('page', 1)
            coordinators = paginator.get_page(page_number)

            # Get distinct institutes - convert to codes
            institute_names = coordinators_list.values_list('institute', flat=True).distinct()
            from main.models import Institute
            institute_codes = set()
            for institute_name in institute_names:
                if institute_name:
                    institute_obj = Institute.objects.filter(name=institute_name).first()
                    if institute_obj and institute_obj.code:
                        institute_codes.add(institute_obj.code)
                    else:
                        institute_codes.add(institute_name)
            institutes = sorted(institute_codes)

            # Pass filtered coordinators to the template
            context = {
                'user_profile': user_profile,
                'coordinators': coordinators,
                'paginator': paginator,
                'institutes': institutes,
            }
            return render(request, 'main/coordinator.html', context)

        except UserProfile.DoesNotExist:
            return redirect('/login')
    
        
@method_decorator(csrf_exempt, name='dispatch')
class DeleteAccountView(View):
    def delete(self, request, user_id, *args, **kwargs):
        try:
            user = get_object_or_404(User, id=user_id)
            
            # Store user info for logging
            username = user.username
            email = user.email
            
            # Log admin activity before deletion
            log_admin_activity(
                request=request,
                action='delete_account',
                description=f"Deleted account: {username} ({email})",
                target_user=user
            )
            
            # 🗑️ COMPREHENSIVE DELETE: Remove all user-related data
            # This ensures complete account removal from MySQL database
            
            try:
                # 1. Delete UserProfile (CASCADE will handle this, but being explicit)
                from main.models import UserProfile
                UserProfile.objects.filter(user=user).delete()
            except Exception as e:
                print(f"Error deleting UserProfile: {e}")
            
            try:
                # 2. Delete evaluation records - using correct field names
                from main.models import Evaluation, EvaluationResponse, EvaluationResult, EvaluationHistory
                
                # Evaluation uses 'evaluator' field
                Evaluation.objects.filter(evaluator=user).delete()
                
                # EvaluationResponse uses 'evaluator' and 'evaluatee' fields
                EvaluationResponse.objects.filter(evaluator=user).delete()
                EvaluationResponse.objects.filter(evaluatee=user).delete()
                
                # EvaluationResult uses 'user' field
                EvaluationResult.objects.filter(user=user).delete()
                
                # EvaluationHistory uses 'user' field
                EvaluationHistory.objects.filter(user=user).delete()
            except Exception as e:
                print(f"Error deleting evaluation records: {e}")
            
            try:
                # 3. Delete AI recommendations if any
                from main.models import AiRecommendation
                AiRecommendation.objects.filter(user=user).delete()
            except Exception as e:
                print(f"Error deleting AiRecommendation: {e}")
            
            try:
                # 4. Delete admin activity logs for this user
                from main.models import AdminActivityLog
                AdminActivityLog.objects.filter(target_user=user).delete()
            except Exception as e:
                print(f"Error deleting AdminActivityLog: {e}")
            
            try:
                # 5. Delete section assignments
                from main.models import SectionAssignment
                SectionAssignment.objects.filter(user=user).delete()
            except Exception as e:
                print(f"Error deleting SectionAssignment: {e}")
            
            try:
                # 6. Delete evaluation failure logs
                from main.models import EvaluationFailureLog
                EvaluationFailureLog.objects.filter(user=user).delete()
            except Exception as e:
                print(f"Error deleting EvaluationFailureLog: {e}")
            
            try:
                # 7. Delete evaluation comments
                from main.models import EvaluationComment
                EvaluationComment.objects.filter(user=user).delete()
            except Exception as e:
                print(f"Error deleting EvaluationComment: {e}")
            
            try:
                # 8. Finally delete the User from auth_user
                user.delete()
            except Exception as e:
                return JsonResponse({'error': f'Failed to delete user account: {str(e)}'}, status=400)
            
            return JsonResponse({
                'message': f'Account {username} ({email}) deleted successfully with all related data',
                'status': 'success'
            }, status=200)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': f'Deletion failed: {str(e)}'}, status=400)
    
    def post(self, request, user_id, *args, **kwargs):
        return self.delete(request, user_id, *args, **kwargs)
    
@method_decorator(cache_control(no_store=True, no_cache=True, must_revalidate=True), name='dispatch')    
class EvaluationView(View):
    def get(self, request):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return redirect('/login')

        try:
            # Get the user profile to check the role
            user_profile = UserProfile.objects.get(user=request.user)

            # Only Admin, Coordinator, Dean, Faculty, and Student can access
            if user_profile.role in [Role.ADMIN, Role.COORDINATOR, Role.DEAN, Role.FACULTY, Role.STUDENT]:
                # 🔍 CRITICAL FIX: Get the correct evaluation type based on user role
                if user_profile.role == Role.STUDENT:
                    # Students evaluate faculty - check for STUDENT evaluation
                    evaluation = Evaluation.objects.filter(
                        is_released=True,
                        evaluation_type='student'
                    ).order_by('-created_at').first()
                    page_title = "Student Evaluation"
                else:
                    # Faculty/Dean/Coordinator evaluate each other - check for PEER evaluation
                    evaluation = Evaluation.objects.filter(
                        is_released=True,
                        evaluation_type='peer'
                    ).order_by('-created_at').first()
                    page_title = "Evaluation"

                # Check if this is a redirect after successful submission
                submitted = request.GET.get('submitted', False)

                # Always pass evaluation to the context — even if it's None
                context = {
                    'evaluation': evaluation,
                    'page_title': page_title,
                    'show_success_popup': submitted  # This triggers the popup
                }
                return render(request, 'main/evaluation.html', context)

            else:
                return HttpResponseForbidden("You do not have permission to access this page.")

        except UserProfile.DoesNotExist:
            return redirect('/login')

    def post(self, request):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return redirect('/login')

        try:
            # Get the user profile to check the role
            user_profile = UserProfile.objects.get(user=request.user)

            # Only Admin, Coordinator, Dean, Faculty, and Student can submit the form
            if user_profile.role in [Role.ADMIN, Role.COORDINATOR, Role.DEAN, Role.FACULTY, Role.STUDENT]:
                # Get the answers from the form submission
                question1 = request.POST.get('question1')
                question2 = request.POST.get('question2')
                question3 = request.POST.get('question3')

                # Save the responses to the database
                response = EvaluationResponse(
                    question1=question1,
                    question2=question2,
                    question3=question3,
                )
                response.save()

                # Redirect back to evaluation page with success parameter
                evaluation_url = reverse('main:evaluation') + '?submitted=true'
                return redirect(evaluation_url)
                
            else:
                return HttpResponseForbidden("You do not have permission to submit this form.")

        except UserProfile.DoesNotExist:
            return redirect('/login')
        
class EvaluationConfigView(View):
    def get(self, request, *args, **kwargs):
        student_evaluation_released = Evaluation.is_evaluation_period_active('student')
        peer_evaluation_released = Evaluation.is_evaluation_period_active('peer')

        context = {
            'page_title': 'Evaluation Configuration',
            'student_evaluation_released': student_evaluation_released,
            'peer_evaluation_released': peer_evaluation_released,
            'evaluation_period_ended': not student_evaluation_released,  # Add this
        }
        return render(request, 'main/evaluationconfig.html', context)
# Update your release/unrelease functions to return better messages
def release_student_evaluation(request):
    """
    NEW FLOW: When admin clicks release (starts new evaluation):
    1. Move old EvaluationResult records to EvaluationHistory (archive previous results)
    2. Create new EvaluationPeriod with is_active=True
    3. Create/update Evaluation record with evaluator='students' and link to period
    4. Students can now evaluate
    """
    logger.debug("release_student_evaluation called")
    logger.debug(f"Request method: {request.method}")
    logger.debug(f"User: {request.user}")
    
    if request.method == 'POST':
        logger.debug("Processing POST request to release student evaluation")
        try:
            from django.utils import timezone
            
            # Check if there's already an active student evaluation period
            active_period = EvaluationPeriod.objects.filter(evaluation_type='student', is_active=True).exists()
            logger.debug(f"Active student evaluation period exists: {active_period}")
            
            if active_period:
                logger.info("Attempting to release evaluation when period is already active")
                return JsonResponse({'success': False, 'error': "Student evaluation is already released."})

            # STEP 1: Move current EvaluationResult records to EvaluationHistory
            # This moves old results from profile settings to history when starting new evaluation
            logger.info("Moving current EvaluationResult records to history...")
            archived_count = move_current_results_to_history()
            logger.info(f"Moved {archived_count} results to evaluation history")
            
            # STEP 2: Create a new active evaluation period with unique name
            period_timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
            new_period = EvaluationPeriod.objects.create(
                name=f"Student Evaluation {period_timestamp}",
                evaluation_type='student',
                start_date=timezone.now(),
                end_date=timezone.now() + timezone.timedelta(days=30),
                is_active=True
            )
            logger.info(f"Created new evaluation period: {new_period.name}")

            # STEP 3: Create or update Evaluation record with evaluator='students'
            evaluation, created = Evaluation.objects.update_or_create(
                evaluation_type='student',
                defaults={
                    'is_released': True,
                    'evaluation_period': new_period,
                    'evaluator': 'students'  # Students evaluate teachers
                }
            )
            action = "Created" if created else "Updated"
            logger.info(f"{action} student evaluation record with evaluator='students'")

            log_admin_activity(
                request=request,
                action='release_evaluation',
                description=f"Started new evaluation period '{new_period.name}'. Previous results ({archived_count} records) moved to history."
            )
            
            # Send email notifications asynchronously (won't block response)
            email_notification = {'sent': 0, 'failed': 0, 'message': 'Emails are being sent in background'}
            try:
                import threading
                def send_emails_background():
                    try:
                        logger.info("Background: Sending email notifications about evaluation release")
                        email_result = EvaluationEmailService.send_evaluation_released_notification('student')
                        logger.info(f"Background: Email notification result: {email_result}")
                    except Exception as e:
                        logger.error(f"Background: Email notification failed: {e}")
                
                # Start email sending in background thread
                email_thread = threading.Thread(target=send_emails_background, daemon=True)
                email_thread.start()
                logger.info("Email notification thread started in background")
            except Exception as e:
                logger.error(f"Failed to start email thread: {e}")
                email_notification['message'] = 'Email notification skipped due to error'
            
            response_data = {
                'success': True,
                'message': f'New evaluation period started: {new_period.name}. Previous results ({archived_count} records) moved to evaluation history. Students can now evaluate.',
                'student_evaluation_released': True,
                'evaluation_period_ended': False,
                'results_archived': archived_count,
                'new_period': new_period.name,
                'email_notification': email_notification
            }
            logger.debug(f"Returning success: {response_data}")
            return JsonResponse(response_data)
        
        except Exception as e:
            logger.error(f"Exception in release_student_evaluation: {e}", exc_info=True)
            return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})
    
    logger.debug("Not a POST request")
    return JsonResponse({'success': False, 'error': 'Invalid request'})


def generate_and_save_ai_recommendations_for_period(period):
    """
    Generate and save AI recommendations for all users who have evaluation results in this period
    Called when a period ends (unrelease) to preserve AI recommendations for history
    """
    from main.models import EvaluationResult, AiRecommendation, SectionAssignment
    from main.services.teaching_ai_service import TeachingAIRecommendationService
    
    ai_service = TeachingAIRecommendationService()
    recommendations_saved = 0
    
    # Get all unique users who have results in this period
    users_with_results = EvaluationResult.objects.filter(
        evaluation_period=period
    ).values_list('user', flat=True).distinct()
    
    for user_id in users_with_results:
        try:
            user = User.objects.get(id=user_id)
            
            # Get user's assigned sections
            assigned_sections = SectionAssignment.objects.filter(user=user).select_related('section')
            
            # Get results for each section
            for assignment in assigned_sections:
                section = assignment.section
                section_code = section.code
                
                # Get evaluation result for this section
                try:
                    result = EvaluationResult.objects.get(
                        user=user,
                        section=section,
                        evaluation_period=period
                    )
                    
                    # Prepare section data for AI recommendations
                    section_data = {
                        'has_data': True,
                        'category_scores': [
                            result.category_a_score,
                            result.category_b_score,
                            result.category_c_score,
                            result.category_d_score
                        ],
                        'total_percentage': result.total_percentage,
                        'evaluation_count': result.total_responses,
                        'positive_comments': [],
                        'negative_comments': [],
                        'mixed_comments': [],
                        'question_scores': []
                    }
                    
                    # Calculate individual question scores from responses
                    responses = EvaluationResponse.objects.filter(
                        evaluatee=user,
                        student_section=section_code,
                        evaluation_period=period
                    )
                    
                    if responses.exists():
                        # Get all question fields (q1 through q19)
                        question_fields = [f'q{i}' for i in range(1, 20)]
                        question_texts = {
                            'q1': 'Demonstrates mastery of the subject matter',
                            'q2': 'Draws and shares conclusions from relevant experiences',
                            'q3': 'Integrates subject with relevant disciplines',
                            'q4': 'Organizes subject matter effectively',
                            'q5': 'Provides relevant and updated references',
                            'q6': 'Maintains discipline in the classroom',
                            'q7': 'Holds interest of students throughout the period',
                            'q8': 'Manages classroom interactions effectively',
                            'q9': 'Starts and ends class on time',
                            'q10': 'Demonstrates leadership and professionalism',
                            'q11': 'Comes to class prepared',
                            'q12': 'Complies with course requirements',
                            'q13': 'Returns checked tests/assignments on time',
                            'q14': 'Shows mastery in using educational technology',
                            'q15': 'Explains concepts clearly',
                            'q16': 'Shows enthusiasm in teaching',
                            'q17': 'Encourages participation and discussion',
                            'q18': 'Demonstrates fairness in grading',
                            'q19': 'Overall teaching effectiveness'
                        }
                        
                        for field in question_fields:
                            # Calculate average for this question
                            scores = responses.values_list(field, flat=True)
                            valid_scores = [s for s in scores if s is not None and s > 0]
                            if valid_scores:
                                avg_score = sum(valid_scores) / len(valid_scores)
                                percentage = (avg_score / 5.0) * 100
                                section_data['question_scores'].append({
                                    'question': question_texts.get(field, field),
                                    'score': round(avg_score, 2),
                                    'percentage': round(percentage, 1)
                                })
                    
                    # Get comments for this section
                    comments = EvaluationResponse.objects.filter(
                        evaluatee=user,
                        student_section=section_code,
                        evaluation_period=period,
                        comments__isnull=False
                    ).exclude(comments='').values_list('comments', flat=True)
                    
                    # Categorize comments
                    for comment in comments:
                        sentiment = TeachingAIRecommendationService.analyze_comment_sentiment(comment)
                        if sentiment == 'positive':
                            section_data['positive_comments'].append(comment)
                        elif sentiment == 'negative':
                            section_data['negative_comments'].append(comment)
                        elif sentiment == 'mixed':
                            section_data['mixed_comments'].append(comment)
                    
                    # Generate AI recommendations for this section
                    recommendations = ai_service.get_recommendations(
                        user=user,
                        section_data=section_data,
                        section_code=section_code,
                        role=user.userprofile.role if hasattr(user, 'userprofile') else "Faculty"
                    )
                    
                    # Save recommendations to database
                    if recommendations and isinstance(recommendations, list):
                        for rec in recommendations:
                            if isinstance(rec, dict):
                                AiRecommendation.objects.create(
                                    user=user,
                                    evaluation_period=period,
                                    title=str(rec.get('title', '')[:255]),
                                    description=rec.get('description', ''),
                                    priority=rec.get('priority', ''),
                                    reason=rec.get('reason', ''),
                                    recommendation=rec.get('description', ''),
                                    evaluation_type='student',
                                    section_code=section_code
                                )
                                recommendations_saved += 1
                                
                except EvaluationResult.DoesNotExist:
                    # No result for this section, skip
                    continue
                    
        except Exception as e:
            logger.error(f"Error generating AI recommendations for user {user_id}: {str(e)}")
            continue
    
    return recommendations_saved


def unrelease_student_evaluation(request):
    """
    NEW FLOW: When admin clicks unrelease (ends evaluation):
    1. Process evaluation responses into EvaluationResult (visible in profile settings)
    2. Set EvaluationPeriod to is_active=False
    3. Set Evaluation.is_released=False
    4. Results stay in EvaluationResult until next release moves them to history
    """
    if request.method == 'POST':
        try:
            # Check if there's an active period
            active_period = EvaluationPeriod.objects.filter(
                evaluation_type='student',
                is_active=True
            ).first()
            
            if not active_period:
                return JsonResponse({
                    'success': False,
                    'error': 'No active student evaluation period found.'
                })
            
            # Set Evaluation to unreleased
            evaluations = Evaluation.objects.filter(evaluation_type='student')
            evaluations.update(is_released=False)

            # Process the period
            # STEP 1: Process all evaluation responses from this period into EvaluationResult
            # This makes results visible in profile settings
            logger.info(f"Processing evaluation results for period: {active_period.name}")
            processed_count = process_evaluation_period_to_results(active_period)
            logger.info(f"Processed {processed_count} evaluation results")
            
            # STEP 2: Deactivate the evaluation period (set is_active=False)
            active_period.is_active = False
            active_period.end_date = timezone.now()
            active_period.save()
            logger.info(f"Deactivated evaluation period: {active_period.name}")
            logger.info(f"Results are now visible in profile settings (EvaluationResult table)")
            
            # Log admin activity
            log_admin_activity(
                request=request,
                action='unrelease_evaluation',
                description=f"Ended student evaluation period '{active_period.name}'. Processed {processed_count} results now visible in profile settings."
            )
            
            # Send email notifications asynchronously (won't block response)
            email_notification = {'sent': 0, 'failed': 0, 'message': 'Emails are being sent in background'}
            try:
                import threading
                def send_emails_background():
                    try:
                        logger.info("Background: Sending email notifications about evaluation close")
                        email_result = EvaluationEmailService.send_evaluation_unreleased_notification('student')
                        logger.info(f"Background: Email notification result: {email_result}")
                    except Exception as e:
                        logger.error(f"Background: Email notification failed: {e}")
                
                # Start email sending in background thread
                email_thread = threading.Thread(target=send_emails_background, daemon=True)
                email_thread.start()
                logger.info("Email notification thread started in background")
            except Exception as e:
                logger.error(f"Failed to start email thread: {e}")
                email_notification['message'] = 'Email notification skipped due to error'
            
            message = f'Student evaluation period "{active_period.name}" has ended. Results processed for {processed_count} staff members and are now visible in profile settings.'
            
            return JsonResponse({
                'success': True,
                'message': message,
                'processed_count': processed_count,
                'student_evaluation_released': False,
                'evaluation_period_ended': True,
                'period_name': active_period.name,
                'email_notification': email_notification
            })
        except Exception as e:
            logger.error(f"Error in unrelease_student_evaluation: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Server error: {str(e)}'
            })
    
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request'
    })

def release_peer_evaluation(request):
    """
    NEW FLOW for peer evaluation release:
    1. Move old EvaluationResult records to EvaluationHistory
    2. Create new EvaluationPeriod with is_active=True
    3. Create/update Evaluation record with evaluator='peer'
    """
    if request.method == 'POST':
        try:
            from django.utils import timezone
            
            # Check if there's already an active peer evaluation period
            active_period = EvaluationPeriod.objects.filter(evaluation_type='peer', is_active=True).exists()
            
            if active_period:
                return JsonResponse({
                    'success': False, 
                    'error': "Peer evaluation is already released."
                })

            # STEP 1: Move current EvaluationResult records to EvaluationHistory
            logger.info("Moving current peer EvaluationResult records to history...")
            archived_count = move_current_results_to_history()
            logger.info(f"Moved {archived_count} results to evaluation history")

            # STEP 2: Create new active evaluation period with unique name
            period_timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
            evaluation_period = EvaluationPeriod.objects.create(
                name=f"Peer Evaluation {period_timestamp}",
                evaluation_type='peer',
                start_date=timezone.now(),
                end_date=timezone.now() + timezone.timedelta(days=30),
                is_active=True
            )
            logger.info(f"Created new peer evaluation period: {evaluation_period.name}")

            # STEP 3: Create or update Evaluation record with evaluator='peer'
            evaluation, created = Evaluation.objects.update_or_create(
                evaluation_type='peer',
                defaults={
                    'is_released': True,
                    'evaluation_period': evaluation_period,
                    'evaluator': 'peer'  # Peer evaluation (teachers evaluate each other)
                }
            )
            action = "Created" if created else "Updated"
            logger.info(f"{action} peer evaluation record with evaluator='peer'")

            # Send email notifications asynchronously
            email_notification = {'sent': 0, 'failed': 0, 'message': 'Emails are being sent in background'}
            try:
                import threading
                def send_emails_background():
                    try:
                        logger.info("Background: Sending email notifications about peer evaluation release")
                        email_result = EvaluationEmailService.send_evaluation_released_notification('peer')
                        logger.info(f"Background: Email notification result: {email_result}")
                    except Exception as e:
                        logger.error(f"Background: Email notification failed: {e}")
                
                email_thread = threading.Thread(target=send_emails_background, daemon=True)
                email_thread.start()
                logger.info("Email notification thread started in background")
            except Exception as e:
                logger.error(f"Failed to start email thread: {e}")
                email_notification['message'] = 'Email notification skipped due to error'
            
            return JsonResponse({
                'success': True,
                'message': f'Peer evaluation period started: {evaluation_period.name}. Previous results ({archived_count} records) moved to history. Staff can now evaluate peers.',
                'peer_evaluation_released': True,
                'evaluation_period_ended': False,
                'results_archived': archived_count,
                'new_period': evaluation_period.name,
                'email_notification': email_notification
            })
        except Exception as e:
            logger.error(f"Exception in release_peer_evaluation: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Server error: {str(e)}'
            })
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request'
    })

def unrelease_peer_evaluation(request):
    """
    NEW FLOW for peer evaluation unrelease:
    1. Process responses into EvaluationResult (visible in profile settings)
    2. Set EvaluationPeriod to is_active=False
    3. Set Evaluation.is_released=False
    """
    if request.method == 'POST':
        try:
            # Get the active peer evaluation period
            active_period = EvaluationPeriod.objects.filter(
                evaluation_type='peer',
                is_active=True
            ).first()

            if not active_period:
                return JsonResponse({
                    'success': False,
                    'error': 'No active peer evaluation period found.'
                })
            
            # Set Evaluation to unreleased
            evaluations = Evaluation.objects.filter(evaluation_type='peer')
            evaluations.update(is_released=False)

            # STEP 1: Process peer evaluation responses into EvaluationResult
            logger.info(f"Processing peer evaluation results for period: {active_period.name}")
            processing_results = process_peer_evaluation_results(evaluation_period=active_period)
            logger.info(f"Processed {processing_results.get('processed_count', 0)} peer results")

            # STEP 2: Deactivate the evaluation period
            active_period.is_active = False
            active_period.end_date = timezone.now()
            active_period.save()
            logger.info(f"Deactivated peer evaluation period: {active_period.name}")

            # Send email notifications asynchronously (won't block response)
            email_notification = {'sent': 0, 'failed': 0, 'message': 'Emails are being sent in background'}
            try:
                import threading
                def send_emails_background():
                    try:
                        logger.info("Background: Sending email notifications about peer evaluation close")
                        email_result = EvaluationEmailService.send_evaluation_unreleased_notification('peer')
                        logger.info(f"Background: Email notification result: {email_result}")
                    except Exception as e:
                        logger.error(f"Background: Email notification failed: {e}")
                
                # Start email sending in background thread
                email_thread = threading.Thread(target=send_emails_background, daemon=True)
                email_thread.start()
                logger.info("Email notification thread started in background")
            except Exception as e:
                logger.error(f"Failed to start email thread: {e}")
                email_notification['message'] = 'Email notification skipped due to error'

            message = f'Peer evaluation period "{active_period.name}" has ended.'

            if processing_results['success']:
                processed_count = processing_results['processed_count']
                message += f' Successfully processed evaluation results for {processed_count} staff members.'
            else:
                message += ' But evaluation processing failed. Please check the logs.'

            return JsonResponse({
                'success': True,
                'message': message,
                'peer_evaluation_released': False,
                'evaluation_period_ended': True,
                'period_name': active_period.name,
                'email_notification': email_notification
            })
        except Exception as e:
            logger.error(f"Error in unrelease_peer_evaluation: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Server error: {str(e)}'
            })
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request'
    })


def release_upward_evaluation(request):
    """
    Release upward evaluation (Faculty → Coordinator):
    1. Move old EvaluationResult records to EvaluationHistory
    2. Create new EvaluationPeriod with is_active=True
    3. Create/update Evaluation record with evaluator='upward'
    """
    if request.method == 'POST':
        try:
            from django.utils import timezone
            
            # Check if there's already an active upward evaluation period
            active_period = EvaluationPeriod.objects.filter(evaluation_type='upward', is_active=True).exists()
            
            if active_period:
                return JsonResponse({
                    'success': False, 
                    'error': "Upward evaluation is already released."
                })

            # STEP 1: Move current EvaluationResult records to EvaluationHistory
            logger.info("Moving current upward EvaluationResult records to history...")
            archived_count = move_current_results_to_history()
            logger.info(f"Moved {archived_count} results to evaluation history")

            # STEP 2: Create new active evaluation period with unique name
            period_timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
            evaluation_period = EvaluationPeriod.objects.create(
                name=f"Upward Evaluation {period_timestamp}",
                evaluation_type='upward',
                start_date=timezone.now(),
                end_date=timezone.now() + timezone.timedelta(days=30),
                is_active=True
            )
            logger.info(f"Created new upward evaluation period: {evaluation_period.name}")

            # STEP 3: Create or update Evaluation record with evaluator='upward'
            evaluation, created = Evaluation.objects.update_or_create(
                evaluation_type='upward',
                defaults={
                    'is_released': True,
                    'evaluation_period': evaluation_period,
                    'evaluator': 'upward'  # Faculty evaluate coordinators
                }
            )
            action = "Created" if created else "Updated"
            logger.info(f"{action} upward evaluation record with evaluator='upward'")

            # Send email notifications to Faculty only
            logger.info("Background: Sending email notifications about upward evaluation release")
            email_result = EvaluationEmailService.send_evaluation_released_notification('upward')
            logger.info(f"Email notification result: {email_result.get('message', 'Unknown')}")

            log_admin_activity(
                request=request,
                action='release_evaluation',
                description=f"Started upward evaluation period '{evaluation_period.name}'. Previous results ({archived_count} records) moved to history."
            )

            return JsonResponse({
                'success': True,
                'message': f'Upward evaluation period started: {evaluation_period.name}. Previous results ({archived_count} records) moved to history. Faculty can now evaluate coordinators.',
                'upward_evaluation_released': True,
                'evaluation_period_ended': False,
                'results_archived': archived_count,
                'new_period': evaluation_period.name,
                'emails_sent': email_result.get('sent_count', 0)
            })
        except Exception as e:
            logger.error(f"Exception in release_upward_evaluation: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Server error: {str(e)}'
            })
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request'
    })


def unrelease_upward_evaluation(request):
    """
    Unrelease upward evaluation:
    1. Process responses into EvaluationResult (visible to admin only)
    2. Set EvaluationPeriod to is_active=False
    3. Set Evaluation.is_released=False
    """
    if request.method == 'POST':
        try:
            # Get the active upward evaluation period
            active_period = EvaluationPeriod.objects.filter(
                evaluation_type='upward',
                is_active=True
            ).first()

            if not active_period:
                return JsonResponse({
                    'success': False,
                    'error': 'No active upward evaluation period found.'
                })
            
            # Set Evaluation to unreleased
            evaluations = Evaluation.objects.filter(evaluation_type='upward')
            evaluations.update(is_released=False)

            # STEP 1: Process upward evaluation responses into EvaluationResult
            logger.info(f"Processing upward evaluation results for period: {active_period.name}")
            processing_results = process_upward_evaluation_results(evaluation_period=active_period)
            logger.info(f"Processed {processing_results.get('processed_count', 0)} upward results")

            # STEP 2: Deactivate the evaluation period
            active_period.is_active = False
            active_period.end_date = timezone.now()
            active_period.save()
            logger.info(f"Deactivated upward evaluation period: {active_period.name}")

            # Send email notifications to Faculty only
            logger.info("Background: Sending email notifications about upward evaluation closure")
            email_result = EvaluationEmailService.send_evaluation_unreleased_notification('upward')
            logger.info(f"Email notification result: {email_result.get('message', 'Unknown')}")

            log_admin_activity(
                request=request,
                action='unrelease_evaluation',
                description=f"Ended upward evaluation period '{active_period.name}'. Processed {processing_results.get('processed_count', 0)} coordinator evaluations."
            )

            message = f'Upward evaluation period "{active_period.name}" has ended.'

            if processing_results['success']:
                processed_count = processing_results['processed_count']
                message += f' Successfully processed evaluation results for {processed_count} coordinators (visible to admin only).'
            else:
                message += ' But evaluation processing failed. Please check the logs.'

            return JsonResponse({
                'success': True,
                'message': message,
                'upward_evaluation_released': False,
                'evaluation_period_ended': True,
                'period_name': active_period.name,
                'emails_sent': email_result.get('sent_count', 0)
            })
        except Exception as e:
            logger.error(f"Error in unrelease_upward_evaluation: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Server error: {str(e)}'
            })
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request'
    })


def release_dean_evaluation(request):
    """
    Release dean evaluation (Faculty → Dean):
    1. Move old EvaluationResult records to EvaluationHistory
    2. Create new EvaluationPeriod with is_active=True
    3. Create/update Evaluation record with evaluator='dean'
    """
    if request.method == 'POST':
        try:
            from django.utils import timezone
            
            # Check if there's already an active dean evaluation period
            active_period = EvaluationPeriod.objects.filter(evaluation_type='dean', is_active=True).exists()
            
            if active_period:
                return JsonResponse({
                    'success': False, 
                    'error': "Dean evaluation is already released."
                })

            # STEP 1: Move current EvaluationResult records to EvaluationHistory
            logger.info("Moving current dean EvaluationResult records to history...")
            archived_count = move_current_results_to_history()
            logger.info(f"Moved {archived_count} results to evaluation history")

            # STEP 2: Create new active evaluation period with unique name
            period_timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
            evaluation_period = EvaluationPeriod.objects.create(
                name=f"Dean Evaluation {period_timestamp}",
                evaluation_type='dean',
                start_date=timezone.now(),
                end_date=timezone.now() + timezone.timedelta(days=30),
                is_active=True
            )
            logger.info(f"Created new dean evaluation period: {evaluation_period.name}")

            # STEP 3: Create or update Evaluation record with evaluator='dean'
            evaluation, created = Evaluation.objects.update_or_create(
                evaluation_type='dean',
                defaults={
                    'is_released': True,
                    'evaluation_period': evaluation_period,
                    'evaluator': 'dean'  # Faculty evaluate deans
                }
            )
            action = "Created" if created else "Updated"
            logger.info(f"{action} dean evaluation record with evaluator='dean'")

            # Send email notifications to Faculty only
            logger.info("Background: Sending email notifications about dean evaluation release")
            email_result = EvaluationEmailService.send_evaluation_released_notification('dean')
            logger.info(f"Email notification result: {email_result.get('message', 'Unknown')}")

            log_admin_activity(
                request=request,
                action='release_evaluation',
                description=f"Started dean evaluation period '{evaluation_period.name}'. Previous results ({archived_count} records) moved to history."
            )

            return JsonResponse({
                'success': True,
                'message': f'Dean evaluation period started: {evaluation_period.name}. Previous results ({archived_count} records) moved to history. Faculty can now evaluate deans.',
                'dean_evaluation_released': True,
                'evaluation_period_ended': False,
                'results_archived': archived_count,
                'new_period': evaluation_period.name,
                'emails_sent': email_result.get('sent_count', 0)
            })
        except Exception as e:
            logger.error(f"Exception in release_dean_evaluation: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Server error: {str(e)}'
            })
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request'
    })


def unrelease_dean_evaluation(request):
    """
    Unrelease dean evaluation:
    1. Process responses into EvaluationResult (visible to admin only)
    2. Set EvaluationPeriod to is_active=False
    3. Set Evaluation.is_released=False
    """
    if request.method == 'POST':
        try:
            # Get the active dean evaluation period
            active_period = EvaluationPeriod.objects.filter(
                evaluation_type='dean',
                is_active=True
            ).first()

            if not active_period:
                return JsonResponse({
                    'success': False,
                    'error': 'No active dean evaluation period found.'
                })
            
            # Set Evaluation to unreleased
            evaluations = Evaluation.objects.filter(evaluation_type='dean')
            evaluations.update(is_released=False)

            # STEP 1: Process dean evaluation responses into EvaluationResult
            logger.info(f"Processing dean evaluation results for period: {active_period.name}")
            processing_results = process_dean_evaluation_results(evaluation_period=active_period)
            logger.info(f"Processed {processing_results.get('processed_count', 0)} dean results")

            # STEP 2: Deactivate the evaluation period
            active_period.is_active = False
            active_period.end_date = timezone.now()
            active_period.save()
            logger.info(f"Deactivated dean evaluation period: {active_period.name}")

            # Send email notifications to Faculty only
            logger.info("Background: Sending email notifications about dean evaluation closure")
            email_result = EvaluationEmailService.send_evaluation_unreleased_notification('dean')
            logger.info(f"Email notification result: {email_result.get('message', 'Unknown')}")

            log_admin_activity(
                request=request,
                action='unrelease_evaluation',
                description=f"Ended dean evaluation period '{active_period.name}'. Processed {processing_results.get('processed_count', 0)} dean evaluations."
            )

            message = f'Dean evaluation period "{active_period.name}" has ended.'

            if processing_results['success']:
                processed_count = processing_results['processed_count']
                message += f' Successfully processed evaluation results for {processed_count} deans (visible to admin only).'
            else:
                message += ' But evaluation processing failed. Please check the logs.'

            return JsonResponse({
                'success': True,
                'message': message,
                'dean_evaluation_released': False,
                'evaluation_period_ended': True,
                'results_processed': processing_results['success'],
                'processed_count': processing_results.get('processed_count', 0),
                'emails_sent': email_result.get('sent_count', 0)
            })
        except Exception as e:
            logger.error(f"Exception in unrelease_dean_evaluation: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Server error: {str(e)}'
            })
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request'
    })


def process_peer_evaluation_results(evaluation_period=None):
    """
    Process peer evaluation results for all staff members after evaluation period ends
    """
    try:
        # Use the provided evaluation period if given; otherwise try to infer
        current_period = evaluation_period
        if not current_period:
            # Fallback: use latest active peer period, if any
            current_period = EvaluationPeriod.objects.filter(
                evaluation_type='peer',
                is_active=True
            ).first()
        if not current_period:
            # As a last resort, use the latest completed peer period
            current_period = EvaluationPeriod.objects.filter(
                evaluation_type='peer',
                is_active=False
            ).order_by('-end_date').first()
        if not current_period:
            return {
                'success': False,
                'error': 'No peer evaluation period available to process.',
                'processed_count': 0,
                'details': []
            }
        
        # Get all staff members who might have been evaluated
        staff_users = User.objects.filter(
            userprofile__role__in=[Role.FACULTY, Role.COORDINATOR, Role.DEAN]
        ).distinct()
        
        processed_count = 0
        processing_details = []
        
        for staff_user in staff_users:
            try:
                # Check if this staff member has any peer evaluations
                evaluation_responses = EvaluationResponse.objects.filter(
                    evaluatee=staff_user,
                    student_section__icontains="Staff"  # Peer evaluations have "Staff" in section
                )
                
                if evaluation_responses.exists():
                    # Process results for this staff member
                    result = process_evaluation_results_for_user(staff_user, current_period)
                    if result:
                        processed_count += 1
                        processing_details.append(f"✅ Processed {staff_user.username}: {result.total_percentage:.1f}% ({result.total_responses} evaluations)")
                    else:
                        processing_details.append(f"❌ Failed to process {staff_user.username}")
                else:
                    processing_details.append(f"➖ No peer evaluations for {staff_user.username}")
                    
            except Exception as e:
                processing_details.append(f"❌ Error processing {staff_user.username}: {str(e)}")
        
        return {
            'success': True,
            'processed_count': processed_count,
            'total_staff': staff_users.count(),
            'details': processing_details,
            'evaluation_period': current_period.name
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return {
            'success': False,
            'error': str(e),
            'error_details': error_details,
            'processed_count': 0,
            'details': [f"❌ System error: {str(e)}"]
        }
    

def process_upward_evaluation_results(evaluation_period=None):
    """
    Process upward evaluation results (Faculty → Coordinator) after evaluation period ends
    """
    try:
        from main.models import UpwardEvaluationResponse
        
        # Use the provided evaluation period if given; otherwise try to infer
        current_period = evaluation_period
        if not current_period:
            # Fallback: use latest active upward period
            current_period = EvaluationPeriod.objects.filter(
                evaluation_type='upward',
                is_active=True
            ).first()
        if not current_period:
            # As a last resort, use the latest completed upward period
            current_period = EvaluationPeriod.objects.filter(
                evaluation_type='upward',
                is_active=False
            ).order_by('-end_date').first()
        if not current_period:
            return {
                'success': False,
                'error': 'No upward evaluation period available to process.',
                'processed_count': 0,
                'details': []
            }
        
        # Get all coordinators who were evaluated
        coordinator_ids = UpwardEvaluationResponse.objects.filter(
            evaluation_period=current_period
        ).values_list('evaluatee', flat=True).distinct()
        
        processed_count = 0
        processing_details = []
        
        for coordinator_id in coordinator_ids:
            try:
                coordinator = User.objects.get(id=coordinator_id)
                
                # Get all upward evaluations for this coordinator in this period
                responses = UpwardEvaluationResponse.objects.filter(
                    evaluatee=coordinator,
                    evaluation_period=current_period
                )
                
                if responses.exists():
                    # Calculate average scores for 15 questions
                    total_score = 0
                    response_count = responses.count()
                    
                    for i in range(1, 16):  # 15 questions
                        question_field = f'question{i}'
                        question_scores = []
                        
                        for response in responses:
                            rating = getattr(response, question_field)
                            score = {
                                'Strongly Disagree': 1,
                                'Disagree': 2,
                                'Neutral': 3,
                                'Agree': 4,
                                'Strongly Agree': 5,
                                'Poor': 1,
                                'Fair': 2,
                                'Satisfactory': 3,
                                'Very Satisfactory': 4,
                                'Outstanding': 5
                            }.get(rating, 3)
                            question_scores.append(score)
                        
                        avg_score = sum(question_scores) / len(question_scores) if question_scores else 0
                        total_score += avg_score
                    
                    # Calculate percentage (15 questions, max 5 points each = 75 total)
                    overall_percentage = (total_score / 75) * 100
                    
                    # Create or update EvaluationResult
                    result, created = EvaluationResult.objects.update_or_create(
                        user=coordinator,
                        evaluation_period=current_period,
                        defaults={
                            'evaluation_type': 'upward',
                            'total_percentage': overall_percentage,
                            'total_responses': response_count,
                            'last_updated': timezone.now()
                        }
                    )
                    
                    processed_count += 1
                    processing_details.append(f"✅ Processed {coordinator.get_full_name() or coordinator.username}: {overall_percentage:.1f}% ({response_count} faculty evaluations)")
                else:
                    processing_details.append(f"➖ No upward evaluations for {coordinator.get_full_name() or coordinator.username}")
                    
            except User.DoesNotExist:
                processing_details.append(f"❌ Coordinator ID {coordinator_id} not found")
            except Exception as e:
                processing_details.append(f"❌ Error processing coordinator ID {coordinator_id}: {str(e)}")
        
        return {
            'success': True,
            'processed_count': processed_count,
            'total_coordinators': len(coordinator_ids),
            'details': processing_details,
            'evaluation_period': current_period.name
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return {
            'success': False,
            'error': str(e),
            'error_details': error_details,
            'processed_count': 0,
            'details': [f"❌ System error: {str(e)}"]
        }


def process_dean_evaluation_results(evaluation_period=None):
    """
    Process dean evaluation results (Faculty → Dean) after evaluation period ends
    """
    try:
        from main.models import DeanEvaluationResponse
        
        # Use the provided evaluation period if given; otherwise try to infer
        current_period = evaluation_period
        if not current_period:
            # Fallback: use latest active dean period
            current_period = EvaluationPeriod.objects.filter(
                evaluation_type='dean',
                is_active=True
            ).first()
        if not current_period:
            # As a last resort, use the latest completed dean period
            current_period = EvaluationPeriod.objects.filter(
                evaluation_type='dean',
                is_active=False
            ).order_by('-end_date').first()
        if not current_period:
            return {
                'success': False,
                'error': 'No dean evaluation period available to process.',
                'processed_count': 0,
                'details': []
            }
        
        # Get all deans who were evaluated
        dean_ids = DeanEvaluationResponse.objects.filter(
            evaluation_period=current_period
        ).values_list('evaluatee', flat=True).distinct()
        
        processed_count = 0
        processing_details = []
        
        for dean_id in dean_ids:
            try:
                dean = User.objects.get(id=dean_id)
                
                # Get all dean evaluations for this dean in this period
                responses = DeanEvaluationResponse.objects.filter(
                    evaluatee=dean,
                    evaluation_period=current_period
                )
                
                if responses.exists():
                    # Calculate average scores for 15 questions
                    total_score = 0
                    response_count = responses.count()
                    
                    for i in range(1, 16):  # 15 questions
                        question_field = f'question{i}'
                        question_scores = []
                        
                        for response in responses:
                            rating = getattr(response, question_field)
                            score = {
                                'Strongly Disagree': 1,
                                'Disagree': 2,
                                'Neutral': 3,
                                'Agree': 4,
                                'Strongly Agree': 5,
                                'Poor': 1,
                                'Fair': 2,
                                'Satisfactory': 3,
                                'Very Satisfactory': 4,
                                'Outstanding': 5
                            }.get(rating, 3)
                            question_scores.append(score)
                        
                        avg_score = sum(question_scores) / len(question_scores) if question_scores else 0
                        total_score += avg_score
                    
                    # Calculate percentage (15 questions, max 5 points each = 75 total)
                    overall_percentage = (total_score / 75) * 100
                    
                    # Create or update EvaluationResult
                    result, created = EvaluationResult.objects.update_or_create(
                        user=dean,
                        evaluation_period=current_period,
                        defaults={
                            'evaluation_type': 'dean',
                            'total_percentage': overall_percentage,
                            'total_responses': response_count,
                            'last_updated': timezone.now()
                        }
                    )
                    
                    processed_count += 1
                    processing_details.append(f"✅ Processed {dean.get_full_name() or dean.username}: {overall_percentage:.1f}% ({response_count} faculty evaluations)")
                else:
                    processing_details.append(f"➖ No dean evaluations for {dean.get_full_name() or dean.username}")
                    
            except User.DoesNotExist:
                processing_details.append(f"❌ Dean ID {dean_id} not found")
            except Exception as e:
                processing_details.append(f"❌ Error processing dean ID {dean_id}: {str(e)}")
        
        return {
            'success': True,
            'processed_count': processed_count,
            'total_deans': len(dean_ids),
            'details': processing_details,
            'evaluation_period': current_period.name
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return {
            'success': False,
            'error': str(e),
            'error_details': error_details,
            'processed_count': 0,
            'details': [f"❌ System error: {str(e)}"]
        }


def release_all_evaluations(request):
    print("🔍 DEBUG: release_all_evaluations called")
    
    if request.method == 'POST':
        print("🔍 DEBUG: Processing POST request for release all")
        try:
            # Check if user is admin
            if not request.user.is_authenticated or not request.user.is_superuser:
                return JsonResponse({'success': False, 'error': 'Permission denied'})
            
            print("🔍 DEBUG: User is authorized")
            
            from django.utils import timezone
            
            # ✅ FIXED: Only archive results that have already been completed (ended periods)
            # Don't archive the current period's results - they should remain as "current"
            # until a NEW set of results replaces them in the next cycle
            
            # Archive results from INACTIVE periods that haven't been archived yet
            previous_student_periods = EvaluationPeriod.objects.filter(
                evaluation_type='student',
                is_active=False  # Only archive ENDED periods
            ).exclude(
                id__in=EvaluationHistory.objects.values_list('evaluation_period_id', flat=True)
            )
            for period in previous_student_periods:
                archived_count = archive_period_results_to_history(period)
                print(f"🔍 DEBUG: Archived {archived_count} results from previous student period: {period.name}")
            
            previous_peer_periods = EvaluationPeriod.objects.filter(
                evaluation_type='peer',
                is_active=False  # Only archive ENDED periods
            ).exclude(
                id__in=EvaluationHistory.objects.values_list('evaluation_period_id', flat=True)
            )
            for period in previous_peer_periods:
                archived_count = archive_period_results_to_history(period)
                print(f"🔍 DEBUG: Archived {archived_count} results from previous peer period: {period.name}")
            
            # Now deactivate currently active periods (these will NOT be archived yet)
            active_student_periods = EvaluationPeriod.objects.filter(
                evaluation_type='student',
                is_active=True
            )
            student_deactivated_count = active_student_periods.update(is_active=False, end_date=timezone.now())
            print(f"🔍 DEBUG: Deactivated {student_deactivated_count} active student periods (NOT archived yet)")
            
            active_peer_periods = EvaluationPeriod.objects.filter(
                evaluation_type='peer',
                is_active=True
            )
            peer_deactivated_count = active_peer_periods.update(is_active=False, end_date=timezone.now())
            print(f"🔍 DEBUG: Deactivated {peer_deactivated_count} active peer periods (NOT archived yet)")
            
            # Create new student evaluation period with unique timestamp
            student_period = EvaluationPeriod.objects.create(
                name=f"Student Evaluation {timezone.now().strftime('%B %d, %Y %H:%M')}",
                evaluation_type='student',
                start_date=timezone.now(),
                end_date=timezone.now() + timezone.timedelta(days=30),
                is_active=True
            )
            print(f"🔍 DEBUG: Created new student period: {student_period.name}")
            
            # Create new peer evaluation period with unique timestamp
            peer_period = EvaluationPeriod.objects.create(
                name=f"Peer Evaluation {timezone.now().strftime('%B %d, %Y %H:%M')}",
                evaluation_type='peer',
                start_date=timezone.now(),
                end_date=timezone.now() + timezone.timedelta(days=30),
                is_active=True
            )
            print(f"🔍 DEBUG: Created new peer period: {peer_period.name}")
            
            # Check if student evaluations exist, if not create them
            student_evaluations = Evaluation.objects.filter(evaluation_type='student')
            if not student_evaluations.exists():
                print("🔍 DEBUG: No student evaluations found, creating new ones...")
                # Create student evaluation form
                Evaluation.objects.create(
                    evaluation_type='student',
                    is_released=True,
                    evaluation_period=student_period
                )
                student_updated = 1
                print(f"🔍 DEBUG: Created 1 new student evaluation")
            else:
                # Release existing student evaluations
                student_evaluations = student_evaluations.filter(is_released=False)
                student_count = student_evaluations.count()
                student_updated = student_evaluations.update(is_released=True, evaluation_period=student_period)
                print(f"🔍 DEBUG: Released {student_updated}/{student_count} student evaluations")
            
            # Check if peer evaluations exist, if not create them
            peer_evaluations = Evaluation.objects.filter(evaluation_type='peer')
            if not peer_evaluations.exists():
                print("🔍 DEBUG: No peer evaluations found, creating new ones...")
                # Create peer evaluation form
                Evaluation.objects.create(
                    evaluation_type='peer',
                    is_released=True,
                    evaluation_period=peer_period
                )
                peer_updated = 1
                print(f"🔍 DEBUG: Created 1 new peer evaluation")
            else:
                # Release existing peer evaluations
                peer_evaluations = peer_evaluations.filter(is_released=False)
                peer_count = peer_evaluations.count()
                peer_updated = peer_evaluations.update(is_released=True, evaluation_period=peer_period)
                print(f"🔍 DEBUG: Released {peer_updated}/{peer_count} peer evaluations")
            
            if student_updated > 0 or peer_updated > 0:
                # Log admin activity
                log_admin_activity(
                    request=request,
                    action='release_evaluation',
                    description=f"Released both student ({student_updated}) and peer ({peer_updated}) evaluation forms. Previous periods archived."
                )
                
                response_data = {
                    'success': True,
                    'message': f'✅ Both student and peer evaluations have been released! (Student: {student_updated}, Peer: {peer_updated})',
                    'student_evaluation_released': True,
                    'peer_evaluation_released': True,
                    'evaluation_period_ended': False
                }
                print(f"🔍 DEBUG: Success - {response_data['message']}")
                return JsonResponse(response_data)
            else:
                response_data = {
                    'success': False, 
                    'error': 'No evaluations to release (they might already be released).'
                }
                print(f"🔍 DEBUG: No evaluations to release")
                return JsonResponse(response_data)
                
        except Exception as e:
            print(f"❌ DEBUG: Exception in release_all_evaluations: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})
    
    print("🔍 DEBUG: Not a POST request")
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def unrelease_all_evaluations(request):
    print("🔍 DEBUG: unrelease_all_evaluations called")
    
    if request.method == 'POST':
        print("🔍 DEBUG: Processing POST request for unrelease all")
        try:
            # Check if user is admin
            if not request.user.is_authenticated or not request.user.is_superuser:
                return JsonResponse({'success': False, 'error': 'Permission denied'})
            
            print("🔍 DEBUG: User is authorized")
            
            from django.utils import timezone
            
            # Unrelease student evaluations
            student_evaluations = Evaluation.objects.filter(is_released=True, evaluation_type='student')
            student_updated = student_evaluations.update(is_released=False)
            print(f"🔍 DEBUG: Unreleased {student_updated} student evaluations")
            
            # Unrelease peer evaluations
            peer_evaluations = Evaluation.objects.filter(is_released=True, evaluation_type='peer')
            peer_updated = peer_evaluations.update(is_released=False)
            print(f"🔍 DEBUG: Unreleased {peer_updated} peer evaluations")
            
            # Capture active periods BEFORE deactivation
            student_active_period = EvaluationPeriod.objects.filter(
                evaluation_type='student',
                is_active=True
            ).first()
            peer_active_period = EvaluationPeriod.objects.filter(
                evaluation_type='peer',
                is_active=True
            ).first()

            # Deactivate student evaluation periods
            student_periods = EvaluationPeriod.objects.filter(
                evaluation_type='student',
                is_active=True
            )
            student_periods_count = student_periods.count()
            student_periods.update(is_active=False, end_date=timezone.now())
            print(f"🔍 DEBUG: Deactivated {student_periods_count} student evaluation period(s)")
            
            # Deactivate peer evaluation periods
            peer_periods = EvaluationPeriod.objects.filter(
                evaluation_type='peer',
                is_active=True
            )
            peer_periods_count = peer_periods.count()
            peer_periods.update(is_active=False, end_date=timezone.now())
            print(f"🔍 DEBUG: Deactivated {peer_periods_count} peer evaluation period(s)")
            
            # Process results for both using the captured periods
            student_processing = process_all_evaluation_results(evaluation_period=student_active_period) if student_active_period else {'success': False, 'processed_count': 0}
            peer_processing = process_peer_evaluation_results(evaluation_period=peer_active_period) if peer_active_period else {'success': False, 'processed_count': 0}
            
            message = 'Both student and peer evaluations have been unreleased. Evaluation periods ended.'
            
            # Add processing details
            if student_processing['success']:
                message += f" Student results: {student_processing['processed_count']} processed."
            if peer_processing['success']:
                message += f" Peer results: {peer_processing['processed_count']} processed."
            
            if student_updated > 0 or peer_updated > 0:
                # Log admin activity
                log_admin_activity(
                    request=request,
                    action='unrelease_evaluation',
                    description=f"Unreleased both student ({student_updated}) and peer ({peer_updated}) evaluation forms. Evaluation periods ended."
                )
                
                response_data = {
                    'success': True,
                    'message': message,
                    'student_evaluation_released': False,
                    'peer_evaluation_released': False,
                    'evaluation_period_ended': True
                }
                print(f"🔍 DEBUG: Success - {message}")
                return JsonResponse(response_data)
            else:
                response_data = {
                    'success': False, 
                    'error': 'No evaluations to unrelease.'
                }
                print(f"🔍 DEBUG: No evaluations to unrelease")
                return JsonResponse(response_data)
                
        except Exception as e:
            print(f"❌ DEBUG: Exception in unrelease_all_evaluations: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})
    
    print("🔍 DEBUG: Not a POST request")
    return JsonResponse({'success': False, 'error': 'Invalid request'})
        
@method_decorator(cache_control(no_store=True, no_cache=True, must_revalidate=True), name='dispatch')       
class CoordinatorDetailView(View):

    @method_decorator(evaluation_results_required)
    def get(self, request, id):
        if not request.user.is_authenticated:
            return redirect('/login')

        try:
            user_profile = UserProfile.objects.get(user=request.user)
            coordinator = get_object_or_404(UserProfile, id=id)

            # Permission check
            if user_profile.role in [Role.COORDINATOR, Role.DEAN] and coordinator.institute != user_profile.institute:
                return HttpResponseForbidden("You do not have permission to access this coordinator's details.")

            # Get the ACTIVE evaluation period for student evaluations (matching profile settings logic)
            latest_student_period = EvaluationPeriod.objects.filter(
                evaluation_type='student',
                is_active=True
            ).first()
            
            # Get the ACTIVE evaluation period for peer evaluations
            latest_peer_period = EvaluationPeriod.objects.filter(
                evaluation_type='peer',
                is_active=True
            ).first()

            # Get assigned sections for this coordinator
            assigned_sections = SectionAssignment.objects.filter(user=coordinator.user)
            
            # Calculate scores for each section and create section mapping
            section_scores = {}
            section_map = {}  # This will map section IDs to section codes
            
            for section_assignment in assigned_sections:
                section = section_assignment.section
                section_code = section.code
                section_id = section.id
                
                # Add to section mapping
                section_map[section_id] = section_code

                # Calculate scores for this specific section - NOW WITH 4 CATEGORIES
                # Pass the latest period to filter by most recent evaluation results
                category_scores = compute_category_scores(coordinator.user, section_code, latest_student_period)
                
                a_avg, b_avg, c_avg, d_avg, total_percentage, total_a, total_b, total_c, total_d = category_scores
                
                # Get evaluation count for this section from EvaluationResponse (filtered by active period if exists)
                eval_filter_kwargs = {
                    'evaluatee': coordinator.user,
                    'student_section': section_code
                }
                if latest_student_period:
                    eval_filter_kwargs['submitted_at__gte'] = latest_student_period.start_date
                    eval_filter_kwargs['submitted_at__lte'] = latest_student_period.end_date
                evaluation_count = EvaluationResponse.objects.filter(**eval_filter_kwargs).count()
                
                # Only include sections that have evaluations
                if total_percentage > 0:
                    section_scores[section_code] = {
                        'category_scores': [a_avg, b_avg, c_avg, d_avg],  # Now 4 categories
                        'total_percentage': total_percentage,
                        'has_data': True,
                        'evaluation_count': evaluation_count  # Add evaluation count
                    }
                else:
                    section_scores[section_code] = {
                        'category_scores': [0, 0, 0, 0],  # Now 4 zeros
                        'total_percentage': 0,
                        'has_data': False,
                        'evaluation_count': 0
                    }

            # Calculate PEER evaluation scores (overall, no section breakdown)
            # Filter by active peer evaluation period using date range
            peer_filter_kwargs = {'evaluatee': coordinator.user}
            if latest_peer_period:
                peer_filter_kwargs['submitted_at__gte'] = latest_peer_period.start_date
                peer_filter_kwargs['submitted_at__lte'] = latest_peer_period.end_date
                peer_filter_kwargs['evaluation_period__evaluation_type'] = 'peer'
            else:
                # If no active peer period, get all peer evaluations
                peer_filter_kwargs['evaluation_period__evaluation_type'] = 'peer'
            peer_responses = EvaluationResponse.objects.filter(**peer_filter_kwargs)
            
            peer_evaluation_count = peer_responses.count()
            
            if peer_evaluation_count > 0:
                # Calculate peer scores using the same 4-category system
                # Pass the latest peer period to filter by most recent results
                peer_scores = compute_category_scores(coordinator.user, section_code=None, evaluation_period=latest_peer_period)
                p_a_avg, p_b_avg, p_c_avg, p_d_avg, p_total_percentage, _, _, _, _ = peer_scores
                
                peer_data = {
                    'category_scores': [p_a_avg, p_b_avg, p_c_avg, p_d_avg],
                    'total_percentage': p_total_percentage,
                    'has_data': True,
                    'evaluation_count': peer_evaluation_count
                }
            else:
                peer_data = {
                    'category_scores': [0, 0, 0, 0],
                    'total_percentage': 0,
                    'has_data': False,
                    'evaluation_count': 0
                }

            # Calculate IRREGULAR evaluation scores
            # Filter by active student evaluation period using date range
            irregular_filter_kwargs = {'evaluatee': coordinator.user}
            if latest_student_period:
                irregular_filter_kwargs['submitted_at__gte'] = latest_student_period.start_date
                irregular_filter_kwargs['submitted_at__lte'] = latest_student_period.end_date
            irregular_responses = IrregularEvaluation.objects.filter(**irregular_filter_kwargs)
            irregular_evaluation_count = irregular_responses.count()
            
            if irregular_evaluation_count > 0:
                # Calculate irregular scores manually (same logic as compute_category_scores)
                rating_to_numeric = {
                    'Poor': 1,
                    'Unsatisfactory': 2,
                    'Satisfactory': 3,
                    'Very Satisfactory': 4,
                    'Outstanding': 5
                }
                
                category_a_total = category_b_total = category_c_total = category_d_total = 0
                count_a = count_b = count_c = count_d = 0
                
                for response in irregular_responses:
                    # Category A: Questions 1-4 (35%)
                    for i in range(1, 5):
                        question_key = f'question{i}'
                        rating_text = getattr(response, question_key, 'Poor')
                        score = rating_to_numeric.get(rating_text, 1)
                        category_a_total += score
                        count_a += 1
                    
                    # Category B: Questions 5-8 (25%)
                    for i in range(5, 9):
                        question_key = f'question{i}'
                        rating_text = getattr(response, question_key, 'Poor')
                        score = rating_to_numeric.get(rating_text, 1)
                        category_b_total += score
                        count_b += 1
                    
                    # Category C: Questions 9-12 (20%)
                    for i in range(9, 13):
                        question_key = f'question{i}'
                        rating_text = getattr(response, question_key, 'Poor')
                        score = rating_to_numeric.get(rating_text, 1)
                        category_c_total += score
                        count_c += 1
                    
                    # Category D: Questions 13-15 (20%)
                    for i in range(13, 16):
                        question_key = f'question{i}'
                        rating_text = getattr(response, question_key, 'Poor')
                        score = rating_to_numeric.get(rating_text, 1)
                        category_d_total += score
                        count_d += 1
                
                # Calculate averages with weights
                max_score_per_question = 5
                a_weight, b_weight, c_weight, d_weight = 0.35, 0.25, 0.20, 0.20
                
                def scaled_avg(total, count, weight):
                    if count == 0:
                        return 0
                    average_score = total / count
                    return (average_score / max_score_per_question) * weight * 100
                
                irr_a_avg = scaled_avg(category_a_total, count_a, a_weight)
                irr_b_avg = scaled_avg(category_b_total, count_b, b_weight)
                irr_c_avg = scaled_avg(category_c_total, count_c, c_weight)
                irr_d_avg = scaled_avg(category_d_total, count_d, d_weight)
                irr_total_percentage = irr_a_avg + irr_b_avg + irr_c_avg + irr_d_avg
                
                irregular_data = {
                    'category_scores': [irr_a_avg, irr_b_avg, irr_c_avg, irr_d_avg],
                    'total_percentage': irr_total_percentage,
                    'has_data': True,
                    'evaluation_count': irregular_evaluation_count
                }
            else:
                irregular_data = {
                    'category_scores': [0, 0, 0, 0],
                    'total_percentage': 0,
                    'has_data': False,
                    'evaluation_count': 0
                }

            # Convert to JSON for JavaScript
            import json
            section_scores_json = json.dumps(section_scores)
            section_map_json = json.dumps(section_map)
            peer_data_json = json.dumps(peer_data)
            irregular_data_json = json.dumps(irregular_data)
            
            # Calculate overall statistics for the template
            total_sections = assigned_sections.count()
            sections_with_data = sum(1 for scores in section_scores.values() if scores['has_data'])
            # Filter total evaluations by active student period if exists
            total_eval_filter_kwargs = {'evaluatee': coordinator.user}
            if latest_student_period:
                total_eval_filter_kwargs['submitted_at__gte'] = latest_student_period.start_date
                total_eval_filter_kwargs['submitted_at__lte'] = latest_student_period.end_date
            total_evaluations = EvaluationResponse.objects.filter(**total_eval_filter_kwargs).count()

            # Get all sections and years for section assignment editing (for Dean/Coordinator viewing others)
            sections = Section.objects.all().order_by('year_level', 'code')
            years = list(Section.objects.values_list('year_level', flat=True).distinct().order_by('year_level'))
            currently_assigned_ids = [assignment.section.id for assignment in assigned_sections]
            
            # Check if current user can edit sections (Dean can edit Coordinator/Faculty, Coordinator can edit Faculty)
            can_edit_sections = False
            if user_profile.role == Role.DEAN and coordinator.role in [Role.COORDINATOR, Role.FACULTY]:
                can_edit_sections = True
            elif user_profile.role == Role.COORDINATOR and coordinator.role == Role.FACULTY:
                can_edit_sections = True

            context = {
                'coordinator': coordinator,
                'faculty': coordinator,  # Add faculty key for faculty_detail.html compatibility
                'assigned_sections': assigned_sections,
                'section_scores': section_scores,
                'section_scores_json': section_scores_json,  # JSON for JavaScript
                'section_map_json': section_map_json,        # JSON for JavaScript
                'peer_data': peer_data,
                'peer_data_json': peer_data_json,            # JSON for JavaScript
                'irregular_data': irregular_data,
                'irregular_data_json': irregular_data_json,  # JSON for JavaScript
                'has_any_data': any(scores['has_data'] for scores in section_scores.values()),
                'total_sections': total_sections,
                'sections_with_data': sections_with_data,
                'total_evaluations': total_evaluations,
                'evaluation_period_ended': can_view_evaluation_results('student'),
                'sections': sections,
                'years': years,
                'currently_assigned_ids': currently_assigned_ids,
                'can_edit_sections': can_edit_sections,
                'current_user_role': user_profile.role,
            }

            # Render appropriate template based on role
            if coordinator.role == 'Faculty':
                return render(request, 'main/faculty_detail.html', context)
            else:
                return render(request, 'main/coordinator_detail.html', context)

        except UserProfile.DoesNotExist:
            return redirect('/login')

    def post(self, request, id):
        user = request.user
        if not user.is_authenticated:
            return redirect('/login')

        try:
            user_profile = UserProfile.objects.get(user=user)
            coordinator = get_object_or_404(UserProfile, id=id)

            # Permission check for POST as well
            if user_profile.role in [Role.COORDINATOR, Role.DEAN] and coordinator.institute != user_profile.institute:
                return HttpResponseForbidden("You do not have permission to modify this coordinator's details.")

            # Check what action is being performed
            action = request.POST.get('action', '')
            
            # Handle section assignment separately
            if action == 'assign_sections':
                # Check if user has permission to edit sections
                can_edit = False
                if user_profile.role == Role.DEAN and coordinator.role in [Role.COORDINATOR, Role.FACULTY]:
                    can_edit = True
                elif user_profile.role == Role.COORDINATOR and coordinator.role == Role.FACULTY:
                    can_edit = True
                    
                if not can_edit:
                    return HttpResponseForbidden("You do not have permission to modify section assignments.")
                
                # Get selected sections from form
                selected_section_ids = request.POST.getlist('sections')
                
                # Remove all existing assignments
                SectionAssignment.objects.filter(user=coordinator.user).delete()
                
                # Add new assignments
                sections_assigned = []
                for section_id in selected_section_ids:
                    section = Section.objects.get(id=section_id)
                    SectionAssignment.objects.create(user=coordinator.user, section=section)
                    sections_assigned.append(section.code)
                
                if len(sections_assigned) > 0:
                    sections_list = ", ".join(sections_assigned)
                    messages.success(request, f"✅ Successfully assigned {len(sections_assigned)} section(s) to {coordinator.user.get_full_name() or coordinator.user.username}: {sections_list}")
                else:
                    messages.success(request, f"✅ All section assignments have been removed for {coordinator.user.get_full_name() or coordinator.user.username}.")
                
                # Redirect back to detail page
                if coordinator.role == 'Faculty':
                    return redirect('main:faculty_detail', id=coordinator.id)
                else:
                    return redirect('main:coordinator_detail', id=coordinator.id)

            try:
                index_url = reverse('main:index')
            except:
                index_url = '/'
            
            next_url = request.POST.get('next', request.META.get('HTTP_REFERER', index_url))

            username = request.POST.get("username")
            email = request.POST.get("email")
            new_password = request.POST.get("new_password1")
            confirm_password = request.POST.get("new_password2")

            # Email validation
            if not re.match(r"^[a-zA-Z0-9._%+-]+@(gmail\.com|cca\.edu\.ph)$", email):
                # Rebuild the context for error display
                assigned_sections = SectionAssignment.objects.filter(user=coordinator.user)
                section_scores = self._get_section_scores(coordinator, assigned_sections)
                
                context = self._build_context(coordinator, assigned_sections, section_scores)
                context['error'] = 'Invalid email address. Please use an email ending with @gmail.com or @cca.edu.ph.'
                context['next_url'] = next_url
                
                return render(request, 'main/coordinator_detail.html', context)

            # Password validation
            if new_password and new_password != confirm_password:
                assigned_sections = SectionAssignment.objects.filter(user=coordinator.user)
                section_scores = self._get_section_scores(coordinator, assigned_sections)
                
                context = self._build_context(coordinator, assigned_sections, section_scores)
                context['error'] = 'Passwords do not match.'
                context['next_url'] = next_url
                
                return render(request, 'main/coordinator_detail.html', context)

            # Update coordinator user information
            coordinator_user = coordinator.user
            coordinator_user.username = username
            coordinator_user.email = email

            if new_password:
                coordinator_user.set_password(new_password)
                # If the current user is updating their own password, update session
                if user.id == coordinator_user.id:
                    update_session_auth_hash(request, coordinator_user)

            coordinator_user.save()

            # Add success parameter to URL
            if "?" in next_url:
                next_url += "&updated=true"
            else:
                next_url += "?updated=true"

            messages.success(request, "Coordinator profile updated successfully.")
            return redirect(next_url)
            
        except UserProfile.DoesNotExist:
            return redirect('/login')

    def _get_section_scores(self, coordinator, assigned_sections):
        """Helper method to calculate section scores"""
        section_scores = {}
        section_map = {}
        
        for section_assignment in assigned_sections:
            section = section_assignment.section
            section_code = section.code
            section_id = section.id
            
            section_map[section_id] = section_code

            category_scores = compute_category_scores(coordinator.user, section_code)
            a_avg, b_avg, c_avg, d_avg, total_percentage, total_a, total_b, total_c, total_d = category_scores
            
            # Get evaluation count for this section from EvaluationResponse
            evaluation_count = EvaluationResponse.objects.filter(
                evaluatee=coordinator.user,
                student_section=section_code
            ).count()
            
            if total_percentage > 0:
                section_scores[section_code] = {
                    'category_scores': [a_avg, b_avg, c_avg, d_avg],  # Now 4 categories
                    'total_percentage': total_percentage,
                    'has_data': True,
                    'evaluation_count': evaluation_count
                }
            else:
                section_scores[section_code] = {
                    'category_scores': [0, 0, 0, 0],  # Now 4 zeros
                    'total_percentage': 0,
                    'has_data': False,
                    'evaluation_count': 0
                }
        
        return section_scores

    def _build_context(self, coordinator, assigned_sections, section_scores):
        """Helper method to build context for template"""
        import json
        
        # Calculate overall statistics
        total_sections = assigned_sections.count()
        sections_with_data = sum(1 for scores in section_scores.values() if scores['has_data'])
        total_evaluations = EvaluationResponse.objects.filter(evaluatee=coordinator.user).count()
        
        return {
            'coordinator': coordinator,
            'assigned_sections': assigned_sections,
            'section_scores': section_scores,
            'section_scores_json': json.dumps(section_scores),
            'section_map_json': json.dumps({sa.section.id: sa.section.code for sa in assigned_sections}),
            'has_any_data': any(scores['has_data'] for scores in section_scores.values()),
            'total_sections': total_sections,
            'sections_with_data': sections_with_data,
            'total_evaluations': total_evaluations,
        }
        
@method_decorator(cache_control(no_store=True, no_cache=True, must_revalidate=True), name='dispatch')
class FacultyDetailView(View):
    def get(self, request, id):
        if not request.user.is_authenticated:
            return redirect('/login')

        try:
            user_profile = UserProfile.objects.get(user=request.user)
            faculty = get_object_or_404(UserProfile, id=id)

            # Check if the user has permission to view the coordinator
            if user_profile.role in [Role.COORDINATOR, Role.DEAN] and faculty.institute != user_profile.institute:
                return HttpResponseForbidden("You do not have permission to access this coordinator's details.")

            context = {
                'faculty': faculty
            }
            return render(request, 'main/coordinator_detail.html', context)

        except UserProfile.DoesNotExist:
            return redirect('/login')
   
def custom_logout(request):
    logout(request)  # Log out the user
    request.session.flush()  # Clear session data

    # Redirect to login page and prevent caching
    response = redirect('login')  # Make sure 'custom_login' is the correct URL name
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response

def submit_evaluation(request):
    print("=" * 80)
    print(f"SUBMIT EVALUATION CALLED - Method: {request.method}")
    print("=" * 80)
    
    if request.method == 'POST':
        # Check if user is authenticated
        if not request.user.is_authenticated:
            print("ERROR: User not authenticated")
            messages.error(request, 'You must be logged in to submit an evaluation.')
            return redirect('main:login')

        try:
            # ✅ ADDED: Check if evaluation period is active
            print(f"User: {request.user.username}")
            print(f"POST keys: {list(request.POST.keys())}")
            logger.info(f"🔍 Submit evaluation called by {request.user.username}")
            logger.info(f"🔍 POST data keys: {list(request.POST.keys())}")
            is_active = Evaluation.is_evaluation_period_active()
            print(f"Evaluation period active: {is_active}")
            logger.info(f"🔍 Evaluation period active: {is_active}")
            if not is_active:
                print("ERROR: Evaluation period not active")
                messages.error(request, 'Evaluation period has ended. You cannot submit evaluations at this time.')
                logger.warning(f"⚠️ Evaluation period not active for {request.user.username}")
                return redirect('main:evaluationform')

            # Retrieve the evaluatee
            evaluatee_id = request.POST.get('evaluatee')
            print(f"Evaluatee ID: {evaluatee_id}")
            logger.info(f"🔍 Evaluatee ID: {evaluatee_id}")
            
            if not evaluatee_id:
                messages.error(request, 'No instructor selected.')
                return redirect('main:evaluationform')
            
            try:
                evaluatee = User.objects.get(id=evaluatee_id)
                evaluatee_profile = evaluatee.userprofile
            except User.DoesNotExist:
                messages.error(request, 'Selected instructor does not exist.')
                return redirect('main:evaluationform')

            # ✅ UPDATED VALIDATION: Check if user can evaluate this staff member
            evaluator_profile = request.user.userprofile
            
            # Student evaluating staff (Faculty, Coordinator, Dean)
            if evaluator_profile.role == Role.STUDENT and evaluatee_profile.role in [Role.FACULTY, Role.COORDINATOR, Role.DEAN]:
                # Irregular students can evaluate any instructor - skip section check
                if not evaluator_profile.is_irregular:
                    # Regular students: Check if student's section is assigned to this staff member
                    if evaluator_profile.section:
                        is_assigned = SectionAssignment.objects.filter(
                            user=evaluatee,
                            section=evaluator_profile.section
                        ).exists()
                        
                        if not is_assigned:
                            messages.error(request, f'You cannot evaluate {evaluatee.username} as you are not in their assigned section.')
                            return redirect('main:evaluationform')
                    else:
                        messages.error(request, 'You cannot evaluate instructors as you are not assigned to any section.')
                        return redirect('main:evaluationform')

            # ✅ ADDED: Staff peer evaluation (Faculty, Coordinator, Dean evaluating each other)
            elif evaluator_profile.role in [Role.FACULTY, Role.COORDINATOR, Role.DEAN] and evaluatee_profile.role in [Role.FACULTY, Role.COORDINATOR, Role.DEAN]:
                # Check if they are from the same institute
                if evaluator_profile.institute != evaluatee_profile.institute:
                    messages.error(request, f'You cannot evaluate {evaluatee.username} as they are from a different institute.')
                    return redirect('main:evaluationform')
                
                # Check if it's a self-evaluation
                if request.user.id == evaluatee.id:
                    messages.error(request, 'You cannot evaluate yourself.')
                    return redirect('main:evaluationform')

            else:
                messages.error(request, 'You do not have permission to evaluate this user.')
                return redirect('main:evaluationform')

            # Get the current active evaluation period
            # Determine evaluation type based on user roles
            if evaluator_profile.role == Role.STUDENT:
                evaluation_type = 'student'
                total_questions = 19  # Student evaluation has 19 questions
            else:
                evaluation_type = 'peer'
                total_questions = 15  # Peer evaluation has 15 questions
            
            try:
                current_period = EvaluationPeriod.objects.get(
                    evaluation_type=evaluation_type,
                    is_active=True
                )
            except EvaluationPeriod.DoesNotExist:
                messages.error(request, 'No active evaluation period found.')
                return redirect('main:evaluationform')

            # Prevent duplicate evaluation IN THE SAME PERIOD (checked later based on irregular status)
            # Allow re-evaluation in different periods

            # Convert numeric values to text ratings
            rating_map = {
                '1': 'Poor',
                '2': 'Unsatisfactory', 
                '3': 'Satisfactory',
                '4': 'Very Satisfactory',
                '5': 'Outstanding'
            }
            
            # Validate all questions and convert to text
            questions = {}
            for i in range(1, total_questions + 1):  # Use dynamic question count based on evaluation type
                question_key = f'question{i}'
                question_value = request.POST.get(question_key)
                
                if not question_value:
                    messages.error(request, f'All questions must be answered. Missing: Question {i}')
                    return redirect('main:evaluationform')
                
                if question_value not in rating_map:
                    messages.error(request, f'Invalid rating for question {i}.')
                    return redirect('main:evaluationform')
                    
                questions[question_key] = rating_map[question_value]

            # Get student information (for students) or staff information
            student_number = request.POST.get('studentNumber', '')
            student_section = request.POST.get('student_section', '')

            # ✅ FIXED: Properly set student_section based on user role
            evaluator_profile = request.user.userprofile
            
            if evaluator_profile.role == Role.STUDENT:
                # Use the student's actual section from their profile
                if evaluator_profile.section:
                    student_section = evaluator_profile.section.code
                
                else:
                    student_section = 'No Section'
                    
            elif evaluator_profile.role in [Role.FACULTY, Role.COORDINATOR, Role.DEAN]:
                # For staff evaluations, use their institute
                student_section = f"{evaluator_profile.institute} Staff"
                

            # Get comments (NEW FIELD)
            comments = request.POST.get('comments', '')

            

            # Create and save the evaluation response
            logger.info(f"🔍 Creating evaluation with {len(questions)} questions")
            logger.info(f"🔍 Questions dict: {questions}")
            
            # Check if evaluator is an irregular student
            if evaluator_profile.role == Role.STUDENT and evaluator_profile.is_irregular:
                # Save to IrregularEvaluation table
                logger.info(f"🔍 Irregular student detected - saving to IrregularEvaluation")
                
                # Check for duplicate irregular evaluation
                if IrregularEvaluation.objects.filter(
                    evaluator=request.user,
                    evaluatee=evaluatee,
                    evaluation_period=current_period
                ).exists():
                    messages.error(request, 'You have already evaluated this instructor in this evaluation period.')
                    return redirect('main:evaluationform')
                
                evaluation_response = IrregularEvaluation(
                    evaluator=request.user,
                    evaluatee=evaluatee,
                    evaluation_period=current_period,
                    student_number=student_number,
                    comments=comments,
                    **questions
                )
                evaluation_response.save()
                logger.info(f"✅ Irregular evaluation saved successfully! ID: {evaluation_response.id}")
            else:
                # Save to regular EvaluationResponse table
                logger.info(f"🔍 Regular student/staff evaluation - saving to EvaluationResponse")
                
                # Check for duplicate regular evaluation in current period
                if EvaluationResponse.objects.filter(
                    evaluator=request.user,
                    evaluatee=evaluatee,
                    evaluation_period=current_period
                ).exists():
                    messages.error(request, 'You have already evaluated this instructor in this evaluation period.')
                    return redirect('main:evaluationform')
                
                evaluation_response = EvaluationResponse(
                    evaluator=request.user,
                    evaluatee=evaluatee,
                    evaluation_period=current_period,
                    student_number=student_number,
                    student_section=student_section,
                    comments=comments,
                    **questions
                )
                evaluation_response.save()
                logger.info(f"✅ Evaluation saved successfully! ID: {evaluation_response.id}")

            

            messages.success(request, 'Evaluation submitted successfully!')

            evaluation_url = reverse('main:evaluation') + '?submitted=true'
            return redirect(evaluation_url)

        except Exception as e:
            print("=" * 80)
            print(f"EXCEPTION OCCURRED: {str(e)}")
            print("=" * 80)
            import traceback
            traceback.print_exc()
            
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('main:evaluationform')

    print("Method was not POST, redirecting")
    return redirect('main:evaluationform')


def submit_upward_evaluation(request):
    """
    Handle submission of upward evaluation (Faculty → Coordinator)
    """
    print("=" * 80)
    print(f"SUBMIT UPWARD EVALUATION CALLED - Method: {request.method}")
    print("=" * 80)
    
    if request.method == 'POST':
        # Check if user is authenticated
        if not request.user.is_authenticated:
            print("ERROR: User not authenticated")
            messages.error(request, 'You must be logged in to submit an evaluation.')
            return redirect('main:login')

        try:
            evaluator_profile = request.user.userprofile
            
            # ✅ ONLY FACULTY can submit upward evaluation
            if evaluator_profile.role != Role.FACULTY:
                messages.error(request, 'Only faculty members can submit upward evaluations.')
                return redirect('main:index')
            
            print(f"User: {request.user.username} (Faculty)")
            logger.info(f"🔍 Upward evaluation submission by {request.user.username}")
            
            # Get the coordinator being evaluated
            coordinator_id = request.POST.get('coordinator_id')
            print(f"Coordinator ID: {coordinator_id}")
            
            if not coordinator_id:
                messages.error(request, 'No coordinator selected.')
                return redirect('main:evaluation_form_upward')
            
            try:
                coordinator = User.objects.get(id=coordinator_id)
                coordinator_profile = coordinator.userprofile
            except User.DoesNotExist:
                messages.error(request, 'Selected coordinator does not exist.')
                return redirect('main:evaluation_form_upward')
            
            # Validate coordinator role
            if coordinator_profile.role != Role.COORDINATOR:
                messages.error(request, 'You can only evaluate coordinators.')
                return redirect('main:evaluation_form_upward')
            
            # Validate same institute
            if evaluator_profile.institute != coordinator_profile.institute:
                messages.error(request, 'You can only evaluate your own institute coordinator.')
                return redirect('main:evaluation_form_upward')

            # Get the current active upward evaluation period
            try:
                current_period = EvaluationPeriod.objects.get(
                    evaluation_type='upward',
                    is_active=True
                )
            except EvaluationPeriod.DoesNotExist:
                messages.error(request, 'No active upward evaluation period found.')
                return redirect('main:evaluation_form_upward')

            # Check for duplicate evaluation in this period
            from main.models import UpwardEvaluationResponse
            if UpwardEvaluationResponse.objects.filter(
                evaluator=request.user,
                evaluatee=coordinator,
                evaluation_period=current_period
            ).exists():
                messages.error(request, 'You have already evaluated this coordinator in this evaluation period.')
                return redirect('main:evaluation_form_upward')

            # Convert numeric values to text ratings
            rating_map = {
                '1': 'Strongly Disagree',
                '2': 'Disagree', 
                '3': 'Neutral',
                '4': 'Agree',
                '5': 'Strongly Agree'
            }
            
            # Validate all 15 questions and convert to text
            questions = {}
            for i in range(1, 16):  # 15 questions for upward evaluation
                question_key = f'question{i}'
                question_value = request.POST.get(question_key)
                
                if not question_value:
                    messages.error(request, f'All questions must be answered. Missing: Question {i}')
                    return redirect('main:evaluation_form_upward')
                
                if question_value not in rating_map:
                    messages.error(request, f'Invalid rating for question {i}.')
                    return redirect('main:evaluation_form_upward')
                    
                questions[question_key] = rating_map[question_value]

            # Get comments
            comments = request.POST.get('comments', '')

            # Create and save the upward evaluation response
            logger.info(f"🔍 Creating upward evaluation with 15 questions")
            
            evaluation_response = UpwardEvaluationResponse(
                evaluator=request.user,
                evaluatee=coordinator,
                evaluation_period=current_period,
                comments=comments,
                **questions
            )
            evaluation_response.save()
            logger.info(f"✅ Upward evaluation saved successfully! ID: {evaluation_response.id}")

            messages.success(request, 'Upward evaluation submitted successfully!')
            return redirect('main:evaluation_form_upward')

        except Exception as e:
            print("=" * 80)
            print(f"EXCEPTION OCCURRED: {str(e)}")
            print("=" * 80)
            import traceback
            traceback.print_exc()
            
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('main:evaluation_form_upward')

    print("Method was not POST, redirecting")
    return redirect('main:evaluation_form_upward')


def evaluation_form_dean(request):
    """
    Display the dean evaluation form (Faculty → Dean).
    Only faculty can access this form.
    Faculty evaluates their dean only.
    """
    if not request.user.is_authenticated:
        return redirect('/login')
    
    # Check if user has agreed to terms (reuse upward terms since they're on same page)
    if not request.session.get('upward_terms_agreed'):
        return redirect('upward_evaluation_terms')

    try:
        user_profile = UserProfile.objects.get(user=request.user)

        # ✅ ONLY FACULTY can access dean evaluation form
        if user_profile.role != Role.FACULTY:
            return render(request, 'main/no_permission.html', {
                'message': 'Only faculty members can access the dean evaluation form.',
                'page_title': 'Access Denied',
            })
        
        logger.info(f"🔍 evaluation_form_dean accessed by {request.user.username} (Faculty)")
        
        # STEP 1: Get the current active dean evaluation period
        logger.info("📍 STEP 1: Looking for active dean evaluation period...")
        try:
            current_dean_period = EvaluationPeriod.objects.get(
                evaluation_type='dean',
                is_active=True
            )
            logger.info(f"✅ Found active dean period: ID={current_dean_period.id}, Name={current_dean_period.name}")
        except EvaluationPeriod.DoesNotExist:
            logger.warning("❌ No active dean evaluation period found!")
            return render(request, 'main/no_active_evaluation.html', {
                'message': 'No active dean evaluation period found.',
                'page_title': 'Evaluation Unavailable',
            })
        except Exception as e:
            logger.error(f"❌ Error getting active dean period: {e}")
            return render(request, 'main/no_active_evaluation.html', {
                'message': 'Error retrieving evaluation period.',
                'page_title': 'Evaluation Unavailable',
            })

        # STEP 2: Check if dean evaluation is released and linked to this period
        logger.info("📍 STEP 2: Looking for released dean evaluation linked to active period...")
        evaluation = Evaluation.objects.filter(
            is_released=True,
            evaluation_type='dean',
            evaluation_period=current_dean_period
        ).first()

        if not evaluation:
            logger.warning(f"❌ No released dean evaluation linked to active period!")
            return render(request, 'main/no_active_evaluation.html', {
                'message': 'No active dean evaluation is currently available.',
                'page_title': 'Evaluation Unavailable',
            })
        
        logger.info(f"✅ Found released dean evaluation: ID={evaluation.id}, Period={evaluation.evaluation_period_id}")

        # STEP 3: Get all deans from the faculty's institute
        logger.info("📍 STEP 3: Getting deans...")
        
        if not user_profile.institute:
            logger.warning(f"❌ Faculty {request.user.username} has no institute assigned!")
            return render(request, 'main/no_active_evaluation.html', {
                'message': 'Your institute information is not set up. Please contact administrator.',
                'page_title': 'Configuration Required',
            })
        
        # Get all deans from the same institute
        dean_profiles = UserProfile.objects.filter(
            role=Role.DEAN,
            institute=user_profile.institute
        )
        
        if not dean_profiles.exists():
            logger.warning(f"❌ No dean found for institute '{user_profile.institute}'!")
            return render(request, 'main/no_active_evaluation.html', {
                'message': 'Your institute has no dean assigned. Please contact administrator.',
                'page_title': 'Configuration Required',
            })
        
        deans = User.objects.filter(userprofile__in=dean_profiles)
        logger.info(f"✅ Found {deans.count()} dean(s)")

        # STEP 4: Get list of already evaluated deans in this period
        logger.info("📍 STEP 4: Checking evaluated deans...")
        from main.models import DeanEvaluationResponse
        
        evaluated_ids = list(DeanEvaluationResponse.objects.filter(
            evaluator=request.user,
            evaluation_period=current_dean_period
        ).values_list('evaluatee_id', flat=True))

        logger.info(f"✅ User has evaluated {len(evaluated_ids)} dean(s) in this period")

        # ✅ Get dean evaluation questions from database
        from main.models import DeanEvaluationQuestion
        dean_questions = DeanEvaluationQuestion.objects.filter(
            is_active=True
        ).order_by('question_number')
        
        context = {
            'evaluation': evaluation,
            'deans': deans,
            'evaluated_ids': evaluated_ids,
            'questions': dean_questions,
            'page_title': 'Dean Evaluation Form',
        }
        response = render(request, 'main/evaluationform_dean.html', context)
        # Prevent browser caching
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found. Please contact administrator.")
        return redirect('/login')


def submit_dean_evaluation(request):
    """
    Handle submission of dean evaluation (Faculty → Dean)
    """
    print("=" * 80)
    print(f"SUBMIT DEAN EVALUATION CALLED - Method: {request.method}")
    print("=" * 80)
    
    if request.method == 'POST':
        # Check if user is authenticated
        if not request.user.is_authenticated:
            print("ERROR: User not authenticated")
            messages.error(request, 'You must be logged in to submit an evaluation.')
            return redirect('main:login')

        try:
            evaluator_profile = request.user.userprofile
            
            # ✅ ONLY FACULTY can submit dean evaluation
            if evaluator_profile.role != Role.FACULTY:
                messages.error(request, 'Only faculty members can submit dean evaluations.')
                return redirect('main:index')
            
            print(f"User: {request.user.username} (Faculty)")
            logger.info(f"🔍 Dean evaluation submission by {request.user.username}")
            
            # Get the dean being evaluated
            dean_id = request.POST.get('dean_id')
            print(f"Dean ID: {dean_id}")
            
            if not dean_id:
                messages.error(request, 'No dean selected.')
                return redirect('main:evaluation_form_dean')
            
            try:
                dean = User.objects.get(id=dean_id)
                dean_profile = dean.userprofile
            except User.DoesNotExist:
                messages.error(request, 'Selected dean does not exist.')
                return redirect('main:evaluation_form_dean')
            
            # Validate dean role
            if dean_profile.role != Role.DEAN:
                messages.error(request, 'You can only evaluate deans.')
                return redirect('main:evaluation_form_dean')
            
            # Validate same institute
            if evaluator_profile.institute != dean_profile.institute:
                messages.error(request, 'You can only evaluate your own institute dean.')
                return redirect('main:evaluation_form_dean')

            # Get the current active dean evaluation period
            try:
                current_period = EvaluationPeriod.objects.get(
                    evaluation_type='dean',
                    is_active=True
                )
            except EvaluationPeriod.DoesNotExist:
                messages.error(request, 'No active dean evaluation period found.')
                return redirect('main:evaluation_form_dean')

            # Check for duplicate evaluation in this period
            from main.models import DeanEvaluationResponse
            if DeanEvaluationResponse.objects.filter(
                evaluator=request.user,
                evaluatee=dean,
                evaluation_period=current_period
            ).exists():
                messages.error(request, 'You have already evaluated this dean in this evaluation period.')
                return redirect('main:evaluation_form_dean')

            # Convert numeric values to text ratings
            rating_map = {
                '1': 'Strongly Disagree',
                '2': 'Disagree', 
                '3': 'Neutral',
                '4': 'Agree',
                '5': 'Strongly Agree'
            }
            
            # Validate all 15 questions and convert to text
            questions = {}
            for i in range(1, 16):  # 15 questions for dean evaluation
                question_key = f'question{i}'
                question_value = request.POST.get(question_key)
                
                if not question_value:
                    messages.error(request, f'All questions must be answered. Missing: Question {i}')
                    return redirect('main:evaluation_form_dean')
                
                if question_value not in rating_map:
                    messages.error(request, f'Invalid rating for question {i}.')
                    return redirect('main:evaluation_form_dean')
                    
                questions[question_key] = rating_map[question_value]

            # Get comments
            comments = request.POST.get('comments', '')

            # Create and save the dean evaluation response
            logger.info(f"🔍 Creating dean evaluation with 15 questions")
            
            evaluation_response = DeanEvaluationResponse(
                evaluator=request.user,
                evaluatee=dean,
                evaluation_period=current_period,
                comments=comments,
                **questions
            )
            evaluation_response.save()
            logger.info(f"✅ Dean evaluation saved successfully! ID: {evaluation_response.id}")

            messages.success(request, 'Dean evaluation submitted successfully!')
            return redirect('main:evaluation_form_dean')

        except Exception as e:
            print("=" * 80)
            print(f"EXCEPTION OCCURRED: {str(e)}")
            print("=" * 80)
            import traceback
            traceback.print_exc()
            
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('main:evaluation_form_dean')

    print("Method was not POST, redirecting")
    return redirect('main:evaluation_form_dean')
    

def process_results(request):
    if request.method == 'POST':
        # ✅ FIX: Only process student evaluation results, not peer
        success, processing_results = EvaluationService.process_evaluation_results('student')
        
        if success:
            failure_count = len([r for r in processing_results if "Failed" in r])
            return JsonResponse({
                'success': True,
                'message': f'Processed STUDENT evaluation results. Found {failure_count} failures.',
                'processing_results': processing_results,
                'evaluation_type': 'student'  # Make it clear what was processed
            })
        else:
            return JsonResponse({
                'success': False,
                'error': processing_results[0] if processing_results else 'Student evaluation processing failed'
            })
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request'
    })


class EvaluationFormView(View):
    def get(self, request):
        # 🔐 Redirect to login if not authenticated
        if not request.user.is_authenticated:
            return redirect('/login')

        try:
            user_profile = request.user.userprofile

            # ✅ Check release statuses once
            student_eval_released = Evaluation.objects.filter(is_released=True, evaluation_type='student').exists()
            peer_eval_released = Evaluation.objects.filter(is_released=True, evaluation_type='peer').exists()

            # 🔹 STUDENT VIEW
            if user_profile.role == Role.STUDENT:
                if not student_eval_released:
                    return render(request, 'main/no_active_evaluation.html', {
                        'message': 'No student evaluation is currently available.',
                        'page_title': 'Evaluation Unavailable',
                    })

                evaluation = Evaluation.objects.filter(
                    is_released=True,
                    evaluation_type='student'
                ).order_by('-created_at').first()

                # ✅ SHOW ALL INSTRUCTORS (FACULTY, COORDINATOR, DEAN) ASSIGNED TO STUDENT'S SECTION
                # 🔥 IRREGULAR STUDENTS: Show ALL instructors (except admin) regardless of section
                if user_profile.is_irregular:
                    # Irregular students can evaluate ALL instructors in the system
                    faculty = User.objects.filter(
                        userprofile__role__in=[Role.FACULTY, Role.COORDINATOR, Role.DEAN]
                    )
                else:
                    # Regular students: show only instructors assigned to their section
                    student_section = user_profile.section
                    
                    if student_section:
                        # Get ALL instructors (faculty, coordinators, deans) assigned to this student's section
                        section_assignments = SectionAssignment.objects.filter(
                            section=student_section
                        ).select_related('user', 'user__userprofile')
                        
                        assigned_instructor_ids = list(section_assignments.values_list('user_id', flat=True))
                        
                        # Get the actual user objects with their profiles
                        faculty = User.objects.filter(
                            id__in=assigned_instructor_ids,
                            userprofile__role__in=[Role.FACULTY, Role.COORDINATOR, Role.DEAN]
                        )
                        
                    else:
                        # Fallback if student has no section assigned - show all faculty from institute
                        faculty = User.objects.filter(
                            userprofile__role__in=[Role.FACULTY, Role.COORDINATOR, Role.DEAN],
                            userprofile__institute=user_profile.institute
                        )
                    

                # ✅ Auto-fill student number from user profile
                student_number = user_profile.studentnumber if user_profile.studentnumber else ""

                # ✅ Auto-fill section from user profile
                student_section_display = ""
                if user_profile.section:
                    section_obj = user_profile.section
                    if hasattr(section_obj, 'section_name'):
                        student_section_display = section_obj.section_name
                    elif hasattr(section_obj, 'name'):
                        student_section_display = section_obj.name
                    elif hasattr(section_obj, 'code'):
                        student_section_display = section_obj.code
                    elif hasattr(section_obj, 'section_code'):
                        student_section_display = section_obj.section_code
                    elif hasattr(section_obj, 'title'):
                        student_section_display = section_obj.title
                    else:
                        student_section_display = str(section_obj)
                else:
                    # Check if student is irregular
                    if user_profile.is_irregular:
                        student_section_display = "Irregular"
                    else:
                        student_section_display = "Not assigned"

                # ✅ Get already evaluated instructors for this student IN CURRENT PERIOD
                try:
                    current_period = EvaluationPeriod.objects.get(
                        evaluation_type='student',
                        is_active=True
                    )
                    # Get regular evaluations
                    evaluated_ids = list(EvaluationResponse.objects.filter(
                        evaluator=request.user,
                        evaluation_period=current_period
                    ).values_list('evaluatee_id', flat=True))
                    
                    # Also check irregular evaluations if user is irregular student
                    if user_profile.is_irregular:
                        irregular_evaluated_ids = list(IrregularEvaluation.objects.filter(
                            evaluator=request.user,
                            evaluation_period=current_period
                        ).values_list('evaluatee_id', flat=True))
                        evaluated_ids.extend(irregular_evaluated_ids)
                except EvaluationPeriod.DoesNotExist:
                    evaluated_ids = []

                # ✅ Get student evaluation questions from database
                from .models import EvaluationQuestion
                student_questions = EvaluationQuestion.objects.filter(
                    evaluation_type='student',
                    is_active=True
                ).order_by('question_number')

                context = {
                    'evaluation': evaluation,
                    'faculty': faculty,
                    'student_evaluation_released': True,
                    'peer_evaluation_released': peer_eval_released,
                    'student_number': student_number,
                    'student_section': student_section_display,
                    'evaluated_ids': list(evaluated_ids),
                    'questions': student_questions,
                    'page_title': 'Teacher Evaluation Form',
                }
                response = render(request, 'main/evaluationform.html', context)
                # Prevent browser caching to ensure updated questions appear
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response

            # 🔹 STAFF VIEW (Faculty, Dean, Coordinator) - PEER EVALUATION
            elif user_profile.role in [Role.FACULTY, Role.DEAN, Role.COORDINATOR]:
                evaluation = Evaluation.objects.filter(
                    is_released=True,
                    evaluation_type='peer'
                ).order_by('-created_at').first()

                if not evaluation:
                    return render(request, 'main/no_active_evaluation.html', {
                        'message': 'No peer evaluation is currently available.',
                        'page_title': 'Evaluation Unavailable',
                    })

                # For staff peer evaluation, show appropriate colleagues based on user role
                # Faculty should only see other faculty members
                # Coordinators and Deans can see all staff (Faculty, Coordinators, Deans)
                logger.info(f"Peer evaluation - User: {request.user.username}, Role: {user_profile.role}, Institute: {user_profile.institute}")
                
                if user_profile.role == Role.FACULTY:
                    # Faculty users only see other faculty from same institute
                    staff_members = User.objects.filter(
                        userprofile__role=Role.FACULTY,
                        userprofile__institute=user_profile.institute
                    ).exclude(id=request.user.id)
                    logger.info(f"Faculty filtering - Found {staff_members.count()} colleagues")
                else:
                    # Coordinators and Deans see all staff from same institute
                    staff_members = User.objects.filter(
                        userprofile__role__in=[Role.FACULTY, Role.COORDINATOR, Role.DEAN],
                        userprofile__institute=user_profile.institute
                    ).exclude(id=request.user.id)
                    logger.info(f"Dean/Coordinator filtering - Found {staff_members.count()} colleagues")

                # ✅ Get already evaluated staff for this user IN CURRENT PERIOD
                try:
                    current_period = EvaluationPeriod.objects.get(
                        evaluation_type='peer',
                        is_active=True
                    )
                    evaluated_ids = EvaluationResponse.objects.filter(
                        evaluator=request.user,
                        evaluation_period=current_period
                    ).values_list('evaluatee_id', flat=True)
                except EvaluationPeriod.DoesNotExist:
                    evaluated_ids = []

                context = {
                    'evaluation': evaluation,
                    'faculty': staff_members,  # Now includes deans and coordinators
                    'student_evaluation_released': student_eval_released,
                    'peer_evaluation_released': evaluation is not None,
                    'evaluated_ids': list(evaluated_ids),
                    'page_title': 'Peer Evaluation Form',
                }
                return render(request, 'main/evaluationform_staffs.html', context)

            # 🚫 Other roles (e.g., Admin, etc.)
            else:
                return HttpResponseForbidden("You do not have permission to access this page.")

        except UserProfile.DoesNotExist:
            return redirect('/login')

def compute_category_scores(evaluatee, section_code=None, evaluation_period=None):
    """
    Calculate evaluation scores for a specific evaluatee and optional section
    CRITICAL: Now accepts evaluation_period to filter responses by date range
    
    IMPORTANT: This function ONLY uses EvaluationResponse, NOT IrregularEvaluation.
    Irregular student evaluations are excluded from overall results calculations.
    They are displayed separately in profile views but do not affect final scores.
    """
    
    # Filter responses by evaluatee
    # NOTE: Using EvaluationResponse only - irregular evaluations excluded by design
    responses = EvaluationResponse.objects.filter(evaluatee=evaluatee)
    
    # CRITICAL FIX: If evaluation period provided, filter responses by its date range
    if evaluation_period:
        responses = responses.filter(
            submitted_at__gte=evaluation_period.start_date,
            submitted_at__lte=evaluation_period.end_date
        )
    
    # Filter by section if provided
    if section_code:        
        responses = responses.filter(student_section=section_code)
    

    # Rating to numeric value mapping
    rating_to_numeric = {
        'Poor': 1,
        'Unsatisfactory': 2,
        'Satisfactory': 3,
        'Very Satisfactory': 4,
        'Outstanding': 5
    }

    # Initialize totals for 4 categories
    category_a_total = category_b_total = category_c_total = category_d_total = 0
    count_a = count_b = count_c = count_d = 0

    for response in responses:
        
        
        # Category A: Questions 1-4 (Mastery of Subject Matter) - 35%
        for i in range(1, 5):
            question_key = f'question{i}'
            rating_text = getattr(response, question_key, 'Poor')
            score = rating_to_numeric.get(rating_text, 1)
            category_a_total += score
            count_a += 1
            

        # Category B: Questions 5-8 (Classroom Management) - 25%
        for i in range(5, 9):
            question_key = f'question{i}'
            rating_text = getattr(response, question_key, 'Poor')
            score = rating_to_numeric.get(rating_text, 1)
            category_b_total += score
            count_b += 1
            

        # Category C: Questions 9-12 (Compliance to Policies) - 20%
        for i in range(9, 13):
            question_key = f'question{i}'
            rating_text = getattr(response, question_key, 'Poor')
            score = rating_to_numeric.get(rating_text, 1)
            category_c_total += score
            count_c += 1
            

        # Category D: Questions 13-15 (Personality) - 20%
        for i in range(13, 16):
            question_key = f'question{i}'
            rating_text = getattr(response, question_key, 'Poor')
            score = rating_to_numeric.get(rating_text, 1)
            category_d_total += score
            count_d += 1
            

    # CORRECTED WEIGHTS to match template
    max_score_per_question = 5
    a_weight = 0.35  # Mastery of Subject Matter
    b_weight = 0.25  # Classroom Management  
    c_weight = 0.20  # Compliance to Policies
    d_weight = 0.20  # Personality

    # Compute averages per category as a percent of their weights
    def scaled_avg(total, count, weight):
        if count == 0:
            return 0
        average_score = total / count  # average out of 5
        result = (average_score / max_score_per_question) * weight * 100
        
        return result

    a_avg = scaled_avg(category_a_total, count_a, a_weight)
    b_avg = scaled_avg(category_b_total, count_b, b_weight)
    c_avg = scaled_avg(category_c_total, count_c, c_weight)
    d_avg = scaled_avg(category_d_total, count_d, d_weight)

    total_percentage = a_avg + b_avg + c_avg + d_avg

    final_result = [
        round(a_avg, 2),
        round(b_avg, 2),
        round(c_avg, 2),
        round(d_avg, 2),
        round(total_percentage, 2),
        category_a_total,
        category_b_total,
        category_c_total,
        category_d_total
    ]
    
    
    
    return final_result

def compute_peer_scores(evaluatee, evaluation_period=None):
    """
    Calculate peer evaluation scores - simple average of 15 questions (100% total)
    Peer evaluations don't have categories, just overall percentage
    
    IMPORTANT: This function ONLY uses EvaluationResponse, NOT IrregularEvaluation.
    Irregular student evaluations are excluded from overall results calculations.
    """
    # Filter responses by evaluatee and evaluation period
    # NOTE: Using EvaluationResponse only - irregular evaluations excluded by design
    responses = EvaluationResponse.objects.filter(evaluatee=evaluatee)
    
    # MUST filter by evaluation_period to get only peer evaluation responses
    if evaluation_period:
        responses = responses.filter(evaluation_period=evaluation_period)
    
    if not responses.exists():
        return [0, 0, 0, 0, 0, 0, 0, 0, 0]  # Return zeros matching the format
    
    # Rating to numeric value mapping
    rating_to_numeric = {
        'Poor': 1,
        'Unsatisfactory': 2,
        'Satisfactory': 3,
        'Very Satisfactory': 4,
        'Outstanding': 5
    }
    
    total_score = 0
    total_questions = 0
    
    for response in responses:
        # Peer evaluation has 15 questions
        for i in range(1, 16):
            question_key = f'question{i}'
            rating_text = getattr(response, question_key, 'Poor')
            score = rating_to_numeric.get(rating_text, 1)
            total_score += score
            total_questions += 1
    
    # Calculate simple average as percentage
    if total_questions == 0:
        total_percentage = 0
    else:
        average_score = total_score / total_questions  # Average out of 5
        total_percentage = (average_score / 5) * 100  # Convert to percentage
    
    # Return format compatible with existing code (no categories for peer)
    return [
        0,  # No category A
        0,  # No category B
        0,  # No category C
        0,  # No category D
        round(total_percentage, 2),  # Total percentage
        0,  # No category A total
        0,  # No category B total
        0,  # No category C total
        0   # No category D total
    ]

def evaluation_form_staffs(request):
    """
    Display the staff peer evaluation form.
    Note: Form submission is handled by submit_evaluation() view
    
    CRITICAL FIX: Must check for active period FIRST, then linked evaluation record
    """
    if not request.user.is_authenticated:
        return redirect('/login')

    try:
        user_profile = UserProfile.objects.get(user=request.user)

        # ✅ ALLOW DEAN/COORDINATOR/FACULTY to access staff evaluation form
        if user_profile.role in [Role.DEAN, Role.COORDINATOR, Role.FACULTY]:
            # 🔍 DEBUG: Log the request
            logger.info(f"🔍 evaluation_form_staffs accessed by {request.user.username} ({user_profile.role})")
            
            # STEP 1: Get the current active peer evaluation period
            logger.info("📍 STEP 1: Looking for active peer evaluation period...")
            try:
                current_peer_period = EvaluationPeriod.objects.get(
                    evaluation_type='peer',
                    is_active=True
                )
                logger.info(f"✅ Found active peer period: ID={current_peer_period.id}, Name={current_peer_period.name}")
            except EvaluationPeriod.DoesNotExist:
                logger.warning("❌ No active peer evaluation period found!")
                logger.info("🔧 ATTEMPTING TO AUTO-CREATE MISSING PEER PERIOD...")
                
                # FALLBACK: Auto-create period if it doesn't exist
                # This handles the case where release_peer_evaluation may not have run
                try:
                    from django.utils import timezone
                    current_peer_period = EvaluationPeriod.objects.create(
                        name=f"Peer Evaluation {timezone.now().strftime('%B %Y')}",
                        evaluation_type='peer',
                        start_date=timezone.now(),
                        end_date=timezone.now() + timezone.timedelta(days=30),
                        is_active=True
                    )
                    logger.warning(f"⚠️  AUTO-CREATED peer period: ID={current_peer_period.id}")
                    logger.info("💡 HINT: Admin should run 'Release Evaluations' to properly set up evaluations")
                except Exception as create_error:
                    logger.error(f"❌ Failed to auto-create period: {create_error}")
                    return render(request, 'main/no_active_evaluation.html', {
                        'message': 'No active peer evaluation period found.',
                        'page_title': 'Evaluation Unavailable',
                    })
            except Exception as e:
                logger.error(f"❌ Error getting active peer period: {e}")
                return render(request, 'main/no_active_evaluation.html', {
                    'message': 'Error retrieving evaluation period.',
                    'page_title': 'Evaluation Unavailable',
                })

            # STEP 2: Check if peer evaluation is released and linked to this period
            logger.info("📍 STEP 2: Looking for released peer evaluation linked to active period...")
            evaluation = Evaluation.objects.filter(
                is_released=True,
                evaluation_type='peer',
                evaluation_period=current_peer_period
            ).first()

            if not evaluation:
                # Log available peer evaluations for debugging
                all_peer_evals = Evaluation.objects.filter(evaluation_type='peer').order_by('-created_at')[:3]
                logger.warning(f"❌ No released peer evaluation linked to active period!")
                logger.warning(f"   Available peer evaluations: {[(e.id, e.is_released, e.evaluation_period_id) for e in all_peer_evals]}")
                
                logger.info("🔧 ATTEMPTING TO AUTO-CREATE MISSING EVALUATION...")
                
                # FALLBACK: Auto-create the evaluation record if it doesn't exist
                try:
                    evaluation = Evaluation.objects.create(
                        evaluation_type='peer',
                        is_released=True,
                        evaluation_period=current_peer_period
                    )
                    logger.warning(f"⚠️  AUTO-CREATED peer evaluation: ID={evaluation.id}")
                    logger.info("💡 HINT: Admin should run 'Release Evaluations' to properly set up evaluations")
                except Exception as create_error:
                    logger.error(f"❌ Failed to auto-create evaluation: {create_error}")
                    return render(request, 'main/no_active_evaluation.html', {
                        'message': 'No active peer evaluation is currently available for staff members.',
                        'page_title': 'Evaluation Unavailable',
                    })
            
            logger.info(f"✅ Found released peer evaluation: ID={evaluation.id}, Period={evaluation.evaluation_period_id}")

            # STEP 3: Fetch the list of staff members (Faculty, Coordinators, Deans), excluding the currently logged-in user
            logger.info("📍 STEP 3: Getting available staff members...")
            
            # Faculty should only see other faculty members
            # Coordinators and Deans can see all staff
            if user_profile.role == Role.FACULTY:
                staff_members = User.objects.filter(
                    userprofile__role=Role.FACULTY,
                    userprofile__institute=user_profile.institute
                ).exclude(id=request.user.id)
                logger.info(f"✅ Faculty user - showing only faculty colleagues: {staff_members.count()} members")
            else:
                staff_members = User.objects.filter(
                    userprofile__role__in=[Role.FACULTY, Role.COORDINATOR, Role.DEAN],
                    userprofile__institute=user_profile.institute
                ).exclude(id=request.user.id)
                logger.info(f"✅ Dean/Coordinator user - showing all staff: {staff_members.count()} members")

            # STEP 4: Get already evaluated staff members FOR THIS PERIOD ONLY
            logger.info("📍 STEP 4: Getting already-evaluated staff list...")
            evaluated_ids = EvaluationResponse.objects.filter(
                evaluator=request.user,
                evaluation_period=current_peer_period
            ).values_list('evaluatee_id', flat=True)

            logger.info(f"✅ User has already evaluated {len(evaluated_ids)} staff members in this period")

            # ✅ All checks passed - prepare context
            logger.info("✅ ALL CHECKS PASSED - Rendering form...")
            
            # ✅ Get peer evaluation questions from database
            from .models import PeerEvaluationQuestion
            peer_questions = PeerEvaluationQuestion.objects.filter(
                is_active=True
            ).order_by('question_number')
            
            context = {
                'evaluation': evaluation,
                'faculty': staff_members,
                'evaluated_ids': list(evaluated_ids),
                'questions': peer_questions,
                'page_title': 'Peer Evaluation Form',
            }
            response = render(request, 'main/evaluationform_staffs.html', context)
            # Prevent browser caching to ensure updated questions appear
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response

        else:
            return render(request, 'main/no_permission.html', {
                'message': 'You do not have permission to access the staff evaluation form.',
                'page_title': 'Access Denied',
            })

    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found. Please contact administrator.")
        return redirect('/login')


def upward_evaluation_terms(request):
    """
    Display terms & conditions page before upward evaluation.
    Only faculty can access this page.
    """
    if not request.user.is_authenticated:
        return redirect('/login')
    
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        
        # Only faculty can access upward evaluation
        if user_profile.role != Role.FACULTY:
            return render(request, 'main/no_permission.html', {
                'message': 'Only faculty members can access the upward evaluation.',
                'page_title': 'Access Denied',
            })
        
        # Check if there's an active upward evaluation period
        try:
            current_upward_period = EvaluationPeriod.objects.get(
                evaluation_type='upward',
                is_active=True
            )
            
            # Check if upward evaluation is released and linked to this period
            evaluation = Evaluation.objects.filter(
                is_released=True,
                evaluation_type='upward',
                evaluation_period=current_upward_period
            ).first()
            
        except EvaluationPeriod.DoesNotExist:
            evaluation = None
        
        context = {
            'evaluation': evaluation,
            'page_title': 'Upward Evaluation Agreement'
        }
        
        return render(request, 'main/evaluationform_upward_terms.html', context)
    
    except UserProfile.DoesNotExist:
        return redirect('/login')


def upward_terms_agree(request):
    """
    Handle terms agreement and store in session.
    """
    if request.method == 'POST':
        request.session['upward_terms_agreed'] = True
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


def evaluation_form_upward(request):
    """
    Display the upward evaluation form (Faculty → Coordinator).
    Only faculty can access this form.
    Faculty evaluates their coordinator only.
    """
    if not request.user.is_authenticated:
        return redirect('/login')
    
    # Check if user has agreed to terms
    if not request.session.get('upward_terms_agreed'):
        return redirect('upward_evaluation_terms')

    try:
        user_profile = UserProfile.objects.get(user=request.user)

        # ✅ ONLY FACULTY can access upward evaluation form
        if user_profile.role != Role.FACULTY:
            return render(request, 'main/no_permission.html', {
                'message': 'Only faculty members can access the upward evaluation form.',
                'page_title': 'Access Denied',
            })
        
        logger.info(f"🔍 evaluation_form_upward accessed by {request.user.username} (Faculty)")
        
        # STEP 1: Get the current active upward evaluation period
        logger.info("📍 STEP 1: Looking for active upward evaluation period...")
        try:
            current_upward_period = EvaluationPeriod.objects.get(
                evaluation_type='upward',
                is_active=True
            )
            logger.info(f"✅ Found active upward period: ID={current_upward_period.id}, Name={current_upward_period.name}")
        except EvaluationPeriod.DoesNotExist:
            logger.warning("❌ No active upward evaluation period found!")
            return render(request, 'main/no_active_evaluation.html', {
                'message': 'No active upward evaluation period found.',
                'page_title': 'Evaluation Unavailable',
            })
        except Exception as e:
            logger.error(f"❌ Error getting active upward period: {e}")
            return render(request, 'main/no_active_evaluation.html', {
                'message': 'Error retrieving evaluation period.',
                'page_title': 'Evaluation Unavailable',
            })

        # STEP 2: Check if upward evaluation is released and linked to this period
        logger.info("📍 STEP 2: Looking for released upward evaluation linked to active period...")
        evaluation = Evaluation.objects.filter(
            is_released=True,
            evaluation_type='upward',
            evaluation_period=current_upward_period
        ).first()

        if not evaluation:
            logger.warning(f"❌ No released upward evaluation linked to active period!")
            return render(request, 'main/no_active_evaluation.html', {
                'message': 'No active upward evaluation is currently available.',
                'page_title': 'Evaluation Unavailable',
            })
        
        logger.info(f"✅ Found released upward evaluation: ID={evaluation.id}, Period={evaluation.evaluation_period_id}")

        # STEP 3: Get all coordinators from the faculty's institute
        logger.info("📍 STEP 3: Getting coordinators...")
        
        if not user_profile.institute:
            logger.warning(f"❌ Faculty {request.user.username} has no institute assigned!")
            return render(request, 'main/no_active_evaluation.html', {
                'message': 'Your institute information is not set up. Please contact administrator.',
                'page_title': 'Configuration Required',
            })
        
        # Get all coordinators from the same institute
        coordinator_profiles = UserProfile.objects.filter(
            role=Role.COORDINATOR,
            institute=user_profile.institute
        )
        
        if not coordinator_profiles.exists():
            logger.warning(f"❌ No coordinator found for institute '{user_profile.institute}'!")
            return render(request, 'main/no_active_evaluation.html', {
                'message': 'Your institute has no coordinator assigned. Please contact administrator.',
                'page_title': 'Configuration Required',
            })
        
        coordinators = User.objects.filter(userprofile__in=coordinator_profiles)
        logger.info(f"✅ Found {coordinators.count()} coordinator(s)")

        # STEP 4: Get list of already evaluated coordinators in this period
        logger.info("📍 STEP 4: Checking evaluated coordinators...")
        from main.models import UpwardEvaluationResponse
        
        evaluated_ids = list(UpwardEvaluationResponse.objects.filter(
            evaluator=request.user,
            evaluation_period=current_upward_period
        ).values_list('evaluatee_id', flat=True))

        logger.info(f"✅ User has evaluated {len(evaluated_ids)} coordinator(s) in this period")

        # ✅ Get upward evaluation questions from database
        from main.models import UpwardEvaluationQuestion
        upward_questions = UpwardEvaluationQuestion.objects.filter(
            is_active=True
        ).order_by('question_number')
        
        context = {
            'evaluation': evaluation,
            'coordinators': coordinators,
            'evaluated_ids': evaluated_ids,
            'questions': upward_questions,
            'page_title': 'Upward Evaluation Form',
        }
        response = render(request, 'main/evaluationform_upward.html', context)
        # Prevent browser caching
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found. Please contact administrator.")
        return redirect('/login')


def evaluated(request):
    evaluator = request.user
    evaluator_profile = evaluator.userprofile

    # Check for active evaluation periods
    active_student_period = EvaluationPeriod.objects.filter(
        evaluation_type='student',
        is_active=True
    ).first()
    
    active_peer_period = EvaluationPeriod.objects.filter(
        evaluation_type='peer',
        is_active=True
    ).first()

    # Determine who can be evaluated based on evaluator role and active periods
    faculty = User.objects.none()  # Start with empty queryset
    
    if evaluator_profile.role == Role.STUDENT:
        # Students can evaluate faculty during student evaluation periods
        if active_student_period:
            # Get faculty assigned to the student's section
            if evaluator_profile.section:
                faculty = User.objects.filter(
                    userprofile__role__in=[Role.FACULTY, Role.DEAN, Role.COORDINATOR],
                    sectionassignment__section=evaluator_profile.section
                ).distinct()
    
    elif evaluator_profile.role in [Role.FACULTY, Role.DEAN, Role.COORDINATOR]:
        # Faculty/Staff can evaluate other faculty during peer evaluation periods
        if active_peer_period:
            # Get all faculty except themselves
            faculty = User.objects.filter(
                userprofile__role__in=[Role.FACULTY, Role.DEAN, Role.COORDINATOR]
            ).exclude(id=evaluator.id).distinct()

    # Get IDs of users this evaluator has already evaluated in current period
    evaluated_ids = list(
        EvaluationResponse.objects.filter(evaluator=evaluator)
        .values_list('evaluatee_id', flat=True)
    )

    # Get evaluation questions
    from .models import EvaluationQuestion
    if evaluator_profile.role == Role.STUDENT and active_student_period:
        questions = EvaluationQuestion.objects.filter(is_active=True).order_by('question_number')
    elif evaluator_profile.role in [Role.FACULTY, Role.DEAN, Role.COORDINATOR] and active_peer_period:
        questions = EvaluationQuestion.objects.filter(is_active=True).order_by('question_number')
    else:
        questions = EvaluationQuestion.objects.none()

    context = {
        'evaluated_ids': evaluated_ids,
        'faculty': faculty,
        'questions': questions,
        'active_student_period': active_student_period,
        'active_peer_period': active_peer_period,
        'evaluator_role': evaluator_profile.role,
    }

    return render(request, 'evaluationform.html', context)
@method_decorator(profile_settings_allowed, name='dispatch')    
class DeanProfileSettingsView(View):
    
    def get(self, request):
        user = request.user
        if user.is_authenticated:
            try:
                index_url = reverse('main:index')
            except:
                index_url = '/'
            
            next_url = request.GET.get('next', request.META.get('HTTP_REFERER', index_url))
            
            if user.userprofile.role != 'Dean':
                return redirect(index_url)
            
            evaluation_data = self.get_evaluation_data(user)
            ai_recommendations = self.get_ai_recommendations(user)
            assigned_sections = self.get_assigned_sections(user)
            section_scores = self.get_section_scores(user, assigned_sections)
            
            # Get peer evaluation scores
            peer_scores = self.get_peer_evaluation_scores(user)
            
            # Get irregular student evaluation scores
            irregular_scores = self.get_irregular_evaluation_scores(user)
            
            # Convert to JSON for JavaScript
            import json
            section_scores_json = json.dumps(section_scores)
            # Convert to list to avoid queryset exhaustion
            assigned_sections_list = list(assigned_sections)
            section_map_json = json.dumps({assignment.section.id: assignment.section.code for assignment in assigned_sections_list})
            peer_scores_json = json.dumps(peer_scores)
            irregular_scores_json = json.dumps(irregular_scores)
            
            # Calculate overall statistics for the template
            total_sections = len(assigned_sections_list)
            sections_with_data = sum(1 for scores in section_scores.values() if scores['has_data'])
            total_evaluations = EvaluationResponse.objects.filter(evaluatee=user).count()

            evaluation_history = self.get_evaluation_history(user)
            
            # Identify current active student evaluation period (if any)
            active_student_period = EvaluationPeriod.objects.filter(evaluation_type='student', is_active=True).order_by('-start_date').first()

            # Get all sections and years for section assignment
            sections = Section.objects.all().order_by('year_level', 'code')
            years = list(Section.objects.values_list('year_level', flat=True).distinct().order_by('year_level'))
            currently_assigned_ids = [assignment.section.id for assignment in assigned_sections_list]

            # Add timestamp for cache busting
            import time
            timestamp = int(time.time())

            return render(request, 'main/dean_profile_settings.html', {
                'user': user,
                'next_url': next_url,
                'evaluation_data': evaluation_data,
                'ai_recommendations': ai_recommendations,
                'assigned_sections': assigned_sections_list,
                'section_scores': section_scores,
                'section_scores_json': section_scores_json,
                'section_map_json': section_map_json,
                'peer_scores': peer_scores,
                'peer_scores_json': peer_scores_json,
                'irregular_scores': irregular_scores,
                'irregular_scores_json': irregular_scores_json,
                'has_any_data': any(scores['has_data'] for scores in section_scores.values()),
                'total_sections': total_sections,
                'sections_with_data': sections_with_data,
                'total_evaluations': total_evaluations,
                'evaluation_period_ended': can_view_evaluation_results('student'),
                'evaluation_history': evaluation_history,
                'active_student_period_id': active_student_period.id if active_student_period else None,
                'sections': sections,
                'years': years,
                'currently_assigned_ids': currently_assigned_ids,
                'timestamp': timestamp,  # Cache busting timestamp
            })
        return redirect('login')
    
    def get_evaluation_history(self, user):
        """Get simplified evaluation history from EvaluationResponse records"""
        # Get all evaluation responses for this user - use submitted_at instead of created_at
        evaluations = EvaluationResponse.objects.filter(
            evaluatee=user
        ).select_related('evaluator').order_by('-submitted_at')
        
        history = []
        
        # Group evaluations by month for simplicity
        from collections import defaultdict
        
        monthly_data = defaultdict(lambda: {
            'period_name': '',
            'date': None,
            'total_responses': 0,
            'total_score': 0,
            'sections': set(),
            'comments': []
        })
        
        for eval_response in evaluations:
            # Group by month-year - use submitted_at instead of created_at
            month_key = eval_response.submitted_at.strftime('%B %Y')
            
            if not monthly_data[month_key]['period_name']:
                monthly_data[month_key]['period_name'] = f"{eval_response.submitted_at.strftime('%B %Y')} Evaluation"
                monthly_data[month_key]['date'] = eval_response.submitted_at
            
            monthly_data[month_key]['total_responses'] += 1
            monthly_data[month_key]['sections'].add(eval_response.student_section or 'Unknown Section')
            
            # Calculate average score for this evaluation
            rating_to_numeric = {
                'Poor': 1, 'Unsatisfactory': 2, 'Satisfactory': 3, 
                'Very Satisfactory': 4, 'Outstanding': 5
            }
            
            total_score = 0
            question_count = 0
            
            for i in range(1, 16):
                question_key = f'question{i}'
                rating_text = getattr(eval_response, question_key, 'Poor')
                score = rating_to_numeric.get(rating_text, 1)
                total_score += score
                question_count += 1
            
            average_score = (total_score / question_count) if question_count > 0 else 0
            monthly_data[month_key]['total_score'] += average_score
            
            # Collect comments
            if eval_response.comments:
                monthly_data[month_key]['comments'].append(eval_response.comments)
        
        # Convert to the format expected by the template
        for month_key, data in monthly_data.items():
            if data['total_responses'] > 0:
                average_score = data['total_score'] / data['total_responses']
                overall_percentage = (average_score / 5) * 100
                
                history.append({
                    'period_name': data['period_name'],
                    'date': data['date'],
                    'section': ', '.join(list(data['sections'])[:3]),  # Show up to 3 sections
                    'average_score': round(average_score, 2),
                    'overall_percentage': round(overall_percentage, 2),
                    'total_responses': data['total_responses'],
                    'comments': data['comments'][:5],  # Show up to 5 comments
                    'comments_count': len(data['comments']),
                    'category_scores': [0, 0, 0, 0],  # Placeholder - you can calculate these if needed
                    'category_percentages': [0, 0, 0, 0]  # Placeholder
                })
        
        # Sort by date descending
        history.sort(key=lambda x: x['date'], reverse=True)
        
        return history[:12]  # Return last 12 months max

    def post(self, request):
        user = request.user
        if user.is_authenticated:
            try:
                index_url = reverse('main:index')
            except:
                index_url = '/'
            
            next_url = request.POST.get('next', request.META.get('HTTP_REFERER', index_url))
            
            if user.userprofile.role != 'Dean':
                return redirect(index_url)

            # Check if this is a section assignment request
            action = request.POST.get('action')
            if action == 'assign_sections':
                selected_section_ids = request.POST.getlist('sections')
                
                # Delete existing section assignments for this user
                SectionAssignment.objects.filter(user=user).delete()
                
                # Create new section assignments
                sections_assigned = []
                for section_id in selected_section_ids:
                    try:
                        section = Section.objects.get(id=section_id)
                        SectionAssignment.objects.create(user=user, section=section)
                        sections_assigned.append(section.code)
                    except Section.DoesNotExist:
                        continue
                
                if len(sections_assigned) > 0:
                    sections_list = ", ".join(sections_assigned)
                    messages.success(request, f"✅ Successfully assigned {len(sections_assigned)} section(s): {sections_list}")
                else:
                    messages.success(request, f"✅ All section assignments have been removed.")
                return redirect('main:dean_profile_settings')

            # Handle profile update (existing code)
            username = request.POST.get("username")
            email = request.POST.get("email")
            new_password = request.POST.get("new_password1")
            confirm_password = request.POST.get("new_password2")

            # Email validation
            if not re.match(r"^[a-zA-Z0-9._%+-]+@(gmail\.com|cca\.edu\.ph)$", email):
                evaluation_data = self.get_evaluation_data(user)
                ai_recommendations = self.get_ai_recommendations(user)
                assigned_sections = self.get_assigned_sections(user)
                section_scores = self.get_section_scores(user, assigned_sections)
                
                # Calculate overall statistics for error context
                total_sections = assigned_sections.count()
                sections_with_data = sum(1 for scores in section_scores.values() if scores['has_data'])
                total_evaluations = EvaluationResponse.objects.filter(evaluatee=user).count()
                
                return render(request, 'main/dean_profile_settings.html', {
                    'user': user,
                    'next_url': next_url,
                    'evaluation_data': evaluation_data,
                    'ai_recommendations': ai_recommendations,
                    'assigned_sections': assigned_sections,
                    'section_scores': section_scores,
                    'total_sections': total_sections,
                    'sections_with_data': sections_with_data,
                    'total_evaluations': total_evaluations,
                    'error': 'Invalid email address. Please use an email ending with @gmail.com or @cca.edu.ph.'
                })

            # Password validation
            if new_password and new_password != confirm_password:
                evaluation_data = self.get_evaluation_data(user)
                ai_recommendations = self.get_ai_recommendations(user)
                assigned_sections = self.get_assigned_sections(user)
               
                section_scores = self.get_section_scores(user, assigned_sections)
                
                # Calculate overall statistics for error context
                total_sections = assigned_sections.count()
                sections_with_data = sum(1 for scores in section_scores.values() if scores['has_data'])
                total_evaluations = EvaluationResponse.objects.filter(evaluatee=user).count()
                
                return render(request, 'main/dean_profile_settings.html', {
                    'user': user,
                    'next_url': next_url,
                    'evaluation_data': evaluation_data,
                    'ai_recommendations': ai_recommendations,
                    'assigned_sections': assigned_sections,
                
                    'section_scores': section_scores,
                    'total_sections': total_sections,
                    'sections_with_data': sections_with_data,
                    'total_evaluations': total_evaluations,
                    'error': 'Passwords do not match.'
                })

            # Update user information
            user.username = username
            user.email = email

            if new_password:
                user.set_password(new_password)
                update_session_auth_hash(request, user)

            user.save()

            # Add success parameter to URL
            if "?" in next_url:
                next_url += "&updated=true"
            else:
                next_url += "?updated=true"

            messages.success(request, "Profile updated successfully.")
            return redirect(next_url)
        return redirect('login')
    
    def get_assigned_sections(self, user):
        """Get assigned sections for the coordinator"""
        return SectionAssignment.objects.filter(user=user)
    
    def get_section_scores(self, user, assigned_sections):
        """Get scores for each assigned section from EvaluationResult table"""
        from main.models import EvaluationResult
        section_scores = {}
        
        # Get the most recent INACTIVE period that has actually ended (not future periods)
        # Results are stored in EvaluationResult when period ends (unrelease)
        from django.utils import timezone
        latest_period = EvaluationPeriod.objects.filter(
            evaluation_type='student',
            is_active=False,
            end_date__lte=timezone.now()  # Only past periods
        ).order_by('-end_date').first()
        
        # Build unified list of sections: assigned + any sections actually evaluated (from results)
        assigned_section_objs = [a.section for a in assigned_sections]
        dynamic_result_sections = []
        if latest_period:
            dynamic_result_sections = [r.section for r in EvaluationResult.objects.filter(
                user=user,
                evaluation_period=latest_period
            ).select_related('section') if r.section and r.section not in assigned_section_objs]
        sections_to_display = assigned_section_objs + dynamic_result_sections

        for section in sections_to_display:
            section_code = section.code
            
            # Try to get pre-computed result from EvaluationResult table
            result = None
            if latest_period:
                try:
                    result = EvaluationResult.objects.get(
                        user=user,
                        section=section,
                        evaluation_period=latest_period
                    )
                except EvaluationResult.DoesNotExist:
                    pass
            
            if result:
                # Use pre-computed results from EvaluationResult table
                a_avg = result.category_a_score
                b_avg = result.category_b_score
                c_avg = result.category_c_score
                d_avg = result.category_d_score
                total_percentage = result.total_percentage
                evaluation_count = result.total_responses
                has_data = True
                
                # Get comments from the responses in this period
                comments_queryset = EvaluationResponse.objects.filter(
                    evaluatee=user,
                    student_section=section_code,
                    submitted_at__gte=latest_period.start_date,
                    submitted_at__lte=latest_period.end_date,
                    comments__isnull=False
                ).exclude(comments='').values_list('comments', flat=True)
            else:
                # No results yet - section has no data
                a_avg = b_avg = c_avg = d_avg = total_percentage = 0
                evaluation_count = 0
                has_data = False
                comments_queryset = []
            
            # Categorize comments using sentiment analysis
            positive_comments = []
            negative_comments = []
            mixed_comments = []
            
            for comment in comments_queryset:
                sentiment = TeachingAIRecommendationService.analyze_comment_sentiment(comment)
                if sentiment == 'positive':
                    positive_comments.append(comment)
                elif sentiment == 'negative':
                    negative_comments.append(comment)
                elif sentiment == 'mixed':
                    mixed_comments.append(comment)
            
            section_scores[section_code] = {
                'category_scores': [
                    round(a_avg, 2),
                    round(b_avg, 2),
                    round(c_avg, 2),
                    round(d_avg, 2)
                ],
                'total_percentage': round(total_percentage, 2),
                'has_data': has_data,
                'evaluation_count': evaluation_count,
                'section_name': section.code,
                'positive_comments': positive_comments,
                'negative_comments': negative_comments,
                'mixed_comments': mixed_comments
            }
        
        return section_scores

    
    def get_evaluation_data(self, user):
        # Get assigned sections for this coordinator
        assigned_sections = self.get_assigned_sections(user)
        
        # Calculate overall scores across all assigned sections
        total_category_a = total_category_b = total_category_c = total_category_d = 0
        total_count_a = total_count_b = total_count_c = total_count_d = 0
        total_responses = 0        # Get the most recent COMPLETED period (same as section scores)
        from django.utils import timezone
        latest_period = EvaluationPeriod.objects.filter(
            evaluation_type='student',
            is_active=False,
            end_date__lte=timezone.now()
        ).order_by('-end_date').first()
        
        for section_assignment in assigned_sections:
            section = section_assignment.section
            section_code = section.code
            
            # Calculate scores for this specific section
            category_scores = compute_category_scores(user, section_code, evaluation_period=latest_period)
            a_avg, b_avg, c_avg, d_avg, total_percentage, total_a, total_b, total_c, total_d = category_scores
            
            # Only include sections that have evaluations
            if total_percentage > 0:
                # For overall calculation, we need to accumulate totals and counts
                section_responses = EvaluationResponse.objects.filter(
                    evaluatee=user,
                    student_section=section_code
                )
                
                # Filter by completed period to match section scores
                if latest_period:
                    section_responses = section_responses.filter(evaluation_period=latest_period)
                
                if section_responses.exists():
                    total_responses += section_responses.count()
                    
                    # Recalculate raw totals for proper averaging
                    rating_to_numeric = {
                        'Poor': 1, 'Unsatisfactory': 2, 'Satisfactory': 3, 
                        'Very Satisfactory': 4, 'Outstanding': 5
                    }
                    
                    for response in section_responses:
                        # Category A: Questions 1-4 (Mastery of Subject Matter - 35%)
                        for i in range(1, 5):
                            question_key = f'question{i}'
                            rating_text = getattr(response, question_key, 'Poor')
                            score = rating_to_numeric.get(rating_text, 1)
                            total_category_a += score
                            total_count_a += 1

                        # Category B: Questions 5-8 (Classroom Management - 25%)
                        for i in range(5, 9):
                            question_key = f'question{i}'
                            rating_text = getattr(response, question_key, 'Poor')
                            score = rating_to_numeric.get(rating_text, 1)
                            total_category_b += score
                            total_count_b += 1

                        # Category C: Questions 9-12 (Compliance to Policies - 20%)
                        for i in range(9, 13):
                            question_key = f'question{i}'
                            rating_text = getattr(response, question_key, 'Poor')
                            score = rating_to_numeric.get(rating_text, 1)
                            total_category_c += score
                            total_count_c += 1

                        # Category D: Questions 13-15 (Personality - 20%)
                        for i in range(13, 16):
                            question_key = f'question{i}'
                            rating_text = getattr(response, question_key, 'Poor')
                            score = rating_to_numeric.get(rating_text, 1)
                            total_category_d += score
                            total_count_d += 1
        
        # CORRECTED: Use proper weights for 4 categories
        max_score_per_question = 5
        a_weight = 0.35  # Mastery of Subject Matter
        b_weight = 0.25  # Classroom Management
        c_weight = 0.20  # Compliance to Policies
        d_weight = 0.20  # Personality
        
        def scaled_avg(total, count, weight):
            if count == 0:
                return 0.00
            average_score = total / count
            return (average_score / max_score_per_question) * weight * 100
        
        a_avg = scaled_avg(total_category_a, total_count_a, a_weight)
        b_avg = scaled_avg(total_category_b, total_count_b, b_weight)
        c_avg = scaled_avg(total_category_c, total_count_c, c_weight)
        d_avg = scaled_avg(total_category_d, total_count_d, d_weight)
        
        total_percentage = a_avg + b_avg + c_avg + d_avg
        
        # FETCH COMMENTS FROM ALL SECTIONS FOR OVERALL VIEW
        # IMPORTANT: Only student evaluation comments from completed period
        comments_query = EvaluationResponse.objects.filter(
            evaluatee=user,
            comments__isnull=False
        ).exclude(comments='')
        
        # Filter by completed period to match section scores
        if latest_period:
            comments_query = comments_query.filter(evaluation_period=latest_period)
        
        all_comments = comments_query.values_list('comments', flat=True)
        
        # Categorize all comments using sentiment analysis
        positive_comments = []
        negative_comments = []
        mixed_comments = []
        
        for comment in all_comments:
            sentiment = TeachingAIRecommendationService.analyze_comment_sentiment(comment)
            if sentiment == 'positive':
                positive_comments.append(comment)
            elif sentiment == 'negative':
                negative_comments.append(comment)
            elif sentiment == 'mixed':
                mixed_comments.append(comment)
        
        # CORRECTED: Use proper max scores for percentage calculations
        max_scores = [35, 25, 20, 20]  # Updated to match category weights
        category_percentages = [
            round((a_avg / max_scores[0]) * 100, 2) if max_scores[0] > 0 else 0.00,
            round((b_avg / max_scores[1]) * 100, 2) if max_scores[1] > 0 else 0.00,
            round((c_avg / max_scores[2]) * 100, 2) if max_scores[2] > 0 else 0.00,
            round((d_avg / max_scores[3]) * 100, 2) if max_scores[3] > 0 else 0.00
        ]
        
        return {
            'has_data': total_responses > 0,
            'overall_score': round(total_percentage, 2) if total_percentage else 0.00,
            'category_scores': [
                round(a_avg, 2) if a_avg else 0.00,
                round(b_avg, 2) if b_avg else 0.00,
                round(c_avg, 2) if c_avg else 0.00,
                round(d_avg, 2) if d_avg else 0.00
            ],
            'category_percentages': category_percentages,
            'total_responses': total_responses,
            'positive_comments': positive_comments,
            'negative_comments': negative_comments,
            'mixed_comments': mixed_comments,
            'average_rating': round((total_category_a + total_category_b + total_category_c + total_category_d) / (total_responses * 15) * 5, 2) if total_responses > 0 else 0.00,
            'completion_rate': min(100.00, round(total_responses * 10, 2)),
            'improvement': 2.50,
            'rating_distribution': [2, 5, 12, 25, 40]
        }
    
    def get_ai_recommendations(self, user, section_data=None, section_code=None):
        """Get AI recommendations - retrieve saved ones for archived periods or generate new ones"""
        from main.models import AiRecommendation, EvaluationPeriod
        
        # Get the latest completed student period
        latest_student_period = EvaluationPeriod.objects.filter(
            evaluation_type='student',
            is_active=False
        ).order_by('-end_date').first()
        
        # Check if we have saved recommendations for this period and section
        if latest_student_period and section_code:
            saved_recs = AiRecommendation.objects.filter(
                user=user,
                evaluation_period=latest_student_period,
                section_code=section_code,
                evaluation_type='student'
            ).order_by('created_at')
            
            if saved_recs.exists():
                # Return saved recommendations
                return [
                    {
                        'title': rec.title,
                        'description': rec.description,
                        'priority': rec.priority,
                        'reason': rec.reason
                    }
                    for rec in saved_recs
                ]
        
        # Generate new recommendations if none saved
        ai_service = TeachingAIRecommendationService()
        recommendations = ai_service.get_recommendations(
            user=user,
            section_data=section_data,
            section_code=section_code,
            role="Dean"
        )
        
        # Save recommendations if we have a period and they're not already saved
        if latest_student_period and section_code and recommendations:
            for rec in recommendations:
                if isinstance(rec, dict):
                    AiRecommendation.objects.get_or_create(
                        user=user,
                        evaluation_period=latest_student_period,
                        section_code=section_code,
                        evaluation_type='student',
                        title=str(rec.get('title', '')[:255]),
                        defaults={
                            'description': rec.get('description', ''),
                            'priority': rec.get('priority', ''),
                            'reason': rec.get('reason', ''),
                            'recommendation': rec.get('description', '')
                        }
                    )
        
        return recommendations
    
    def get_peer_evaluation_scores(self, user):
        """Calculate peer evaluation scores (evaluations from other staff members)"""
        # Get the most recent INACTIVE peer period that has ended
        from django.utils import timezone
        latest_peer_period = EvaluationPeriod.objects.filter(
            evaluation_type='peer',
            is_active=False,
            end_date__lte=timezone.now()
        ).order_by('-end_date').first()
        
        # Peer evaluations are identified by having "Staff" in student_section field
        peer_evaluations = EvaluationResponse.objects.filter(
            evaluatee=user,
            student_section__icontains="Staff"
        )
        
        # Filter by the latest completed peer period
        if latest_peer_period:
            peer_evaluations = peer_evaluations.filter(evaluation_period=latest_peer_period)
        
        evaluation_count = peer_evaluations.count()
        
        if evaluation_count == 0:
            return {
                'has_data': False,
                'category_scores': [0, 0, 0, 0],
                'total_percentage': 0,
                'evaluation_count': 0
            }
        
        # Calculate scores from peer evaluations
        rating_to_numeric = {
            'Poor': 1, 'Unsatisfactory': 2, 'Satisfactory': 3, 
            'Very Satisfactory': 4, 'Outstanding': 5
        }
        
        total_score = 0
        total_count = 0
        
        for response in peer_evaluations:
            # Peer evaluations: Questions 1-15 (no categories, simple average)
            for i in range(1, 16):
                question_key = f'question{i}'
                rating_text = getattr(response, question_key, 'Poor')
                score = rating_to_numeric.get(rating_text, 1)
                total_score += score
                total_count += 1
        
        # Calculate simple average percentage
        if total_count > 0:
            average_score = total_score / total_count
            total_percentage = (average_score / 5) * 100
        else:
            total_percentage = 0
        
        # Fetch peer comments and categorize them
        peer_comments = peer_evaluations.filter(
            comments__isnull=False
        ).exclude(comments='').values_list('comments', flat=True)
        
        positive_comments = []
        negative_comments = []
        
        for comment in peer_comments:
            sentiment = TeachingAIRecommendationService.analyze_comment_sentiment(comment)
            if sentiment == 'positive':
                positive_comments.append(comment)
            elif sentiment == 'negative':
                negative_comments.append(comment)
        
        return {
            'has_data': True,
            'category_scores': [0, 0, 0, 0],  # Peer evaluations don't have categories
            'total_percentage': round(total_percentage, 2),
            'evaluation_count': evaluation_count,
            'total_evaluations': evaluation_count,  # For template compatibility
            'positive_comments': positive_comments,
            'negative_comments': negative_comments
        }
    
    def get_irregular_evaluation_scores(self, user):
        """Calculate irregular student evaluation scores"""
        # Get the most recent INACTIVE student period that has ended
        from django.utils import timezone
        latest_student_period = EvaluationPeriod.objects.filter(
            evaluation_type='student',
            is_active=False,
            end_date__lte=timezone.now()
        ).order_by('-end_date').first()
        
        irregular_evaluations = IrregularEvaluation.objects.filter(evaluatee=user)
        
        # Filter by the latest completed student period
        if latest_student_period:
            irregular_evaluations = irregular_evaluations.filter(evaluation_period=latest_student_period)
        
        evaluation_count = irregular_evaluations.count()
        
        if evaluation_count == 0:
            return {
                'has_data': False,
                'category_scores': [0, 0, 0, 0],
                'total_percentage': 0,
                'evaluation_count': 0
            }
        
        rating_to_numeric = {
            'Poor': 1, 'Unsatisfactory': 2, 'Satisfactory': 3, 
            'Very Satisfactory': 4, 'Outstanding': 5
        }
        
        total_category_a = total_category_b = total_category_c = total_category_d = 0
        total_count_a = total_count_b = total_count_c = total_count_d = 0
        
        for response in irregular_evaluations:
            for i in range(1, 7):
                question_key = f'question{i}'
                rating_text = getattr(response, question_key, 'Poor')
                score = rating_to_numeric.get(rating_text, 1)
                total_category_a += score
                total_count_a += 1

            for i in range(7, 13):
                question_key = f'question{i}'
                rating_text = getattr(response, question_key, 'Poor')
                score = rating_to_numeric.get(rating_text, 1)
                total_category_b += score
                total_count_b += 1

            for i in range(13, 17):
                question_key = f'question{i}'
                rating_text = getattr(response, question_key, 'Poor')
                score = rating_to_numeric.get(rating_text, 1)
                total_category_c += score
                total_count_c += 1

            for i in range(17, 20):
                question_key = f'question{i}'
                rating_text = getattr(response, question_key, 'Poor')
                score = rating_to_numeric.get(rating_text, 1)
                total_category_d += score
                total_count_d += 1
        
        max_score_per_question = 5
        a_weight = 0.35  # Mastery of Subject Matter
        b_weight = 0.25  # Classroom Management
        c_weight = 0.20  # Compliance to Policies
        d_weight = 0.20  # Personality
        
        def scaled_avg(total, count, weight):
            if count == 0:
                return 0.00
            average_score = total / count
            return (average_score / max_score_per_question) * weight * 100
        
        a_avg = scaled_avg(total_category_a, total_count_a, a_weight)
        b_avg = scaled_avg(total_category_b, total_count_b, b_weight)
        c_avg = scaled_avg(total_category_c, total_count_c, c_weight)
        d_avg = scaled_avg(total_category_d, total_count_d, d_weight)
        
        total_percentage = a_avg + b_avg + c_avg + d_avg
        
        irregular_comments = irregular_evaluations.filter(
            comments__isnull=False
        ).exclude(comments='').values_list('comments', flat=True)
        
        positive_comments = []
        negative_comments = []
        
        for comment in irregular_comments:
            sentiment = TeachingAIRecommendationService.analyze_comment_sentiment(comment)
            if sentiment == 'positive':
                positive_comments.append(comment)
            elif sentiment == 'negative':
                negative_comments.append(comment)
        
        return {
            'has_data': True,
            'category_scores': [round(a_avg, 2), round(b_avg, 2), round(c_avg, 2), round(d_avg, 2)],
            'total_percentage': round(total_percentage, 2),
            'evaluation_count': evaluation_count,
            'total_evaluations': evaluation_count,  # For template compatibility
            'positive_comments': positive_comments,
            'negative_comments': negative_comments
        }

@method_decorator(profile_settings_allowed, name='dispatch')    
class CoordinatorProfileSettingsView(View):
    
    def get(self, request):
        user = request.user
        if user.is_authenticated:
            try:
                index_url = reverse('main:index')
            except:
                index_url = '/'
            
            next_url = request.GET.get('next', request.META.get('HTTP_REFERER', index_url))
            
            if user.userprofile.role != 'Coordinator':
                return redirect(index_url)
            
            evaluation_data = self.get_evaluation_data(user)
            ai_recommendations = self.get_ai_recommendations(user)
            assigned_sections = self.get_assigned_sections(user)
            section_scores = self.get_section_scores(user, assigned_sections)
            
            # Get peer evaluation scores
            peer_scores = self.get_peer_evaluation_scores(user)
            
            # Get irregular student evaluation scores
            irregular_scores = self.get_irregular_evaluation_scores(user)
            
            # Convert to JSON for JavaScript
            import json
            section_scores_json = json.dumps(section_scores)
            # Convert to list to avoid queryset exhaustion
            assigned_sections_list = list(assigned_sections)
            section_map_json = json.dumps({assignment.section.id: assignment.section.code for assignment in assigned_sections_list})
            peer_scores_json = json.dumps(peer_scores)
            irregular_scores_json = json.dumps(irregular_scores)
            
            # Calculate overall statistics for the template
            total_sections = len(assigned_sections_list)
            sections_with_data = sum(1 for scores in section_scores.values() if scores['has_data'])
            total_evaluations = EvaluationResponse.objects.filter(evaluatee=user).count()

            evaluation_history = self.get_evaluation_history(user)
            
            # Get all sections and years for section assignment
            sections = Section.objects.all().order_by('year_level', 'code')
            years = list(Section.objects.values_list('year_level', flat=True).distinct().order_by('year_level'))
            currently_assigned_ids = [assignment.section.id for assignment in assigned_sections_list]
            
            # Add timestamp for cache busting
            import time
            timestamp = int(time.time())

            return render(request, 'main/coordinator_profile_settings.html', {
                'user': user,
                'next_url': next_url,
                'evaluation_data': evaluation_data,
                'ai_recommendations': ai_recommendations,
                'assigned_sections': assigned_sections_list,
                'section_scores': section_scores,
                'section_scores_json': section_scores_json,
                'section_map_json': section_map_json,
                'peer_scores': peer_scores,
                'peer_scores_json': peer_scores_json,
                'irregular_scores': irregular_scores,
                'irregular_scores_json': irregular_scores_json,
                'has_any_data': any(scores['has_data'] for scores in section_scores.values()),
                'total_sections': total_sections,
                'sections_with_data': sections_with_data,
                'total_evaluations': total_evaluations,
                'evaluation_period_ended': can_view_evaluation_results('student'),
                'evaluation_history': evaluation_history,
                'sections': sections,
                'years': years,
                'currently_assigned_ids': currently_assigned_ids,
                'timestamp': timestamp,
            })
        return redirect('login')
    
    def get_evaluation_history(self, user):
        """Get simplified evaluation history from EvaluationResponse records"""
        # Get all evaluation responses for this user - use submitted_at instead of created_at
        evaluations = EvaluationResponse.objects.filter(
            evaluatee=user
        ).select_related('evaluator').order_by('-submitted_at')
        
        history = []
        
        # Group evaluations by month for simplicity
        from collections import defaultdict
        
        monthly_data = defaultdict(lambda: {
            'period_name': '',
            'date': None,
            'total_responses': 0,
            'total_score': 0,
            'sections': set(),
            'comments': []
        })
        
        for eval_response in evaluations:
            # Group by month-year - use submitted_at instead of created_at
            month_key = eval_response.submitted_at.strftime('%B %Y')
            
            if not monthly_data[month_key]['period_name']:
                monthly_data[month_key]['period_name'] = f"{eval_response.submitted_at.strftime('%B %Y')} Evaluation"
                monthly_data[month_key]['date'] = eval_response.submitted_at
            
            monthly_data[month_key]['total_responses'] += 1
            monthly_data[month_key]['sections'].add(eval_response.student_section or 'Unknown Section')
            
            # Calculate average score for this evaluation
            rating_to_numeric = {
                'Poor': 1, 'Unsatisfactory': 2, 'Satisfactory': 3, 
                'Very Satisfactory': 4, 'Outstanding': 5
            }
            
            total_score = 0
            question_count = 0
            
            for i in range(1, 16):
                question_key = f'question{i}'
                rating_text = getattr(eval_response, question_key, 'Poor')
                score = rating_to_numeric.get(rating_text, 1)
                total_score += score
                question_count += 1
            
            average_score = (total_score / question_count) if question_count > 0 else 0
            monthly_data[month_key]['total_score'] += average_score
            
            # Collect comments
            if eval_response.comments:
                monthly_data[month_key]['comments'].append(eval_response.comments)
        
        # Convert to the format expected by the template
        for month_key, data in monthly_data.items():
            if data['total_responses'] > 0:
                average_score = data['total_score'] / data['total_responses']
                overall_percentage = (average_score / 5) * 100
                
                history.append({
                    'period_name': data['period_name'],
                    'date': data['date'],
                    'section': ', '.join(list(data['sections'])[:3]),  # Show up to 3 sections
                    'average_score': round(average_score, 2),
                    'overall_percentage': round(overall_percentage, 2),
                    'total_responses': data['total_responses'],
                    'comments': data['comments'][:5],  # Show up to 5 comments
                    'comments_count': len(data['comments']),
                    'category_scores': [0, 0, 0, 0],  # Placeholder - you can calculate these if needed
                    'category_percentages': [0, 0, 0, 0]  # Placeholder
                })
        
        # Sort by date descending
        history.sort(key=lambda x: x['date'], reverse=True)
        
        return history[:12]  # Return last 12 months max

    def post(self, request):
        user = request.user
        if user.is_authenticated:
            try:
                index_url = reverse('main:index')
            except:
                index_url = '/'
            
            next_url = request.POST.get('next', request.META.get('HTTP_REFERER', index_url))
            
            if user.userprofile.role != 'Coordinator':
                return redirect(index_url)

            # Check if this is a section assignment request
            action = request.POST.get('action')
            if action == 'assign_sections':
                selected_section_ids = request.POST.getlist('sections')
                
                # Delete existing section assignments for this user
                SectionAssignment.objects.filter(user=user).delete()
                
                # Create new section assignments
                sections_assigned = []
                for section_id in selected_section_ids:
                    try:
                        section = Section.objects.get(id=section_id)
                        SectionAssignment.objects.create(user=user, section=section)
                        sections_assigned.append(section.code)
                    except Section.DoesNotExist:
                        continue
                
                if len(sections_assigned) > 0:
                    sections_list = ", ".join(sections_assigned)
                    messages.success(request, f"✅ Successfully assigned {len(sections_assigned)} section(s): {sections_list}")
                else:
                    messages.success(request, f"✅ All section assignments have been removed.")
                return redirect('main:coordinator_profile_settings')

            # Handle profile update (existing code)
            username = request.POST.get("username")
            email = request.POST.get("email")
            new_password = request.POST.get("new_password1")
            confirm_password = request.POST.get("new_password2")

            # Email validation
            if not re.match(r"^[a-zA-Z0-9._%+-]+@(gmail\.com|cca\.edu\.ph)$", email):
                evaluation_data = self.get_evaluation_data(user)
                ai_recommendations = self.get_ai_recommendations(user)
                assigned_sections = self.get_assigned_sections(user)
                section_scores = self.get_section_scores(user, assigned_sections)
                
                # Calculate overall statistics for error context
                total_sections = assigned_sections.count()
                sections_with_data = sum(1 for scores in section_scores.values() if scores['has_data'])
                total_evaluations = EvaluationResponse.objects.filter(evaluatee=user).count()
                
                return render(request, 'main/coordinator_profile_settings.html', {
                    'user': user,
                    'next_url': next_url,
                    'evaluation_data': evaluation_data,
                    'ai_recommendations': ai_recommendations,
                    'assigned_sections': assigned_sections,
                    'section_scores': section_scores,
                    'total_sections': total_sections,
                    'sections_with_data': sections_with_data,
                    'total_evaluations': total_evaluations,
                    'error': 'Invalid email address. Please use an email ending with @gmail.com or @cca.edu.ph.'
                })

            # Password validation
            if new_password and new_password != confirm_password:
                evaluation_data = self.get_evaluation_data(user)
                ai_recommendations = self.get_ai_recommendations(user)
                assigned_sections = self.get_assigned_sections(user)
                section_scores = self.get_section_scores(user, assigned_sections)
                
                # Calculate overall statistics for error context
                total_sections = assigned_sections.count()
                sections_with_data = sum(1 for scores in section_scores.values() if scores['has_data'])
                total_evaluations = EvaluationResponse.objects.filter(evaluatee=user).count()
                
                return render(request, 'main/coordinator_profile_settings.html', {
                    'user': user,
                    'next_url': next_url,
                    'evaluation_data': evaluation_data,
                    'ai_recommendations': ai_recommendations,
                    'assigned_sections': assigned_sections,
                    'section_scores': section_scores,
                    'total_sections': total_sections,
                    'sections_with_data': sections_with_data,
                    'total_evaluations': total_evaluations,
                    'error': 'Passwords do not match.'
                })

            # Update user information
            user.username = username
            user.email = email

            if new_password:
                user.set_password(new_password)
                update_session_auth_hash(request, user)

            user.save()

            # Add success parameter to URL
            if "?" in next_url:
                next_url += "&updated=true"
            else:
                next_url += "?updated=true"

            messages.success(request, "Profile updated successfully.")
            return redirect(next_url)
        return redirect('login')
    
    def get_assigned_sections(self, user):
        """Get assigned sections for the coordinator"""
        return SectionAssignment.objects.filter(user=user)
    
    def get_section_scores(self, user, assigned_sections):
        """Get scores for each assigned section from EvaluationResult table"""
        from main.models import EvaluationResult
        section_scores = {}
        
        # Get the most recent INACTIVE period that has actually ended (not future periods)
        # Results are stored in EvaluationResult when period ends (unrelease)
        from django.utils import timezone
        latest_period = EvaluationPeriod.objects.filter(
            evaluation_type='student',
            is_active=False,
            end_date__lte=timezone.now()  # Only past periods
        ).order_by('-end_date').first()
        
        # Build unified list of sections: assigned + any sections actually evaluated (from results)
        assigned_section_objs = [a.section for a in assigned_sections]
        dynamic_result_sections = []
        if latest_period:
            dynamic_result_sections = [r.section for r in EvaluationResult.objects.filter(
                user=user,
                evaluation_period=latest_period
            ).select_related('section') if r.section and r.section not in assigned_section_objs]
        sections_to_display = assigned_section_objs + dynamic_result_sections

        for section in sections_to_display:
            section_code = section.code
            
            # Try to get pre-computed result from EvaluationResult table
            result = None
            if latest_period:
                try:
                    result = EvaluationResult.objects.get(
                        user=user,
                        section=section,
                        evaluation_period=latest_period
                    )
                except EvaluationResult.DoesNotExist:
                    pass
            
            if result:
                # Use pre-computed results from EvaluationResult table
                a_avg = result.category_a_score
                b_avg = result.category_b_score
                c_avg = result.category_c_score
                d_avg = result.category_d_score
                total_percentage = result.total_percentage
                evaluation_count = result.total_responses
                has_data = True
                
                # Get comments from the responses in this period
                comments_queryset = EvaluationResponse.objects.filter(
                    evaluatee=user,
                    student_section=section_code,
                    submitted_at__gte=latest_period.start_date,
                    submitted_at__lte=latest_period.end_date,
                    comments__isnull=False
                ).exclude(comments='').values_list('comments', flat=True)
            else:
                # No results yet - section has no data
                a_avg = b_avg = c_avg = d_avg = total_percentage = 0
                evaluation_count = 0
                has_data = False
                comments_queryset = []
            
            # Categorize comments using sentiment analysis
            positive_comments = []
            negative_comments = []
            mixed_comments = []
            
            for comment in comments_queryset:
                sentiment = TeachingAIRecommendationService.analyze_comment_sentiment(comment)
                if sentiment == 'positive':
                    positive_comments.append(comment)
                elif sentiment == 'negative':
                    negative_comments.append(comment)
                elif sentiment == 'mixed':
                    mixed_comments.append(comment)
            
            section_scores[section_code] = {
                'category_scores': [
                    round(a_avg, 2),
                    round(b_avg, 2),
                    round(c_avg, 2),
                    round(d_avg, 2)
                ],
                'total_percentage': round(total_percentage, 2),
                'has_data': has_data,
                'evaluation_count': evaluation_count,
                'section_name': section.code,
                'positive_comments': positive_comments,
                'negative_comments': negative_comments,
                'mixed_comments': mixed_comments
            }
        
        return section_scores

    
    def get_evaluation_data(self, user):
        # Get assigned sections for this coordinator
        assigned_sections = self.get_assigned_sections(user)
        
        # Calculate overall scores across all assigned sections
        total_category_a = total_category_b = total_category_c = total_category_d = 0
        total_count_a = total_count_b = total_count_c = total_count_d = 0
        total_responses = 0        # Get the most recent COMPLETED period (same as section scores)
        from django.utils import timezone
        latest_period = EvaluationPeriod.objects.filter(
            evaluation_type='student',
            is_active=False,
            end_date__lte=timezone.now()
        ).order_by('-end_date').first()
        
        for section_assignment in assigned_sections:
            section = section_assignment.section
            section_code = section.code
            
            # Calculate scores for this specific section
            category_scores = compute_category_scores(user, section_code, evaluation_period=latest_period)
            a_avg, b_avg, c_avg, d_avg, total_percentage, total_a, total_b, total_c, total_d = category_scores
            
            # Only include sections that have evaluations
            if total_percentage > 0:
                # For overall calculation, we need to accumulate totals and counts
                section_responses = EvaluationResponse.objects.filter(
                    evaluatee=user,
                    student_section=section_code
                )
                
                # Filter by completed period to match section scores
                if latest_period:
                    section_responses = section_responses.filter(evaluation_period=latest_period)
                
                if section_responses.exists():
                    total_responses += section_responses.count()
                    
                    # Recalculate raw totals for proper averaging
                    rating_to_numeric = {
                        'Poor': 1, 'Unsatisfactory': 2, 'Satisfactory': 3, 
                        'Very Satisfactory': 4, 'Outstanding': 5
                    }
                    
                    for response in section_responses:
                        # Category A: Questions 1-4 (Mastery of Subject Matter - 35%)
                        for i in range(1, 5):
                            question_key = f'question{i}'
                            rating_text = getattr(response, question_key, 'Poor')
                            score = rating_to_numeric.get(rating_text, 1)
                            total_category_a += score
                            total_count_a += 1

                        # Category B: Questions 5-8 (Classroom Management - 25%)
                        for i in range(5, 9):
                            question_key = f'question{i}'
                            rating_text = getattr(response, question_key, 'Poor')
                            score = rating_to_numeric.get(rating_text, 1)
                            total_category_b += score
                            total_count_b += 1

                        # Category C: Questions 9-12 (Compliance to Policies - 20%)
                        for i in range(9, 13):
                            question_key = f'question{i}'
                            rating_text = getattr(response, question_key, 'Poor')
                            score = rating_to_numeric.get(rating_text, 1)
                            total_category_c += score
                            total_count_c += 1

                        # Category D: Questions 13-15 (Personality - 20%)
                        for i in range(13, 16):
                            question_key = f'question{i}'
                            rating_text = getattr(response, question_key, 'Poor')
                            score = rating_to_numeric.get(rating_text, 1)
                            total_category_d += score
                            total_count_d += 1
        
        # CORRECTED: Use proper weights for 4 categories
        max_score_per_question = 5
        a_weight = 0.35  # Mastery of Subject Matter
        b_weight = 0.25  # Classroom Management
        c_weight = 0.20  # Compliance to Policies
        d_weight = 0.20  # Personality
        
        def scaled_avg(total, count, weight):
            if count == 0:
                return 0.00
            average_score = total / count
            return (average_score / max_score_per_question) * weight * 100
        
        a_avg = scaled_avg(total_category_a, total_count_a, a_weight)
        b_avg = scaled_avg(total_category_b, total_count_b, b_weight)
        c_avg = scaled_avg(total_category_c, total_count_c, c_weight)
        d_avg = scaled_avg(total_category_d, total_count_d, d_weight)
        
        total_percentage = a_avg + b_avg + c_avg + d_avg
        
        # FETCH COMMENTS FROM ALL SECTIONS FOR OVERALL VIEW
        # IMPORTANT: Only student evaluation comments from completed period
        comments_query = EvaluationResponse.objects.filter(
            evaluatee=user,
            comments__isnull=False
        ).exclude(comments='')
        
        # Filter by completed period to match section scores
        if latest_period:
            comments_query = comments_query.filter(evaluation_period=latest_period)
        
        all_comments = comments_query.values_list('comments', flat=True)
        
        # Categorize all comments using sentiment analysis
        positive_comments = []
        negative_comments = []
        mixed_comments = []
        
        for comment in all_comments:
            sentiment = TeachingAIRecommendationService.analyze_comment_sentiment(comment)
            if sentiment == 'positive':
                positive_comments.append(comment)
            elif sentiment == 'negative':
                negative_comments.append(comment)
            elif sentiment == 'mixed':
                mixed_comments.append(comment)
        
        # CORRECTED: Use proper max scores for percentage calculations
        max_scores = [35, 25, 20, 20]  # Updated to match category weights
        category_percentages = [
            round((a_avg / max_scores[0]) * 100, 2) if max_scores[0] > 0 else 0.00,
            round((b_avg / max_scores[1]) * 100, 2) if max_scores[1] > 0 else 0.00,
            round((c_avg / max_scores[2]) * 100, 2) if max_scores[2] > 0 else 0.00,
            round((d_avg / max_scores[3]) * 100, 2) if max_scores[3] > 0 else 0.00
        ]
        
        return {
            'has_data': total_responses > 0,
            'overall_score': round(total_percentage, 2) if total_percentage else 0.00,
            'category_scores': [
                round(a_avg, 2) if a_avg else 0.00,
                round(b_avg, 2) if b_avg else 0.00,
                round(c_avg, 2) if c_avg else 0.00,
                round(d_avg, 2) if d_avg else 0.00
            ],
            'category_percentages': category_percentages,
            'total_responses': total_responses,
            'positive_comments': positive_comments,
            'negative_comments': negative_comments,
            'mixed_comments': mixed_comments,
            'average_rating': round((total_category_a + total_category_b + total_category_c + total_category_d) / (total_responses * 15) * 5, 2) if total_responses > 0 else 0.00,
            'completion_rate': min(100.00, round(total_responses * 10, 2)),
            'improvement': 2.50,
            'rating_distribution': [2, 5, 12, 25, 40]
        }
    
    def get_ai_recommendations(self, user, section_data=None, section_code=None):
        """Get AI recommendations - retrieve saved ones for archived periods or generate new ones"""
        from main.models import AiRecommendation, EvaluationPeriod
        
        # Get the latest completed student period
        latest_student_period = EvaluationPeriod.objects.filter(
            evaluation_type='student',
            is_active=False
        ).order_by('-end_date').first()
        
        # Check if we have saved recommendations for this period and section
        if latest_student_period and section_code:
            saved_recs = AiRecommendation.objects.filter(
                user=user,
                evaluation_period=latest_student_period,
                section_code=section_code,
                evaluation_type='student'
            ).order_by('created_at')
            
            if saved_recs.exists():
                # Return saved recommendations
                return [
                    {
                        'title': rec.title,
                        'description': rec.description,
                        'priority': rec.priority,
                        'reason': rec.reason
                    }
                    for rec in saved_recs
                ]
        
        # Generate new recommendations if none saved
        ai_service = TeachingAIRecommendationService()
        recommendations = ai_service.get_recommendations(
            user=user,
            section_data=section_data,
            section_code=section_code,
            role="Coordinator"
        )
        
        # Save recommendations if we have a period and they're not already saved
        if latest_student_period and section_code and recommendations:
            for rec in recommendations:
                if isinstance(rec, dict):
                    AiRecommendation.objects.get_or_create(
                        user=user,
                        evaluation_period=latest_student_period,
                        section_code=section_code,
                        evaluation_type='student',
                        title=str(rec.get('title', '')[:255]),
                        defaults={
                            'description': rec.get('description', ''),
                            'priority': rec.get('priority', ''),
                            'reason': rec.get('reason', ''),
                            'recommendation': rec.get('description', '')
                        }
                    )
        
        return recommendations
    
    def get_peer_evaluation_scores(self, user):
        """Calculate peer evaluation scores (evaluations from other staff members)"""
        # Get the most recent INACTIVE peer period that has ended
        from django.utils import timezone
        latest_peer_period = EvaluationPeriod.objects.filter(
            evaluation_type='peer',
            is_active=False,
            end_date__lte=timezone.now()
        ).order_by('-end_date').first()
        
        # Peer evaluations are identified by having "Staff" in student_section field
        peer_evaluations = EvaluationResponse.objects.filter(
            evaluatee=user,
            student_section__icontains="Staff"
        )
        
        # Filter by the latest completed peer period
        if latest_peer_period:
            peer_evaluations = peer_evaluations.filter(evaluation_period=latest_peer_period)
        
        evaluation_count = peer_evaluations.count()
        
        if evaluation_count == 0:
            return {
                'has_data': False,
                'category_scores': [0, 0, 0, 0],
                'total_percentage': 0,
                'evaluation_count': 0
            }
        
        # Calculate scores from peer evaluations
        rating_to_numeric = {
            'Poor': 1, 'Unsatisfactory': 2, 'Satisfactory': 3, 
            'Very Satisfactory': 4, 'Outstanding': 5
        }
        
        total_score = 0
        total_count = 0
        
        for response in peer_evaluations:
            # Peer evaluations: Questions 1-15 (no categories, simple average)
            for i in range(1, 16):
                question_key = f'question{i}'
                rating_text = getattr(response, question_key, 'Poor')
                score = rating_to_numeric.get(rating_text, 1)
                total_score += score
                total_count += 1
        
        # Calculate simple average percentage
        if total_count > 0:
            average_score = total_score / total_count
            total_percentage = (average_score / 5) * 100
        else:
            total_percentage = 0
        
        # Fetch peer comments and categorize them
        peer_comments = peer_evaluations.filter(
            comments__isnull=False
        ).exclude(comments='').values_list('comments', flat=True)
        
        positive_comments = []
        negative_comments = []
        
        for comment in peer_comments:
            sentiment = TeachingAIRecommendationService.analyze_comment_sentiment(comment)
            if sentiment == 'positive':
                positive_comments.append(comment)
            elif sentiment == 'negative':
                negative_comments.append(comment)
        
        return {
            'has_data': True,
            'category_scores': [0, 0, 0, 0],  # Peer evaluations don't have categories
            'total_percentage': round(total_percentage, 2),
            'evaluation_count': evaluation_count,
            'total_evaluations': evaluation_count,  # For template compatibility
            'positive_comments': positive_comments,
            'negative_comments': negative_comments
        }
    
    def get_irregular_evaluation_scores(self, user):
        """Calculate irregular student evaluation scores"""
        # Get the most recent INACTIVE student period that has ended
        from django.utils import timezone
        latest_student_period = EvaluationPeriod.objects.filter(
            evaluation_type='student',
            is_active=False,
            end_date__lte=timezone.now()
        ).order_by('-end_date').first()
        
        irregular_evaluations = IrregularEvaluation.objects.filter(evaluatee=user)
        
        # Filter by the latest completed student period
        if latest_student_period:
            irregular_evaluations = irregular_evaluations.filter(evaluation_period=latest_student_period)
        
        evaluation_count = irregular_evaluations.count()
        
        if evaluation_count == 0:
            return {
                'has_data': False,
                'category_scores': [0, 0, 0, 0],
                'total_percentage': 0,
                'evaluation_count': 0
            }
        
        rating_to_numeric = {
            'Poor': 1, 'Unsatisfactory': 2, 'Satisfactory': 3, 
            'Very Satisfactory': 4, 'Outstanding': 5
        }
        
        total_category_a = total_category_b = total_category_c = total_category_d = 0
        total_count_a = total_count_b = total_count_c = total_count_d = 0
        
        for response in irregular_evaluations:
            for i in range(1, 7):
                question_key = f'question{i}'
                rating_text = getattr(response, question_key, 'Poor')
                score = rating_to_numeric.get(rating_text, 1)
                total_category_a += score
                total_count_a += 1

            for i in range(7, 13):
                question_key = f'question{i}'
                rating_text = getattr(response, question_key, 'Poor')
                score = rating_to_numeric.get(rating_text, 1)
                total_category_b += score
                total_count_b += 1

            for i in range(13, 17):
                question_key = f'question{i}'
                rating_text = getattr(response, question_key, 'Poor')
                score = rating_to_numeric.get(rating_text, 1)
                total_category_c += score
                total_count_c += 1

            for i in range(17, 20):
                question_key = f'question{i}'
                rating_text = getattr(response, question_key, 'Poor')
                score = rating_to_numeric.get(rating_text, 1)
                total_category_d += score
                total_count_d += 1
        
        max_score_per_question = 5
        a_weight = 0.35  # Mastery of Subject Matter
        b_weight = 0.25  # Classroom Management
        c_weight = 0.20  # Compliance to Policies
        d_weight = 0.20  # Personality
        
        def scaled_avg(total, count, weight):
            if count == 0:
                return 0.00
            average_score = total / count
            return (average_score / max_score_per_question) * weight * 100
        
        a_avg = scaled_avg(total_category_a, total_count_a, a_weight)
        b_avg = scaled_avg(total_category_b, total_count_b, b_weight)
        c_avg = scaled_avg(total_category_c, total_count_c, c_weight)
        d_avg = scaled_avg(total_category_d, total_count_d, d_weight)
        
        total_percentage = a_avg + b_avg + c_avg + d_avg
        
        irregular_comments = irregular_evaluations.filter(
            comments__isnull=False
        ).exclude(comments='').values_list('comments', flat=True)
        
        positive_comments = []
        negative_comments = []
        
        for comment in irregular_comments:
            sentiment = TeachingAIRecommendationService.analyze_comment_sentiment(comment)
            if sentiment == 'positive':
                positive_comments.append(comment)
            elif sentiment == 'negative':
                negative_comments.append(comment)
        
        return {
            'has_data': True,
            'category_scores': [round(a_avg, 2), round(b_avg, 2), round(c_avg, 2), round(d_avg, 2)],
            'total_percentage': round(total_percentage, 2),
            'evaluation_count': evaluation_count,
            'total_evaluations': evaluation_count,  # For template compatibility
            'positive_comments': positive_comments,
            'negative_comments': negative_comments
        }

@method_decorator(profile_settings_allowed, name='dispatch')        
class FacultyProfileSettingsView(View):

    
    def get(self, request):
        user = request.user
        if user.is_authenticated:
            try:
                index_url = reverse('main:index')
            except:
                index_url = '/'
            
            next_url = request.GET.get('next', request.META.get('HTTP_REFERER', index_url))
            
            if user.userprofile.role != 'Faculty':
                return redirect(index_url)
            
            # Get assigned sections for this faculty
            assigned_sections = self.get_assigned_sections(user)
            
            
            # Check if faculty has any assigned sections
            has_sections = assigned_sections.exists()
            
            # Get section scores and map
            section_scores = self.get_section_scores(user, assigned_sections) if has_sections else {}
            section_scores_json = json.dumps(section_scores)
            
            # Get peer evaluation scores
            peer_scores = self.get_peer_evaluation_scores(user)
            peer_scores_json = json.dumps(peer_scores)
            
            # Get irregular student evaluation scores
            irregular_scores = self.get_irregular_evaluation_scores(user)
            irregular_scores_json = json.dumps(irregular_scores)
            
            # Create section map for JavaScript
            section_map = {}
            if has_sections:
                for assignment in assigned_sections:
                    section_map[assignment.section.id] = assignment.section.code
            
            section_map_json = json.dumps(section_map)
            has_any_data = any(scores.get('has_data', False) for scores in section_scores.values()) if has_sections else False

            evaluation_history = self.get_evaluation_history(user)
            
            # Get all sections and years for section assignment
            sections = Section.objects.all().order_by('year_level', 'code')
            years = list(Section.objects.values_list('year_level', flat=True).distinct().order_by('year_level'))
            currently_assigned_ids = [assignment.section.id for assignment in assigned_sections]
            
            # Add timestamp for cache busting
            import time
            timestamp = int(time.time())

            return render(request, 'main/faculty_profile_settings.html', {
                'user': user,
                'next_url': next_url,
                'assigned_sections': assigned_sections,
                'section_scores': section_scores,
                'section_scores_json': section_scores_json,
                'section_map_json': section_map_json,
                'peer_scores': peer_scores,
                'peer_scores_json': peer_scores_json,
                'irregular_scores': irregular_scores,
                'irregular_scores_json': irregular_scores_json,
                'has_any_data': has_any_data,
                'has_sections': has_sections,
                'evaluation_period_ended': can_view_evaluation_results('student'),
                'evaluation_history': evaluation_history,
                'sections': sections,
                'years': years,
                'currently_assigned_ids': currently_assigned_ids,
                'timestamp': timestamp,
            })
        return redirect('login')

    def get_evaluation_history(self, user):
        """Get simplified evaluation history from EvaluationResponse records"""
        # Get all evaluation responses for this user - use submitted_at instead of created_at
        evaluations = EvaluationResponse.objects.filter(
            evaluatee=user
        ).select_related('evaluator').order_by('-submitted_at')
        
        history = []
        
        # Group evaluations by month for simplicity
        from collections import defaultdict
        
        monthly_data = defaultdict(lambda: {
            'period_name': '',
            'date': None,
            'total_responses': 0,
            'total_score': 0,
            'sections': set(),
            'comments': []
        })
        
        for eval_response in evaluations:
            # Group by month-year - use submitted_at instead of created_at
            month_key = eval_response.submitted_at.strftime('%B %Y')
            
            if not monthly_data[month_key]['period_name']:
                monthly_data[month_key]['period_name'] = f"{eval_response.submitted_at.strftime('%B %Y')} Evaluation"
                monthly_data[month_key]['date'] = eval_response.submitted_at
            
            monthly_data[month_key]['total_responses'] += 1
            monthly_data[month_key]['sections'].add(eval_response.student_section or 'Unknown Section')
            
            # Calculate average score for this evaluation
            rating_to_numeric = {
                'Poor': 1, 'Unsatisfactory': 2, 'Satisfactory': 3, 
                'Very Satisfactory': 4, 'Outstanding': 5
            }
            
            total_score = 0
            question_count = 0
            
            for i in range(1, 16):
                question_key = f'question{i}'
                rating_text = getattr(eval_response, question_key, 'Poor')
                score = rating_to_numeric.get(rating_text, 1)
                total_score += score
                question_count += 1
            
            average_score = (total_score / question_count) if question_count > 0 else 0
            monthly_data[month_key]['total_score'] += average_score
            
            # Collect comments
            if eval_response.comments:
                monthly_data[month_key]['comments'].append(eval_response.comments)
        
        # Convert to the format expected by the template
        for month_key, data in monthly_data.items():
            if data['total_responses'] > 0:
                average_score = data['total_score'] / data['total_responses']
                overall_percentage = (average_score / 5) * 100
                
                history.append({
                    'period_name': data['period_name'],
                    'date': data['date'],
                    'section': ', '.join(list(data['sections'])[:3]),  # Show up to 3 sections
                    'average_score': round(average_score, 2),
                    'overall_percentage': round(overall_percentage, 2),
                    'total_responses': data['total_responses'],
                    'comments': data['comments'][:5],  # Show up to 5 comments
                    'comments_count': len(data['comments']),
                    'category_scores': [0, 0, 0, 0],  # Placeholder - you can calculate these if needed
                    'category_percentages': [0, 0, 0, 0]  # Placeholder
                })
        
        # Sort by date descending
        history.sort(key=lambda x: x['date'], reverse=True)
        
        return history[:12]  # Return last 12 months max
    
    def get_assigned_sections(self, user):
        """Get assigned sections for the faculty"""
        return SectionAssignment.objects.filter(user=user)
    
    def get_section_scores(self, user, assigned_sections):
        """Get scores for each assigned section from EvaluationResult table"""
        from main.models import EvaluationResult
        section_scores = {}
        
        # Get the most recent INACTIVE period that has actually ended (not future periods)
        # Results are stored in EvaluationResult when period ends (unrelease)
        from django.utils import timezone
        latest_period = EvaluationPeriod.objects.filter(
            evaluation_type='student',
            is_active=False,
            end_date__lte=timezone.now()  # Only past periods
        ).order_by('-end_date').first()
        
        for section_assignment in assigned_sections:
            section = section_assignment.section
            section_code = section.code
            
            # Try to get pre-computed result from EvaluationResult table
            result = None
            if latest_period:
                try:
                    result = EvaluationResult.objects.get(
                        user=user,
                        section=section,
                        evaluation_period=latest_period
                    )
                except EvaluationResult.DoesNotExist:
                    pass
            
            if result:
                # Use pre-computed results from EvaluationResult table
                a_avg = result.category_a_score
                b_avg = result.category_b_score
                c_avg = result.category_c_score
                d_avg = result.category_d_score
                total_percentage = result.total_percentage
                evaluation_count = result.total_responses
                has_data = True
                
                # Get comments from the responses in this period
                comments_queryset = EvaluationResponse.objects.filter(
                    evaluatee=user,
                    student_section=section_code,
                    submitted_at__gte=latest_period.start_date,
                    submitted_at__lte=latest_period.end_date,
                    comments__isnull=False
                ).exclude(comments='').values_list('comments', flat=True)
            else:
                # No results yet - section has no data
                a_avg = b_avg = c_avg = d_avg = total_percentage = 0
                evaluation_count = 0
                has_data = False
                comments_queryset = []
            
            # Categorize comments using sentiment analysis
            positive_comments = []
            negative_comments = []
            mixed_comments = []
            
            for comment in comments_queryset:
                sentiment = TeachingAIRecommendationService.analyze_comment_sentiment(comment)
                if sentiment == 'positive':
                    positive_comments.append(comment)
                elif sentiment == 'negative':
                    negative_comments.append(comment)
                elif sentiment == 'mixed':
                    mixed_comments.append(comment)
            
            section_scores[section_code] = {
                'category_scores': [
                    round(a_avg, 2),
                    round(b_avg, 2),
                    round(c_avg, 2),
                    round(d_avg, 2)
                ],
                'total_percentage': round(total_percentage, 2),
                'has_data': has_data,
                'evaluation_count': evaluation_count,
                'section_name': section.code,
                'positive_comments': positive_comments,
                'negative_comments': negative_comments,
                'mixed_comments': mixed_comments
            }
        
        return section_scores

    
    def get_rating_distribution(self, user, section_code):
        """Get the actual rating distribution for a section"""
        # Get all responses for this section
        responses = EvaluationResponse.objects.filter(
            evaluatee=user,
            student_section=section_code
        )
        
        if not responses.exists():
            return [0, 0, 0, 0, 0]
        
        # Initialize counters for each rating level
        poor = 0
        unsatisfactory = 0
        satisfactory = 0
        very_satisfactory = 0
        outstanding = 0
        
        # Rating to numeric mapping for calculation
        rating_values = {
            'Poor': 1,
            'Unsatisfactory': 2, 
            'Satisfactory': 3,
            'Very Satisfactory': 4,
            'Outstanding': 5
        }
        
        # Count ratings across all questions and responses
        for response in responses:
            # Check all 15 questions
            for i in range(1, 16):
                question_key = f'question{i}'
                rating = getattr(response, question_key, 'Poor')
                
                # Convert rating to numeric and categorize
                numeric_rating = rating_values.get(rating, 1)
                if numeric_rating == 1:
                    poor += 1
                elif numeric_rating == 2:
                    unsatisfactory += 1
                elif numeric_rating == 3:
                    satisfactory += 1
                elif numeric_rating == 4:
                    very_satisfactory += 1
                elif numeric_rating == 5:
                    outstanding += 1
        
        # Return the distribution
        return [poor, unsatisfactory, satisfactory, very_satisfactory, outstanding]
    
    def get_evaluation_data(self, user):
        """Get evaluation data for the faculty - WITH SECTION FILTERING"""
        # Get assigned sections for this faculty
        assigned_sections = self.get_assigned_sections(user)
        
        # Calculate overall scores across all assigned sections
        total_category_a = total_category_b = total_category_c = total_category_d = 0
        total_count_a = total_count_b = total_count_c = total_count_d = 0
        total_responses = 0        # Get the most recent COMPLETED period (same as section scores)
        from django.utils import timezone
        latest_period = EvaluationPeriod.objects.filter(
            evaluation_type='student',
            is_active=False,
            end_date__lte=timezone.now()
        ).order_by('-end_date').first()
        
        # Initialize overall rating distribution
        overall_rating_distribution = [0, 0, 0, 0, 0]
        
        for section_assignment in assigned_sections:
            section = section_assignment.section
            section_code = section.code
            
            # Calculate scores for this specific section
            category_scores = compute_category_scores(user, section_code, evaluation_period=latest_period)
            a_avg, b_avg, c_avg, d_avg, total_percentage, total_a, total_b, total_c, total_d = category_scores
            
            # Only include sections that have evaluations
            if total_percentage > 0:
                # For overall calculation, we need to accumulate totals and counts
                # Since compute_category_scores returns weighted averages, we need to recalculate
                # Let's get the actual responses for this section to calculate properly
                section_responses = EvaluationResponse.objects.filter(
                    evaluatee=user,
                    student_section=section_code
                )
                
                # Filter by completed period to match section scores
                if latest_period:
                    section_responses = section_responses.filter(evaluation_period=latest_period)
                
                if section_responses.exists():
                    total_responses += section_responses.count()
                    
                    # Get section rating distribution and add to overall
                    section_distribution = self.get_rating_distribution(user, section_code)
                    for i in range(5):
                        overall_rating_distribution[i] += section_distribution[i]
                    
                    # Recalculate raw totals for proper averaging
                    rating_to_numeric = {
                        'Poor': 1, 'Unsatisfactory': 2, 'Satisfactory': 3, 
                        'Very Satisfactory': 4, 'Outstanding': 5
                    }
                    
                    for response in section_responses:
                        # Category A: Questions 1-4
                        for i in range(1, 5):
                            question_key = f'question{i}'
                            rating_text = getattr(response, question_key, 'Poor')
                            score = rating_to_numeric.get(rating_text, 1)
                            total_category_a += score
                            total_count_a += 1

                        # Category B: Questions 5-8
                        for i in range(5, 9):
                            question_key = f'question{i}'
                            rating_text = getattr(response, question_key, 'Poor')
                            score = rating_to_numeric.get(rating_text, 1)
                            total_category_b += score
                            total_count_b += 1

                        # Category C: Questions 9-12
                        for i in range(9, 13):
                            question_key = f'question{i}'
                            rating_text = getattr(response, question_key, 'Poor')
                            score = rating_to_numeric.get(rating_text, 1)
                            total_category_c += score
                            total_count_c += 1

                        # Category D: Questions 13-15
                        for i in range(13, 16):
                            question_key = f'question{i}'
                            rating_text = getattr(response, question_key, 'Poor')
                            score = rating_to_numeric.get(rating_text, 1)
                            total_category_d += score
                            total_count_d += 1
        
        # Compute weighted averages
        max_score_per_question = 5
        a_weight, b_weight, c_weight, d_weight = 0.25, 0.25, 0.25, 0.25
        
        def scaled_avg(total, count, weight):
            if count == 0:
                return 0
            average_score = total / count
            return (average_score / max_score_per_question) * weight * 100
        
        a_avg = scaled_avg(total_category_a, total_count_a, a_weight)
        b_avg = scaled_avg(total_category_b, total_count_b, b_weight)
        c_avg = scaled_avg(total_category_c, total_count_c, c_weight)
        d_avg = scaled_avg(total_category_d, total_count_d, d_weight)
        
        total_percentage = a_avg + b_avg + c_avg + d_avg
        
        # Calculate percentage of maximum for each category
        max_scores = [25, 25, 25, 25]
        category_percentages = [
            round((a_avg / max_scores[0]) * 100, 1) if max_scores[0] > 0 else 0,
            round((b_avg / max_scores[1]) * 100, 1) if max_scores[1] > 0 else 0,
            round((c_avg / max_scores[2]) * 100, 1) if max_scores[2] > 0 else 0,
            round((d_avg / max_scores[3]) * 100, 1) if max_scores[3] > 0 else 0
        ]
        
        # Calculate completion rate (you might want to adjust this based on your logic)
        completion_rate = min(100, total_responses * 2)  # Adjust this calculation as needed
        
        return {
            'has_data': total_responses > 0,
            'overall_score': round(total_percentage, 1),
            'category_scores': [round(a_avg, 1), round(b_avg, 1), round(c_avg, 1), round(d_avg, 1)],
            'category_percentages': category_percentages,
            'total_responses': total_responses,
            'average_rating': round((total_category_a + total_category_b + total_category_c + total_category_d) / (total_responses * 15) * 5, 1) if total_responses > 0 else 0,
            'completion_rate': completion_rate,
            'improvement': 2.5,  # This could be calculated by comparing with previous period
            'rating_distribution': overall_rating_distribution
        }
    
    def get_ai_recommendations(self, user, section_data=None, section_code=None):
        """Get AI recommendations - retrieve saved ones for archived periods or generate new ones"""
        from main.models import AiRecommendation, EvaluationPeriod
        
        # Get the latest completed student period
        latest_student_period = EvaluationPeriod.objects.filter(
            evaluation_type='student',
            is_active=False
        ).order_by('-end_date').first()
        
        # Check if we have saved recommendations for this period and section
        if latest_student_period and section_code:
            saved_recs = AiRecommendation.objects.filter(
                user=user,
                evaluation_period=latest_student_period,
                section_code=section_code,
                evaluation_type='student'
            ).order_by('created_at')
            
            if saved_recs.exists():
                # Return saved recommendations
                return [
                    {
                        'title': rec.title,
                        'description': rec.description,
                        'priority': rec.priority,
                        'reason': rec.reason
                    }
                    for rec in saved_recs
                ]
        
        # Generate new recommendations if none saved
        ai_service = TeachingAIRecommendationService()
        recommendations = ai_service.get_recommendations(
            user=user,
            section_data=section_data,
            section_code=section_code,
            role="Faculty"
        )
        
        # Save recommendations if we have a period and they're not already saved
        if latest_student_period and section_code and recommendations:
            for rec in recommendations:
                if isinstance(rec, dict):
                    AiRecommendation.objects.get_or_create(
                        user=user,
                        evaluation_period=latest_student_period,
                        section_code=section_code,
                        evaluation_type='student',
                        title=str(rec.get('title', '')[:255]),
                        defaults={
                            'description': rec.get('description', ''),
                            'priority': rec.get('priority', ''),
                            'reason': rec.get('reason', ''),
                            'recommendation': rec.get('description', '')
                        }
                    )
        
        return recommendations
    
    def get_peer_evaluation_scores(self, user):
        """Calculate peer evaluation scores (evaluations from other staff members)"""
        # Get the most recent INACTIVE peer period that has ended
        from django.utils import timezone
        latest_peer_period = EvaluationPeriod.objects.filter(
            evaluation_type='peer',
            is_active=False,
            end_date__lte=timezone.now()
        ).order_by('-end_date').first()
        
        # Peer evaluations are identified by having "Staff" in student_section field
        peer_evaluations = EvaluationResponse.objects.filter(
            evaluatee=user,
            student_section__icontains="Staff"
        )
        
        # Filter by the latest completed peer period
        if latest_peer_period:
            peer_evaluations = peer_evaluations.filter(evaluation_period=latest_peer_period)
        
        evaluation_count = peer_evaluations.count()
        
        if evaluation_count == 0:
            return {
                'has_data': False,
                'category_scores': [0, 0, 0, 0],
                'total_percentage': 0,
                'evaluation_count': 0
            }
        
        # Calculate scores from peer evaluations
        rating_to_numeric = {
            'Poor': 1, 'Unsatisfactory': 2, 'Satisfactory': 3, 
            'Very Satisfactory': 4, 'Outstanding': 5
        }
        
        total_score = 0
        total_count = 0
        
        for response in peer_evaluations:
            # Peer evaluations: Questions 1-15 (no categories, simple average)
            for i in range(1, 16):
                question_key = f'question{i}'
                rating_text = getattr(response, question_key, 'Poor')
                score = rating_to_numeric.get(rating_text, 1)
                total_score += score
                total_count += 1
        
        # Calculate simple average percentage
        if total_count > 0:
            average_score = total_score / total_count
            total_percentage = (average_score / 5) * 100
        else:
            total_percentage = 0
        
        # Fetch peer comments and categorize them
        peer_comments = peer_evaluations.filter(
            comments__isnull=False
        ).exclude(comments='').values_list('comments', flat=True)
        
        positive_comments = []
        negative_comments = []
        
        for comment in peer_comments:
            sentiment = TeachingAIRecommendationService.analyze_comment_sentiment(comment)
            if sentiment == 'positive':
                positive_comments.append(comment)
            elif sentiment == 'negative':
                negative_comments.append(comment)
        
        return {
            'has_data': True,
            'category_scores': [0, 0, 0, 0],  # Peer evaluations don't have categories
            'total_percentage': round(total_percentage, 2),
            'evaluation_count': evaluation_count,
            'total_evaluations': evaluation_count,  # For template compatibility
            'positive_comments': positive_comments,
            'negative_comments': negative_comments
        }
    
    def get_irregular_evaluation_scores(self, user):
        """Calculate irregular student evaluation scores"""
        # Query irregular evaluations for this user
        irregular_evaluations = IrregularEvaluation.objects.filter(evaluatee=user)
        
        evaluation_count = irregular_evaluations.count()
        
        if evaluation_count == 0:
            return {
                'has_data': False,
                'category_scores': [0, 0, 0, 0],
                'total_percentage': 0,
                'evaluation_count': 0
            }
        
        # Calculate scores (using same structure as student evaluations - 19 questions)
        rating_to_numeric = {
            'Poor': 1, 'Unsatisfactory': 2, 'Satisfactory': 3, 
            'Very Satisfactory': 4, 'Outstanding': 5
        }
        
        total_category_a = total_category_b = total_category_c = total_category_d = 0
        total_count_a = total_count_b = total_count_c = total_count_d = 0
        
        for response in irregular_evaluations:
            # Category A: Questions 1-6 (Mastery of Subject Matter - 30%)
            for i in range(1, 7):
                question_key = f'question{i}'
                rating_text = getattr(response, question_key, 'Poor')
                score = rating_to_numeric.get(rating_text, 1)
                total_category_a += score
                total_count_a += 1

            # Category B: Questions 7-12 (Classroom Management - 30%)
            for i in range(7, 13):
                question_key = f'question{i}'
                rating_text = getattr(response, question_key, 'Poor')
                score = rating_to_numeric.get(rating_text, 1)
                total_category_b += score
                total_count_b += 1

            # Category C: Questions 13-16 (Compliance to Policies - 20%)
            for i in range(13, 17):
                question_key = f'question{i}'
                rating_text = getattr(response, question_key, 'Poor')
                score = rating_to_numeric.get(rating_text, 1)
                total_category_c += score
                total_count_c += 1

            # Category D: Questions 17-19 (Personality - 20%)
            for i in range(17, 20):
                question_key = f'question{i}'
                rating_text = getattr(response, question_key, 'Poor')
                score = rating_to_numeric.get(rating_text, 1)
                total_category_d += score
                total_count_d += 1
        
        # Calculate weighted averages
        max_score_per_question = 5
        a_weight = 0.35  # Mastery of Subject Matter
        b_weight = 0.25  # Classroom Management
        c_weight = 0.20  # Compliance to Policies
        d_weight = 0.20  # Personality
        
        def scaled_avg(total, count, weight):
            if count == 0:
                return 0.00
            average_score = total / count
            return (average_score / max_score_per_question) * weight * 100
        
        a_avg = scaled_avg(total_category_a, total_count_a, a_weight)
        b_avg = scaled_avg(total_category_b, total_count_b, b_weight)
        c_avg = scaled_avg(total_category_c, total_count_c, c_weight)
        d_avg = scaled_avg(total_category_d, total_count_d, d_weight)
        
        total_percentage = a_avg + b_avg + c_avg + d_avg
        
        # Fetch irregular comments and categorize them
        irregular_comments = irregular_evaluations.filter(
            comments__isnull=False
        ).exclude(comments='').values_list('comments', flat=True)
        
        positive_comments = []
        negative_comments = []
        
        for comment in irregular_comments:
            sentiment = TeachingAIRecommendationService.analyze_comment_sentiment(comment)
            if sentiment == 'positive':
                positive_comments.append(comment)
            elif sentiment == 'negative':
                negative_comments.append(comment)
        
        return {
            'has_data': True,
            'category_scores': [round(a_avg, 2), round(b_avg, 2), round(c_avg, 2), round(d_avg, 2)],
            'total_percentage': round(total_percentage, 2),
            'evaluation_count': evaluation_count,
            'total_evaluations': evaluation_count,  # For template compatibility
            'positive_comments': positive_comments,
            'negative_comments': negative_comments
        }

    def post(self, request):
        """Handle POST requests for profile updates and section assignments"""
        user = request.user
        if not user.is_authenticated:
            return redirect('/login')

        try:
            user_profile = UserProfile.objects.get(user=user)
            
            if user_profile.role != 'Faculty':
                return HttpResponseForbidden("You do not have permission to access this page.")

            try:
                index_url = reverse('main:index')
            except:
                index_url = '/'
            
            next_url = request.POST.get('next', request.META.get('HTTP_REFERER', index_url))

            # Check if this is a section assignment request
            action = request.POST.get('action')
            if action == 'assign_sections':
                selected_section_ids = request.POST.getlist('sections')
                
                # Delete existing section assignments for this user
                SectionAssignment.objects.filter(user=user).delete()
                
                # Create new section assignments
                sections_assigned = []
                for section_id in selected_section_ids:
                    try:
                        section = Section.objects.get(id=section_id)
                        SectionAssignment.objects.create(user=user, section=section)
                        sections_assigned.append(section.code)
                    except Section.DoesNotExist:
                        continue
                
                if len(sections_assigned) > 0:
                    sections_list = ", ".join(sections_assigned)
                    messages.success(request, f"✅ Successfully assigned {len(sections_assigned)} section(s): {sections_list}")
                else:
                    messages.success(request, f"✅ All section assignments have been removed.")
                return redirect('main:faculty_profile_settings')

            # Handle profile update (existing code)
            username = request.POST.get("username")
            email = request.POST.get("email")
            new_password = request.POST.get("new_password1")
            confirm_password = request.POST.get("new_password2")

            # Email validation
            if not re.match(r"^[a-zA-Z0-9._%+-]+@(gmail\.com|cca\.edu\.ph)$", email):
                # Rebuild the context for error display
                assigned_sections = self.get_assigned_sections(user)
                section_scores = self.get_section_scores(user, assigned_sections) if assigned_sections.exists() else {}
                
                context = self._build_context(user, assigned_sections, section_scores)
                context['error'] = 'Invalid email address. Please use an email ending with @gmail.com or @cca.edu.ph.'
                context['next_url'] = next_url
                
                return render(request, 'main/faculty_profile_settings.html', context)

            # Password validation
            if new_password and new_password != confirm_password:
                assigned_sections = self.get_assigned_sections(user)
                section_scores = self.get_section_scores(user, assigned_sections) if assigned_sections.exists() else {}
                
                context = self._build_context(user, assigned_sections, section_scores)
                context['error'] = 'Passwords do not match.'
                context['next_url'] = next_url
                
                return render(request, 'main/faculty_profile_settings.html', context)

            # Update user information
            user.username = username
            user.email = email

            if new_password:
                user.set_password(new_password)
                update_session_auth_hash(request, user)

            user.save()

            # Add success parameter to URL
            if "?" in next_url:
                next_url += "&updated=true"
            else:
                next_url += "?updated=true"

            messages.success(request, "Profile updated successfully.")
            return redirect(next_url)
            
        except UserProfile.DoesNotExist:
            return redirect('/login')

    def _build_context(self, user, assigned_sections, section_scores):
        """Helper method to build context for template"""
        has_sections = assigned_sections.exists()
        
        # Create section map for JavaScript
        section_map = {}
        if has_sections:
            for assignment in assigned_sections:
                section_map[assignment.section.id] = assignment.section.code
        
        return {
            'user': user,
            'assigned_sections': assigned_sections,
            'section_scores': section_scores,
            'section_scores_json': json.dumps(section_scores),
            'section_map_json': json.dumps(section_map),
            'evaluation_data': self.get_evaluation_data(user),
            'ai_recommendations': self.get_ai_recommendations(user),
            'has_any_data': any(scores.get('has_data', False) for scores in section_scores.values()) if has_sections else False,
            'has_sections': has_sections
        }
    

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .models import Section, SectionAssignment

def assign_section(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile_user = user.userprofile

    if request.method == "POST":
        # Get multiple section IDs
        section_ids = request.POST.getlist("sections")
        
        assigned_sections_list = []
        for section_id in section_ids:
            if section_id:  # Skip empty values
                section = get_object_or_404(Section, id=section_id)
                assigned_sections_list.append(section.code)
                
                if profile_user.role == "Student":
                    # Store old section for comparison
                    old_section = profile_user.section
                    
                    # ✅ DELETE EVALUATIONS IF SECTION IS CHANGING
                    if old_section and old_section != section:
                        
                        
                        # Delete evaluations where this student is the EVALUATOR (submitted evaluations)
                        evaluations_as_evaluator = EvaluationResponse.objects.filter(
                            evaluator=user
                        )
                        evaluator_count = evaluations_as_evaluator.count()
                        
                        # Delete evaluations where this student is the EVALUATEE (evaluations about them)
                        evaluations_as_evaluatee = EvaluationResponse.objects.filter(
                            evaluatee=user
                        )
                        evaluatee_count = evaluations_as_evaluatee.count()
                        
                        # Delete all evaluations
                        total_deleted = evaluator_count + evaluatee_count
                        evaluations_as_evaluator.delete()
                        evaluations_as_evaluatee.delete()
                        
                    
                    # Students still get single section
                    profile_user.section = section
                    profile_user.save()
                else:
                    # Staff get multiple sections
                    SectionAssignment.objects.get_or_create(
                        user=user,
                        section=section,
                        role=profile_user.role.lower()
                    )
        
        # Log admin activity
        if assigned_sections_list:
            log_admin_activity(
                request=request,
                action='assign_section',
                description=f"Assigned section(s) {', '.join(assigned_sections_list)} to {user.username} ({profile_user.role})",
                target_user=user
            )

        next_url = request.POST.get('next', reverse('main:index'))
        return redirect(next_url + ("&" if "?" in next_url else "?") + "updated=true")

    # Handle GET
    if profile_user.role == "Student":
        sections = Section.objects.all()
    else:
        sections = Section.objects.all()
        # Get currently assigned sections
        assigned_sections = SectionAssignment.objects.filter(user=user)
        currently_assigned_ids = assigned_sections.values_list('section_id', flat=True)

    years = [1, 2, 3, 4]
    next_url = request.GET.get('next', request.META.get('HTTP_REFERER', reverse('main:index')))

    context = {
        "target_user_profile": profile_user,
        "sections": sections,
        "years": years,
        "next_url": next_url,
    }
    
    # Add assigned sections info for staff
    if profile_user.role != "Student":
        context["assigned_sections"] = assigned_sections
        context["currently_assigned_ids"] = list(currently_assigned_ids)

    return render(request, "main/update.html", context)


def remove_section_assignment(request, assignment_id):
    """Remove a section assignment via AJAX and delete associated evaluation responses"""
    if request.method == 'POST':
        try:
            # Get the assignment
            assignment = SectionAssignment.objects.get(id=assignment_id)
            user = assignment.user
            section = assignment.section
            
            # Optional: Check if the current user has permission to remove this assignment
            # For example, only allow admin or the user themselves to remove assignments
            if not (request.user.is_superuser or request.user == assignment.user):
                return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
            
            # ✅ DELETE EVALUATION RESPONSES FOR THIS USER IN THE ASSIGNED SECTION
            section_code = assignment.section.code
            
            # Delete evaluations where this user is the EVALUATEE (evaluations about them)
            evaluations_as_evaluatee = EvaluationResponse.objects.filter(
                evaluatee=user,
                student_section=section_code
            )
            evaluatee_count = evaluations_as_evaluatee.count()
            evaluations_as_evaluatee.delete()
            
            # Delete evaluations where this user is the EVALUATOR (evaluations they submitted)
            evaluations_as_evaluator = EvaluationResponse.objects.filter(
                evaluator=user,
                student_section=section_code
            )
            evaluator_count = evaluations_as_evaluator.count()
            evaluations_as_evaluator.delete()
            
            # Log admin activity
            log_admin_activity(
                request=request,
                action='remove_section',
                description=f"Removed section {section.code} from {user.username}",
                target_user=user,
                target_section=section
            )
            
            # Delete the section assignment
            assignment.delete()
            
            # Return success with deletion details
            return JsonResponse({
                'success': True,
                'message': f'Section assignment removed successfully. Deleted {evaluatee_count} evaluations received and {evaluator_count} evaluations submitted in this section.',
                'deleted_evaluatee_count': evaluatee_count,
                'deleted_evaluator_count': evaluator_count
            })
            
        except SectionAssignment.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Section assignment not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)
    
@method_decorator(csrf_exempt, name='dispatch')
class AIRecommendationsAPIView(View):
    """
    Shared AI recommendations API for all user roles
    """
    def post(self, request):
        try:
            user = request.user
            if not user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            data = json.loads(request.body)
            section_data = data.get('section_data', {})
            section_code = data.get('section_code', 'Overall')
            is_overall = data.get('is_overall', False)
            evaluation_type = data.get('evaluation_type', 'student')  # ADD THIS LINE
            role = data.get('role', getattr(user, 'userprofile', None) and user.userprofile.role or 'Educator')
            period_id = data.get('period_id')
            
            print(f"🔍 API RECEIVED - Evaluation Type: {evaluation_type}")  # DEBUG LOG
            
            # Validate section_data structure
            if section_data and not isinstance(section_data, dict):
                section_data = {}
            
            # Get AI recommendations using the shared service
            ai_service = TeachingAIRecommendationService()
            recommendations = ai_service.get_recommendations(
                user=user,
                section_data=section_data,
                section_code=section_code,
                role=role,
                evaluation_type=evaluation_type  # PASS IT TO THE SERVICE
            )

            # Optionally persist recommendations for a specific period
            if period_id:
                try:
                    period = EvaluationPeriod.objects.get(id=period_id)
                    # Refresh saved recommendations for this user+period to avoid duplicates
                    AiRecommendation.objects.filter(user=user, evaluation_period=period).delete()
                    # Save each recommendation item
                    for rec in (recommendations or []):
                        AiRecommendation.objects.create(
                            user=user,
                            evaluation_period=period,
                            title=str(rec.get('title', '')[:255]) if isinstance(rec, dict) else '',
                            description=rec.get('description', '') if isinstance(rec, dict) else (str(rec) if rec else ''),
                            priority=rec.get('priority', '') if isinstance(rec, dict) else '',
                            reason=rec.get('reason', '') if isinstance(rec, dict) else '',
                            recommendation=rec.get('description', '') if isinstance(rec, dict) else (str(rec) if rec else ''),
                            evaluation_type=evaluation_type,
                            section_code=section_code if section_code and section_code != 'Overall' else None
                        )
                except EvaluationPeriod.DoesNotExist:
                    pass
            
            # Add request metadata to response for debugging
            response_data = {
                'recommendations': recommendations,
                'metadata': {
                    'section_code': section_code,
                    'role': role,
                    'evaluation_type': evaluation_type,  # INCLUDE IN RESPONSE
                    'is_overall': is_overall,
                    'timestamp': time.time(),
                    'has_section_data': bool(section_data and section_data.get('has_data'))
                }
            }
            
            print(f"✅ API RESPONSE - Evaluation Type: {evaluation_type}")  # DEBUG LOG
            
            # Create response with no-cache headers
            response = JsonResponse(response_data, safe=False)
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
            return response
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON Error: {e}")
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            print(f"❌ API Error: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': f'Failed to generate recommendations: {str(e)}'}, status=500)


class StudentCommentsAPIView(View):
    """
    API to fetch student comments for a section
    Comments are anonymous - no student name or section displayed
    """
    @method_decorator(login_required(login_url='login'))
    def post(self, request):
        try:
            user = request.user
            if not user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            # Check if user is faculty, coordinator, or dean
            try:
                user_profile = UserProfile.objects.get(user=user)
                if user_profile.role not in [Role.FACULTY, Role.COORDINATOR, Role.DEAN]:
                    return JsonResponse({'error': 'Only faculty, coordinators, and deans can view comments'}, status=403)
            except UserProfile.DoesNotExist:
                return JsonResponse({'error': 'User profile not found'}, status=403)
            
            data = json.loads(request.body)
            section_id = data.get('section_id')
            section_code = data.get('section_code')
            
            print(f"\n{'='*60}")
            print(f"🔍 StudentCommentsAPIView - Fetching comments")
            print(f"   User: {user.username}")
            print(f"   Role: {user_profile.role}")
            print(f"   Section Code: {section_code}")
            print(f"   Section ID: {section_id}")
            print(f"{'='*60}")
            
            comments = []
            
            if section_id == 'overall' or section_id == 'peer':
                # For overall/peer, get ALL comments TO this user
                # Dean/Coordinator/Faculty are being evaluated BY students
                
                # Regular student evaluations
                evaluation_responses = EvaluationResponse.objects.filter(
                    evaluatee=user,
                    comments__isnull=False
                ).exclude(comments='')
                
                # Irregular student evaluations
                irregular_responses = IrregularEvaluation.objects.filter(
                    evaluatee=user,
                    comments__isnull=False
                ).exclude(comments='')
                
            else:
                # For a specific section, get comments FROM students about their experience
                try:
                    section_id = int(section_id)
                    section = Section.objects.get(id=section_id)
                    
                    # Get all students in this section (regular students only)
                    students_in_section = User.objects.filter(
                        userprofile__section=section
                    ).values_list('id', flat=True)
                    
                    # Get evaluation responses where:
                    # - evaluator is a student in that section
                    # - evaluatee is the faculty member being evaluated
                    # - they left a comment
                    # For faculty: evaluatee is themselves
                    # For coordinator/dean: evaluatee is any faculty in their purview
                    
                    if user_profile.role == Role.FACULTY:
                        # Faculty sees comments FROM students in their section about them
                        evaluation_responses = EvaluationResponse.objects.filter(
                            evaluatee=user,
                            evaluator_id__in=students_in_section,
                            comments__isnull=False
                        ).exclude(comments='').distinct()
                    else:
                        # Coordinator/Dean sees comments from students in section about any faculty
                        evaluation_responses = EvaluationResponse.objects.filter(
                            evaluator_id__in=students_in_section,
                            evaluatee__userprofile__section=section,
                            comments__isnull=False
                        ).exclude(comments='').distinct()
                    
                    # ALSO include irregular student evaluations for this faculty
                    # Irregular students don't have a section but can evaluate any instructor
                    irregular_responses = IrregularEvaluation.objects.filter(
                        evaluatee=user,
                        comments__isnull=False
                    ).exclude(comments='').distinct()
                    
                except (ValueError, Section.DoesNotExist) as e:
                    print(f"❌ Section Error: {e}")
                    evaluation_responses = EvaluationResponse.objects.none()
                    irregular_responses = IrregularEvaluation.objects.none()
            
            # Extract comments from regular evaluations
            for response in evaluation_responses:
                if response.comments and response.comments.strip():
                    comments.append(response.comments.strip())
            
            # Extract comments from irregular student evaluations
            for response in irregular_responses:
                if response.comments and response.comments.strip():
                    comments.append(response.comments.strip())
            
            print(f"   Total regular evaluation responses: {evaluation_responses.count()}")
            print(f"   Total irregular evaluation responses: {irregular_responses.count()}")
            print(f"   Comments extracted: {len(comments)}")
            if comments:
                for idx, comment in enumerate(comments, 1):
                    print(f"     {idx}. {comment[:60]}...")
            print(f"{'='*60}\n")
            
            # Create response
            response_data = {
                'comments': comments,
                'total_comments': len(comments),
                'section_code': section_code,
                'metadata': {
                    'timestamp': time.time(),
                }
            }
            
            # Create response with no-cache headers
            response = JsonResponse(response_data, safe=False)
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
            return response
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON Error: {e}")
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            print(f"❌ API Error: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': f'Failed to fetch comments: {str(e)}'}, status=500)

        
@login_required
def admin_evaluation_control(request):
    if not request.user.is_superuser:
        return redirect('main:index')
    
    from .services.evaluation_service import EvaluationService
    
    evaluation_status = EvaluationService.get_evaluation_status()
    staff_stats = []
    
    staff_users = User.objects.filter(userprofile__role__in=['Faculty', 'Coordinator', 'Dean'])
    for user in staff_users:
        stats = EvaluationService.get_user_failure_stats(user)
        staff_stats.append({
            'user': user,
            'stats': stats
        })
    
    context = {
        'evaluation_status': evaluation_status,
        'staff_stats': staff_stats,
    }
    return render(request, 'main/admin_control.html', context)

@login_required
def manage_evaluations(request):
    """View for managing evaluation periods - release/unrelease student, peer, and upward evaluations"""
    if not request.user.is_superuser:
        return redirect('main:index')
    
    from django.utils import timezone
    
    # Check for active student evaluation period
    student_period = EvaluationPeriod.objects.filter(
        evaluation_type='student',
        is_active=True
    ).first()
    
    # Check for active peer evaluation period
    peer_period = EvaluationPeriod.objects.filter(
        evaluation_type='peer',
        is_active=True
    ).first()
    
    # Check for active upward evaluation period
    upward_period = EvaluationPeriod.objects.filter(
        evaluation_type='upward',
        is_active=True
    ).first()
    
    context = {
        'student_active': student_period is not None,
        'student_period_name': student_period.name if student_period else None,
        'student_period_start': student_period.start_date if student_period else None,
        'peer_active': peer_period is not None,
        'peer_period_name': peer_period.name if peer_period else None,
        'peer_period_start': peer_period.start_date if peer_period else None,
        'upward_active': upward_period is not None,
        'upward_period_name': upward_period.name if upward_period else None,
        'upward_period_start': upward_period.start_date if upward_period else None,
    }
    
    return render(request, 'main/manage_evaluations.html', context)

@login_required
def admin_activity_logs(request):
    """Dedicated view for admin activity logs"""
    if not request.user.is_superuser:
        return redirect('main:index')
    
    # Get recent admin activity logs with pagination
    from django.core.paginator import Paginator
    
    all_activities = AdminActivityLog.objects.all()
    paginator = Paginator(all_activities, 50)  # Show 50 per page
    
    page_number = request.GET.get('page', 1)
    activities = paginator.get_page(page_number)
    
    # Get statistics
    total_logs = all_activities.count()
    action_stats = {}
    for value, label in AdminActivityLog.ACTION_CHOICES:
        count = all_activities.filter(action=value).count()
        if count > 0:
            action_stats[label] = count
    
    # Calculate next log deletion date (next Sunday midnight or 7 days from now, whichever is sooner)
    from django.utils import timezone as dj_timezone
    import datetime
    now = dj_timezone.now()
    # Next Sunday midnight
    days_ahead = 6 - now.weekday()  # 0=Monday, 6=Sunday
    if days_ahead < 0:
        days_ahead += 7
    next_sunday = (now + datetime.timedelta(days=days_ahead)).replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
    # 7 days from now
    seven_days = now + datetime.timedelta(days=7)
    # Use the sooner of the two
    next_deletion = min(next_sunday, seven_days)
    context = {
        'activities': activities,
        'total_logs': total_logs,
        'action_stats': action_stats,
        'next_log_deletion': next_deletion,
    }
    return render(request, 'main/activity_logs.html', context)

def manage_institutes_courses(request):
    """View for managing institutes and courses"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('main:index')
    return render(request, 'main/manage_institutes_courses.html')

def reset_failures(request):
    if request.method == 'POST':
        success = EvaluationService.reset_failures()
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'All failure counts and logs have been reset successfully.'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to reset failures'
            })
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request'
    })

def reset_selected_failures(request):
    if request.method == 'POST':
        selected_users = request.POST.get('selected_users', '')
        
        if not selected_users:
            messages.error(request, 'No users selected.')
            return redirect('main:admin_control')
        
        try:
            user_ids = [int(id) for id in selected_users.split(',') if id.strip()]
            
            # Reset selected users
            reset_count = UserProfile.objects.filter(user_id__in=user_ids).update(
                evaluation_failure_count=0,
                failure_alert_sent=False,
                last_evaluation_failure_date=None
            )
            
            messages.success(request, f'Successfully reset failure counts for {reset_count} user(s).')
            
        except Exception as e:
            messages.error(request, f'Error resetting selected users: {str(e)}')
    
    return redirect('main:admin_control')

from django.utils import timezone

from django.utils import timezone

class EvaluationHistoryView(View):
    @method_decorator(login_required)
    def get(self, request):
        user = request.user
        
        try:
            user_profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return redirect('main:index')
        
        # Group evaluations by period (combine student and peer from same period)
        from collections import defaultdict
        periods_dict = defaultdict(lambda: {
            'period_name': '',
            'period_id': None,
            'start_date': None,
            'end_date': None,
            'student_count': 0,
            'peer_count': 0,
            'irregular_count': 0,
            'overall_score': 0,
            'total_responses': 0
        })
        
        # Get all completed/inactive periods for this user
        # Only show periods that actually exist in database and have responses
        from django.db import models
        completed_periods = EvaluationPeriod.objects.filter(
            is_active=False
        ).filter(
            models.Q(evaluationresponse__evaluatee=user) | 
            models.Q(irregularevaluation__evaluatee=user)
        ).distinct().order_by('-created_at')  # Order by creation time to get latest first
        
        evaluation_history = []
        rating_values = {'Poor': 1, 'Unsatisfactory': 2, 'Satisfactory': 3, 'Very Satisfactory': 4, 'Outstanding': 5}
        
        # Group periods by timestamp - combine "Student Evaluation" and "Peer Evaluation" with same timestamp
        import re
        from collections import defaultdict
        timestamp_groups = defaultdict(list)
        
        for period in completed_periods:
            # Extract timestamp pattern from period name to group related periods
            # Match patterns like "December 02, 2025 19:36" or "December 2025"
            timestamp_match = re.search(r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}(?:\s+\d{1,2}:\d{2})?)', period.name)
            
            if timestamp_match:
                timestamp_key = timestamp_match.group(1)
            else:
                # If no timestamp, use full name as key
                timestamp_key = period.name
            
            # Group all periods with same timestamp together
            timestamp_groups[timestamp_key].append(period)
        
        # Process each timestamp group - ONE entry per timestamp combining ALL evaluation types from all related periods
        for timestamp_key, periods_in_group in timestamp_groups.items():
            # Get the representative period (first one) for display info
            representative_period = periods_in_group[0]
            
            # Collect ALL responses from ALL periods in this timestamp group
            all_period_ids = [p.id for p in periods_in_group]
            # Get ALL evaluations across ALL periods in this group (student, irregular, peer)
            regular_responses = EvaluationResponse.objects.filter(
                evaluatee=user,
                evaluation_period__id__in=all_period_ids
            ).exclude(evaluator__userprofile__role__in=[Role.FACULTY, Role.COORDINATOR, Role.DEAN])
            
            irregular_responses = IrregularEvaluation.objects.filter(
                evaluatee=user,
                evaluation_period__id__in=all_period_ids
            )
            
            peer_responses = EvaluationResponse.objects.filter(
                evaluatee=user,
                evaluation_period__id__in=all_period_ids,
                evaluator__userprofile__role__in=[Role.FACULTY, Role.COORDINATOR, Role.DEAN]
            )
            
            # Calculate combined average score
            all_scores = []
            
            # Regular student scores (19 questions)
            for response in regular_responses:
                total = 0
                count = 0
                for i in range(1, 20):
                    rating = getattr(response, f'question{i}', None)
                    if rating and rating in rating_values:
                        total += rating_values[rating]
                        count += 1
                if count > 0:
                    all_scores.append((total / (count * 5)) * 100)
            
            # Irregular scores (19 questions)
            for response in irregular_responses:
                total = 0
                count = 0
                for i in range(1, 20):
                    rating = getattr(response, f'question{i}', None)
                    if rating and rating in rating_values:
                        total += rating_values[rating]
                        count += 1
                if count > 0:
                    all_scores.append((total / (count * 5)) * 100)
            
            # Peer scores (15 questions)
            for response in peer_responses:
                total = 0
                count = 0
                for i in range(1, 16):
                    rating = getattr(response, f'question{i}', None)
                    if rating and rating in rating_values:
                        total += rating_values[rating]
                        count += 1
                if count > 0:
                    all_scores.append((total / (count * 5)) * 100)
            
            # Skip if no evaluations
            if not all_scores:
                continue
            
            overall_score = sum(all_scores) / len(all_scores)
            total_responses = len(all_scores)
            
            # Create clean display name without type prefix
            display_name = re.sub(r'^(Student|Peer|Irregular)\s+Evaluation\s+', 'Evaluation Period ', representative_period.name)
            
            evaluation_history.append({
                'period_name': display_name,
                'evaluation_period_id': representative_period.id,
                'period_start_date': representative_period.start_date,
                'period_end_date': representative_period.end_date,
                'overall_percentage': overall_score,
                'total_responses': total_responses,
                'student_responses': regular_responses.count(),
                'irregular_responses': irregular_responses.count(),
                'peer_responses': peer_responses.count(),
                'all_period_ids': all_period_ids  # Store all period IDs for PDF generation
            })
        
        # Calculate summary statistics
        total_evaluations = len(evaluation_history)
        average_percentage = sum([eval['overall_percentage'] for eval in evaluation_history]) / total_evaluations if total_evaluations > 0 else 0
        latest_score = evaluation_history[0]['overall_percentage'] if total_evaluations > 0 else 0
        
        # Get user's assigned sections for all roles (for display purposes)
        from main.models import SectionAssignment
        assigned_sections_qs = SectionAssignment.objects.filter(user=user).select_related('section')
        user_sections = [{'id': a.section.id, 'code': a.section.code, 'name': str(a.section)} for a in assigned_sections_qs]
        
        context = {
            'user_profile': user_profile,
            'evaluation_history': evaluation_history,
            'total_evaluations': total_evaluations,
            'average_percentage': round(average_percentage, 2),
            'latest_score': round(latest_score, 2),
            'page_title': 'Evaluation History',
            'evaluation_period_active': Evaluation.is_evaluation_period_active('student'),
            'user_sections': user_sections
        }
        
        return render(request, 'main/evaluation_history_simple.html', context)
    
def process_evaluation_results_for_user(user, evaluation_period=None):
    """
    Process evaluation responses and create/update EvaluationResult records for a specific user
    CRITICAL: Only processes responses within the specified period's date range
    Handles both student evaluations (with categories) and peer evaluations (simple average)
    """
    from django.utils import timezone
    
    # If no evaluation period provided, use the latest completed one
    if not evaluation_period:
        evaluation_period = EvaluationPeriod.objects.filter(
            is_active=False,
            evaluation_type='student'
        ).order_by('-end_date').first()
    
    if not evaluation_period:
        # Create a new evaluation period if none exists
        evaluation_period = EvaluationPeriod.objects.create(
            name=f"Evaluation {timezone.now().strftime('%Y-%m')}",
            evaluation_type='student',
            start_date=timezone.now() - timezone.timedelta(days=30),
            end_date=timezone.now(),
            is_active=False
        )
    
    # CRITICAL FIX: Filter responses by the evaluation_period foreign key
    # This is more reliable than date range filtering
    responses = EvaluationResponse.objects.filter(
        evaluatee=user,
        evaluation_period=evaluation_period
    )
    
    if not responses.exists():
        return None
    
    # Determine if this is a peer evaluation or student evaluation
    is_peer_evaluation = evaluation_period.evaluation_type == 'peer'
    
    if is_peer_evaluation:
        # Use peer scoring (simple average of 15 questions, no categories)
        category_scores = compute_peer_scores(user, evaluation_period=evaluation_period)
    else:
        # Use student scoring (4 categories with weights)
        category_scores = compute_category_scores(user, evaluation_period=evaluation_period)
    
    a_avg, b_avg, c_avg, d_avg, total_percentage, total_a, total_b, total_c, total_d = category_scores
    
    # Calculate rating distribution for THIS period
    rating_distribution = get_rating_distribution(user, evaluation_period=evaluation_period)
    poor, unsatisfactory, satisfactory, very_satisfactory, outstanding = rating_distribution
    
    # Calculate average rating (convert percentage to 5-point scale)
    average_rating = (total_percentage / 20)
    
    # Get the most common section from evaluations in THIS period (or use assigned sections)
    section = None
    if hasattr(user, 'userprofile') and user.userprofile.section:
        section = user.userprofile.section
    else:
        # Try to find the most common section from evaluations IN THIS PERIOD
        from django.db.models import Count
        section_counts = responses.values('student_section').annotate(count=Count('id')).order_by('-count')
        if section_counts:
            most_common_section = section_counts.first()['student_section']
            if most_common_section:
                try:
                    section = Section.objects.get(code=most_common_section)
                except Section.DoesNotExist:
                    pass
    
    # Create or update EvaluationResult
    try:
        evaluation_result, created = EvaluationResult.objects.update_or_create(
            user=user,
            evaluation_period=evaluation_period,
            section=section,
            defaults={
                'category_a_score': round(a_avg, 2),
                'category_b_score': round(b_avg, 2),
                'category_c_score': round(c_avg, 2),
                'category_d_score': round(d_avg, 2),
                'total_percentage': round(total_percentage, 2),
                'average_rating': round(average_rating, 2),
                'total_responses': responses.count(),
                'poor_count': poor,
                'unsatisfactory_count': unsatisfactory,
                'satisfactory_count': satisfactory,
                'very_satisfactory_count': very_satisfactory,
                'outstanding_count': outstanding,
                'calculated_at': timezone.now()
            }
        )
        
        
        return evaluation_result
        
    except Exception as e:
        logger.error(f"Error processing evaluation results for {user.username}: {str(e)}", exc_info=True)
        return None

def archive_period_results_to_history(evaluation_period):
    """
    Archive all EvaluationResult records for a period to EvaluationHistory
    This is called when a NEW period is being released (to archive the OLD period)
    After archiving, deletes the old results from EvaluationResult table
    """
    try:
        # Get all results for this evaluation period
        results = EvaluationResult.objects.filter(evaluation_period=evaluation_period)
        
        archived_count = 0
        for result in results:
            # Create a history record from the result
            history = EvaluationHistory.create_from_result(result)
            archived_count += 1
            logger.info(f"Archived result for {result.user.username} to history: {result.total_percentage}%")
        
        # DELETE the old results from EvaluationResult after archiving to history
        # This ensures only current period results remain in EvaluationResult table
        if archived_count > 0:
            deleted_count = results.delete()[0]
            logger.info(f"Deleted {deleted_count} old evaluation results from EvaluationResult table after archiving")
        
        logger.info(f"Successfully archived {archived_count} evaluation results to history for period: {evaluation_period.name}")
        return archived_count
        
    except Exception as e:
        logger.error(f"Error archiving period results to history: {str(e)}", exc_info=True)
        return 0

def get_rating_distribution(user, evaluation_period=None):
    """Get rating distribution for a user
    CRITICAL: Now accepts evaluation_period to filter responses by date range
    """
    responses = EvaluationResponse.objects.filter(evaluatee=user)
    
    # CRITICAL FIX: If evaluation period provided, filter responses by its date range
    if evaluation_period:
        responses = responses.filter(
            submitted_at__gte=evaluation_period.start_date,
            submitted_at__lte=evaluation_period.end_date
        )
    
    poor = unsatisfactory = satisfactory = very_satisfactory = outstanding = 0
    
    rating_values = {
        'Poor': 1,
        'Unsatisfactory': 2, 
        'Satisfactory': 3,
        'Very Satisfactory': 4,
        'Outstanding': 5
    }
    
    for response in responses:
        for i in range(1, 16):
            question_key = f'question{i}'
            rating = getattr(response, question_key, 'Poor')
            numeric_rating = rating_values.get(rating, 1)
            
            if numeric_rating == 1:
                poor += 1
            elif numeric_rating == 2:
                unsatisfactory += 1
            elif numeric_rating == 3:
                satisfactory += 1
            elif numeric_rating == 4:
                very_satisfactory += 1
            elif numeric_rating == 5:
                outstanding += 1
    
    return [poor, unsatisfactory, satisfactory, very_satisfactory, outstanding]

def move_current_results_to_history():
    """
    Move all current EvaluationResult records to EvaluationHistory
    This is called when starting a NEW evaluation period (when admin clicks RELEASE)
    After moving, deletes all records from EvaluationResult table
    Returns: count of records moved
    """
    try:
        results = EvaluationResult.objects.all()
        moved_count = 0
        
        for result in results:
            # Create history record from result
            EvaluationHistory.create_from_result(result)
            moved_count += 1
            logger.info(f"Moved result to history: {result.user.username} - {result.evaluation_period.name}")
        
        # Delete all results from EvaluationResult after moving to history
        if moved_count > 0:
            deleted_count = results.delete()[0]
            logger.info(f"Cleared {deleted_count} records from EvaluationResult table after moving to history")
        
        return moved_count
        
    except Exception as e:
        logger.error(f"Error moving results to history: {str(e)}", exc_info=True)
        return 0

def process_evaluation_period_to_results(evaluation_period):
    """
    Process all evaluation responses from a period and create EvaluationResult records
    This is called when admin UNRELEASES (ends) an evaluation period
    These results will be displayed in instructor profile settings
    Returns: count of results processed
    """
    try:
        from main.models import EvaluationResult, Section
        
        # Get all staff members
        staff_users = User.objects.filter(
            userprofile__role__in=[Role.FACULTY, Role.COORDINATOR, Role.DEAN]
        ).distinct()
        
        processed_count = 0
        
        for staff_user in staff_users:
            # Get all responses for this user in this period
            responses = EvaluationResponse.objects.filter(
                evaluatee=staff_user,
                submitted_at__gte=evaluation_period.start_date,
                submitted_at__lte=evaluation_period.end_date
            )
            
            if not responses.exists():
                continue
            
            # Group responses by section
            sections_evaluated = set(responses.values_list('student_section', flat=True).distinct())
            
            for section_code in sections_evaluated:
                if not section_code:
                    continue
                
                # Get section object
                try:
                    section = Section.objects.get(code=section_code)
                except Section.DoesNotExist:
                    logger.warning(f"Section {section_code} not found")
                    continue
                
                # Filter responses for this section
                section_responses = responses.filter(student_section=section_code)
                
                if not section_responses.exists():
                    continue
                
                # Calculate category scores
                category_scores = compute_category_scores_from_responses(section_responses)
                
                # Get rating distribution
                rating_dist = get_rating_distribution_from_responses(section_responses)
                
                # Create or update EvaluationResult
                result, created = EvaluationResult.objects.update_or_create(
                    user=staff_user,
                    evaluation_period=evaluation_period,
                    section=section,
                    defaults={
                        'category_a_score': category_scores['category_a'],
                        'category_b_score': category_scores['category_b'],
                        'category_c_score': category_scores['category_c'],
                        'category_d_score': category_scores['category_d'],
                        'total_percentage': category_scores['total_percentage'],
                        'average_rating': category_scores['average_rating'],
                        'total_responses': section_responses.count(),
                        'total_questions': 15,
                        'poor_count': rating_dist[0],
                        'unsatisfactory_count': rating_dist[1],
                        'satisfactory_count': rating_dist[2],
                        'very_satisfactory_count': rating_dist[3],
                        'outstanding_count': rating_dist[4],
                    }
                )
                
                processed_count += 1
                action = "Created" if created else "Updated"
                logger.info(f"{action} EvaluationResult for {staff_user.username} - {section_code}: {category_scores['total_percentage']:.1f}%")
        
        logger.info(f"Processed {processed_count} evaluation results for period: {evaluation_period.name}")
        return processed_count
        
    except Exception as e:
        logger.error(f"Error processing evaluation period to results: {str(e)}", exc_info=True)
        return 0

def compute_category_scores_from_responses(responses):
    """
    Compute category scores from a queryset of EvaluationResponse objects
    Returns dict with category scores and totals
    """
    rating_values = {'Poor': 1, 'Unsatisfactory': 2, 'Satisfactory': 3, 'Very Satisfactory': 4, 'Outstanding': 5}
    
    # Category mappings (question number -> category)
    category_a_questions = [1, 2, 3, 4, 5]  # Mastery (35%)
    category_b_questions = [6, 7, 8, 9]     # Classroom Management (25%)
    category_c_questions = [10, 11, 12]     # Compliance (20%)
    category_d_questions = [13, 14, 15]     # Personality (20%)
    
    total_a = total_b = total_c = total_d = 0
    count_a = count_b = count_c = count_d = 0
    
    for response in responses:
        # Category A
        for q in category_a_questions:
            rating = getattr(response, f'question{q}', 'Poor')
            total_a += rating_values.get(rating, 1)
            count_a += 1
        
        # Category B
        for q in category_b_questions:
            rating = getattr(response, f'question{q}', 'Poor')
            total_b += rating_values.get(rating, 1)
            count_b += 1
        
        # Category C
        for q in category_c_questions:
            rating = getattr(response, f'question{q}', 'Poor')
            total_c += rating_values.get(rating, 1)
            count_c += 1
        
        # Category D
        for q in category_d_questions:
            rating = getattr(response, f'question{q}', 'Poor')
            total_d += rating_values.get(rating, 1)
            count_d += 1
    
    # Calculate averages (1-5 scale)
    avg_a = (total_a / count_a) if count_a > 0 else 0
    avg_b = (total_b / count_b) if count_b > 0 else 0
    avg_c = (total_c / count_c) if count_c > 0 else 0
    avg_d = (total_d / count_d) if count_d > 0 else 0
    
    # Convert to percentages with weights
    category_a = (avg_a / 5) * 35  # 35% weight
    category_b = (avg_b / 5) * 25  # 25% weight
    category_c = (avg_c / 5) * 20  # 20% weight
    category_d = (avg_d / 5) * 20  # 20% weight
    
    total_percentage = category_a + category_b + category_c + category_d
    
    # Calculate overall average rating
    total_ratings = total_a + total_b + total_c + total_d
    total_questions = count_a + count_b + count_c + count_d
    average_rating = (total_ratings / total_questions) if total_questions > 0 else 0
    
    return {
        'category_a': round(category_a, 2),
        'category_b': round(category_b, 2),
        'category_c': round(category_c, 2),
        'category_d': round(category_d, 2),
        'total_percentage': round(total_percentage, 2),
        'average_rating': round(average_rating, 2)
    }

def get_rating_distribution_from_responses(responses):
    """
    Get rating distribution counts from a queryset of responses
    Returns [poor, unsatisfactory, satisfactory, very_satisfactory, outstanding]
    """
    rating_values = {'Poor': 1, 'Unsatisfactory': 2, 'Satisfactory': 3, 'Very Satisfactory': 4, 'Outstanding': 5}
    
    poor = unsatisfactory = satisfactory = very_satisfactory = outstanding = 0
    
    for response in responses:
        for i in range(1, 16):
            rating = getattr(response, f'question{i}', 'Poor')
            numeric_rating = rating_values.get(rating, 1)
            
            if numeric_rating == 1:
                poor += 1
            elif numeric_rating == 2:
                unsatisfactory += 1
            elif numeric_rating == 3:
                satisfactory += 1
            elif numeric_rating == 4:
                very_satisfactory += 1
            elif numeric_rating == 5:
                outstanding += 1
    
    return [poor, unsatisfactory, satisfactory, very_satisfactory, outstanding]

def process_all_evaluation_results(evaluation_period=None):
    """
    Process evaluation results for all staff members (Faculty, Coordinators, Deans)
    after evaluation period ends - THIS IS CALLED WHEN ADMIN UNRELEASES EVALUATION
    """
    try:
        # Use the provided evaluation period if available; otherwise try to infer
        current_period = evaluation_period
        if not current_period:
            current_period = EvaluationPeriod.objects.filter(
                evaluation_type='student',
                is_active=True
            ).first()
        if not current_period:
            current_period = EvaluationPeriod.objects.filter(
                evaluation_type='student',
                is_active=False
            ).order_by('-end_date').first()
        if not current_period:
            return {
                'success': False,
                'error': 'No student evaluation period available to process.',
                'processed_count': 0,
                'details': []
            }
        
        # Get all staff members who might have been evaluated
        staff_users = User.objects.filter(
            userprofile__role__in=[Role.FACULTY, Role.COORDINATOR, Role.DEAN]
        ).distinct()
        
        processed_count = 0
        processing_details = []
        
        for staff_user in staff_users:
            try:
                # Check if this staff member has any evaluations in this period
                evaluation_responses = EvaluationResponse.objects.filter(evaluatee=staff_user)
                
                if evaluation_responses.exists():
                    # Process results for this staff member
                    result = process_evaluation_results_for_user(staff_user, current_period)
                    if result:
                        processed_count += 1
                        processing_details.append(f"✅ Processed {staff_user.username}: {result.total_percentage:.1f}% ({result.total_responses} evaluations)")
                    else:
                        processing_details.append(f"❌ Failed to process {staff_user.username}")
                else:
                    processing_details.append(f"➖ No evaluations for {staff_user.username}")
                    
            except Exception as e:
                processing_details.append(f"❌ Error processing {staff_user.username}: {str(e)}")
        
        return {
            'success': True,
            'processed_count': processed_count,
            'total_staff': staff_users.count(),
            'details': processing_details,
            'evaluation_period': current_period.name
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return {
            'success': False,
            'error': str(e),
            'error_details': error_details,
            'processed_count': 0,
            'details': [f"❌ System error: {str(e)}"]
        }

        
  

# Import/Export Views
from main.services.import_export_service import AccountImportExportService

@method_decorator(login_required(login_url='login'), name='dispatch')
class ExportAccountsView(View):
    """Export all accounts to Excel file."""
    
    def get(self, request):
        # Check if user is admin
        try:
            if not request.user.is_authenticated:
                return HttpResponseForbidden("You must be logged in to export accounts.")
            
            profile = request.user.userprofile
            if profile.role != Role.ADMIN:
                return HttpResponseForbidden("You do not have permission to export accounts.")
        except UserProfile.DoesNotExist:
            return HttpResponseForbidden("User profile not found. You do not have permission to export accounts.")
        
        try:
            # Generate Excel file
            excel_file = AccountImportExportService.export_accounts_to_excel()
            
            # Log the export action
            log_admin_activity(
                request=request,
                action='export_accounts',
                description='Exported all accounts to Excel file',
                target_user=None
            )
            
            # Return file as download
            response = HttpResponse(
                excel_file.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="accounts_export.xlsx"'
            return response
            
        except Exception as e:
            # If export fails, return error response instead of redirecting
            return HttpResponse(
                f"Error exporting accounts: {str(e)}",
                status=500,
                content_type='text/plain'
            )


@method_decorator(login_required(login_url='login'), name='dispatch')
class ImportAccountsView(View):
    """Import accounts from Excel file."""
    
    def get(self, request):
        # Check if user is admin
        try:
            if not request.user.is_authenticated:
                return HttpResponseForbidden("You must be logged in to import accounts.")
            
            profile = request.user.userprofile
            if profile.role != Role.ADMIN:
                return HttpResponseForbidden("You do not have permission to import accounts.")
        except UserProfile.DoesNotExist:
            return HttpResponseForbidden("User profile not found. You do not have permission to import accounts.")
        
        return render(request, 'main/import_accounts.html')
    
    def post(self, request):
        # Check if user is admin
        try:
            if not request.user.is_authenticated:
                return HttpResponseForbidden("You must be logged in to import accounts.")
            
            profile = request.user.userprofile
            if profile.role != Role.ADMIN:
                return HttpResponseForbidden("You do not have permission to import accounts.")
        except UserProfile.DoesNotExist:
            return HttpResponseForbidden("User profile not found. You do not have permission to import accounts.")
        
        # Check if file was uploaded
        if 'excel_file' not in request.FILES:
            messages.error(request, "No file uploaded.")
            return render(request, 'main/import_accounts.html')
        
        excel_file = request.FILES['excel_file']
        
        # Validate file format
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, "Please upload an Excel file (.xlsx or .xls).")
            return render(request, 'main/import_accounts.html')
        
        try:
            # Import accounts
            result = AccountImportExportService.import_accounts_from_excel(excel_file)
            
            # Log the import action
            log_admin_activity(
                request=request,
                action='import_accounts',
                description=f"Imported accounts: Created={result['created']}, Updated={result['updated']}, Skipped={result['skipped']}",
                target_user=None
            )
            
            # Prepare response data
            context = {
                'import_result': result,
                'show_result': True
            }
            
            if result['success']:
                messages.success(
                    request,
                    f"Import completed! Created: {result['created']}, Updated: {result['updated']}, Skipped: {result['skipped']}"
                )
            else:
                messages.error(request, "Import failed. Please check the errors below.")
            
            return render(request, 'main/import_accounts.html', context)
            
        except Exception as e:
            messages.error(request, f"Error importing accounts: {str(e)}")
            return render(request, 'main/import_accounts.html')


# ============================================================================
# EVALUATION QUESTIONS MANAGEMENT
# ============================================================================

@login_required(login_url='login')
def manage_evaluation_questions(request):
    """Admin view to manage all evaluation questions"""
    from .models import EvaluationQuestion, PeerEvaluationQuestion
    
    # Check if user is admin
    user_profile = get_object_or_404(UserProfile, user=request.user)
    if user_profile.role != Role.ADMIN:
        messages.error(request, "You don't have permission to manage evaluation questions.")
        return redirect('main:index')
    
    # Get all questions
    student_questions = EvaluationQuestion.objects.filter(evaluation_type='student').order_by('question_number')
    peer_questions = PeerEvaluationQuestion.objects.all().order_by('question_number')
    
    context = {
        'student_questions': student_questions,
        'peer_questions': peer_questions,
        'page_title': 'Manage Evaluation Questions'
    }
    
    return render(request, 'main/manage_evaluation_questions.html', context)


@login_required(login_url='login')
def update_evaluation_question(request, question_type, question_id):
    """Update a single evaluation question"""
    from .models import EvaluationQuestion, PeerEvaluationQuestion
    
    # Check if user is admin
    user_profile = get_object_or_404(UserProfile, user=request.user)
    if user_profile.role != Role.ADMIN:
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    
    try:
        if question_type == 'student':
            question = get_object_or_404(EvaluationQuestion, id=question_id, evaluation_type='student')
        elif question_type == 'peer':
            question = get_object_or_404(PeerEvaluationQuestion, question_number=question_id)
        else:
            return JsonResponse({'success': False, 'message': 'Invalid question type'}, status=400)
        
        if request.method == 'POST':
            question_text = request.POST.get('question_text', '').strip()
            is_active = request.POST.get('is_active') == 'on'
            
            if not question_text:
                return JsonResponse({'success': False, 'message': 'Question text cannot be empty'}, status=400)
            
            question.question_text = question_text
            question.is_active = is_active
            question.save()
            
            # Log admin activity
            log_admin_activity(
                request.user,
                f'update_{question_type}_question',
                description=f'Updated {question_type} evaluation question #{question.question_number if question_type == "peer" else question.question_number}'
            )
            
            return JsonResponse({
                'success': True, 
                'message': f'{question_type.capitalize()} question updated successfully'
            })
        
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)
        
    except Exception as e:
        logger.error(f"Error updating question: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required(login_url='login')
def bulk_update_evaluation_questions(request):
    """Bulk update evaluation questions"""
    from .models import EvaluationQuestion, PeerEvaluationQuestion
    
    # Check if user is admin
    user_profile = get_object_or_404(UserProfile, user=request.user)
    if user_profile.role != Role.ADMIN:
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)
    
    try:
        data = json.loads(request.body)
        question_type = data.get('question_type')  # 'student' or 'peer'
        questions = data.get('questions', [])  # List of {id, question_text}
        
        if not question_type or question_type not in ['student', 'peer']:
            return JsonResponse({'success': False, 'message': 'Invalid question type'}, status=400)
        
        updated_count = 0
        
        for q_data in questions:
            q_id = q_data.get('id')
            q_text = q_data.get('question_text', '').strip()
            
            if not q_text:
                continue
            
            try:
                if question_type == 'student':
                    question = EvaluationQuestion.objects.get(id=q_id, evaluation_type='student')
                else:
                    question = PeerEvaluationQuestion.objects.get(question_number=q_id)
                
                question.question_text = q_text
                question.save()
                updated_count += 1
            except Exception as e:
                logger.error(f"Error updating question {q_id}: {str(e)}")
                continue
        
        # Log admin activity
        log_admin_activity(
            request.user,
            f'bulk_update_{question_type}_questions',
            description=f'Bulk updated {updated_count} {question_type} evaluation questions'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully updated {updated_count} questions',
            'updated_count': updated_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error in bulk update: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required(login_url='login')
def reset_evaluation_questions(request):
    """Reset evaluation questions to default values"""
    from .models import EvaluationQuestion, PeerEvaluationQuestion
    
    # Check if user is admin
    user_profile = get_object_or_404(UserProfile, user=request.user)
    if user_profile.role != Role.ADMIN:
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)
    
    try:
        # Default questions
        default_student_questions = [
            "Demonstrates mastery of the subject and the ability to translate competencies into meaningful lessons.",
            "Shows ability to stimulate independent and critical thinking",
            "Is focused and explains the lesson clearly",
            "Knowledgable and uses a variety of teaching strategies.",
            "Demonstrates enthusiasm for the subject matter",
            "Establishes and communicates clearly parameters for student classroom behaviour based on student handbook and OVPAA Guidelines for the conduct of Flexible Learning Modalities.",
            "Promote self-discipline, respect and treats all students in fair and equitable manner.",
            "Keeps accurate accounting of student's attendance and records",
            "Demonstrates fairness and consistency in handling student's problems.",
            "Maintains harmonious relations with students characterized by mutual respect and understanding.",
            "Reports to class regularly.",
            "Demonstrates exceptional punctuality in observing work hours and college official functions.",
            "Returns quizzes, examination results, assignments and other activities on time.",
            "Informs the students on their academic performances and grades.",
            "Uses Google Meet and Classroom as the official platform for online classes.",
            "Commands respect by example in appearance, manners and behaviour and language.",
            "Maintains a good disposition.",
            "Relates well with students in a pleasing manner.",
            "Possesses a sense of balance that combines good humor, sincerity and fairness when confronted with difficulties in the classroom",
        ]
        
        default_peer_questions = [
            "Effectively communicates with others in the workplace",
            "Listens actively and values others' opinions and perspectives",
            "Shows respect in all professional interactions",
            "Contributes actively to team discussions and collaborative efforts",
            "Completes assigned duties and responsibilities on time",
            "Demonstrates reliability and accountability in work",
            "Takes initiative when appropriate and needed",
            "Makes valuable contributions to institutional goals and objectives",
            "Shows leadership qualities when needed or appropriate",
            "Helps resolve conflicts constructively when they arise",
            "Accepts and applies feedback for personal and professional improvement",
            "Maintains focus and engagement in professional duties",
            "Is prepared and organized in carrying out responsibilities",
            "Demonstrates strong work ethic and professional integrity",
            "Would you want to work with this colleague again in future projects?",
        ]
        
        # Reset student questions
        for i, question_text in enumerate(default_student_questions, 1):
            EvaluationQuestion.objects.update_or_create(
                evaluation_type='student',
                question_number=i,
                defaults={'question_text': question_text, 'is_active': True}
            )
        
        # Reset peer questions
        for i, question_text in enumerate(default_peer_questions, 1):
            PeerEvaluationQuestion.objects.update_or_create(
                question_number=i,
                defaults={'question_text': question_text, 'is_active': True}
            )
        
        # Log admin activity
        log_admin_activity(
            request.user,
            'reset_evaluation_questions',
            description='Reset all evaluation questions to default values'
        )
        
        messages.success(request, 'All evaluation questions have been reset to default values.')
        return redirect('main:manage_evaluation_questions')
        
    except Exception as e:
        logger.error(f"Error resetting questions: {str(e)}")
        messages.error(request, f'Error resetting questions: {str(e)}')
        return redirect('main:manage_evaluation_questions')


# ============================================
# EVALUATION HISTORY API ENDPOINTS
# ============================================

@login_required
@require_http_methods(["GET"])
def api_evaluation_history(request):
    """API endpoint to fetch user's evaluation history"""
    try:
        user = request.user
        records = EvaluationHistory.objects.filter(
            user=user
        ).select_related('evaluation_period').order_by('-archived_at')
        
        data = []
        for r in records:
            data.append({
                'id': r.id,
                'evaluation_period_id': r.evaluation_period.id,
                'evaluation_period_name': r.evaluation_period.name,
                'evaluation_type': r.evaluation_period.evaluation_type,
                'period_start_date': r.period_start_date.isoformat(),
                'period_end_date': r.period_end_date.isoformat(),
                'archived_at': r.archived_at.isoformat(),
                'total_percentage': float(r.total_percentage or 0),
                'total_responses': r.total_responses or 0,
                'average_rating': float(r.average_rating or 0)
            })
        
        return JsonResponse({
            'success': True,
            'history_records': data,
            'count': len(data)
        })
    except Exception as e:
        logger.error(f"Error fetching evaluation history: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_evaluation_history_detail(request, history_id):
    """API endpoint to fetch detailed evaluation history record"""
    try:
        user = request.user
        r = EvaluationHistory.objects.select_related(
            'evaluation_period', 'user'
        ).get(id=history_id, user=user)
        
        data = {
            'id': r.id,
            'evaluation_period_name': r.evaluation_period.name,
            'evaluation_period_id': r.evaluation_period.id,
            'evaluation_type': r.evaluation_period.evaluation_type,
            'period_start_date': r.period_start_date.isoformat(),
            'period_end_date': r.period_end_date.isoformat(),
            'archived_at': r.archived_at.isoformat(),
            'total_percentage': float(r.total_percentage or 0),
            'category_a_score': float(r.category_a_score or 0),
            'category_b_score': float(r.category_b_score or 0),
            'category_c_score': float(r.category_c_score or 0),
            'category_d_score': float(r.category_d_score or 0),
            'total_responses': r.total_responses or 0,
            'average_rating': float(r.average_rating or 0),
            'poor_count': r.poor_count or 0,
            'unsatisfactory_count': r.unsatisfactory_count or 0,
            'satisfactory_count': r.satisfactory_count or 0,
            'very_satisfactory_count': r.very_satisfactory_count or 0,
            'outstanding_count': r.outstanding_count or 0
        }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
    except EvaluationHistory.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'History record not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error fetching evaluation history detail: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_evaluation_history_by_period(request, period_id):
    """Return aggregate dataset for a period: overall (student), peer, and per assigned section.
    Includes sections even with no data, marked accordingly.
    """
    try:
        user = request.user
        from django.utils import timezone as dj_tz
        from main.models import EvaluationPeriod, SectionAssignment, Section

        # Find the student evaluation period by id
        try:
            period = EvaluationPeriod.objects.get(id=period_id)
        except EvaluationPeriod.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Period not found'}, status=404)

        # Build overall (student) from history if available, else compute
        overall_data = None
        try:
            # Prefer archived overall (section is null)
            hist_overall = EvaluationHistory.objects.filter(
                user=user,
                evaluation_period=period,
                evaluation_type='student',
                section__isnull=True
            ).first()
            if hist_overall:
                overall_data = {
                    'has_data': (hist_overall.total_responses or 0) > 0 or (hist_overall.total_percentage or 0) > 0,
                    'category_scores': [
                        float(hist_overall.category_a_score or 0),
                        float(hist_overall.category_b_score or 0),
                        float(hist_overall.category_c_score or 0),
                        float(hist_overall.category_d_score or 0),
                    ],
                    'total_percentage': float(hist_overall.total_percentage or 0),
                    'total_responses': int(hist_overall.total_responses or 0),
                    'average_rating': float(hist_overall.average_rating or 0)
                }
        except Exception:
            overall_data = None

        if overall_data is None:
            # Compute on-demand within period range
            a,b,c,d,total, *_ = compute_category_scores(user, evaluation_period=period)
            # Count responses in period
            resp_count = EvaluationResponse.objects.filter(
                evaluatee=user,
                submitted_at__gte=period.start_date,
                submitted_at__lte=period.end_date
            ).count()
            overall_data = {
                'has_data': resp_count > 0 and total > 0,
                'category_scores': [a,b,c,d],
                'total_percentage': total,
                'total_responses': resp_count,
                'average_rating': round(total/20, 2) if resp_count > 0 else 0.0
            }

        # Peer overall: try matching peer history record for same month/year
        peer_data = None
        try:
            peer_hist = EvaluationHistory.objects.filter(
                user=user,
                evaluation_type='peer',
                section__isnull=True,
                period_start_date__month=period.start_date.month,
                period_start_date__year=period.start_date.year
            ).order_by('-period_start_date').first()
            if peer_hist:
                peer_data = {
                    'has_data': (peer_hist.total_responses or 0) > 0 or (peer_hist.total_percentage or 0) > 0,
                    'category_scores': [
                        float(peer_hist.category_a_score or 0),
                        float(peer_hist.category_b_score or 0),
                        float(peer_hist.category_c_score or 0),
                        float(peer_hist.category_d_score or 0),
                    ],
                    'total_percentage': float(peer_hist.total_percentage or 0),
                    'total_responses': int(peer_hist.total_responses or 0),
                    'average_rating': float(peer_hist.average_rating or 0)
                }
        except Exception:
            peer_data = None

        # Sections: include assigned sections even if no data
        assigned_sections = SectionAssignment.objects.filter(user=user).select_related('section')
        sections_payload = []
        for assign in assigned_sections:
            sec = assign.section
            # Prefer archived per-section history
            hist_section = EvaluationHistory.objects.filter(
                user=user,
                evaluation_period=period,
                evaluation_type='student',
                section=sec
            ).first()
            if hist_section:
                has_data = (hist_section.total_responses or 0) > 0 or (hist_section.total_percentage or 0) > 0
                sections_payload.append({
                    'section_id': sec.id,
                    'section_code': sec.code,
                    'section_name': str(sec),
                    'has_data': has_data,
                    'category_scores': [
                        float(hist_section.category_a_score or 0),
                        float(hist_section.category_b_score or 0),
                        float(hist_section.category_c_score or 0),
                        float(hist_section.category_d_score or 0),
                    ],
                    'total_percentage': float(hist_section.total_percentage or 0),
                    'evaluation_count': int(hist_section.total_responses or 0)
                })
            else:
                # Compute on-demand for this section within period
                a,b,c,d,total, *_ = compute_category_scores(user, section_code=sec.code, evaluation_period=period)
                resp_count = EvaluationResponse.objects.filter(
                    evaluatee=user,
                    student_section=sec.code,
                    submitted_at__gte=period.start_date,
                    submitted_at__lte=period.end_date
                ).count()
                sections_payload.append({
                    'section_id': sec.id,
                    'section_code': sec.code,
                    'section_name': str(sec),
                    'has_data': resp_count > 0 and total > 0,
                    'category_scores': [a,b,c,d],
                    'total_percentage': total,
                    'evaluation_count': resp_count
                })

        return JsonResponse({
            'success': True,
            'period': {
                'id': period.id,
                'name': period.name,
                'start_date': period.start_date.isoformat(),
                'end_date': period.end_date.isoformat()
            },
            'overall': overall_data,
            'peer': peer_data,
            'sections': sections_payload
        })
    except Exception as e:
        logger.error(f"Error building history dataset: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============= Institute & Course Management API =============

from django.views.decorators.http import require_http_methods
import json

@require_http_methods(["GET"])
def api_list_institutes(request):
    """Get all institutes"""
    try:
        from main.models import Institute
        institutes = Institute.objects.all().values('id', 'name', 'code')
        return JsonResponse({
            'success': True,
            'institutes': list(institutes)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["POST"])
@csrf_exempt
def api_add_institute(request):
    """Add a new institute"""
    try:
        from main.models import Institute
        data = json.loads(request.body)
        institute = Institute.objects.create(
            name=data['name'],
            code=data['code']
        )
        log_admin_activity(
            request=request,
            action='add_institute',
            description=f"Added institute: {institute.name} ({institute.code})"
        )
        return JsonResponse({
            'success': True,
            'institute': {
                'id': institute.id,
                'name': institute.name,
                'code': institute.code
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["GET"])
def api_get_institute(request, institute_id):
    """Get single institute details"""
    try:
        from main.models import Institute
        institute = Institute.objects.get(id=institute_id)
        return JsonResponse({
            'success': True,
            'institute': {
                'id': institute.id,
                'name': institute.name,
                'code': institute.code
            }
        })
    except Institute.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Institute not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["POST"])
@csrf_exempt
def api_update_institute(request, institute_id):
    """Update institute"""
    try:
        from main.models import Institute
        institute = Institute.objects.get(id=institute_id)
        data = json.loads(request.body)
        institute.name = data['name']
        institute.code = data['code']
        institute.save()
        log_admin_activity(
            request=request,
            action='update_institute',
            description=f"Updated institute: {institute.name} ({institute.code})"
        )
        return JsonResponse({'success': True})
    except Institute.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Institute not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["POST"])
@csrf_exempt
def api_delete_institute(request, institute_id):
    """Delete institute"""
    try:
        from main.models import Institute
        institute = Institute.objects.get(id=institute_id)
        institute_name = institute.name
        institute.delete()
        log_admin_activity(
            request=request,
            action='delete_institute',
            description=f"Deleted institute: {institute_name}"
        )
        return JsonResponse({'success': True})
    except Institute.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Institute not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["GET"])
def api_list_courses(request):
    """Get all courses with institute names"""
    try:
        from main.models import Course
        courses = Course.objects.select_related('institute').all()
        courses_data = [{
            'id': c.id,
            'name': c.name,
            'code': c.code,
            'institute_id': c.institute.id,
            'institute_name': c.institute.name
        } for c in courses]
        return JsonResponse({
            'success': True,
            'courses': courses_data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["POST"])
@csrf_exempt
def api_add_course(request):
    """Add a new course"""
    try:
        from main.models import Course, Institute
        data = json.loads(request.body)
        institute = Institute.objects.get(id=data['institute_id'])
        course = Course.objects.create(
            name=data['name'],
            code=data.get('code', ''),
            institute=institute
        )
        log_admin_activity(
            request=request,
            action='add_course',
            description=f"Added course: {course.name} to {institute.name}"
        )
        return JsonResponse({
            'success': True,
            'course': {
                'id': course.id,
                'name': course.name,
                'code': course.code,
                'institute_name': institute.name
            }
        })
    except Institute.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Institute not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["GET"])
def api_get_course(request, course_id):
    """Get single course details"""
    try:
        from main.models import Course
        course = Course.objects.select_related('institute').get(id=course_id)
        return JsonResponse({
            'success': True,
            'course': {
                'id': course.id,
                'name': course.name,
                'code': course.code,
                'institute_id': course.institute.id,
                'institute_name': course.institute.name
            }
        })
    except Course.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Course not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["POST"])
@csrf_exempt
def api_update_course(request, course_id):
    """Update course"""
    try:
        from main.models import Course
        course = Course.objects.get(id=course_id)
        data = json.loads(request.body)
        course.name = data['name']
        course.code = data.get('code', '')
        course.save()
        log_admin_activity(
            request=request,
            action='update_course',
            description=f"Updated course: {course.name}"
        )
        return JsonResponse({'success': True})
    except Course.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Course not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["POST"])
@csrf_exempt
def api_delete_course(request, course_id):
    """Delete course"""
    try:
        from main.models import Course
        course = Course.objects.get(id=course_id)
        course_name = course.name
        course.delete()
        log_admin_activity(
            request=request,
            action='delete_course',
            description=f"Deleted course: {course_name}"
        )
        return JsonResponse({'success': True})
    except Course.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Course not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def compute_overall_scores_for_period(user, period_or_periods, assigned_sections):
    """
    Compute overall scores across all sections for a specific period or multiple periods
    Returns dict with category scores and overall average
    period_or_periods can be a single period or a list of period IDs
    """
    rating_values = {'Poor': 1, 'Unsatisfactory': 2, 'Satisfactory': 3, 'Very Satisfactory': 4, 'Outstanding': 5}
    
    # Handle both single period and list of period IDs
    if isinstance(period_or_periods, list):
        period_ids = period_or_periods
    else:
        period_ids = [period_or_periods.id]
    
    category_a_total = 0
    category_b_total = 0
    category_c_total = 0
    category_d_total = 0
    total_responses = 0
    
    for assignment in assigned_sections:
        section = assignment.section
        # Get responses across all periods
        responses = EvaluationResponse.objects.filter(
            evaluatee=user,
            student_section=section.code,
            evaluation_period__id__in=period_ids
        ).exclude(evaluator__userprofile__role__in=[Role.FACULTY, Role.COORDINATOR, Role.DEAN])
        
        for response in responses:
            # Category A (questions 1-3)
            a_total = sum([rating_values.get(getattr(response, f'question{i}'), 0) for i in range(1, 4)])
            # Category B (questions 4-7)
            b_total = sum([rating_values.get(getattr(response, f'question{i}'), 0) for i in range(4, 8)])
            # Category C (questions 8-11)
            c_total = sum([rating_values.get(getattr(response, f'question{i}'), 0) for i in range(8, 12)])
            # Category D (questions 12-15)
            d_total = sum([rating_values.get(getattr(response, f'question{i}'), 0) for i in range(12, 16)])
            
            if a_total > 0 or b_total > 0 or c_total > 0 or d_total > 0:
                category_a_total += (a_total / 15) * 100  # 3 questions * 5 points = 15
                category_b_total += (b_total / 20) * 100  # 4 questions * 5 points = 20
                category_c_total += (c_total / 20) * 100  # 4 questions * 5 points = 20
                category_d_total += (d_total / 20) * 100  # 4 questions * 5 points = 20
                total_responses += 1
    
    if total_responses > 0:
        return {
            'has_data': True,
            'category_a': category_a_total / total_responses,
            'category_b': category_b_total / total_responses,
            'category_c': category_c_total / total_responses,
            'category_d': category_d_total / total_responses,
            'overall': (category_a_total + category_b_total + category_c_total + category_d_total) / (total_responses * 4),
            'total_responses': total_responses
        }
    
    return {'has_data': False}


def compute_peer_scores_for_period(user, period_or_periods):
    """
    Compute peer evaluation scores for a specific period or multiple periods
    Returns dict with count and average
    """
    rating_values = {'Poor': 1, 'Unsatisfactory': 2, 'Satisfactory': 3, 'Very Satisfactory': 4, 'Outstanding': 5}
    
    # Handle both single period and list of period IDs
    if isinstance(period_or_periods, list):
        period_ids = period_or_periods
    else:
        period_ids = [period_or_periods.id]
    
    peer_responses = EvaluationResponse.objects.filter(
        evaluatee=user,
        evaluation_period__id__in=period_ids,
        evaluator__userprofile__role__in=[Role.FACULTY, Role.COORDINATOR, Role.DEAN]
    )
    
    if not peer_responses.exists():
        return {'has_data': False}
    
    scores = []
    for response in peer_responses:
        total = 0
        count = 0
        for i in range(1, 16):  # 15 questions for peer
            rating = getattr(response, f'question{i}', None)
            if rating and rating in rating_values:
                total += rating_values[rating]
                count += 1
        if count > 0:
            scores.append((total / (count * 5)) * 100)
    
    if scores:
        return {
            'has_data': True,
            'count': len(scores),
            'average': sum(scores) / len(scores)
        }
    
    return {'has_data': False}


def compute_irregular_scores_for_period(user, period_or_periods):
    """
    Compute irregular student evaluation scores for a specific period or multiple periods
    Returns dict with count and average
    """
    from main.models import IrregularEvaluation
    
    rating_values = {'Poor': 1, 'Unsatisfactory': 2, 'Satisfactory': 3, 'Very Satisfactory': 4, 'Outstanding': 5}
    
    # Handle both single period and list of period IDs
    if isinstance(period_or_periods, list):
        period_ids = period_or_periods
    else:
        period_ids = [period_or_periods.id]
    
    irregular_responses = IrregularEvaluation.objects.filter(
        evaluatee=user,
        evaluation_period__id__in=period_ids
    )
    
    if not irregular_responses.exists():
        return {'has_data': False}
    
    scores = []
    for response in irregular_responses:
        total = 0
        count = 0
        for i in range(1, 20):  # 19 questions for irregular
            rating = getattr(response, f'question{i}', None)
            if rating and rating in rating_values:
                total += rating_values[rating]
                count += 1
        if count > 0:
            scores.append((total / (count * 5)) * 100)
    
    if scores:
        return {
            'has_data': True,
            'count': len(scores),
            'average': sum(scores) / len(scores)
        }
    
    return {'has_data': False}


@login_required
def download_evaluation_history_pdf(request, period_id):
    """
    Generate comprehensive PDF report for archived evaluation period
    Shows same data as profile settings: Overall, Sections, Peer, Irregular, Comments, AI Recommendations
    """
    try:
        from io import BytesIO
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from django.http import HttpResponse
        import re
        
        user = request.user
        
        # Get the evaluation period
        period = EvaluationPeriod.objects.get(id=period_id)
        
        # Verify user has access to this data
        if not user.userprofile.role in [Role.FACULTY, Role.COORDINATOR, Role.DEAN]:
            return HttpResponse("Access denied", status=403)
        
        # Find ALL periods with the same timestamp (e.g., "Student Evaluation" and "Peer Evaluation" for same date)
        timestamp_match = re.search(r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}(?:\s+\d{1,2}:\d{2})?)', period.name)
        
        if timestamp_match:
            timestamp_key = timestamp_match.group(1)
            # Find all periods with this timestamp
            related_periods = EvaluationPeriod.objects.filter(
                name__icontains=timestamp_key,
                is_active=False
            )
            all_period_ids = [p.id for p in related_periods]
        else:
            # No timestamp match, use single period
            all_period_ids = [period_id]
        
        # Check if there's any data across ALL related periods
        student_responses = EvaluationResponse.objects.filter(evaluatee=user, evaluation_period__id__in=all_period_ids)
        irregular_responses = IrregularEvaluation.objects.filter(evaluatee=user, evaluation_period__id__in=all_period_ids)
        
        if not student_responses.exists() and not irregular_responses.exists():
            return HttpResponse("No evaluation data found for this period", status=404)
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Container for PDF elements
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#283593'),
            spaceAfter=6,
            fontName='Helvetica-Bold'
        )
        
        # Title
        story.append(Paragraph("Teacher Evaluation Report", title_style))
        story.append(Paragraph(f"Evaluation Period: {period.name}", styles['Heading3']))
        story.append(Paragraph(f"Instructor: {user.get_full_name() or user.username}", styles['Normal']))
        story.append(Paragraph(f"Generated: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Get assigned sections for this user
        from main.models import SectionAssignment
        assigned_sections = SectionAssignment.objects.filter(user=user).select_related('section')
        
        # ========== SECTION BREAKDOWN ==========
        story.append(Paragraph("Section-wise Performance", heading_style))
        
        section_scores_list = []
        for assignment in assigned_sections:
            section = assignment.section
            # Get responses across all periods
            responses = EvaluationResponse.objects.filter(
                evaluatee=user,
                student_section=section.code,
                evaluation_period__id__in=all_period_ids
            ).exclude(evaluator__userprofile__role__in=[Role.FACULTY, Role.COORDINATOR, Role.DEAN])
            
            response_count = responses.count()
            if response_count > 0:
                # Calculate category scores manually
                rating_values = {'Poor': 1, 'Unsatisfactory': 2, 'Satisfactory': 3, 'Very Satisfactory': 4, 'Outstanding': 5}
                total_score = 0
                for resp in responses:
                    resp_total = sum([rating_values.get(getattr(resp, f'question{i}'), 0) for i in range(1, 20)])
                    total_score += (resp_total / 95) * 100  # 19 questions * 5 = 95
                
                total_percentage = total_score / response_count if response_count > 0 else 0
                
                section_scores_list.append({
                    'section': section.code,
                    'score': total_percentage,
                    'responses': response_count
                })
        
        if section_scores_list:
            section_data = [['Section', 'Responses', 'Score', 'Rating']]
            for item in sorted(section_scores_list, key=lambda x: x['score'], reverse=True):
                rating = 'Outstanding' if item['score'] >= 90 else \
                         'Very Satisfactory' if item['score'] >= 80 else \
                         'Satisfactory' if item['score'] >= 70 else \
                         'Needs Improvement'
                section_data.append([
                    item['section'],
                    str(item['responses']),
                    f"{item['score']:.2f}%",
                    rating
                ])
            
            section_table = Table(section_data, colWidths=[1.5*inch, 1.2*inch, 1.3*inch, 1.5*inch])
            section_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#283593')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
            ]))
            story.append(section_table)
        else:
            story.append(Paragraph("No section evaluation data available.", styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # ========== PEER EVALUATION ==========
        story.append(Paragraph("Peer Evaluation Results", heading_style))
        
        peer_data = compute_peer_scores_for_period(user, all_period_ids)
        
        if peer_data['has_data']:
            peer_table_data = [
                ['Metric', 'Value'],
                ['Number of Evaluators', str(peer_data['count'])],
                ['Average Score', f"{peer_data['average']:.2f}%"],
            ]
            peer_table = Table(peer_table_data, colWidths=[3*inch, 2*inch])
            peer_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8f5e9')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ]))
            story.append(peer_table)
        else:
            story.append(Paragraph("No peer evaluation data available.", styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # ========== IRREGULAR STUDENT EVALUATION ==========
        story.append(Paragraph("Irregular Student Evaluation Results", heading_style))
        
        irregular_data = compute_irregular_scores_for_period(user, all_period_ids)
        
        if irregular_data['has_data']:
            irregular_table_data = [
                ['Metric', 'Value'],
                ['Number of Evaluators', str(irregular_data['count'])],
                ['Average Score', f"{irregular_data['average']:.2f}%"],
            ]
            irregular_table = Table(irregular_table_data, colWidths=[3*inch, 2*inch])
            irregular_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff3e0')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ]))
            story.append(irregular_table)
        else:
            story.append(Paragraph("No irregular student evaluation data available.", styles['Normal']))
        
        story.append(Spacer(1, 0.2*inch))
        
        # ========== STUDENT COMMENTS ==========
        story.append(PageBreak())
        story.append(Paragraph("Student Comments", heading_style))
        
        # Get comments from regular student evaluations - ONLY from periods in all_period_ids
        regular_comments = EvaluationResponse.objects.filter(
            evaluatee=user,
            evaluation_period__id__in=all_period_ids,
            comments__isnull=False
        ).exclude(comments='').exclude(
            evaluator__userprofile__role__in=[Role.FACULTY, Role.COORDINATOR, Role.DEAN]
        )
        
        # Get comments from irregular evaluations - ONLY from periods in all_period_ids
        irregular_comments_qs = IrregularEvaluation.objects.filter(
            evaluatee=user,
            evaluation_period__id__in=all_period_ids,
            comments__isnull=False
        ).exclude(comments='')
        
        if regular_comments.exists() or irregular_comments_qs.exists():
            comment_num = 1
            for response in regular_comments:
                clean_comment = re.sub('<[^<]+?>', '', response.comments)
                story.append(Paragraph(f"<b>Comment {comment_num} [Student]:</b> {clean_comment}", styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
                comment_num += 1
            
            for response in irregular_comments_qs:
                clean_comment = re.sub('<[^<]+?>', '', response.comments)
                story.append(Paragraph(f"<b>Comment {comment_num} [Irregular Student]:</b> {clean_comment}", styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
                comment_num += 1
        else:
            story.append(Paragraph("No student comments provided.", styles['Normal']))
        
        # ========== FOOTER ==========
        story.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.gray, alignment=TA_CENTER)
        story.append(Paragraph(f"This report is confidential and generated from the Edulytics Evaluation System.", footer_style))
        story.append(Paragraph(f"© {timezone.now().year} Edulytics. All rights reserved.", footer_style))
        
        # Build PDF
        doc.build(story)
        
        # Return PDF response
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        filename = f"Evaluation_Report_{user.username}_{period.name.replace(' ', '_')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except EvaluationPeriod.DoesNotExist:
        return HttpResponse("Evaluation period not found", status=404)
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)



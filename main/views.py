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
from .models import Evaluation, EvaluationResponse, Section, SectionAssignment, EvaluationFailureLog, AdminActivityLog
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

                # Distinct list of student courses
                course = students_list.values_list('course', flat=True).distinct()

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
                
                # ✅ Get distinct institutes from dean list
                institutes = deans_list.values_list('institute', flat=True).distinct()

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
            
            institutes = coordinators_list.values_list('institute', flat=True).distinct()

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

            institutes = coordinators_list.values_list('institute', flat=True).distinct()

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
                    page_title = "Staff Evaluation"

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
    logger.debug("release_student_evaluation called")
    logger.debug(f"Request method: {request.method}")
    logger.debug(f"User: {request.user}")
    
    if request.method == 'POST':
        logger.debug("Processing POST request to release student evaluation")
        try:
            from django.utils import timezone
            
            # Check if any student evaluation is already released
            student_released = Evaluation.objects.filter(is_released=True, evaluation_type='student').exists()
            logger.debug(f"Student evaluation already released: {student_released}")
            
            if student_released:
                logger.info("Attempting to release already released student evaluation")
                return JsonResponse({'success': False, 'error': "Student evaluation is already released."})

            # CRITICAL: Process results from previous active period BEFORE archiving
            logger.info("Processing results from previous evaluation period...")
            previous_period = EvaluationPeriod.objects.filter(
                evaluation_type='student',
                is_active=True
            ).first()
            
            if previous_period:
                # Process all staff results for the period that's about to be archived
                staff_users = User.objects.filter(
                    userprofile__role__in=[Role.FACULTY, Role.COORDINATOR, Role.DEAN]
                ).distinct()
                
                for staff_user in staff_users:
                    try:
                        # Only process if there are responses in this period
                        responses_in_period = EvaluationResponse.objects.filter(
                            evaluatee=staff_user,
                            submitted_at__gte=previous_period.start_date,
                            submitted_at__lte=previous_period.end_date
                        )
                        
                        if responses_in_period.exists():
                            result = process_evaluation_results_for_user(staff_user, previous_period)
                            if result:
                                logger.info(f"Processed results for {staff_user.username} in period {previous_period.name}")
                    except Exception as e:
                        logger.error(f"Error processing {staff_user.username}: {str(e)}")
            
            # CRITICAL: Archive the previous active evaluation period AFTER processing results
            logger.info("Archiving previous evaluation periods...")
            previous_periods = EvaluationPeriod.objects.filter(
                evaluation_type='student',
                is_active=True
            )
            
            # Archive results to history for each period before deactivating
            for period in previous_periods:
                archive_period_results_to_history(period)
            
            # ALSO handle case where there are old inactive periods (for backward compatibility)
            # Find the oldest inactive periods that haven't been archived yet
            inactive_periods_without_history = []
            for period in EvaluationPeriod.objects.filter(evaluation_type='student', is_active=False).order_by('start_date'):
                # Check if this period's results are already in history
                has_history = EvaluationHistory.objects.filter(evaluation_period=period).exists()
                if not has_history:
                    inactive_periods_without_history.append(period)
            
            # Archive any old results that haven't been archived yet
            for period in inactive_periods_without_history:
                logger.info(f"Archiving old inactive period: {period.name}")
                archive_period_results_to_history(period)
            
            # Now deactivate the active periods
            archived_periods = previous_periods.update(is_active=False, end_date=timezone.now())
            logger.info(f"Archived {archived_periods} previous evaluation period(s)")

            # Create a new active evaluation period for this release
            new_period, created = EvaluationPeriod.objects.get_or_create(
                name=f"Student Evaluation {timezone.now().strftime('%B %Y')}",
                evaluation_type='student',
                defaults={
                    'start_date': timezone.now(),
                    'end_date': timezone.now() + timezone.timedelta(days=30),
                    'is_active': True
                }
            )
            if created:
                logger.info(f"Created new evaluation period: {new_period.name}")
            else:
                # If period already exists, make sure it's active
                new_period.is_active = True
                new_period.start_date = timezone.now()
                new_period.save()
                logger.info(f"Activated existing evaluation period: {new_period.name}")

            # Release all student evaluations that are not released
            evaluations = Evaluation.objects.filter(is_released=False, evaluation_type='student')
            evaluation_count = evaluations.count()
            logger.debug(f"Found {evaluation_count} unreleased student evaluations")
            
            updated_count = evaluations.update(is_released=True, evaluation_period=new_period)
            logger.info(f"Updated {updated_count} evaluations to released status with new period")

            if updated_count > 0:
                log_admin_activity(
                    request=request,
                    action='release_evaluation',
                    description=f"Released student evaluation form - {updated_count} evaluation(s) activated. Previous periods archived."
                )
                
                # Send email notifications to all users
                logger.info("Sending email notifications about evaluation release")
                email_result = EvaluationEmailService.send_evaluation_released_notification('student')
                logger.info(f"Email notification result: {email_result}")
                
                response_data = {
                    'success': True,
                    'message': 'Student evaluation form has been released. Evaluation period started. Previous evaluation results have been archived.',
                    'student_evaluation_released': True,
                    'evaluation_period_ended': False,
                    'periods_archived': archived_periods,
                    'new_period': new_period.name,
                    'email_notification': {
                        'sent': email_result['sent_count'],
                        'failed': len(email_result['failed_emails']),
                        'message': email_result['message']
                    }
                }
                logger.debug(f"Returning success: {response_data}")
                return JsonResponse(response_data)
            else:
                logger.debug("No evaluations to release")
                return JsonResponse({'success': False, 'error': 'No student evaluations to release.'})
        
        except Exception as e:
            logger.error(f"Exception in release_student_evaluation: {e}", exc_info=True)
            return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})
    
    logger.debug("Not a POST request")
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def unrelease_student_evaluation(request):
    if request.method == 'POST':
        evaluations = Evaluation.objects.filter(is_released=True, evaluation_type='student')
        updated_count = evaluations.update(is_released=False)

        if updated_count > 0:
            # Deactivate the current evaluation period
            active_periods = EvaluationPeriod.objects.filter(
                evaluation_type='student',
                is_active=True
            )
            active_periods.update(is_active=False, end_date=timezone.now())
            logger.info(f"Deactivated {active_periods.count()} evaluation period(s)")
            
            # Log admin activity
            log_admin_activity(
                request=request,
                action='unrelease_evaluation',
                description=f"Unreleased student evaluation form - {updated_count} evaluation(s) deactivated. Evaluation period ended."
            )
            
            # ✅ PROCESS EVALUATION RESULTS FOR ALL STAFF - THIS IS CRITICAL
            processing_results = process_all_evaluation_results()
            
            # Send email notifications to all users
            logger.info("Sending email notifications about evaluation close")
            email_result = EvaluationEmailService.send_evaluation_unreleased_notification('student')
            logger.info(f"Email notification result: {email_result}")
            
            # Build the response message
            message = 'Student evaluation form has been unreleased. Evaluation period ended.'
            
            if processing_results['success']:
                processed_count = processing_results['processed_count']
                total_staff = processing_results['total_staff']
                message += f' Successfully processed evaluation results for {processed_count} out of {total_staff} staff members.'
                
                # Add details for admin
                if processed_count > 0:
                    message += ' Evaluation results are now available in staff history.'
                    
            else:
                message += ' But evaluation processing failed. Please check the logs.'
            
            return JsonResponse({
                'success': True,
                'message': message,
                'processing_results': processing_results,
                'student_evaluation_released': False,
                'evaluation_period_ended': True,
                'email_notification': {
                    'sent': email_result['sent_count'],
                    'failed': len(email_result['failed_emails']),
                    'message': email_result['message']
                }
            })
        else:
            return JsonResponse({
                'success': False, 
                'error': 'No student evaluations to unrelease.'
            })
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request'
    })

def release_peer_evaluation(request):
    if request.method == 'POST':
        try:
            from django.utils import timezone
            
            if Evaluation.is_evaluation_period_active('peer'):
                return JsonResponse({
                    'success': False, 
                    'error': "Peer evaluation is already released."
                })

            # CRITICAL: Process results from previous active period BEFORE archiving
            logger.info("Processing results from previous peer evaluation period...")
            previous_period = EvaluationPeriod.objects.filter(
                evaluation_type='peer',
                is_active=True
            ).first()
            
            if previous_period:
                # Process all staff results for the period that's about to be archived
                staff_users = User.objects.filter(
                    userprofile__role__in=[Role.FACULTY, Role.COORDINATOR, Role.DEAN]
                ).distinct()
                
                for staff_user in staff_users:
                    try:
                        # Only process if there are responses in this period
                        responses_in_period = EvaluationResponse.objects.filter(
                            evaluatee=staff_user,
                            submitted_at__gte=previous_period.start_date,
                            submitted_at__lte=previous_period.end_date
                        )
                        
                        if responses_in_period.exists():
                            result = process_evaluation_results_for_user(staff_user, previous_period)
                            if result:
                                logger.info(f"Processed peer results for {staff_user.username} in period {previous_period.name}")
                    except Exception as e:
                        logger.error(f"Error processing peer {staff_user.username}: {str(e)}")
            
            # CRITICAL: Archive the previous active evaluation period AFTER processing results
            logger.info("Archiving previous peer evaluation periods...")
            previous_periods = EvaluationPeriod.objects.filter(
                evaluation_type='peer',
                is_active=True
            )
            
            # Archive results to history for each period before deactivating
            for period in previous_periods:
                archive_period_results_to_history(period)
            
            # ALSO handle case where there are old inactive periods (for backward compatibility)
            # Find the oldest inactive periods that haven't been archived yet
            inactive_periods_without_history = []
            for period in EvaluationPeriod.objects.filter(evaluation_type='peer', is_active=False).order_by('start_date'):
                # Check if this period's results are already in history
                has_history = EvaluationHistory.objects.filter(evaluation_period=period).exists()
                if not has_history:
                    inactive_periods_without_history.append(period)
            
            # Archive any old results that haven't been archived yet
            for period in inactive_periods_without_history:
                logger.info(f"Archiving old inactive period: {period.name}")
                archive_period_results_to_history(period)
            
            # Now deactivate the active periods
            archived_periods = previous_periods.update(is_active=False, end_date=timezone.now())
            logger.info(f"Archived {archived_periods} previous peer evaluation period(s)")

            # Create a new evaluation period for peer evaluation
            evaluation_period = EvaluationPeriod.objects.create(
                name=f"Peer Evaluation {timezone.now().strftime('%B %Y')}",
                evaluation_type='peer',
                start_date=timezone.now(),
                end_date=timezone.now() + timezone.timedelta(days=30),  # 30-day evaluation period
                is_active=True
            )

            evaluations = Evaluation.objects.filter(is_released=False, evaluation_type='peer')
            updated_count = evaluations.update(is_released=True, evaluation_period=evaluation_period)
            logger.info(f"Updated {updated_count} peer evaluations with new period")

            if updated_count > 0:
                # Send email notifications to all users
                logger.info("Sending email notifications about peer evaluation release")
                email_result = EvaluationEmailService.send_evaluation_released_notification('peer')
                logger.info(f"Email notification result: {email_result}")
                
                return JsonResponse({
                    'success': True,
                    'message': 'Peer evaluation form has been released. Evaluation period started. Previous evaluation results have been archived.',
                    'peer_evaluation_released': True,
                    'evaluation_period_ended': False,
                    'periods_archived': archived_periods,
                    'new_period': evaluation_period.name,
                    'email_notification': {
                        'sent': email_result['sent_count'],
                        'failed': len(email_result['failed_emails']),
                        'message': email_result['message']
                    }
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'error': 'No peer evaluations to release.'
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
    if request.method == 'POST':
        evaluations = Evaluation.objects.filter(is_released=True, evaluation_type='peer')
        updated_count = evaluations.update(is_released=False)

        if updated_count > 0:
            # Deactivate the current evaluation period
            active_periods = EvaluationPeriod.objects.filter(
                evaluation_type='peer',
                is_active=True
            )
            active_periods.update(is_active=False, end_date=timezone.now())
            logger.info(f"Deactivated {active_periods.count()} peer evaluation period(s)")
            
            # Process peer evaluation results
            processing_results = process_peer_evaluation_results()
            
            # Send email notifications to all users
            logger.info("Sending email notifications about peer evaluation close")
            email_result = EvaluationEmailService.send_evaluation_unreleased_notification('peer')
            logger.info(f"Email notification result: {email_result}")
            
            message = 'Peer evaluation form has been unreleased. Evaluation period ended.'
            
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
                'email_notification': {
                    'sent': email_result['sent_count'],
                    'failed': len(email_result['failed_emails']),
                    'message': email_result['message']
                }
            })
        else:
            return JsonResponse({
                'success': False, 
                'error': 'No peer evaluations to unrelease.'
            })
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request'
    })

def process_peer_evaluation_results():
    """
    Process peer evaluation results for all staff members after evaluation period ends
    """
    try:
        # Get or create the peer evaluation period that just ended
        current_period = EvaluationPeriod.objects.filter(
            evaluation_type='peer',
            is_active=True
        ).first()
        
        if not current_period:
            # Create a new evaluation period for this cycle
            current_period = EvaluationPeriod.objects.create(
                name=f"Peer Evaluation {timezone.now().strftime('%B %Y')}",
                evaluation_type='peer',
                start_date=timezone.now() - timezone.timedelta(days=30),
                end_date=timezone.now(),
                is_active=False
            )
        else:
            # Mark the existing period as inactive/ended
            current_period.is_active = False
            current_period.end_date = timezone.now()
            current_period.save()
        
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
    
def release_all_evaluations(request):
    print("🔍 DEBUG: release_all_evaluations called")
    
    if request.method == 'POST':
        print("🔍 DEBUG: Processing POST request for release all")
        try:
            # Check if user is admin
            if not request.user.is_authenticated or not request.user.is_superuser:
                return JsonResponse({'success': False, 'error': 'Permission denied'})
            
            print("🔍 DEBUG: User is authorized")
            
            # Release student evaluations
            student_evaluations = Evaluation.objects.filter(is_released=False, evaluation_type='student')
            student_count = student_evaluations.count()
            student_updated = student_evaluations.update(is_released=True)
            print(f"🔍 DEBUG: Released {student_updated}/{student_count} student evaluations")
            
            # Release peer evaluations
            peer_evaluations = Evaluation.objects.filter(is_released=False, evaluation_type='peer')
            peer_count = peer_evaluations.count()
            peer_updated = peer_evaluations.update(is_released=True)
            print(f"🔍 DEBUG: Released {peer_updated}/{peer_count} peer evaluations")
            
            # Create evaluation periods
            from django.utils import timezone
            
            student_period, student_created = EvaluationPeriod.objects.get_or_create(
                name=f"Student Evaluation {timezone.now().strftime('%B %Y')}",
                evaluation_type='student',
                defaults={
                    'start_date': timezone.now(),
                    'end_date': timezone.now() + timezone.timedelta(days=30),
                    'is_active': True
                }
            )
            print(f"🔍 DEBUG: Student period: {student_period.name}, created: {student_created}")
            
            peer_period, peer_created = EvaluationPeriod.objects.get_or_create(
                name=f"Peer Evaluation {timezone.now().strftime('%B %Y')}",
                evaluation_type='peer',
                defaults={
                    'start_date': timezone.now(),
                    'end_date': timezone.now() + timezone.timedelta(days=30),
                    'is_active': True
                }
            )
            print(f"🔍 DEBUG: Peer period: {peer_period.name}, created: {peer_created}")
            
            if student_updated > 0 or peer_updated > 0:
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
            
            # Unrelease student evaluations
            student_evaluations = Evaluation.objects.filter(is_released=True, evaluation_type='student')
            student_updated = student_evaluations.update(is_released=False)
            print(f"🔍 DEBUG: Unreleased {student_updated} student evaluations")
            
            # Unrelease peer evaluations
            peer_evaluations = Evaluation.objects.filter(is_released=True, evaluation_type='peer')
            peer_updated = peer_evaluations.update(is_released=False)
            print(f"🔍 DEBUG: Unreleased {peer_updated} peer evaluations")
            
            # Process results for both
            student_processing = process_all_evaluation_results()
            peer_processing = process_peer_evaluation_results()
            
            message = 'Both student and peer evaluations have been unreleased. Evaluation periods ended.'
            
            # Add processing details
            if student_processing['success']:
                message += f" Student results: {student_processing['processed_count']} processed."
            if peer_processing['success']:
                message += f" Peer results: {peer_processing['processed_count']} processed."
            
            if student_updated > 0 or peer_updated > 0:
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
                category_scores = compute_category_scores(coordinator.user, section_code)
                
                a_avg, b_avg, c_avg, d_avg, total_percentage, total_a, total_b, total_c, total_d = category_scores
                
                # Get evaluation count for this section from EvaluationResponse
                evaluation_count = EvaluationResponse.objects.filter(
                    evaluatee=coordinator.user,
                    student_section=section_code
                ).count()
                
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

            # Convert to JSON for JavaScript
            import json
            section_scores_json = json.dumps(section_scores)
            section_map_json = json.dumps(section_map)
            
            # Calculate overall statistics for the template
            total_sections = assigned_sections.count()
            sections_with_data = sum(1 for scores in section_scores.values() if scores['has_data'])
            total_evaluations = EvaluationResponse.objects.filter(evaluatee=coordinator.user).count()

            context = {
                'coordinator': coordinator,
                'assigned_sections': assigned_sections,
                'section_scores': section_scores,
                'section_scores_json': section_scores_json,  # JSON for JavaScript
                'section_map_json': section_map_json,        # JSON for JavaScript
                'has_any_data': any(scores['has_data'] for scores in section_scores.values()),
                'total_sections': total_sections,
                'sections_with_data': sections_with_data,
                'total_evaluations': total_evaluations,
                'evaluation_period_ended': can_view_evaluation_results('student'),
            }

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
                # Check if student's section is assigned to this staff member
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
            try:
                current_period = EvaluationPeriod.objects.get(
                    evaluation_type='student',
                    is_active=True
                )
            except EvaluationPeriod.DoesNotExist:
                messages.error(request, 'No active evaluation period found.')
                return redirect('main:evaluationform')

            # Prevent duplicate evaluation IN THE SAME PERIOD
            # Allow re-evaluation in different periods
            if EvaluationResponse.objects.filter(
                evaluator=request.user, 
                evaluatee=evaluatee,
                evaluation_period=current_period
            ).exists():
                messages.error(request, 'You have already evaluated this instructor in this evaluation period.')
                return redirect('main:evaluationform')

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
            for i in range(1, 20):  # Changed to 20 to include questions 1-19
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
            logger.info(f"🔍 Creating EvaluationResponse with {len(questions)} questions")
            logger.info(f"🔍 Questions dict: {questions}")
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
    
def release_student_evaluation(request):
    if request.method == 'POST':
        # Check if any student evaluation is already released
        if Evaluation.objects.filter(is_released=True, evaluation_type='student').exists():
            return JsonResponse({'success': False, 'error': "Student evaluation is already released."})

        # Release all student evaluations that are not released
        evaluations = Evaluation.objects.filter(is_released=False, evaluation_type='student')
        updated_count = evaluations.update(is_released=True)

        # Send email notifications
        if updated_count > 0:
            try:
                email_result = EvaluationEmailService.send_evaluation_released_notification(evaluation_type='student')
                logger.info(f"Email notification result: {email_result}")
            except Exception as e:
                logger.error(f"Failed to send email notifications: {e}", exc_info=True)

        # Return updated status to the frontend
        student_evaluation_released = Evaluation.objects.filter(is_released=True, evaluation_type='student').exists()
        peer_evaluation_released = Evaluation.objects.filter(is_released=True, evaluation_type='peer').exists()

        if updated_count > 0:
            return JsonResponse({
                'success': True,
                'student_evaluation_released': student_evaluation_released,
                'peer_evaluation_released': peer_evaluation_released
            })
        else:
            return JsonResponse({'success': False, 'error': 'No student evaluations to release.'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


# 🔹 Unrelease Student Evaluation
def unrelease_student_evaluation(request):
    if request.method == 'POST':
        # Unrelease all student evaluations that are currently released
        evaluations = Evaluation.objects.filter(is_released=True, evaluation_type='student')
        updated_count = evaluations.update(is_released=False)

        # Send email notifications
        if updated_count > 0:
            try:
                email_result = EvaluationEmailService.send_evaluation_unreleased_notification(evaluation_type='student')
                logger.info(f"Email notification result: {email_result}")
            except Exception as e:
                logger.error(f"Failed to send email notifications: {e}", exc_info=True)

        # Return updated status to the frontend
        student_evaluation_released = Evaluation.objects.filter(is_released=True, evaluation_type='student').exists()
        peer_evaluation_released = Evaluation.objects.filter(is_released=True, evaluation_type='peer').exists()

        if updated_count > 0:
            return JsonResponse({
                'success': True,
                'student_evaluation_released': student_evaluation_released,
                'peer_evaluation_released': peer_evaluation_released
            })
        else:
            return JsonResponse({'success': False, 'error': 'No student evaluations to unrelease.'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


# 🔹 Release Peer Evaluation
def release_peer_evaluation(request):
    if request.method == 'POST':
        try:
            from django.utils import timezone
            
            logger.info("🔹 Starting release_peer_evaluation...")
            
            # CRITICAL: Archive the previous active evaluation period before releasing new one
            logger.info("Archiving previous peer evaluation periods...")
            archived_periods = EvaluationPeriod.objects.filter(
                evaluation_type='peer',
                is_active=True
            ).update(is_active=False, end_date=timezone.now())
            logger.info(f"✅ Archived {archived_periods} previous peer evaluation period(s)")

            # Create a new evaluation period for peer evaluation
            evaluation_period = EvaluationPeriod.objects.create(
                name=f"Peer Evaluation {timezone.now().strftime('%B %Y')}",
                evaluation_type='peer',
                start_date=timezone.now(),
                end_date=timezone.now() + timezone.timedelta(days=30),
                is_active=True
            )
            logger.info(f"✅ Created new peer evaluation period: {evaluation_period.id} - {evaluation_period.name}")

            # 🔹 SMART CLEANUP: Only delete unreleased records from RECENT periods (not all history)
            # Get all old evaluation periods (not the new one we just created)
            old_periods = EvaluationPeriod.objects.filter(
                evaluation_type='peer'
            ).exclude(id=evaluation_period.id)
            
            # Delete unreleased peer evaluations from old periods only
            deleted_count, _ = Evaluation.objects.filter(
                evaluation_type='peer',
                is_released=False,
                evaluation_period__in=old_periods
            ).delete()
            logger.info(f"🗑️  Cleaned up {deleted_count} old unreleased peer evaluation record(s)")

            # Create a FRESH peer evaluation record with the new period
            peer_eval = Evaluation.objects.create(
                evaluation_type='peer',
                is_released=True,
                evaluation_period=evaluation_period
            )
            logger.info(f"✅ Created fresh peer evaluation record: {peer_eval.id} for period {evaluation_period.id}")

            # Verify the record was created and is released
            peer_eval_check = Evaluation.objects.filter(
                id=peer_eval.id,
                evaluation_type='peer',
                is_released=True,
                evaluation_period=evaluation_period
            ).exists()
            logger.info(f"✅ Verification - Peer eval exists with correct period: {peer_eval_check}")

            # Return updated status to the frontend
            student_evaluation_released = Evaluation.objects.filter(is_released=True, evaluation_type='student').exists()
            peer_evaluation_released = Evaluation.objects.filter(is_released=True, evaluation_type='peer').exists()

            logger.info(f"📊 Status: Student Released={student_evaluation_released}, Peer Released={peer_evaluation_released}")

            # Send email notifications
            if peer_evaluation_released:
                try:
                    email_result = EvaluationEmailService.send_evaluation_released_notification(evaluation_type='peer')
                    logger.info(f"Email notification result: {email_result}")
                except Exception as e:
                    logger.error(f"Failed to send email notifications: {e}", exc_info=True)

                return JsonResponse({
                    'success': True,
                    'student_evaluation_released': student_evaluation_released,
                    'peer_evaluation_released': peer_evaluation_released,
                    'periods_archived': archived_periods,
                    'new_period': evaluation_period.name
                })
            else:
                logger.error("❌ Peer evaluation was not created successfully!")
                return JsonResponse({'success': False, 'error': 'Failed to create peer evaluation record.'})
        except Exception as e:
            logger.error(f"❌ Exception in release_peer_evaluation: {e}", exc_info=True)
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


# 🔹 Unrelease Peer Evaluation
def unrelease_peer_evaluation(request):
    if request.method == 'POST':
        try:
            from django.utils import timezone
            
            logger.info("🔹 Starting unrelease_peer_evaluation...")
            
            # Unrelease all peer evaluations that are currently released
            evaluations = Evaluation.objects.filter(is_released=True, evaluation_type='peer')
            updated_count = evaluations.update(is_released=False)
            logger.info(f"✅ Unreleased {updated_count} peer evaluation record(s)")

            # Archive the active peer evaluation period
            archived_periods = EvaluationPeriod.objects.filter(
                evaluation_type='peer',
                is_active=True
            ).update(is_active=False, end_date=timezone.now())
            logger.info(f"✅ Archived {archived_periods} peer evaluation period(s)")

            # Send email notifications
            if updated_count > 0 or archived_periods > 0:
                try:
                    email_result = EvaluationEmailService.send_evaluation_unreleased_notification(evaluation_type='peer')
                    logger.info(f"Email notification result: {email_result}")
                except Exception as e:
                    logger.error(f"Failed to send email notifications: {e}", exc_info=True)

            # Return updated status to the frontend
            student_evaluation_released = Evaluation.objects.filter(is_released=True, evaluation_type='student').exists()
            peer_evaluation_released = Evaluation.objects.filter(is_released=True, evaluation_type='peer').exists()

            if updated_count > 0 or archived_periods > 0:
                return JsonResponse({
                    'success': True,
                    'student_evaluation_released': student_evaluation_released,
                    'peer_evaluation_released': peer_evaluation_released,
                    'periods_archived': archived_periods
                })
            else:
                return JsonResponse({'success': False, 'error': 'No peer evaluations or periods to unrelease.'})
        except Exception as e:
            logger.error(f"❌ Exception in unrelease_peer_evaluation: {e}", exc_info=True)
            return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})

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
                    student_section_display = "Not assigned"

                # ✅ Get already evaluated instructors for this student
                evaluated_ids = EvaluationResponse.objects.filter(
                    evaluator=request.user
                ).values_list('evaluatee_id', flat=True)

                context = {
                    'evaluation': evaluation,
                    'faculty': faculty,
                    'student_evaluation_released': True,
                    'peer_evaluation_released': peer_eval_released,
                    'student_number': student_number,
                    'student_section': student_section_display,
                    'evaluated_ids': list(evaluated_ids),
                    'page_title': 'Teacher Evaluation Form',
                }
                return render(request, 'main/evaluationform.html', context)

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

                # For staff peer evaluation, show staff from same institute (excluding themselves)
                # Include Faculty, Coordinators, and Deans from the same institute
                staff_members = User.objects.filter(
                    userprofile__role__in=[Role.FACULTY, Role.COORDINATOR, Role.DEAN],
                    userprofile__institute=user_profile.institute
                ).exclude(id=request.user.id)

                # ✅ Get already evaluated staff for this user
                evaluated_ids = EvaluationResponse.objects.filter(
                    evaluator=request.user
                ).values_list('evaluatee_id', flat=True)

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
    """
    
    # Filter responses by evaluatee
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
            staff_members = User.objects.filter(
                userprofile__role__in=[Role.FACULTY, Role.COORDINATOR, Role.DEAN],
                userprofile__institute=user_profile.institute
            ).exclude(id=request.user.id)
            
            logger.info(f"✅ Found {staff_members.count()} staff members available for evaluation")

            # STEP 4: Get already evaluated staff members FOR THIS PERIOD ONLY
            logger.info("📍 STEP 4: Getting already-evaluated staff list...")
            evaluated_ids = EvaluationResponse.objects.filter(
                evaluator=request.user,
                evaluation_period=current_peer_period
            ).values_list('evaluatee_id', flat=True)

            logger.info(f"✅ User has already evaluated {len(evaluated_ids)} staff members in this period")

            # ✅ All checks passed - prepare context
            logger.info("✅ ALL CHECKS PASSED - Rendering form...")
            context = {
                'evaluation': evaluation,
                'faculty': staff_members,
                'evaluated_ids': list(evaluated_ids),
                'page_title': 'Peer Evaluation Form',
            }
            return render(request, 'main/evaluationform_staffs.html', context)

        else:
            return render(request, 'main/no_permission.html', {
                'message': 'You do not have permission to access the staff evaluation form.',
                'page_title': 'Access Denied',
            })

    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found. Please contact administrator.")
        return redirect('/login')
def evaluated(request):
    evaluator = request.user

    # Get IDs of users this evaluator has already evaluated
    evaluated_ids = list(  # Convert to list immediately
        EvaluationResponse.objects.filter(evaluator=evaluator)
        .values_list('evaluatee_id', flat=True)
    )

    # Get all faculty users
    faculty = User.objects.filter(userprofile__role=Role.FACULTY)

    context = {
        'evaluated_ids': evaluated_ids,  # Make sure this is a list for template logic
        'faculty': faculty,
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
            
            # Convert to JSON for JavaScript
            import json
            section_scores_json = json.dumps(section_scores)
            section_map_json = json.dumps({assignment.section.id: assignment.section.code for assignment in assigned_sections})
            peer_scores_json = json.dumps(peer_scores)
            
            # Calculate overall statistics for the template
            total_sections = assigned_sections.count()
            sections_with_data = sum(1 for scores in section_scores.values() if scores['has_data'])
            total_evaluations = EvaluationResponse.objects.filter(evaluatee=user).count()

            evaluation_history = self.get_evaluation_history(user)
            
            # Identify current active student evaluation period (if any)
            active_student_period = EvaluationPeriod.objects.filter(evaluation_type='student', is_active=True).order_by('-start_date').first()

            return render(request, 'main/dean_profile_settings.html', {
                'user': user,
                'next_url': next_url,
                'evaluation_data': evaluation_data,
                'ai_recommendations': ai_recommendations,
                'assigned_sections': assigned_sections,
                'section_scores': section_scores,
                'section_scores_json': section_scores_json,
                'section_map_json': section_map_json,
                'peer_scores': peer_scores,
                'peer_scores_json': peer_scores_json,
                'has_any_data': any(scores['has_data'] for scores in section_scores.values()),
                'total_sections': total_sections,
                'sections_with_data': sections_with_data,
                'total_evaluations': total_evaluations,
                'evaluation_period_ended': can_view_evaluation_results('student'),
                'evaluation_history': evaluation_history,
                'active_student_period_id': active_student_period.id if active_student_period else None,
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
        """Calculate scores for each assigned section"""
        section_scores = {}
        
        for section_assignment in assigned_sections:
            section = section_assignment.section
            section_code = section.code
            
            # Calculate scores for this specific section
            category_scores = compute_category_scores(user, section_code)
            a_avg, b_avg, c_avg, d_avg, total_percentage, total_a, total_b, total_c, total_d = category_scores
            
            # Get evaluation count for this section
            evaluation_count = EvaluationResponse.objects.filter(
                evaluatee=user,
                student_section=section_code
            ).count()
            
            # Fetch student comments for this section
            comments_queryset = EvaluationResponse.objects.filter(
                evaluatee=user,
                student_section=section_code,
                comments__isnull=False
            ).exclude(comments='').values_list('comments', flat=True)
            
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
            
            # Include all sections, mark if they have data
            has_data = total_percentage > 0 and evaluation_count > 0
            
            section_scores[section_code] = {
                'category_scores': [
                    round(a_avg, 2) if a_avg else 0,
                    round(b_avg, 2) if b_avg else 0,
                    round(c_avg, 2) if c_avg else 0,
                    round(d_avg, 2) if d_avg else 0
                ],
                'total_percentage': round(total_percentage, 2) if total_percentage else 0,
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
        total_responses = 0
        
        for section_assignment in assigned_sections:
            section = section_assignment.section
            section_code = section.code
            
            # Calculate scores for this specific section
            category_scores = compute_category_scores(user, section_code)
            a_avg, b_avg, c_avg, d_avg, total_percentage, total_a, total_b, total_c, total_d = category_scores
            
            # Only include sections that have evaluations
            if total_percentage > 0:
                # For overall calculation, we need to accumulate totals and counts
                section_responses = EvaluationResponse.objects.filter(
                    evaluatee=user,
                    student_section=section_code
                )
                
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
        all_comments = EvaluationResponse.objects.filter(
            evaluatee=user,
            comments__isnull=False
        ).exclude(comments='').values_list('comments', flat=True)
        
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
        """Get AI recommendations using shared service"""
        ai_service = TeachingAIRecommendationService()
        return ai_service.get_recommendations(
            user=user,
            section_data=section_data,
            section_code=section_code,
            role="Dean"
        )
    
    def get_peer_evaluation_scores(self, user):
        """Calculate peer evaluation scores (evaluations from other staff members)"""
        # Peer evaluations are identified by having "Staff" in student_section field
        peer_evaluations = EvaluationResponse.objects.filter(
            evaluatee=user,
            student_section__icontains="Staff"
        )
        
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
        
        total_category_a = total_category_b = total_category_c = total_category_d = 0
        total_count_a = total_count_b = total_count_c = total_count_d = 0
        
        for response in peer_evaluations:
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
            'category_scores': [
                round(a_avg, 2),
                round(b_avg, 2),
                round(c_avg, 2),
                round(d_avg, 2)
            ],
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
            
            # Convert to JSON for JavaScript
            import json
            section_scores_json = json.dumps(section_scores)
            section_map_json = json.dumps({assignment.section.id: assignment.section.code for assignment in assigned_sections})
            peer_scores_json = json.dumps(peer_scores)
            
            # Calculate overall statistics for the template
            total_sections = assigned_sections.count()
            sections_with_data = sum(1 for scores in section_scores.values() if scores['has_data'])
            total_evaluations = EvaluationResponse.objects.filter(evaluatee=user).count()

            evaluation_history = self.get_evaluation_history(user)
            
            return render(request, 'main/coordinator_profile_settings.html', {
                'user': user,
                'next_url': next_url,
                'evaluation_data': evaluation_data,
                'ai_recommendations': ai_recommendations,
                'assigned_sections': assigned_sections,
                'section_scores': section_scores,
                'section_scores_json': section_scores_json,
                'section_map_json': section_map_json,
                'peer_scores': peer_scores,
                'peer_scores_json': peer_scores_json,
                'has_any_data': any(scores['has_data'] for scores in section_scores.values()),
                'total_sections': total_sections,
                'sections_with_data': sections_with_data,
                'total_evaluations': total_evaluations,
                'evaluation_period_ended': can_view_evaluation_results('student'),
                'evaluation_history': evaluation_history, 
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
        """Calculate scores for each assigned section"""
        section_scores = {}
        
        for section_assignment in assigned_sections:
            section = section_assignment.section
            section_code = section.code
            
            # Calculate scores for this specific section
            category_scores = compute_category_scores(user, section_code)
            a_avg, b_avg, c_avg, d_avg, total_percentage, total_a, total_b, total_c, total_d = category_scores
            
            # Get evaluation count for this section
            evaluation_count = EvaluationResponse.objects.filter(
                evaluatee=user,
                student_section=section_code
            ).count()
            
            # Fetch student comments for this section
            comments_queryset = EvaluationResponse.objects.filter(
                evaluatee=user,
                student_section=section_code,
                comments__isnull=False
            ).exclude(comments='').values_list('comments', flat=True)
            
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
            
            # Include all sections, mark if they have data
            has_data = total_percentage > 0 and evaluation_count > 0
            
            section_scores[section_code] = {
                'category_scores': [
                    round(a_avg, 2) if a_avg else 0,
                    round(b_avg, 2) if b_avg else 0,
                    round(c_avg, 2) if c_avg else 0,
                    round(d_avg, 2) if d_avg else 0
                ],
                'total_percentage': round(total_percentage, 2) if total_percentage else 0,
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
        total_responses = 0
        
        for section_assignment in assigned_sections:
            section = section_assignment.section
            section_code = section.code
            
            # Calculate scores for this specific section
            category_scores = compute_category_scores(user, section_code)
            a_avg, b_avg, c_avg, d_avg, total_percentage, total_a, total_b, total_c, total_d = category_scores
            
            # Only include sections that have evaluations
            if total_percentage > 0:
                # For overall calculation, we need to accumulate totals and counts
                section_responses = EvaluationResponse.objects.filter(
                    evaluatee=user,
                    student_section=section_code
                )
                
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
        all_comments = EvaluationResponse.objects.filter(
            evaluatee=user,
            comments__isnull=False
        ).exclude(comments='').values_list('comments', flat=True)
        
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
        """Get AI recommendations using shared service"""
        ai_service = TeachingAIRecommendationService()
        return ai_service.get_recommendations(
            user=user,
            section_data=section_data,
            section_code=section_code,
            role="Coordinator"
        )
    
    def get_peer_evaluation_scores(self, user):
        """Calculate peer evaluation scores (evaluations from other staff members)"""
        # Peer evaluations are identified by having "Staff" in student_section field
        peer_evaluations = EvaluationResponse.objects.filter(
            evaluatee=user,
            student_section__icontains="Staff"
        )
        
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
        
        total_category_a = total_category_b = total_category_c = total_category_d = 0
        total_count_a = total_count_b = total_count_c = total_count_d = 0
        
        for response in peer_evaluations:
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
            'category_scores': [
                round(a_avg, 2),
                round(b_avg, 2),
                round(c_avg, 2),
                round(d_avg, 2)
            ],
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
            
            # Create section map for JavaScript
            section_map = {}
            if has_sections:
                for assignment in assigned_sections:
                    section_map[assignment.section.id] = assignment.section.code
            
            section_map_json = json.dumps(section_map)
            has_any_data = any(scores.get('has_data', False) for scores in section_scores.values()) if has_sections else False

            evaluation_history = self.get_evaluation_history(user)
            
            return render(request, 'main/faculty_profile_settings.html', {
                'user': user,
                'next_url': next_url,
                'assigned_sections': assigned_sections,
                'section_scores': section_scores,
                'section_scores_json': section_scores_json,
                'section_map_json': section_map_json,
                'peer_scores': peer_scores,
                'peer_scores_json': peer_scores_json,
                'has_any_data': has_any_data,
                'has_sections': has_sections,
                'evaluation_period_ended': can_view_evaluation_results('student'),
                'evaluation_history': evaluation_history,
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
        """Calculate scores for each assigned section"""
        section_scores = {}
        
        for section_assignment in assigned_sections:
            section = section_assignment.section
            section_code = section.code
            
            # Calculate scores for this specific section
            category_scores = compute_category_scores(user, section_code)
            a_avg, b_avg, c_avg, d_avg, total_percentage, total_a, total_b, total_c, total_d = category_scores
            
            # Get actual evaluation count for this section
            evaluation_count = EvaluationResponse.objects.filter(
                evaluatee=user,
                student_section=section_code
            ).count()
            
            # Calculate average rating (convert percentage to 5-point scale)
            average_rating = (total_percentage / 20) if evaluation_count > 0 else 0
            
            # Calculate rating distribution for this section
            rating_distribution = self.get_rating_distribution(user, section_code)
            
            # Include all sections, but mark if they have data
            has_data = total_percentage > 0 and evaluation_count > 0
            
            section_scores[section_code] = {
                'category_scores': [a_avg, b_avg, c_avg, d_avg],
                'total_percentage': total_percentage,
                'has_data': has_data,
                'section_name': section.code,
                'evaluation_count': evaluation_count,
                'average_rating': round(average_rating, 1),
                'rating_distribution': rating_distribution
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
        total_responses = 0
        
        # Initialize overall rating distribution
        overall_rating_distribution = [0, 0, 0, 0, 0]
        
        for section_assignment in assigned_sections:
            section = section_assignment.section
            section_code = section.code
            
            # Calculate scores for this specific section
            category_scores = compute_category_scores(user, section_code)
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
        """Get AI recommendations using shared service"""
        ai_service = TeachingAIRecommendationService()
        return ai_service.get_recommendations(
            user=user,
            section_data=section_data,
            section_code=section_code,
            role="Faculty"
        )
    
    def get_peer_evaluation_scores(self, user):
        """Calculate peer evaluation scores (evaluations from other staff members)"""
        # Peer evaluations are identified by having "Staff" in student_section field
        peer_evaluations = EvaluationResponse.objects.filter(
            evaluatee=user,
            student_section__icontains="Staff"
        )
        
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
        
        total_category_a = total_category_b = total_category_c = total_category_d = 0
        total_count_a = total_count_b = total_count_c = total_count_d = 0
        
        for response in peer_evaluations:
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
            'category_scores': [
                round(a_avg, 2),
                round(b_avg, 2),
                round(c_avg, 2),
                round(d_avg, 2)
            ],
            'total_percentage': round(total_percentage, 2),
            'evaluation_count': evaluation_count,
            'total_evaluations': evaluation_count,  # For template compatibility
            'positive_comments': positive_comments,
            'negative_comments': negative_comments
        }

    def post(self, request):
        """Handle POST requests for profile updates"""
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
                evaluation_responses = EvaluationResponse.objects.filter(
                    evaluatee=user,
                    comments__isnull=False
                ).exclude(comments='')
                
            else:
                # For a specific section, get comments FROM students about their experience
                try:
                    section_id = int(section_id)
                    section = Section.objects.get(id=section_id)
                    
                    # Get all students in this section
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
                    
                except (ValueError, Section.DoesNotExist) as e:
                    print(f"❌ Section Error: {e}")
                    evaluation_responses = EvaluationResponse.objects.none()
            
            # Extract just the comments (no student/section info)
            for response in evaluation_responses:
                if response.comments and response.comments.strip():
                    comments.append(response.comments.strip())
            
            print(f"   Total evaluation responses: {evaluation_responses.count()}")
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
        
        evaluation_history = []
        
        # Get processed evaluation results from EvaluationResult model for COMPLETED periods ONLY
        # Only show results from periods that are marked as inactive (completed)
        evaluation_results = EvaluationResult.objects.filter(
            user=user,
            evaluation_period__is_active=False  # Only show completed periods, not current
        ).select_related('evaluation_period', 'section').order_by('-evaluation_period__start_date')
        
        # Add processed results to history
        for result in evaluation_results:
            # Get student comments for this period
            # Filter by submission date within the evaluation period's date range
            comments = []
            responses = EvaluationResponse.objects.filter(
                evaluatee=user,
                submitted_at__gte=result.evaluation_period.start_date,
                submitted_at__lte=result.evaluation_period.end_date
            ).exclude(comments__isnull=True).exclude(comments='')
            
            for response in responses:
                if response.comments:
                    comments.append(response.comments)
            
            # gather saved AI recommendations for this period
            rec_qs = AiRecommendation.objects.filter(user=user, evaluation_period=result.evaluation_period).order_by('-created_at')
            rec_list = []
            for r in rec_qs:
                rec_list.append({
                    'title': r.title or 'Recommendation',
                    'description': r.description or r.recommendation or '',
                    'priority': r.priority or '',
                    'reason': r.reason or ''
                })

            evaluation_history.append({
                'period_name': result.evaluation_period.name,
                'evaluation_period_id': result.evaluation_period.id,
                'period_start_date': result.evaluation_period.start_date,
                'period_end_date': result.evaluation_period.end_date,
                'date': result.calculated_at,
                'section': result.section.code if result.section else 'All Sections',
                'overall_percentage': result.total_percentage,
                'average_rating': result.average_rating,
                'category_scores': [
                    result.category_a_score,
                    result.category_b_score, 
                    result.category_c_score,
                    result.category_d_score
                ],
                'total_responses': result.total_responses,
                'is_processed': True,
                'source': 'Completed Period',
                'recommendations': rec_list,
                'comments': comments  # Populated with student comments
            })
        
        # NOTE: Current evaluation results are NOT shown here
        # Current results are accessible from the profile settings dropdown
        # They will move to history only after a NEW evaluation period is released
        
        # Sort by date (most recent first)
        evaluation_history.sort(key=lambda x: x['date'], reverse=True)
        
        # Calculate summary statistics
        total_evaluations = len(evaluation_history)
        average_percentage = sum([eval['overall_percentage'] for eval in evaluation_history]) / total_evaluations if total_evaluations > 0 else 0
        latest_score = evaluation_history[0]['overall_percentage'] if total_evaluations > 0 else 0
        
        # Get unique sections from evaluation history for filtering
        sections_in_history = list(set([eval['section'] for eval in evaluation_history if eval['section'] != 'All Sections']))
        
        # Get user's assigned sections for all roles (include sections even if no data)
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
            'sections_in_history': sections_in_history,
            'user_sections': user_sections
        }
        
        return render(request, 'main/evaluation_history.html', context)
    
def process_evaluation_results_for_user(user, evaluation_period=None):
    """
    Process evaluation responses and create/update EvaluationResult records for a specific user
    CRITICAL: Only processes responses within the specified period's date range
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
    
    # CRITICAL FIX: Filter responses by the evaluation period's date range
    # This ensures we only calculate results for responses submitted during THIS period
    responses = EvaluationResponse.objects.filter(
        evaluatee=user,
        submitted_at__gte=evaluation_period.start_date,
        submitted_at__lte=evaluation_period.end_date
    )
    
    if not responses.exists():
        return None
    
    # Calculate overall scores using responses from THIS period only
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
    This is called when a period is being archived/deactivated
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

def process_all_evaluation_results():
    """
    Process evaluation results for all staff members (Faculty, Coordinators, Deans)
    after evaluation period ends - THIS IS CALLED WHEN ADMIN UNRELEASES EVALUATION
    """
    try:
        # Get or create the evaluation period that just ended
        current_period = EvaluationPeriod.objects.filter(
            evaluation_type='student',
            is_active=True
        ).first()
        
        if not current_period:
            # Create a new evaluation period for this cycle
            current_period = EvaluationPeriod.objects.create(
                name=f"Student Evaluation {timezone.now().strftime('%B %Y')}",
                evaluation_type='student',
                start_date=timezone.now() - timezone.timedelta(days=30),  # Assuming 30-day period
                end_date=timezone.now(),
                is_active=False  # Mark as ended
            )
        else:
            # Mark the existing period as inactive/ended
            current_period.is_active = False
            current_period.end_date = timezone.now()
            current_period.save()
        
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


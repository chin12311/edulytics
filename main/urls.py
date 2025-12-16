from django.urls import path
from . import views
from django.conf.urls.static import static
from .views import (
    UpdateUser, CoordinatorDetailView, DeanDetailView, SelectStudentView, EvaluationConfigView, 
    DeanProfileSettingsView, CoordinatorProfileSettingsView, FacultyProfileSettingsView,
    release_student_evaluation, unrelease_student_evaluation,
    release_peer_evaluation, unrelease_peer_evaluation,
    release_upward_evaluation, unrelease_upward_evaluation,
    release_dean_evaluation, unrelease_dean_evaluation,
    submit_evaluation, submit_upward_evaluation, submit_dean_evaluation, evaluated, evaluation_form_staffs, evaluation_form_upward, evaluation_form_dean,
    assign_section, remove_section_assignment, upward_evaluation_terms, upward_terms_agree
)
from .decorators import evaluation_results_required

app_name = 'main'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('select_student/<int:student_id>/', views.SelectStudentView.as_view(), name='select_student'), 
    path('update/<int:user_Id>/', views.UpdateUser.as_view(), name='update'),
    path('faculty/', views.FacultyOnlyView.as_view(), name='faculty'),
    path('coordinator/', views.CoordinatorOnlyView.as_view(), name='coordinators'),
    path('dean/', views.DeanOnlyView.as_view(), name='deans'),
    path('delete/<int:user_id>/', views.DeleteAccountView.as_view(), name='delete_account'),
    path('update/<int:user_Id>/', views.UpdateUser.as_view(), name='update_user'),
    path('evaluation/', views.EvaluationView.as_view(), name='evaluation'),
    path('coordinator/detail/<int:id>/', views.CoordinatorDetailView.as_view(), name='coordinator_detail'),
    path('faculty/detail/<int:id>/', views.CoordinatorDetailView.as_view(), name='faculty_detail'),
    path('dean/detail/<int:id>/', views.DeanDetailView.as_view(), name='dean_detail'),
    path('evaluationconfig/', views.EvaluationConfigView.as_view(), name='evaluationconfig'),
    # Make sure these function-based views are referenced correctly:
    path('release-evaluation/', views.release_student_evaluation, name='release_evaluation'),
    path('unrelease-evaluation/', views.unrelease_student_evaluation, name='unrelease_evaluation'),
    path('release/peer/', views.release_peer_evaluation, name='release_peer_evaluation'),
    path('unrelease/peer/', views.unrelease_peer_evaluation, name='unrelease_peer_evaluation'),
    path('release/upward/', views.release_upward_evaluation, name='release_upward_evaluation'),
    path('unrelease/upward/', views.unrelease_upward_evaluation, name='unrelease_upward_evaluation'),
    path('release/dean/', views.release_dean_evaluation, name='release_dean_evaluation'),
    path('unrelease/dean/', views.unrelease_dean_evaluation, name='unrelease_dean_evaluation'),
    path('release/student_upward/', views.release_student_upward_evaluation, name='release_student_upward_evaluation'),
    path('unrelease/student_upward/', views.unrelease_student_upward_evaluation, name='unrelease_student_upward_evaluation'),
    path('evaluationform/', views.EvaluationFormView.as_view(), name='evaluationform'),
    path('submit_evaluation/', views.submit_evaluation, name='submit_evaluation'),
    path('upward-evaluation-terms/', views.upward_evaluation_terms, name='upward_evaluation_terms'),
    path('upward-terms-agree/', views.upward_terms_agree, name='upward_terms_agree'),
    path('evaluation-upward/', views.evaluation_form_upward, name='evaluation_form_upward'),
    path('submit-upward-evaluation/', views.submit_upward_evaluation, name='submit_upward_evaluation'),
    path('evaluation-dean/', views.evaluation_form_dean, name='evaluation_form_dean'),
    path('submit-dean-evaluation/', views.submit_dean_evaluation, name='submit_dean_evaluation'),
    
    # Student Upward Evaluation (Student → Coordinator)
    path('student-upward-evaluation-terms/', views.student_upward_evaluation_terms, name='student_upward_evaluation_terms'),
    path('student-upward-terms-agree/', views.student_upward_terms_agree, name='student_upward_terms_agree'),
    path('evaluation-student-upward/', views.evaluation_form_student_upward, name='evaluation_form_student_upward'),
    path('submit-student-upward-evaluation/', views.submit_student_upward_evaluation, name='submit_student_upward_evaluation'),
    
    path('evaluate/', views.evaluated, name='evaluate'),
    path('dean/profile-settings/', evaluation_results_required(views.DeanProfileSettingsView.as_view()), name='dean_profile_settings'),
    path('coordinator/settings/',(views.CoordinatorProfileSettingsView.as_view()), name='coordinator_profile_settings'),
    path('faculty/settings/',(views.FacultyProfileSettingsView.as_view()), name='faculty_profile_settings'),
    path('evaluationform_staffs/', views.evaluation_form_staffs, name='evaluationform_staffs'),
    path('assign-section/<int:user_id>/', views.assign_section, name='assign-section'),
    path('update/<int:user_Id>/', views.UpdateUser.as_view(), name='update-user'),
    path('update-profile/<int:user_Id>/remove-assignment/<int:assignment_id>/', views.UpdateUser.as_view(), name='remove-section-assignment'),
    path('remove-section-assignment/<int:assignment_id>/', views.remove_section_assignment, name='remove-section-assignment'),
    path('api/ai-recommendations/', views.AIRecommendationsAPIView.as_view(), name='ai_recommendations'),
    path('api/student-comments/', views.StudentCommentsAPIView.as_view(), name='student_comments'),
    path('api/evaluation-history/', views.api_evaluation_history, name='api_evaluation_history'),
    path('api/evaluation-history/<int:history_id>/', views.api_evaluation_history_detail, name='api_evaluation_history_detail'),
    path('api/evaluation-history/period/<int:period_id>/', views.api_evaluation_history_by_period, name='api_evaluation_history_by_period'),
    path('admin-control/', views.admin_evaluation_control, name='admin_control'),
    path('manage-evaluations/', views.manage_evaluations, name='manage_evaluations'),
    path('activity-logs/', views.admin_activity_logs, name='activity_logs'),
    path('process-results/', views.process_results, name='process_results'),
    path('reset-failures/', views.reset_failures, name='reset_failures'),
    path('reset-selected-failures/', views.reset_selected_failures, name='reset_selected_failures'),
    path('evaluation-history/', views.EvaluationHistoryView.as_view(), name='evaluation_history'),
    path('release-all-evaluations/', views.release_all_evaluations, name='release_all_evaluations'),
    path('unrelease-all-evaluations/', views.unrelease_all_evaluations, name='unrelease_all_evaluations'),
    path('export-accounts/', views.ExportAccountsView.as_view(), name='export_accounts'),
    path('import-accounts/', views.ImportAccountsView.as_view(), name='import_accounts'),
    path('manage-evaluation-questions/', views.manage_evaluation_questions, name='manage_evaluation_questions'),
    path('update-evaluation-question/<str:question_type>/<int:question_id>/', views.update_evaluation_question, name='update_evaluation_question'),
    path('bulk-update-evaluation-questions/', views.bulk_update_evaluation_questions, name='bulk_update_evaluation_questions'),
    path('reset-evaluation-questions/', views.reset_evaluation_questions, name='reset_evaluation_questions'),
    path('manage-institutes-courses/', views.manage_institutes_courses, name='manage_institutes_courses'),
    
    # Institute & Course Management API
    path('api/institutes/', views.api_list_institutes, name='api_list_institutes'),
    path('api/institutes/add/', views.api_add_institute, name='api_add_institute'),
    path('api/institutes/<int:institute_id>/', views.api_get_institute, name='api_get_institute'),
    path('api/institutes/<int:institute_id>/update/', views.api_update_institute, name='api_update_institute'),
    path('api/institutes/<int:institute_id>/delete/', views.api_delete_institute, name='api_delete_institute'),
    path('api/courses/', views.api_list_courses, name='api_list_courses'),
    path('api/courses/add/', views.api_add_course, name='api_add_course'),
    path('api/courses/<int:course_id>/', views.api_get_course, name='api_get_course'),
    path('api/courses/<int:course_id>/update/', views.api_update_course, name='api_update_course'),
    path('api/courses/<int:course_id>/delete/', views.api_delete_course, name='api_delete_course'),
    
    # PDF Download for Evaluation History
    path('download-evaluation-history/<int:period_id>/', views.download_evaluation_history_pdf, name='download_evaluation_history_pdf'),
]
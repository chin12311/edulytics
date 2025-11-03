from django.urls import path
from . import views
from django.conf.urls.static import static
from .views import (
    UpdateUser, CoordinatorDetailView, SelectStudentView, EvaluationConfigView, 
    DeanProfileSettingsView, CoordinatorProfileSettingsView, FacultyProfileSettingsView,
    release_student_evaluation, unrelease_student_evaluation,
    release_peer_evaluation, unrelease_peer_evaluation,
    submit_evaluation, evaluated, evaluation_form_staffs,
    assign_section, remove_section_assignment
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
    path('evaluationconfig/', views.EvaluationConfigView.as_view(), name='evaluationconfig'),
    # Make sure these function-based views are referenced correctly:
    path('release-evaluation/', views.release_student_evaluation, name='release_evaluation'),
    path('unrelease-evaluation/', views.unrelease_student_evaluation, name='unrelease_evaluation'),
    path('release/peer/', views.release_peer_evaluation, name='release_peer_evaluation'),
    path('unrelease/peer/', views.unrelease_peer_evaluation, name='unrelease_peer_evaluation'),
    path('evaluationform/', views.EvaluationFormView.as_view(), name='evaluationform'),
    path('submit_evaluation/', views.submit_evaluation, name='submit_evaluation'),
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
    path('admin-control/', views.admin_evaluation_control, name='admin_control'),
    path('activity-logs/', views.admin_activity_logs, name='activity_logs'),
    path('process-results/', views.process_results, name='process_results'),
    path('reset-failures/', views.reset_failures, name='reset_failures'),
    path('reset-selected-failures/', views.reset_selected_failures, name='reset_selected_failures'),
    path('evaluation-history/', views.EvaluationHistoryView.as_view(), name='evaluation_history'),
    path('release-all-evaluations/', views.release_all_evaluations, name='release_all_evaluations'),
    path('unrelease-all-evaluations/', views.unrelease_all_evaluations, name='unrelease_all_evaluations'),
    path('export-accounts/', views.ExportAccountsView.as_view(), name='export_accounts'),
    path('import-accounts/', views.ImportAccountsView.as_view(), name='import_accounts'),
    
]
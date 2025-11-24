from django.contrib import admin
from .models import UserProfile
from .models import *

# Register your models here.



class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'role_display', 'institute', 'student_section', 'student_info')
    list_filter = ('role', 'institute', 'course', 'section')
    search_fields = ('user__username', 'display_name', 'studentnumber', 'user__email', 'institute')
    
    def role_display(self, obj):
        return obj.get_role_display()
    role_display.short_description = 'Role'
    role_display.admin_order_field = 'role'
    
    def student_section(self, obj):
        if obj.role == Role.STUDENT and obj.section:
            return obj.section
        return "-"
    student_section.short_description = 'Section'
    
    def student_info(self, obj):
        if obj.role == Role.STUDENT:
            info_parts = []
            if obj.studentnumber:
                info_parts.append(obj.studentnumber)
            if obj.course:
                info_parts.append(obj.course)
            return " - ".join(info_parts) if info_parts else "-"
        return "-"
    student_info.short_description = 'Student Info'


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'course')  # Display user and course in the list view
    list_filter = ('course',)  # Enable filtering by course
    search_fields = ('user__username', 'course')  # Allow searching by username and course

# Register Evaluation model with its Admin using the decorator
@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    # Display evaluator name, evaluation type, release status, and created at time
    list_display = ('get_evaluator', 'evaluation_type', 'is_released', 'created_at')
    
    # Add an option to filter based on the release status
    list_filter = ('is_released',)

    # Define the 'get_evaluator' method to safely handle None values
    def get_evaluator(self, obj):
        if obj.evaluator:
            return obj.evaluator.get_full_name() or obj.evaluator.username
        return "Unknown Evaluator"
    
    get_evaluator.short_description = 'Evaluator'

    # Actions for releasing and un-releasing evaluations
    actions = ['release_evaluation', 'unrelease_evaluation']

    # Display the questions in the Django Admin form as a read-only field
    readonly_fields = ('display_questions',)

    def release_evaluation(self, request, queryset):
        queryset.update(is_released=True)
        self.message_user(request, "Selected evaluations have been released.")

    def unreleased_evaluation(self, request, queryset):
        queryset.update(is_released=False)
        self.message_user(request, "Selected evaluations have been unpublished.")

    def display_questions(self, obj):
        if obj.evaluation_type == 'student':
            return """
            ### Evaluation Form for College Teachers

            Rating Scale
            5 - Outstanding
            4 - Very Satisfactory
            3 - Satisfactory
            2 - Unsatisfactory
            1 - Poor

            #### Category A: Mastery of the Subject (5 questions)
            question1. Demonstrates mastery of the subject and the ability to translate competencies into meaningful lessons.
            question2. Shows ability to stimulate independent and critical thinking
            question3. Is focused and explains the lesson clearly
            question4. Knowledgable and uses a variety of teaching strategies.
            question5. Demonstrates enthusiasm for the subject matter

            #### Category B: Classroom Management (5 questions)
            question6. Establishes and communicates clearly parameters for student classroom behaviour based on student handbook and OVPAA Guidelines for the conduct of Flexible Learning Modalities.
            question7. Promote self-discipline, respect and treats all students in fair and equitable manner.
            question8. Keeps accurate accounting of student's attendance and records
            question9. Demonstrates fairness and consistency in handling student's problems.
            question10. Maintains harmonious relations with students characterized by mutual respect and understanding.

            #### Category C: Compliance to Policies (5 questions)
            question11. Reports to class regularly.
            question12. Demonstrates exceptional punctuality in observing work hours and college official functions.
            question13. Returns quizzes, examination results, assignments and other activities on time.
            question14. Informs the students on their academic performances and grades.
            question15. Uses Google Meet and Classroom as the official platform for online classes.

            #### Category D: Personality (4 questions)
            question16. Commands respect by example in appearance, manners and behaviour and language.
            question17. Maintains a good disposition.
            question18. Relates well with students in a pleasing manner.
            question19. Possesses a sense of balance that combines good humor, sincerity and fairness when confronted with difficulties in the classroom.

            TOTAL: 19 questions
            """
        elif obj.evaluation_type == 'peer':
            return """
            ### Peer-to-Peer Evaluation Form

            Rating Scale
            5 - Outstanding
            4 - Very Satisfactory
            3 - Satisfactory
            2 - Unsatisfactory
            1 - Poor

            #### Category 1: Communication and Collaboration (4 questions)
            question1. Effectively communicates with others in the workplace
            question2. Listens actively and values others' opinions and perspectives
            question3. Shows respect in all professional interactions
            question4. Contributes actively to team discussions and collaborative efforts

            #### Category 2: Responsibility and Professionalism (4 questions)
            question5. Completes assigned duties and responsibilities on time
            question6. Demonstrates reliability and accountability in work
            question7. Takes initiative when appropriate and needed
            question8. Makes valuable contributions to institutional goals and objectives

            #### Category 3: Leadership and Work Ethic (7 questions)
            question9. Shows leadership qualities when needed or appropriate
            question10. Helps resolve conflicts constructively when they arise
            question11. Accepts and applies feedback for personal and professional improvement
            question12. Maintains focus and engagement in professional duties
            question13. Is prepared and organized in carrying out responsibilities
            question14. Demonstrates strong work ethic and professional integrity
            question15. Would you want to work with this colleague again in future projects?

            TOTAL: 15 questions
            """
        else:
            return "Unknown evaluation type."
    
    display_questions.short_description = 'Evaluation Questions'

    release_evaluation.short_description = "Mark as Released"
    unreleased_evaluation.short_description = "Mark as Unreleased"

admin.site.register(UserProfile, UserProfileAdmin)


class EvaluationResponseAdmin(admin.ModelAdmin):
    list_display = ['evaluator', 'evaluatee', 'get_student_number_or_id', 'comments_preview']
    search_fields = ['evaluator__username', 'evaluator__first_name', 'evaluator__last_name', 'comments', 'evaluatee__username']
    list_filter = ['evaluator', 'evaluatee']
    
    # Include comments in the fields - supports up to 19 questions for student evaluations
    fields = ['evaluator', 'evaluatee', 'comments'] + [f'question{i}' for i in range(1, 20)]
    
    # Make fields read-only as needed
    readonly_fields = ['evaluator', 'evaluatee'] + [f'question{i}' for i in range(1, 20)]

    def comments_preview(self, obj):
        if obj.comments:
            return obj.comments[:50] + "..." if len(obj.comments) > 50 else obj.comments
        return "No comments"
    comments_preview.short_description = 'Comments Preview'

    def get_student_number_or_id(self, obj):
        profile = getattr(obj.evaluator, 'userprofile', None)
        if profile and profile.role == 'Student':
            return profile.studentnumber
        return f"ID: {obj.id}"

    get_student_number_or_id.short_description = 'Student Number / ID'

    def has_add_permission(self, request):
        return False  

admin.site.register(EvaluationResponse, EvaluationResponseAdmin)
admin.site.register(Section)
admin.site.register(SectionAssignment)
admin.site.register(AiRecommendation)

# Register EvaluationResult
@admin.register(EvaluationResult)
class EvaluationResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'evaluation_period', 'total_percentage', 'total_responses', 'calculated_at')
    list_filter = ('evaluation_period', 'total_percentage')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'evaluation_period__name')
    readonly_fields = ('user', 'evaluation_period', 'section', 'calculated_at', 'last_updated', 'total_percentage', 'average_rating', 'category_a_score', 'category_b_score', 'category_c_score', 'category_d_score')
    ordering = ('-calculated_at',)
    
    def has_add_permission(self, request):
        return False  # Results should be auto-calculated
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete

# Register EvaluationHistory
@admin.register(EvaluationHistory)
class EvaluationHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'evaluation_period', 'evaluation_type', 'total_percentage', 'total_responses', 'archived_at')
    list_filter = ('evaluation_type', 'evaluation_period', 'archived_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'evaluation_period__name')
    readonly_fields = ('user', 'evaluation_period', 'evaluation_type', 'section', 'archived_at', 'period_start_date', 'period_end_date', 'total_percentage', 'average_rating', 'category_a_score', 'category_b_score', 'category_c_score', 'category_d_score')
    ordering = ('-archived_at', '-period_start_date')
    
    def has_add_permission(self, request):
        return False  # History should be auto-created when archiving
    
    def has_change_permission(self, request, obj=None):
        return False  # History records should be immutable
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete

# Register AdminActivityLog
@admin.register(AdminActivityLog)
class AdminActivityLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'admin', 'action', 'target_user', 'target_section', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('admin__username', 'target_user__username', 'description', 'ip_address')
    readonly_fields = ('timestamp', 'admin', 'action', 'target_user', 'target_section', 'description', 'ip_address')
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete logs
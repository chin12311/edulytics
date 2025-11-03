from django.db import models
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q

# 🚫 Removed: from .models import SectionAssignment, Section, UserProfile
# Never import models from the same file — they're already available below.

# ------------------------
# Role Choices
# ------------------------
class Role(models.TextChoices):
    STUDENT = 'Student', 'Student'
    DEAN = 'Dean', 'Dean'
    COORDINATOR = 'Coordinator', 'Coordinator'
    FACULTY = 'Faculty', 'Faculty'
    ADMIN = 'Admin', 'Admin'

class EvaluationFailureLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    evaluation_date = models.DateTimeField(default=timezone.now)
    score = models.FloatField()
    passing_score = models.FloatField(default=70.0)
    alert_sent = models.BooleanField(default=False)
    alert_sent_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-evaluation_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.score}% - {self.evaluation_date.strftime('%Y-%m-%d')}"

# ------------------------
# User Profile
# ------------------------
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Add this field for display names with spaces and capitalization
    display_name = models.CharField(max_length=150, blank=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT
    )

    studentnumber = models.CharField(max_length=7, blank=True, null=True)
    course = models.CharField(max_length=50, blank=True, null=True)

    section = models.ForeignKey(
        'Section',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="students"
    )

    institute = models.CharField(max_length=50, blank=True, null=True)

    # ADD THESE FIELDS FOR FAILURE TRACKING
    evaluation_failure_count = models.IntegerField(default=0)
    last_evaluation_failure_date = models.DateTimeField(null=True, blank=True)
    failure_alert_sent = models.BooleanField(default=False)

    def clean(self):
        if self.role == Role.STUDENT:
            if not self.studentnumber:
                raise ValidationError("Student must have a student number.")
            if not self.course:
                raise ValidationError("Student must have a course.")
            if not self.user.email.endswith("@cca.edu.ph"):
                raise ValidationError("Students must use a @cca.edu.ph email.")
        else:
            if self.studentnumber or self.course or self.section:
                raise ValidationError(
                    f"{self.role} should not have studentnumber, course, or section."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        name = self.display_name if self.display_name else self.user.username
        return f"{name} ({self.role})"

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(role=Role.STUDENT, studentnumber__isnull=False, course__isnull=False) |
                      ~Q(role=Role.STUDENT),
                name="student_fields_required_for_students"
            ),
            models.CheckConstraint(
                check=Q(role=Role.STUDENT) | (Q(studentnumber__isnull=True) & Q(course__isnull=True) & Q(section__isnull=True)),
                name="non_students_cannot_have_student_fields"
            ),
            models.UniqueConstraint(
                fields=["studentnumber"],
                condition=Q(role=Role.STUDENT),
                name="unique_studentnumber_for_students"
            ),
        ]

# ------------------------
# Section
# ------------------------
class Section(models.Model):
    YEAR_CHOICES = [
        (1, "1st Year"),
        (2, "2nd Year"),
        (3, "3rd Year"),
        (4, "4th Year"),
    ]

    code = models.CharField(max_length=10, unique=True)  # e.g., C102
    year_level = models.IntegerField(choices=YEAR_CHOICES)

    def __str__(self):
        return f"{self.code} ({self.get_year_level_display()})"

# ------------------------
# Evaluation Period (MUST BE DEFINED BEFORE Evaluation)
# ------------------------
class EvaluationPeriod(models.Model):
    """Track evaluation periods/semesters"""
    EVALUATION_TYPE_CHOICES = [
        ('student', 'Student'),
        ('peer', 'Peer'),
    ]
    
    name = models.CharField(max_length=100)  # e.g., "1st Semester 2024"
    evaluation_type = models.CharField(
        max_length=10,
        choices=EVALUATION_TYPE_CHOICES,
        default='student'
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        unique_together = ['name', 'evaluation_type']

    def __str__(self):
        return f"{self.name} ({self.evaluation_type})"

# ------------------------
# Evaluation
# ------------------------
class Evaluation(models.Model):
    EVALUATION_TYPE_CHOICES = [
        ('student', 'Student'),
        ('peer', 'Peer'),
    ]

    evaluator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    evaluation_type = models.CharField(
        max_length=10,
        choices=EVALUATION_TYPE_CHOICES,
        default='student'
    )
    is_released = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Link to evaluation period
    evaluation_period = models.ForeignKey(
        EvaluationPeriod, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )

    # Add these methods
    @classmethod
    def is_evaluation_period_active(cls, evaluation_type='student'):
        """Check if evaluation period is active (form is released)"""
        return cls.objects.filter(is_released=True, evaluation_type=evaluation_type).exists()
    
    @classmethod
    def can_view_results(cls, evaluation_type='student'):
        """Check if users can view results (form is unreleased = period ended)"""
        return not cls.is_evaluation_period_active(evaluation_type)

    def save(self, *args, **kwargs):
        # Auto-assign active evaluation period if not set
        if not self.evaluation_period:
            active_period = EvaluationPeriod.objects.filter(
                evaluation_type=self.evaluation_type,
                is_active=True
            ).first()
            if active_period:
                self.evaluation_period = active_period
        super().save(*args, **kwargs)

# ------------------------
# Evaluation Response
# ------------------------
class EvaluationResponse(models.Model):
    evaluator = models.ForeignKey(User, related_name='evaluations', on_delete=models.CASCADE)
    evaluatee = models.ForeignKey(User, related_name='evaluated_by', on_delete=models.CASCADE)

    # Student information
    student_number = models.CharField(max_length=20, blank=True, null=True)
    student_section = models.CharField(max_length=50, blank=True, null=True)
    
    # Timestamp
    submitted_at = models.DateTimeField(default=timezone.now)

    # Default answers
    question1 = models.CharField(max_length=50, default='Poor')
    question2 = models.CharField(max_length=50, default='Poor')
    question3 = models.CharField(max_length=50, default='Poor')
    question4 = models.CharField(max_length=50, default='Poor')
    question5 = models.CharField(max_length=50, default='Poor')
    question6 = models.CharField(max_length=50, default='Poor')
    question7 = models.CharField(max_length=50, default='Poor')
    question8 = models.CharField(max_length=50, default='Poor')
    question9 = models.CharField(max_length=50, default='Poor')
    question10 = models.CharField(max_length=50, default='Poor')
    question11 = models.CharField(max_length=50, default='Poor')
    question12 = models.CharField(max_length=50, default='Poor')
    question13 = models.CharField(max_length=50, default='Poor')
    question14 = models.CharField(max_length=50, default='Poor')
    question15 = models.CharField(max_length=50, default='Poor')

    # ADD COMMENTS FIELD
    comments = models.TextField(blank=True, null=True, verbose_name="Additional Comments/Suggestions")

    class Meta:
        unique_together = ('evaluator', 'evaluatee')

    def __str__(self):
        return f"{self.evaluator.get_full_name() or self.evaluator.username}'s Evaluation for {self.evaluatee.get_full_name() or self.evaluatee.username}"

# ------------------------
# Evaluation Result
# ------------------------
class EvaluationResult(models.Model):
    """Store aggregated evaluation results for each period"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="evaluation_results")
    evaluation_period = models.ForeignKey(EvaluationPeriod, on_delete=models.CASCADE)
    section = models.ForeignKey('Section', on_delete=models.CASCADE, null=True, blank=True)
    
    # Category scores (using the 4-category system)
    category_a_score = models.FloatField(default=0.0)  # Mastery of Subject Matter (35%)
    category_b_score = models.FloatField(default=0.0)  # Classroom Management (25%)
    category_c_score = models.FloatField(default=0.0)  # Compliance to Policies (20%)
    category_d_score = models.FloatField(default=0.0)  # Personality (20%)
    
    # Overall scores
    total_percentage = models.FloatField(default=0.0)
    average_rating = models.FloatField(default=0.0)  # 1-5 scale
    
    # Statistics
    total_responses = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=15)
    
    # Rating distribution
    poor_count = models.IntegerField(default=0)
    unsatisfactory_count = models.IntegerField(default=0)
    satisfactory_count = models.IntegerField(default=0)
    very_satisfactory_count = models.IntegerField(default=0)
    outstanding_count = models.IntegerField(default=0)
    
    # Timestamps
    calculated_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'evaluation_period', 'section']
        ordering = ['-evaluation_period__start_date', 'user__username']

    def __str__(self):
        section_info = f" - {self.section.code}" if self.section else ""
        return f"{self.user.username} - {self.evaluation_period.name}{section_info}"

    @property
    def category_percentages(self):
        """Calculate percentage of maximum for each category"""
        max_scores = [35, 25, 20, 20]  # Maximum possible for each category
        scores = [self.category_a_score, self.category_b_score, self.category_c_score, self.category_d_score]
        
        return [
            round((score / max_score) * 100, 2) if max_score > 0 else 0.0
            for score, max_score in zip(scores, max_scores)
        ]

    @property
    def rating_distribution_percentages(self):
        """Calculate percentage distribution of ratings"""
        total_ratings = sum([
            self.poor_count,
            self.unsatisfactory_count,
            self.satisfactory_count,
            self.very_satisfactory_count,
            self.outstanding_count
        ])
        
        if total_ratings == 0:
            return [0, 0, 0, 0, 0]
            
        return [
            round((self.poor_count / total_ratings) * 100, 2),
            round((self.unsatisfactory_count / total_ratings) * 100, 2),
            round((self.satisfactory_count / total_ratings) * 100, 2),
            round((self.very_satisfactory_count / total_ratings) * 100, 2),
            round((self.outstanding_count / total_ratings) * 100, 2)
        ]

# ------------------------
# Evaluation Comment
# ------------------------
class EvaluationComment(models.Model):
    """Store individual comments from evaluations"""
    evaluation_response = models.ForeignKey(EvaluationResponse, on_delete=models.CASCADE)
    evaluation_result = models.ForeignKey(EvaluationResult, on_delete=models.CASCADE, related_name="comments")
    comment = models.TextField()
    is_positive = models.BooleanField(default=True)
    sentiment_score = models.FloatField(null=True, blank=True)  # Optional: for AI analysis
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment for {self.evaluation_result.user.username} - {self.created_at.date()}"

# ------------------------
# Coordinator
# ------------------------
class Coordinator(models.Model):
    INSTITUTE_CHOICES = [
        ('IBM', 'Institute of Business and Management'),
        ('ICSLIS', 'Institute of Computing Studies and Library Information Science'),
        ('IEAS', 'Institute of Education, Arts and Services')
    ]

    institute = models.CharField(max_length=10, choices=INSTITUTE_CHOICES)

# ------------------------
# AI Recommendation
# ------------------------
class AiRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recommendations")
    recommendation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recommendation for {self.user.email} at {self.created_at}"

# ------------------------
# Admin Activity Log
# ------------------------
class AdminActivityLog(models.Model):
    ACTION_CHOICES = [
        ('create_account', 'Create Account'),
        ('update_account', 'Update Account'),
        ('delete_account', 'Delete Account'),
        ('assign_section', 'Assign Section'),
        ('remove_section', 'Remove Section'),
        ('release_evaluation', 'Release Evaluation'),
        ('unrelease_evaluation', 'Unrelease Evaluation'),
    ]
    
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="admin_activities")
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="targeted_by_admin")
    target_section = models.ForeignKey('Section', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.admin.username if self.admin else 'Unknown'} - {self.get_action_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

# ------------------------
# Section Assignment
# ------------------------
class SectionAssignment(models.Model):
    ROLE_CHOICES = [
        ('dean', 'Dean'),
        ('faculty', 'Faculty'),
        ('coordinator', 'Coordinator'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assigned_sections")
    section = models.ForeignKey('Section', on_delete=models.CASCADE, related_name="assigned_users")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def save(self, *args, **kwargs):
        # Always use the current role from UserProfile
        if hasattr(self.user, "userprofile"):
            self.role = self.user.userprofile.role.lower()
        super().save(*args, **kwargs)

    

    def __str__(self):
        return f"{self.user.username} → {self.section.code} ({self.role})"

# ------------------------
# Assign Section Function
# ------------------------
def assign_section(request, user_id):
    from .models import SectionAssignment  # ✅ local import here to avoid circular import

    if request.method == "POST":
        section_id = request.POST.get("section_id")
        section = get_object_or_404(Section, id=section_id)
        user_profile = get_object_or_404(UserProfile, user_id=user_id)

        SectionAssignment.objects.create(
            user=user_profile.user,
            section=section,
            role=user_profile.role.lower()  # match role from profile
        )
        return redirect("main:index")

    return redirect("main:index")

# ------------------------
# Utility Function
# ------------------------
def can_view_evaluation_results(evaluation_type='student'):
    """Check if users can view evaluation results (only when unreleased)"""
    return not Evaluation.objects.filter(
        is_released=True, 
        evaluation_type=evaluation_type
    ).exists()
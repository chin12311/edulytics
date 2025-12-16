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

# ------------------------
# Institute and Course Models
# ------------------------
class Institute(models.Model):
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Course(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, blank=True)
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE, related_name='courses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        unique_together = [['name', 'institute']]
    
    def __str__(self):
        return f"{self.name} - {self.institute.name}"

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

    # Student number format: XX-XXXX (e.g., 21-1766) - max 7 characters
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
    
    # Profile picture
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    # Irregular student flag - no section, can evaluate all instructors
    is_irregular = models.BooleanField(default=False)

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
            if self.user and not self.user.email.endswith("@cca.edu.ph"):
                raise ValidationError("Students must use a @cca.edu.ph email.")
        else:
            # Non-students should NOT have student fields (check for truthy values, not just existence)
            if self.studentnumber or self.course or self.section:
                raise ValidationError(
                    f"{self.role} should not have studentnumber, course, or section."
                )

    def save(self, *args, **kwargs):
        # Only call full_clean if skip_validation is not set
        # This prevents double validation
        if not kwargs.pop('skip_validation', False):
            self.full_clean()
        super().save(*args, **kwargs)
    
    def get_course_code(self):
        """Get the course code/acronym from the full course name"""
        if not self.course:
            return ""
        
        # Try to find the course in the database
        try:
            course_obj = Course.objects.filter(name=self.course).first()
            if course_obj and course_obj.code:
                return course_obj.code
        except:
            pass
        
        # Fallback to the full course name if no code found
        return self.course
    
    def get_institute_code(self):
        """Get the institute code/acronym from the full institute name"""
        if not self.institute:
            return ""
        
        # Try to find the institute in the database
        try:
            institute_obj = Institute.objects.filter(name=self.institute).first()
            if institute_obj and institute_obj.code:
                return institute_obj.code
        except:
            pass
        
        # Fallback to the full institute name if no code found
        return self.institute

    def __str__(self):
        name = self.display_name if self.display_name else self.user.username
        return f"{name} ({self.role})"

    class Meta:
        ordering = ['-id']  # Order by ID descending to show newest first
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
        ('upward', 'Upward'),
        ('dean', 'Dean'),
        ('student_upward', 'Student Upward'),
    ]
    
    name = models.CharField(max_length=100)  # e.g., "1st Semester 2024"
    evaluation_type = models.CharField(
        max_length=20,
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
        ('upward', 'Upward'),
        ('dean', 'Dean'),
        ('student_upward', 'Student Upward'),
    ]
    
    EVALUATOR_CHOICES = [
        ('students', 'Students'),
        ('peer', 'Peer'),
    ]

    evaluator = models.CharField(
        max_length=20,
        choices=EVALUATOR_CHOICES,
        default='students',
        help_text='Who evaluates: students evaluate teachers, peer means teachers evaluate each other'
    )
    evaluation_type = models.CharField(
        max_length=20,
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
    evaluator = models.ForeignKey(User, related_name='evaluations', on_delete=models.CASCADE, db_index=True)
    evaluatee = models.ForeignKey(User, related_name='evaluated_by', on_delete=models.CASCADE, db_index=True)
    evaluation_period = models.ForeignKey(EvaluationPeriod, on_delete=models.CASCADE, null=True, blank=True, db_index=True)

    # Student information
    student_number = models.CharField(max_length=20, blank=True, null=True)
    student_section = models.CharField(max_length=50, blank=True, null=True)
    
    # Timestamp
    submitted_at = models.DateTimeField(default=timezone.now, db_index=True)

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
    question16 = models.CharField(max_length=50, default='Poor')
    question17 = models.CharField(max_length=50, default='Poor')
    question18 = models.CharField(max_length=50, default='Poor')
    question19 = models.CharField(max_length=50, default='Poor')

    # ADD COMMENTS FIELD
    comments = models.TextField(blank=True, null=True, verbose_name="Additional Comments/Suggestions")

    class Meta:
        # Allow same evaluator to evaluate same evaluatee in different periods
        # But prevent duplicate evaluation within the same period
        unique_together = ('evaluator', 'evaluatee', 'evaluation_period')

    def __str__(self):
        return f"{self.evaluator.get_full_name() or self.evaluator.username}'s Evaluation for {self.evaluatee.get_full_name() or self.evaluatee.username}"

# ------------------------
# Irregular Student Evaluation (Separate from regular evaluations)
# ------------------------
class IrregularEvaluation(models.Model):
    evaluator = models.ForeignKey(User, related_name='irregular_evaluations', on_delete=models.CASCADE, db_index=True)
    evaluatee = models.ForeignKey(User, related_name='irregular_evaluated_by', on_delete=models.CASCADE, db_index=True)
    evaluation_period = models.ForeignKey(EvaluationPeriod, on_delete=models.CASCADE, null=True, blank=True, db_index=True)

    # Student information
    student_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Timestamp
    submitted_at = models.DateTimeField(default=timezone.now, db_index=True)

    # Evaluation questions (same as regular)
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
    question16 = models.CharField(max_length=50, default='Poor')
    question17 = models.CharField(max_length=50, default='Poor')
    question18 = models.CharField(max_length=50, default='Poor')
    question19 = models.CharField(max_length=50, default='Poor')

    comments = models.TextField(blank=True, null=True, verbose_name="Additional Comments/Suggestions")

    class Meta:
        unique_together = ('evaluator', 'evaluatee', 'evaluation_period')
        verbose_name = "Irregular Student Evaluation"
        verbose_name_plural = "Irregular Student Evaluations"

    def __str__(self):
        return f"[IRREGULAR] {self.evaluator.get_full_name() or self.evaluator.username}'s Evaluation for {self.evaluatee.get_full_name() or self.evaluatee.username}"

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
# Evaluation History
# ------------------------
class EvaluationHistory(models.Model):
    """
    Dedicated table for storing historical evaluation results.
    This separates archived evaluation data from current active results.
    Makes it easy to query and display evaluation history.
    """
    EVALUATION_TYPE_CHOICES = [
        ('student', 'Student Evaluation'),
        ('peer', 'Peer Evaluation'),
        ('upward', 'Upward Evaluation'),
        ('dean', 'Dean Evaluation'),
        ('student_upward', 'Student Upward Evaluation'),
    ]
    
    # Link to the user being evaluated
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="evaluation_history")
    
    # Evaluation period information
    evaluation_period = models.ForeignKey(
        EvaluationPeriod, 
        on_delete=models.CASCADE,
        related_name="history_records"
    )
    evaluation_type = models.CharField(
        max_length=20, 
        choices=EVALUATION_TYPE_CHOICES,
        default='student'
    )
    
    # Section information
    section = models.ForeignKey(
        'Section', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="history_records"
    )
    
    # Category scores (same as EvaluationResult)
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
    archived_at = models.DateTimeField(auto_now_add=True)
    period_start_date = models.DateTimeField(null=True, blank=True)  # Snapshot of period start
    period_end_date = models.DateTimeField(null=True, blank=True)    # Snapshot of period end
    
    class Meta:
        unique_together = ['user', 'evaluation_period', 'section']
        ordering = ['-period_start_date', 'user__username']
        indexes = [
            models.Index(fields=['user', '-period_start_date']),
            models.Index(fields=['evaluation_type', '-period_start_date']),
        ]
    
    def __str__(self):
        section_info = f" - {self.section.code}" if self.section else ""
        return f"{self.user.username} - {self.evaluation_period.name}{section_info} - {self.total_percentage}%"
    
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
    
    @classmethod
    def create_from_result(cls, result):
        """Create a history record from an EvaluationResult"""
        return cls.objects.create(
            user=result.user,
            evaluation_period=result.evaluation_period,
            evaluation_type=result.evaluation_period.evaluation_type,
            section=result.section,
            category_a_score=result.category_a_score,
            category_b_score=result.category_b_score,
            category_c_score=result.category_c_score,
            category_d_score=result.category_d_score,
            total_percentage=result.total_percentage,
            average_rating=result.average_rating,
            total_responses=result.total_responses,
            total_questions=result.total_questions,
            poor_count=result.poor_count,
            unsatisfactory_count=result.unsatisfactory_count,
            satisfactory_count=result.satisfactory_count,
            very_satisfactory_count=result.very_satisfactory_count,
            outstanding_count=result.outstanding_count,
            period_start_date=result.evaluation_period.start_date,
            period_end_date=result.evaluation_period.end_date,
        )

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
    EVALUATION_TYPE_CHOICES = [
        ('student', 'Student'),
        ('peer', 'Peer'),
        ('upward', 'Upward'),
        ('dean', 'Dean'),
        ('student_upward', 'Student Upward'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recommendations")
    evaluation_period = models.ForeignKey(EvaluationPeriod, on_delete=models.CASCADE, null=True, blank=True, related_name="ai_recommendations")

    # Structured fields matching AI service output
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=20, blank=True)
    reason = models.TextField(blank=True)

    # Optional legacy field (kept for backward compatibility)
    recommendation = models.TextField(blank=True)

    evaluation_type = models.CharField(max_length=20, choices=EVALUATION_TYPE_CHOICES, default='student')
    section_code = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "evaluation_period"]),
        ]

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


# ------------------------
# Evaluation Questions Models
# ------------------------
class EvaluationQuestion(models.Model):
    """Store evaluation questions for student and peer evaluations"""
    EVALUATION_TYPE_CHOICES = [
        ('student', 'Student Evaluation'),
        ('peer', 'Peer Evaluation'),
        ('upward', 'Upward Evaluation'),
        ('dean', 'Dean Evaluation'),
        ('student_upward', 'Student Upward Evaluation'),
    ]
    
    evaluation_type = models.CharField(max_length=20, choices=EVALUATION_TYPE_CHOICES, default='student')
    question_number = models.IntegerField()  # 1, 2, 3, ..., 19
    question_text = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('evaluation_type', 'question_number')
        ordering = ['evaluation_type', 'question_number']
    
    def __str__(self):
        return f"{self.get_evaluation_type_display()} - Q{self.question_number}: {self.question_text[:50]}..."


class PeerEvaluationQuestion(models.Model):
    """Store peer evaluation questions (15 questions total)"""
    question_number = models.IntegerField(primary_key=True)  # 1-11
    question_text = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['question_number']
    
    def __str__(self):
        return f"Peer Q{self.question_number}: {self.question_text[:50]}..."


class UpwardEvaluationQuestion(models.Model):
    """Store upward evaluation questions (Faculty → Coordinator, 15 questions)"""
    question_number = models.IntegerField(primary_key=True)  # 1-15
    question_text = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['question_number']
    
    def __str__(self):
        return f"Upward Q{self.question_number}: {self.question_text[:50]}..."


class UpwardEvaluationResponse(models.Model):
    """Store faculty responses when evaluating their coordinator"""
    evaluator = models.ForeignKey(User, related_name='upward_evaluations', on_delete=models.CASCADE, db_index=True)
    evaluatee = models.ForeignKey(User, related_name='upward_evaluated_by', on_delete=models.CASCADE, db_index=True)
    evaluation_period = models.ForeignKey(EvaluationPeriod, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    
    # Timestamp
    submitted_at = models.DateTimeField(default=timezone.now, db_index=True)

    # 15 questions for upward evaluation
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

    # Comments field
    comments = models.TextField(blank=True, null=True, verbose_name="Additional Comments/Suggestions")

    class Meta:
        # Prevent duplicate evaluation within the same period
        unique_together = ('evaluator', 'evaluatee', 'evaluation_period')

    def __str__(self):
        return f"{self.evaluator.get_full_name() or self.evaluator.username}'s Upward Evaluation for {self.evaluatee.get_full_name() or self.evaluatee.username}"


class DeanEvaluationQuestion(models.Model):
    """Store dean evaluation questions (Faculty → Dean)"""
    question_number = models.IntegerField(primary_key=True)
    question_text = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['question_number']
    
    def __str__(self):
        return f"Dean Q{self.question_number}: {self.question_text[:50]}..."


class DeanEvaluationResponse(models.Model):
    """Store faculty responses when evaluating their dean"""
    evaluator = models.ForeignKey(User, related_name='dean_evaluations', on_delete=models.CASCADE, db_index=True)
    evaluatee = models.ForeignKey(User, related_name='dean_evaluated_by', on_delete=models.CASCADE, db_index=True)
    evaluation_period = models.ForeignKey(EvaluationPeriod, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    
    # Timestamp
    submitted_at = models.DateTimeField(default=timezone.now, db_index=True)

    # Questions for dean evaluation (will add based on Jotform)
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

    # Comments field
    comments = models.TextField(blank=True, null=True, verbose_name="Additional Comments/Suggestions")

    class Meta:
        # Prevent duplicate evaluation within the same period
        unique_together = ('evaluator', 'evaluatee', 'evaluation_period')

    def __str__(self):
        return f"{self.evaluator.get_full_name() or self.evaluator.username}'s Dean Evaluation for {self.evaluatee.get_full_name() or self.evaluatee.username}"


# Student → Coordinator Upward Evaluation (12 questions in 4 categories)
class StudentUpwardEvaluationQuestion(models.Model):
    """
    Student → Coordinator Upward Evaluation Questions
    12 questions grouped into 4 categories (3 questions per category)
    """
    question_number = models.IntegerField(primary_key=True, unique=True)
    question_text = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['question_number']

    def __str__(self):
        return f"Q{self.question_number}: {self.question_text[:50]}"


class StudentUpwardEvaluationResponse(models.Model):
    """
    Stores a Student's upward evaluation response for a Coordinator
    12 questions with comments
    """
    # Who is evaluating whom
    evaluator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_upward_evaluations_given', db_index=True)
    evaluatee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_upward_evaluations_received', db_index=True)
    
    # Link to evaluation period
    evaluation_period = models.ForeignKey(EvaluationPeriod, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    
    # Timestamp
    submitted_at = models.DateTimeField(default=timezone.now, db_index=True)

    # 12 questions for student upward evaluation (Student → Coordinator)
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

    # Comments field
    comments = models.TextField(blank=True, null=True, verbose_name="Additional Comments/Suggestions")

    class Meta:
        # Prevent duplicate evaluation within the same period
        unique_together = ('evaluator', 'evaluatee', 'evaluation_period')

    def __str__(self):
        return f"{self.evaluator.get_full_name() or self.evaluator.username}'s Student Upward Evaluation for {self.evaluatee.get_full_name() or self.evaluatee.username}"
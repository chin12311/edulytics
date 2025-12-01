from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from main.models import Section
from main.models import UserProfile, Section, Role
import logging

logger = logging.getLogger(__name__)


class RegisterForm(forms.Form):
    # Display name field for the name with spaces
    display_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your full name (with spaces)'}),
        label="Full Name"
    )

    # Email Field
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'your.email@domain.com'}),
        required=True
    )

    # Password fields
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter password'}),
        label="Password"
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}),
        label="Confirm Password"
    )

    # Role Field
    role = forms.ChoiceField(
        choices=[
            ('', 'Select Role'),
            ('Student', 'Student'),
            ('Dean', 'Dean'),
            ('Faculty', 'Faculty'),
            ('Coordinator', 'Coordinator')
        ],
        required=True
    )

    # Course (For Students)
    course = forms.ChoiceField(
        choices=[
            ('', 'Select Course'),
            ('BSCS', 'Bachelor of Science in Computer Science'),
            ('BSIS', 'Bachelor of Science in Information Systems'),
            ('ACT', 'Associate in Computer Technology'),
            ('BLIS', 'Bachelor of Library and Information Science'),
            ('BSA', 'Bachelor of Science in Accountancy'),
            ('BSBA', 'Bachelor of Science in Business Administration'),
            ('BSED', 'Bachelor of Secondary Education'),
            ('BEED', 'Bachelor of Elementary Education')
        ],
        required=False
    )

    # Student Number (For Students)
    studentNumber = forms.CharField(
        max_length=7,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g., 2024001'})
    )

    # Institute (For Non-students)
    institute = forms.ChoiceField(
        choices=[
            ('', 'Select Institute'),
            ('IBM', 'Institute of Business and Management'),
            ('ICSLIS', 'Institute of Computing Studies and Library Information Science'),
            ('IEAS', 'Institute of Education, Arts and Services')
        ],
        required=False
    )

    # Section (For Students)
    section = forms.ModelChoiceField(
        queryset=Section.objects.all(),
        required=False,
        empty_label="Select Section"
    )
    
    # Irregular Student Flag
    is_irregular = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Check if student has no fixed section"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['display_name'].help_text = "This will be your display name with spaces and capitalization."

    def clean_password1(self):
        """Validate password1 has minimum requirements"""
        password = self.cleaned_data.get("password1")
        
        # Null/empty check
        if not password:
            raise ValidationError("Password is required.")
        
        # Minimum length
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        
        # Check complexity requirements
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValidationError(
                "Password must contain uppercase, lowercase, digit, and special character (!@#$%^&*()_+-=[]{}|;:,.<>?)"
            )
        
        return password

    def clean_password2(self):
        """Check that the two password entries match"""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        
        # Null/empty check
        if not password2:
            raise ValidationError("Password confirmation is required.")
        
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        role = self.cleaned_data.get('role')

        # Null/empty check
        if not email or not email.strip():
            raise ValidationError("Email is required.")

        # Whitespace validation
        email = email.strip()
        if email != self.cleaned_data.get('email'):
            self.cleaned_data['email'] = email

        # Email format validation (already done by EmailField, but explicit check)
        if '@' not in email or '.' not in email:
            raise ValidationError("Please enter a valid email address.")

        if role == 'Student':
            if not email.endswith('@cca.edu.ph'):
                raise ValidationError("Students must register with a @cca.edu.ph email address.")
        else:
            allowed_domains = ['@gmail.com', '@cca.edu.ph']
            if not any(email.endswith(domain) for domain in allowed_domains):
                raise ValidationError("Please use a valid email address (e.g., Gmail or cca.edu.ph).")

        # Check for existing email (case-insensitive)
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("A user with this email already exists.")

        return email

    def clean(self):
        cleaned_data = super().clean()
        
        email = cleaned_data.get('email', '').strip() if cleaned_data.get('email') else None
        role = cleaned_data.get('role', '').strip() if cleaned_data.get('role') else None
        student_number = cleaned_data.get('studentNumber', '').strip() if cleaned_data.get('studentNumber') else None
        course = cleaned_data.get('course', '').strip() if cleaned_data.get('course') else None
        institute = cleaned_data.get('institute', '').strip() if cleaned_data.get('institute') else None
        section = cleaned_data.get('section')
        display_name = cleaned_data.get('display_name', '').strip() if cleaned_data.get('display_name') else None
        is_irregular = cleaned_data.get('is_irregular', False)

        # Validate display name
        if not display_name:
            self.add_error('display_name', "Full name is required.")
        elif len(display_name) < 2:
            self.add_error('display_name', "Full name must be at least 2 characters long.")
        elif len(display_name) > 150:
            self.add_error('display_name', "Full name must not exceed 150 characters.")

        # Null/empty role check
        if not role:
            self.add_error('role', "Please select a role.")

        # Role-specific validation
        if role == 'Student':
            # Student must have number
            if not student_number:
                self.add_error('studentNumber', "Student number is required for students.")
            elif student_number:
                # Remove hyphens for validation
                clean_student_number = student_number.replace('-', '')
                
                # Check if it's exactly 6 digits after removing hyphens
                if len(clean_student_number) != 6 or not clean_student_number.isdigit():
                    self.add_error('studentNumber', "Student number must be exactly 6 digits (e.g., 21-1766).")
                # Optional: You can also validate the format if needed
                elif '-' in student_number and len(student_number) != 7:
                    self.add_error('studentNumber', "Invalid format. Use format: XX-XXXX (e.g., 21-1766).")
            
            # Only require course and section if NOT irregular
            if not is_irregular:
                # Student must have course
                if not course:
                    self.add_error('course', "Course is required for students.")
                
                # Student must have section
                if not section:
                    self.add_error('section', "Section is required for students.")
        else:
            # Non-students must have institute
            if not institute:
                self.add_error('institute', "Institute is required for Dean, Faculty, and Coordinator.")

        # Generate and validate username
        if email:
            username = email.split('@')[0]
            # Remove non-alphanumeric characters, convert to lowercase
            username = ''.join(c for c in username if c.isalnum()).lower()
            
            if not username:
                self.add_error('email', "Unable to generate username from email. Please use a different email.")
                logger.warning(f"Failed to generate username from email: {email}")
                return cleaned_data
            
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
                if counter > 100:  # Safety check to prevent infinite loop
                    self.add_error('email', "Unable to create unique username. Please try again.")
                    logger.error(f"Failed to create unique username for email: {email}")
                    return cleaned_data
                
            # Store the final username for use in save()
            self.final_username = username

        return cleaned_data

    def save(self):
        # Use the pre-validated username from clean method
        username = getattr(self, 'final_username', None)
        if not username:
            # Fallback to original logic if clean wasn't called
            email = self.cleaned_data['email']
            username = email.split('@')[0]
            username = ''.join(c for c in username if c.isalnum()).lower()
            
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
        
        # Get the display name from the form (this is what user entered with spaces)
        display_name = self.cleaned_data['display_name']
        
        # Create user with generated username
        user = User.objects.create_user(
            username=username,  # This is the technical username (no spaces)
            email=self.cleaned_data['email'].lower(),  # Normalize email to lowercase
            password=self.cleaned_data['password1']
        )
        
        # Handle student fields based on role
        role = self.cleaned_data['role']
        
        # For non-students, set student fields to None (not empty strings)
        if role != 'Student':
            studentnumber = None
            course = None
            section = None
            institute = self.cleaned_data.get('institute', '') or None  # Convert empty string to None
            is_irregular = False
        else:
            studentnumber = self.cleaned_data.get('studentNumber', '') or None
            course = self.cleaned_data.get('course', '') or None
            is_irregular = self.cleaned_data.get('is_irregular', False)
            # Irregular students have no section
            if is_irregular:
                section = None
            else:
                section = self.cleaned_data.get('section')
            institute = None  # Students don't have institute (use None, not empty string)
        
        # The signal should have already created the profile
        # Get or create it (in case signal failed)
        try:
            profile = user.userprofile
            logger.info(f"Profile already exists for user {username}, updating it")
        except UserProfile.DoesNotExist:
            profile = UserProfile(user=user)
            logger.warning(f"Signal didn't create profile for {username}, creating manually")
        
        # Update profile with form data
        profile.display_name = display_name
        profile.studentnumber = studentnumber
        profile.course = course
        profile.section = section
        profile.institute = institute
        profile.role = role
        profile.is_irregular = is_irregular
        
        # Call full_clean() to validate before saving
        try:
            profile.full_clean()
            # Save with skip_validation=True to avoid double validation
            profile.save(skip_validation=True)
            logger.info(f"New user registered: {username} ({user.email}) - Role: {role}")
        except Exception as e:
            # If profile update fails, delete the user too
            user.delete()
            logger.error(f"Failed to update profile for {username}: {str(e)}")
            raise
        
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "autocomplete": "email",
            "placeholder": "Email Address..."
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password"}),
        required=True
    )
    
    def clean_email(self):
        """Validate email field is not null/empty"""
        email = self.cleaned_data.get('email')
        
        if not email or not email.strip():
            raise ValidationError("Email is required.")
        
        return email.strip().lower()
    
    def clean_password(self):
        """Validate password field is not null/empty"""
        password = self.cleaned_data.get('password')
        
        if not password:
            raise ValidationError("Password is required.")
        
        if len(password) < 1:
            raise ValidationError("Password cannot be empty.")
        
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        # Both fields must be present
        if not email or not password:
            if not email:
                self.add_error('email', "Email is required.")
            if not password:
                self.add_error('password', "Password is required.")
            return cleaned_data
        
        # Don't validate credentials here - let the view handle it
        # This prevents form validation errors from blocking login
        return cleaned_data





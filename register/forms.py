from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from main.models import Section
from main.models import UserProfile, Section, Role


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
            ('BLIS', 'Bachelor of Library and Information Science')
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['display_name'].help_text = "This will be your display name with spaces and capitalization."

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        role = self.cleaned_data.get('role')

        if not email:
            raise ValidationError("Email is required.")

        if role == 'Student':
            if not email.endswith('@cca.edu.ph'):
                raise ValidationError("Students must register with a @cca.edu.ph email address.")
        else:
            allowed_domains = ['@gmail.com', '@cca.edu.ph']
            if not any(email.endswith(domain) for domain in allowed_domains):
                raise ValidationError("Please use a valid email address (e.g., Gmail or cca.edu.ph).")

        # Check for existing email
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")

        return email

    def clean(self):
        cleaned_data = super().clean()
        
        email = cleaned_data.get('email')
        role = cleaned_data.get('role')
        student_number = cleaned_data.get('studentNumber')
        course = cleaned_data.get('course')
        institute = cleaned_data.get('institute')
        section = cleaned_data.get('section')
        display_name = cleaned_data.get('display_name')

        # Validate display name
        if not display_name:
            self.add_error('display_name', "Full name is required.")
        elif len(display_name.strip()) < 2:
            self.add_error('display_name', "Full name must be at least 2 characters long.")

        if role == 'Student':
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
            
            if not course:
                self.add_error('course', "Course is required for students.")
            
            if not section:
                self.add_error('section', "Section is required for students.")
        else:
            if not institute:
                self.add_error('institute', "Institute is required for Dean, Faculty, and Coordinator.")

        # Generate and validate username
        if email:
            username = email.split('@')[0]
            username = ''.join(c for c in username if c.isalnum())
            
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
                
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
            username = ''.join(c for c in username if c.isalnum())
            
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
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1']
        )
        
        # Handle student fields based on role
        role = self.cleaned_data['role']
        
        # For non-students, set student fields to None (not empty strings)
        if role != 'Student':
            studentnumber = None
            course = None
            section = None
            institute = self.cleaned_data.get('institute', '')
        else:
            studentnumber = self.cleaned_data.get('studentNumber', '')
            course = self.cleaned_data.get('course', '')
            section = self.cleaned_data.get('section')
            institute = ''  # Students don't have institute
        
        # Create profile with proper display_name
        profile = UserProfile.objects.create(
            user=user,
            display_name=display_name,  # This is the user-friendly name with spaces
            studentnumber=studentnumber,
            course=course,
            section=section,
            institute=institute,
            role=role
        )
        
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "autocomplete": "email",
            "placeholder": "Email Address..."
        })
    )
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Password"}))
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        if email and password:
            # Try to find the user by email
            try:
                user = User.objects.get(email=email)
                # Authenticate using the username (not email)
                user = authenticate(username=user.username, password=password)
                if user is None:
                    raise ValidationError("Invalid email or password")
                cleaned_data['user'] = user
            except User.DoesNotExist:
                raise ValidationError("Invalid email or password")
        
        return cleaned_data





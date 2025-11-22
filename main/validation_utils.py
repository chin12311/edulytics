"""
Centralized user input validation utilities for account creation and updates.
"""
import re
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from main.models import UserProfile, Role, Section


class AccountValidator:
    """Centralized validation for user accounts."""
    
    # Validation patterns
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_.-]+$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    STUDENT_NUMBER_PATTERN = re.compile(r'^\d{2}-\d{4}$')  # XX-XXXX format
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    PASSWORD_SPECIAL_CHARS = '!@#$%^&*()_+-=[]{}|;:,.<>?'
    
    @staticmethod
    def validate_username(username, exclude_user_id=None):
        """
        Validate username format and uniqueness.
        
        Args:
            username: Username to validate
            exclude_user_id: User ID to exclude from duplicate check (for updates)
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not username:
            return False, "Username is required"
        
        username = str(username).strip()
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if len(username) > 150:
            return False, "Username must be at most 150 characters"
        
        if not AccountValidator.USERNAME_PATTERN.match(username):
            return False, "Username can only contain letters, numbers, dots, hyphens, and underscores"
        
        # Check for duplicates (excluding current user if updating)
        query = User.objects.filter(username=username)
        if exclude_user_id:
            query = query.exclude(id=exclude_user_id)
        
        if query.exists():
            return False, f"Username '{username}' is already taken"
        
        return True, ""
    
    @staticmethod
    def validate_email(email, exclude_user_id=None):
        """
        Validate email format and uniqueness.
        
        Args:
            email: Email to validate
            exclude_user_id: User ID to exclude from duplicate check (for updates)
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not email:
            return False, "Email is required"
        
        email = str(email).strip().lower()
        
        if not AccountValidator.EMAIL_PATTERN.match(email):
            return False, "Invalid email format"
        
        if len(email) > 254:
            return False, "Email is too long (max 254 characters)"
        
        # Check for duplicates (excluding current user if updating)
        query = User.objects.filter(email=email)
        if exclude_user_id:
            query = query.exclude(id=exclude_user_id)
        
        if query.exists():
            return False, f"Email '{email}' is already registered"
        
        return True, ""
    
    @staticmethod
    def validate_password(password, confirm_password=None):
        """
        Validate password complexity.
        
        Args:
            password: Password to validate
            confirm_password: Confirmation password (optional)
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not password:
            return False, "Password is required"
        
        password = str(password)
        
        # Check length
        if len(password) < AccountValidator.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {AccountValidator.MIN_PASSWORD_LENGTH} characters long"
        
        if len(password) > 128:
            return False, "Password is too long (max 128 characters)"
        
        # Check complexity
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in AccountValidator.PASSWORD_SPECIAL_CHARS for c in password)
        
        if not (has_upper and has_lower and has_digit and has_special):
            return False, (
                "Password must contain uppercase, lowercase, digit, "
                "and special character (!@#$%^&*()_+-=[]{}|;:,.<>?)"
            )
        
        # Check confirmation password if provided
        if confirm_password is not None:
            if password != str(confirm_password):
                return False, "Passwords do not match"
        
        return True, ""
    
    @staticmethod
    def validate_display_name(display_name):
        """
        Validate display name.
        
        Args:
            display_name: Display name to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not display_name:
            return False, "Display name is required"
        
        display_name = str(display_name).strip()
        
        if len(display_name) < 2:
            return False, "Display name must be at least 2 characters"
        
        if len(display_name) > 150:
            return False, "Display name must be at most 150 characters"
        
        # Check for invalid characters (only letters, spaces, hyphens, apostrophes allowed)
        if not re.match(r"^[a-zA-Z\s\-']+$", display_name):
            return False, "Display name can only contain letters, spaces, hyphens, and apostrophes"
        
        return True, ""
    
    @staticmethod
    def validate_role(role):
        """
        Validate role.
        
        Args:
            role: Role to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not role:
            return False, "Role is required"
        
        role = str(role).strip()
        
        valid_roles = [Role.STUDENT, Role.FACULTY, Role.DEAN, Role.COORDINATOR, Role.ADMIN]
        if role not in valid_roles:
            return False, f"Invalid role. Must be one of: Student, Faculty, Dean, Coordinator, Admin"
        
        return True, ""
    
    @staticmethod
    def validate_student_number(student_number):
        """
        Validate student number format (XX-XXXX).
        
        Args:
            student_number: Student number to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not student_number:
            return False, "Student number is required for students"
        
        student_number = str(student_number).strip()
        
        if not AccountValidator.STUDENT_NUMBER_PATTERN.match(student_number):
            return False, "Student number must be in format XX-XXXX (e.g., 21-1766)"
        
        return True, ""
    
    @staticmethod
    def validate_course(course):
        """
        Validate course name.
        
        Args:
            course: Course to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not course:
            return False, "Course is required for students"
        
        course = str(course).strip()
        
        if len(course) < 2:
            return False, "Course must be at least 2 characters"
        
        if len(course) > 50:
            return False, "Course must be at most 50 characters"
        
        return True, ""
    
    @staticmethod
    def validate_section(section_id):
        """
        Validate section exists.
        
        Args:
            section_id: Section ID to validate
            
        Returns:
            tuple: (is_valid, error_message, section_obj)
        """
        if not section_id:
            return False, "Section is required for students", None
        
        try:
            section = Section.objects.get(id=section_id)
            return True, "", section
        except Section.DoesNotExist:
            return False, f"Section with ID {section_id} does not exist", None
    
    @staticmethod
    def validate_institute(institute):
        """
        Validate institute name for staff.
        
        Args:
            institute: Institute to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not institute:
            return False, "Institute is required for staff"
        
        institute = str(institute).strip()
        
        if len(institute) < 2:
            return False, "Institute must be at least 2 characters"
        
        if len(institute) > 50:
            return False, "Institute must be at most 50 characters"
        
        return True, ""
    
    @staticmethod
    def validate_account_create(data):
        """
        Comprehensive validation for account creation.
        
        Args:
            data: Dictionary with username, email, password, confirm_password,
                  display_name, role, and role-specific fields
        
        Returns:
            dict: {'valid': bool, 'errors': dict of field -> error messages}
        """
        errors = {}
        
        # Validate username
        valid, msg = AccountValidator.validate_username(data.get('username'))
        if not valid:
            errors['username'] = msg
        
        # Validate email
        valid, msg = AccountValidator.validate_email(data.get('email'))
        if not valid:
            errors['email'] = msg
        
        # Validate password
        valid, msg = AccountValidator.validate_password(
            data.get('password'),
            data.get('confirm_password')
        )
        if not valid:
            errors['password'] = msg
        
        # Validate display name
        valid, msg = AccountValidator.validate_display_name(data.get('display_name'))
        if not valid:
            errors['display_name'] = msg
        
        # Validate role
        valid, msg = AccountValidator.validate_role(data.get('role'))
        if not valid:
            errors['role'] = msg
        else:
            role = str(data.get('role')).strip().upper()
            
            # Validate role-specific fields
            if role == Role.STUDENT:
                valid, msg = AccountValidator.validate_student_number(data.get('student_number'))
                if not valid:
                    errors['student_number'] = msg
                
                valid, msg = AccountValidator.validate_course(data.get('course'))
                if not valid:
                    errors['course'] = msg
                
                valid, msg, section = AccountValidator.validate_section(data.get('section'))
                if not valid:
                    errors['section'] = msg
            
            elif role in [Role.DEAN, Role.FACULTY, Role.COORDINATOR]:
                valid, msg = AccountValidator.validate_institute(data.get('institute'))
                if not valid:
                    errors['institute'] = msg
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def validate_account_update(data, exclude_user_id):
        """
        Comprehensive validation for account update.
        
        Args:
            data: Dictionary with fields to update
            exclude_user_id: ID of the user being updated (to exclude from duplicate checks)
        
        Returns:
            dict: {'valid': bool, 'errors': dict of field -> error messages}
        """
        errors = {}
        
        # Validate username if provided
        if data.get('username'):
            valid, msg = AccountValidator.validate_username(
                data.get('username'),
                exclude_user_id=exclude_user_id
            )
            if not valid:
                errors['username'] = msg
        
        # Validate email if provided
        if data.get('email'):
            valid, msg = AccountValidator.validate_email(
                data.get('email'),
                exclude_user_id=exclude_user_id
            )
            if not valid:
                errors['email'] = msg
        
        # Validate password if provided (optional on update)
        if data.get('password'):
            valid, msg = AccountValidator.validate_password(
                data.get('password'),
                data.get('confirm_password')
            )
            if not valid:
                errors['password'] = msg
        
        # Validate display name if provided
        if data.get('display_name'):
            valid, msg = AccountValidator.validate_display_name(data.get('display_name'))
            if not valid:
                errors['display_name'] = msg
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

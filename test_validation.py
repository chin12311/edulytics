"""
Test validation utilities for account creation and updates.
"""
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase
from main.models import UserProfile, Role, Section
from main.validation_utils import AccountValidator


class UsernameValidationTests(TestCase):
    """Test username validation."""
    
    def test_valid_username(self):
        """Test valid username."""
        is_valid, msg = AccountValidator.validate_username("john_doe.123")
        assert is_valid, f"Valid username rejected: {msg}"
    
    def test_username_too_short(self):
        """Test username that is too short."""
        is_valid, msg = AccountValidator.validate_username("ab")
        assert not is_valid
        assert "at least 3 characters" in msg
    
    def test_username_too_long(self):
        """Test username that is too long."""
        is_valid, msg = AccountValidator.validate_username("a" * 151)
        assert not is_valid
        assert "at most 150 characters" in msg
    
    def test_username_invalid_characters(self):
        """Test username with invalid characters."""
        is_valid, msg = AccountValidator.validate_username("john@doe")
        assert not is_valid
        assert "only contain letters, numbers" in msg
    
    def test_username_duplicate(self):
        """Test duplicate username."""
        User.objects.create_user(username="john", email="john@test.com", password="Test123!")
        is_valid, msg = AccountValidator.validate_username("john")
        assert not is_valid
        assert "already taken" in msg
    
    def test_username_duplicate_excluded(self):
        """Test duplicate username but excluded from check."""
        user = User.objects.create_user(username="john", email="john@test.com", password="Test123!")
        is_valid, msg = AccountValidator.validate_username("john", exclude_user_id=user.id)
        assert is_valid


class EmailValidationTests(TestCase):
    """Test email validation."""
    
    def test_valid_email(self):
        """Test valid email."""
        is_valid, msg = AccountValidator.validate_email("john@example.com")
        assert is_valid, f"Valid email rejected: {msg}"
    
    def test_invalid_email_format(self):
        """Test invalid email format."""
        is_valid, msg = AccountValidator.validate_email("john@invalid")
        assert not is_valid
        assert "Invalid email format" in msg
    
    def test_email_too_long(self):
        """Test email that is too long."""
        long_email = "a" * 250 + "@example.com"
        is_valid, msg = AccountValidator.validate_email(long_email)
        assert not is_valid
        assert "too long" in msg
    
    def test_email_duplicate(self):
        """Test duplicate email."""
        User.objects.create_user(username="john", email="john@test.com", password="Test123!")
        is_valid, msg = AccountValidator.validate_email("john@test.com")
        assert not is_valid
        assert "already registered" in msg
    
    def test_email_case_insensitive(self):
        """Test email is checked case-insensitively."""
        User.objects.create_user(username="john", email="john@test.com", password="Test123!")
        is_valid, msg = AccountValidator.validate_email("JOHN@TEST.COM")
        assert not is_valid


class PasswordValidationTests(TestCase):
    """Test password validation."""
    
    def test_valid_password(self):
        """Test valid password."""
        is_valid, msg = AccountValidator.validate_password("ValidPass123!")
        assert is_valid, f"Valid password rejected: {msg}"
    
    def test_password_too_short(self):
        """Test password that is too short."""
        is_valid, msg = AccountValidator.validate_password("Short1!")
        assert not is_valid
        assert "at least 8 characters" in msg
    
    def test_password_no_uppercase(self):
        """Test password without uppercase."""
        is_valid, msg = AccountValidator.validate_password("lowercase123!")
        assert not is_valid
        assert "uppercase" in msg
    
    def test_password_no_lowercase(self):
        """Test password without lowercase."""
        is_valid, msg = AccountValidator.validate_password("UPPERCASE123!")
        assert not is_valid
        assert "lowercase" in msg
    
    def test_password_no_digit(self):
        """Test password without digit."""
        is_valid, msg = AccountValidator.validate_password("NoDigitPass!")
        assert not is_valid
        assert "digit" in msg
    
    def test_password_no_special(self):
        """Test password without special character."""
        is_valid, msg = AccountValidator.validate_password("NoSpecialPass123")
        assert not is_valid
        assert "special character" in msg
    
    def test_password_mismatch(self):
        """Test password confirmation mismatch."""
        is_valid, msg = AccountValidator.validate_password(
            "ValidPass123!",
            "DifferentPass123!"
        )
        assert not is_valid
        assert "do not match" in msg
    
    def test_password_match(self):
        """Test password confirmation match."""
        is_valid, msg = AccountValidator.validate_password(
            "ValidPass123!",
            "ValidPass123!"
        )
        assert is_valid


class DisplayNameValidationTests(TestCase):
    """Test display name validation."""
    
    def test_valid_display_name(self):
        """Test valid display name."""
        is_valid, msg = AccountValidator.validate_display_name("John Doe")
        assert is_valid, f"Valid display name rejected: {msg}"
    
    def test_display_name_with_apostrophe(self):
        """Test display name with apostrophe."""
        is_valid, msg = AccountValidator.validate_display_name("O'Brien")
        assert is_valid
    
    def test_display_name_with_hyphen(self):
        """Test display name with hyphen."""
        is_valid, msg = AccountValidator.validate_display_name("Mary-Jane")
        assert is_valid
    
    def test_display_name_too_short(self):
        """Test display name that is too short."""
        is_valid, msg = AccountValidator.validate_display_name("J")
        assert not is_valid
        assert "at least 2 characters" in msg
    
    def test_display_name_too_long(self):
        """Test display name that is too long."""
        is_valid, msg = AccountValidator.validate_display_name("A" * 151)
        assert not is_valid
        assert "at most 150 characters" in msg
    
    def test_display_name_invalid_characters(self):
        """Test display name with invalid characters."""
        is_valid, msg = AccountValidator.validate_display_name("John123")
        assert not is_valid
        assert "only contain letters" in msg


class RoleValidationTests(TestCase):
    """Test role validation."""
    
    def test_valid_roles(self):
        """Test valid roles."""
        for role in [Role.STUDENT, Role.FACULTY, Role.DEAN, Role.COORDINATOR, Role.ADMIN]:
            is_valid, msg = AccountValidator.validate_role(role)
            assert is_valid, f"Valid role {role} rejected: {msg}"
    
    def test_invalid_role(self):
        """Test invalid role."""
        is_valid, msg = AccountValidator.validate_role("INVALID")
        assert not is_valid
        assert "Invalid role" in msg
    
    def test_role_case_insensitive(self):
        """Test role is case-insensitive."""
        is_valid, msg = AccountValidator.validate_role("student")
        assert is_valid


class StudentNumberValidationTests(TestCase):
    """Test student number validation."""
    
    def test_valid_student_number(self):
        """Test valid student number."""
        is_valid, msg = AccountValidator.validate_student_number("21-1766")
        assert is_valid, f"Valid student number rejected: {msg}"
    
    def test_invalid_student_number_format(self):
        """Test invalid student number format."""
        is_valid, msg = AccountValidator.validate_student_number("211766")
        assert not is_valid
        assert "XX-XXXX format" in msg
    
    def test_student_number_missing(self):
        """Test missing student number."""
        is_valid, msg = AccountValidator.validate_student_number("")
        assert not is_valid
        assert "required" in msg


class CourseValidationTests(TestCase):
    """Test course validation."""
    
    def test_valid_course(self):
        """Test valid course."""
        is_valid, msg = AccountValidator.validate_course("Computer Science")
        assert is_valid, f"Valid course rejected: {msg}"
    
    def test_course_too_short(self):
        """Test course that is too short."""
        is_valid, msg = AccountValidator.validate_course("C")
        assert not is_valid
        assert "at least 2 characters" in msg
    
    def test_course_too_long(self):
        """Test course that is too long."""
        is_valid, msg = AccountValidator.validate_course("A" * 51)
        assert not is_valid
        assert "at most 50 characters" in msg


class SectionValidationTests(TestCase):
    """Test section validation."""
    
    def setUp(self):
        """Set up test section."""
        self.section = Section.objects.create(
            code="CS101",
            year_level="Freshman"
        )
    
    def test_valid_section(self):
        """Test valid section."""
        is_valid, msg, section = AccountValidator.validate_section(self.section.id)
        assert is_valid, f"Valid section rejected: {msg}"
        assert section == self.section
    
    def test_invalid_section(self):
        """Test invalid section."""
        is_valid, msg, section = AccountValidator.validate_section(9999)
        assert not is_valid
        assert "does not exist" in msg
        assert section is None
    
    def test_missing_section(self):
        """Test missing section."""
        is_valid, msg, section = AccountValidator.validate_section(None)
        assert not is_valid
        assert "required" in msg


class InstituteValidationTests(TestCase):
    """Test institute validation."""
    
    def test_valid_institute(self):
        """Test valid institute."""
        is_valid, msg = AccountValidator.validate_institute("School of Engineering")
        assert is_valid, f"Valid institute rejected: {msg}"
    
    def test_institute_too_short(self):
        """Test institute that is too short."""
        is_valid, msg = AccountValidator.validate_institute("S")
        assert not is_valid
        assert "at least 2 characters" in msg
    
    def test_institute_too_long(self):
        """Test institute that is too long."""
        is_valid, msg = AccountValidator.validate_institute("A" * 51)
        assert not is_valid
        assert "at most 50 characters" in msg


class AccountCreateValidationTests(TransactionTestCase):
    """Test comprehensive account creation validation."""
    
    def test_valid_student_account_creation(self):
        """Test valid student account creation."""
        section = Section.objects.create(code="CS101", year_level="Freshman")
        
        data = {
            'username': 'newstudent',
            'email': 'student@example.com',
            'password': 'ValidPass123!',
            'confirm_password': 'ValidPass123!',
            'display_name': 'New Student',
            'role': 'STUDENT',
            'student_number': '21-1766',
            'course': 'Computer Science',
            'section': section.id
        }
        
        result = AccountValidator.validate_account_create(data)
        assert result['valid'], f"Valid creation rejected: {result['errors']}"
    
    def test_invalid_student_missing_student_number(self):
        """Test student account without student number."""
        section = Section.objects.create(code="CS102", year_level="Freshman")
        
        data = {
            'username': 'newstudent2',
            'email': 'student2@example.com',
            'password': 'ValidPass123!',
            'confirm_password': 'ValidPass123!',
            'display_name': 'New Student 2',
            'role': 'STUDENT',
            'course': 'Computer Science',
            'section': section.id
        }
        
        result = AccountValidator.validate_account_create(data)
        assert not result['valid']
        assert 'student_number' in result['errors']
    
    def test_valid_staff_account_creation(self):
        """Test valid staff account creation."""
        data = {
            'username': 'newfaculty',
            'email': 'faculty@example.com',
            'password': 'ValidPass123!',
            'confirm_password': 'ValidPass123!',
            'display_name': 'New Faculty',
            'role': 'FACULTY',
            'institute': 'School of Engineering'
        }
        
        result = AccountValidator.validate_account_create(data)
        assert result['valid'], f"Valid staff creation rejected: {result['errors']}"


class AccountUpdateValidationTests(TransactionTestCase):
    """Test comprehensive account update validation."""
    
    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='OldPass123!'
        )
    
    def test_valid_update_username(self):
        """Test valid username update."""
        data = {
            'username': 'newusername'
        }
        
        result = AccountValidator.validate_account_update(data, self.user.id)
        assert result['valid'], f"Valid update rejected: {result['errors']}"
    
    def test_valid_update_password(self):
        """Test valid password update."""
        data = {
            'password': 'NewPass123!',
            'confirm_password': 'NewPass123!'
        }
        
        result = AccountValidator.validate_account_update(data, self.user.id)
        assert result['valid'], f"Valid password update rejected: {result['errors']}"
    
    def test_invalid_update_duplicate_username(self):
        """Test update with duplicate username."""
        User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='Pass123!'
        )
        
        data = {
            'username': 'existing'
        }
        
        result = AccountValidator.validate_account_update(data, self.user.id)
        assert not result['valid']
        assert 'username' in result['errors']
    
    def test_update_exclude_self(self):
        """Test that updating own username is allowed."""
        data = {
            'username': 'testuser'
        }
        
        result = AccountValidator.validate_account_update(data, self.user.id)
        assert result['valid'], f"Self-update rejected: {result['errors']}"

# Validation System Quick Reference

## Quick Links
- **Validation Logic**: `main/validation_utils.py`
- **View Using Validation**: `main/views.py` (UpdateUser class)
- **Import Service Using Validation**: `main/services/import_export_service.py`
- **Tests**: `test_validation.py`

## Validation Rules Summary

### Username
- **Min Length**: 3 characters
- **Max Length**: 150 characters
- **Allowed Characters**: `a-z`, `A-Z`, `0-9`, `.`, `-`, `_`
- **Duplicates**: Not allowed (checked against database)
- **Example**: `john.doe_123` ✓, `ab` ✗

### Email
- **Format**: Valid email format required
- **Max Length**: 254 characters
- **Duplicates**: Not allowed (case-insensitive check)
- **Example**: `john@example.com` ✓, `invalid-email` ✗

### Password
- **Min Length**: 8 characters
- **Max Length**: 128 characters
- **Required Components**:
  - At least 1 uppercase letter (A-Z)
  - At least 1 lowercase letter (a-z)
  - At least 1 digit (0-9)
  - At least 1 special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
- **Example**: `MyPass123!` ✓, `password123` ✗ (no uppercase or special)

### Display Name
- **Min Length**: 2 characters
- **Max Length**: 150 characters
- **Allowed Characters**: Letters, spaces, hyphens, apostrophes
- **Example**: `John O'Brien` ✓, `J` ✗, `John123` ✗

### Role
- **Valid Values**: `STUDENT`, `FACULTY`, `DEAN`, `COORDINATOR`, `ADMIN`
- **Case**: Insensitive (lowercase converted automatically)
- **Required**: Yes
- **Example**: `STUDENT` ✓, `Teacher` ✗

### Student Number (for Students only)
- **Format**: `XX-XXXX` (two digits, hyphen, four digits)
- **Required**: Yes for students
- **Example**: `21-1766` ✓, `211766` ✗, `21-166` ✗

### Course (for Students only)
- **Min Length**: 2 characters
- **Max Length**: 50 characters
- **Required**: Yes for students
- **Example**: `Computer Science` ✓, `C` ✗

### Section (for Students, optional)
- **Type**: Must exist in database
- **Required**: No, but if provided must be valid
- **Example**: Valid section ID from database ✓, Non-existent ID ✗

### Institute (for Staff only)
- **Min Length**: 2 characters
- **Max Length**: 50 characters
- **Required**: Yes for Faculty, Coordinator, Dean
- **Example**: `School of Engineering` ✓, `S` ✗

## Using in Code

### Validate Single Field
```python
from main.validation_utils import AccountValidator

# Validate username
is_valid, error_msg = AccountValidator.validate_username("john_doe")
if not is_valid:
    print(f"Error: {error_msg}")
```

### Validate Complete Account Create
```python
data = {
    'username': 'john_doe',
    'email': 'john@example.com',
    'password': 'MyPass123!',
    'confirm_password': 'MyPass123!',
    'display_name': 'John Doe',
    'role': 'STUDENT',
    'student_number': '21-1766',
    'course': 'Computer Science',
    'section': section_id
}

result = AccountValidator.validate_account_create(data)
if not result['valid']:
    for field, error in result['errors'].items():
        print(f"{field}: {error}")
```

### Validate Account Update
```python
# Only provided fields are validated
data = {
    'username': 'new_username',
    'email': 'new@example.com'
}

# Exclude current user from duplicate checks
result = AccountValidator.validate_account_update(data, exclude_user_id=user_id)
if not result['valid']:
    for field, error in result['errors'].items():
        print(f"{field}: {error}")
```

## Common Validation Responses

### Success Response
```python
is_valid, msg = AccountValidator.validate_username("john_doe")
# is_valid = True
# msg = ""
```

### Error Response (Example: Duplicate Username)
```python
is_valid, msg = AccountValidator.validate_username("existing_user")
# is_valid = False
# msg = "Username 'existing_user' is already taken"
```

### Account Create Result
```python
result = AccountValidator.validate_account_create(data)
# result = {
#     'valid': True/False,
#     'errors': {
#         'username': 'Username error message',
#         'email': 'Email error message',
#         ...
#     }
# }
```

## Error Messages

### Username Errors
- "Username is required"
- "Username must be at least 3 characters long"
- "Username must be at most 150 characters"
- "Username can only contain letters, numbers, dots, hyphens, and underscores"
- "Username 'X' is already taken"

### Email Errors
- "Email is required"
- "Invalid email format"
- "Email is too long (max 254 characters)"
- "Email 'X' is already registered"

### Password Errors
- "Password is required"
- "Password must be at least 8 characters long"
- "Password is too long (max 128 characters)"
- "Password must contain uppercase, lowercase, digit, and special character"
- "Passwords do not match"

### Display Name Errors
- "Display name is required"
- "Display name must be at least 2 characters"
- "Display name must be at most 150 characters"
- "Display name can only contain letters, spaces, hyphens, and apostrophes"

### Role Errors
- "Role is required"
- "Invalid role. Must be one of: STUDENT, FACULTY, DEAN, COORDINATOR, ADMIN"

### Student Number Errors
- "Student number is required for students"
- "Student number must be in format XX-XXXX (e.g., 21-1766)"

### Course Errors
- "Course is required for students"
- "Course must be at least 2 characters"
- "Course must be at most 50 characters"

### Institute Errors
- "Institute is required for staff"
- "Institute must be at least 2 characters"
- "Institute must be at most 50 characters"

## Validation in Views

### In UpdateUser.post()
```python
# Build validation data (only for provided fields)
validation_data = {}
if new_username:
    validation_data['username'] = new_username
if new_email:
    validation_data['email'] = new_email
if new_password:
    validation_data['password'] = new_password
    validation_data['confirm_password'] = confirm_password

# Validate
result = AccountValidator.validate_account_update(
    validation_data,
    exclude_user_id=user.id
)

# Check result
if not result['valid']:
    error_messages = " | ".join(result['errors'].values())
    # Render form with error_messages
```

## Validation in Import Service

### Import from Excel
```python
from main.services.import_export_service import AccountImportExportService

# Import accounts from Excel file
result = AccountImportExportService.import_accounts_from_excel(excel_file)

# Result structure:
# {
#     'success': True/False,
#     'created': 5,
#     'updated': 2,
#     'skipped': 1,
#     'errors': [
#         'Row 3: Invalid email format',
#         'Row 5: Duplicate username in batch',
#         ...
#     ]
# }
```

## Testing Validation

### Run Tests
```bash
python manage.py test test_validation
```

### Test Classes
- `UsernameValidationTests`
- `EmailValidationTests`
- `PasswordValidationTests`
- `DisplayNameValidationTests`
- `RoleValidationTests`
- `StudentNumberValidationTests`
- `CourseValidationTests`
- `SectionValidationTests`
- `InstituteValidationTests`
- `AccountCreateValidationTests`
- `AccountUpdateValidationTests`

## Performance Tips

1. **Validate early**: Check validation before database operations
2. **Exclude self**: Use `exclude_user_id` parameter when validating updates
3. **Batch validation**: For imports, validate before creating transactions
4. **Cache validation**: Don't re-validate unchanged data

## Common Mistakes

❌ **Don't:**
```python
# Missing error checking
is_valid = AccountValidator.validate_username(username)
user = User.objects.create_user(username=username)  # May fail!
```

✓ **Do:**
```python
# Check validation result first
is_valid, msg = AccountValidator.validate_username(username)
if is_valid:
    user = User.objects.create_user(username=username)
else:
    print(f"Validation failed: {msg}")
```

❌ **Don't:**
```python
# Forget to exclude user in updates
result = AccountValidator.validate_account_update({'username': user.username})
if not result['valid']:  # Will always fail on update!
    ...
```

✓ **Do:**
```python
# Always exclude current user on updates
result = AccountValidator.validate_account_update(
    {'username': 'newname'},
    exclude_user_id=user.id
)
```

## Configuration

All validation patterns and limits are defined in `AccountValidator` class:
```python
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_.-]+$')
EMAIL_PATTERN = re.compile(r'^...')
STUDENT_NUMBER_PATTERN = re.compile(r'^\d{2}-\d{4}$')
MIN_PASSWORD_LENGTH = 8
PASSWORD_SPECIAL_CHARS = '!@#$%^&*()_+-=[]{}|;:,.<>?'
```

To change validation rules, update these constants in `validation_utils.py`.

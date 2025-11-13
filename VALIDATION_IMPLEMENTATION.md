# Comprehensive User Input Validation Implementation

## Overview
This document describes the comprehensive validation system implemented to ensure data integrity and security across the application. All user inputs are now validated consistently using centralized validators.

## 1. Validation Utilities Module

### Location
`main/validation_utils.py`

### Key Components

#### AccountValidator Class
Centralized validation for all user account inputs with the following methods:

**Username Validation**
- Minimum length: 3 characters
- Maximum length: 150 characters
- Allowed characters: letters, numbers, dots, hyphens, underscores
- Duplicate checking (with optional exclusion for updates)

**Email Validation**
- Valid email format (regex pattern)
- Maximum length: 254 characters
- Duplicate checking (case-insensitive)
- Unique constraint enforcement

**Password Validation**
- Minimum length: 8 characters
- Maximum length: 128 characters
- Must contain:
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
- Confirmation password matching

**Display Name Validation**
- Minimum length: 2 characters
- Maximum length: 150 characters
- Allowed characters: letters, spaces, hyphens, apostrophes

**Role Validation**
- Must be one of: STUDENT, FACULTY, DEAN, COORDINATOR, ADMIN
- Case-insensitive validation

**Role-Specific Validations**

Student Fields:
- Student Number: XX-XXXX format (e.g., 21-1766)
- Course: 2-50 characters
- Section: Must exist in database

Staff Fields (Faculty, Coordinator, Dean):
- Institute: 2-50 characters

## 2. Updated Views

### UpdateUser View (`main/views.py`)

**Improvements:**
- Uses AccountValidator.validate_account_update() for all updates
- Comprehensive error messages for each validation failure
- Validation data structure for clear error reporting
- Supports optional fields (only validate provided data)
- Proper context rendering with error display

**Validated Fields:**
- Username (with duplicate checking)
- Email (with duplicate checking and format validation)
- Password (with complexity requirements)
- Display Name (with format validation)

### ImportAccountsView (`main/views.py`)

**Improvements:**
- File format validation (.xlsx, .xls files only)
- Excel file parsing with header validation
- Required column checking

## 3. Enhanced Import Service

### Location
`main/services/import_export_service.py`

### Improvements

**Comprehensive Input Validation:**
- All fields validated using AccountValidator methods
- Role-specific field validation
- Duplicate detection within batch and database
- Section existence checking
- Institute validation for staff roles

**Import Process:**
1. Header validation
2. Row-by-row processing with error tracking
3. Field-level validation using AccountValidator
4. Batch duplicate detection
5. Database duplicate detection (excluding updates)
6. Role-specific field validation
7. Transaction handling with rollback on critical errors

**Enhanced Error Reporting:**
- Row-specific error messages
- Field-level error identification
- Clear error descriptions for user feedback
- Summary of created/updated/skipped accounts

**Duplicate Checking:**
- Username uniqueness verification
- Email uniqueness verification (case-insensitive)
- Batch-level duplicate detection
- Database-level duplicate detection

## 4. Test Coverage

### Location
`test_validation.py`

### Test Classes

**UsernameValidationTests**
- Valid username acceptance
- Length constraints (min/max)
- Character validation
- Duplicate detection

**EmailValidationTests**
- Valid format acceptance
- Format validation
- Length constraints
- Duplicate detection (case-insensitive)

**PasswordValidationTests**
- Complexity requirements
- Character set validation
- Confirmation matching
- Length constraints

**DisplayNameValidationTests**
- Format validation
- Character set validation
- Length constraints

**RoleValidationTests**
- Valid role acceptance
- Case-insensitive validation
- Invalid role rejection

**StudentNumberValidationTests**
- Format validation (XX-XXXX)
- Presence validation

**CourseValidationTests**
- Length constraints
- Presence validation

**SectionValidationTests**
- Existence validation
- ID validation

**InstituteValidationTests**
- Length constraints
- Presence validation

**AccountCreateValidationTests**
- Complete student account creation flow
- Complete staff account creation flow
- Missing required fields detection

**AccountUpdateValidationTests**
- Partial update validation
- Optional field handling
- Self-update exclusion

## 5. Key Features

### 1. Centralized Validation
All validation logic is in one place (`AccountValidator`), making it:
- Easy to maintain
- Consistent across the application
- Reusable in multiple views and services

### 2. Comprehensive Error Messages
Each validation includes:
- Specific error message explaining the issue
- Clear constraints (min/max, allowed characters, etc.)
- Actionable feedback for users

### 3. Duplicate Detection
Multi-level duplicate checking:
- Database-level check for existing users
- Batch-level check for duplicates within import
- Case-insensitive email checking

### 4. Role-Based Validation
Different validation rules based on user role:
- Students: student number, course, section
- Staff: institute name
- All roles: username, email, password, display name

### 5. Flexible Update Validation
For account updates:
- Only validates provided fields
- Excludes current user from duplicate checks
- Supports optional password updates

## 6. Usage Examples

### In Views
```python
# Update validation
validation_result = AccountValidator.validate_account_update(
    data={'username': 'newuser', 'email': 'new@example.com'},
    exclude_user_id=user.id
)

if not validation_result['valid']:
    errors = validation_result['errors']  # Dict of field -> error message
```

### In Import Service
```python
# Validate username
valid, msg = AccountValidator.validate_username(
    username,
    exclude_user_id=existing_user_id
)
if not valid:
    errors.append(msg)

# Validate role-specific fields
if role == Role.STUDENT:
    valid, msg = AccountValidator.validate_student_number(student_number)
    valid, msg = AccountValidator.validate_course(course)
```

## 7. Security Considerations

### Input Sanitization
- All inputs are stripped of leading/trailing whitespace
- Email addresses are normalized to lowercase
- Usernames and special fields are validated for format

### Duplicate Prevention
- Case-insensitive email checking prevents duplicates with different cases
- Username checking prevents exact duplicates
- Batch import checks prevent bulk duplicates

### Password Security
- Strong password requirements enforced
- Confirmation password matching required
- No password length restrictions that would cause issues

### Role Enforcement
- Role validation prevents invalid role assignments
- Role-specific field validation ensures data consistency

## 8. Error Handling

### Validation Errors
- Caught and returned in structured format
- User-friendly error messages
- Field-specific error identification

### Database Errors
- Transaction handling in imports
- Rollback on critical failures
- Error logging for debugging

## 9. Performance Considerations

### Database Queries
- Select-related queries for preventing N+1 problems
- Efficient duplicate checking
- Batch transaction handling

### Validation Performance
- Simple regex patterns for format checking
- Early exit on validation failures
- Minimal database queries for basic validation

## 10. Migration Notes

### For Existing Systems
- All new accounts follow validation rules
- Existing accounts are not re-validated on import
- Update validation is opt-in (only validates provided fields)

### Backward Compatibility
- Import service accepts old Excel format
- Section lookup by code (not ID)
- Graceful handling of missing optional fields

## 11. Testing

### Running Tests
```bash
python manage.py test test_validation
```

### Coverage
- Unit tests for each validation method
- Integration tests for complete flows
- Error handling tests
- Edge case tests

## 12. Configuration Constants

Located in `AccountValidator` class:
```python
USERNAME_PATTERN = r'^[a-zA-Z0-9_.-]+$'
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
STUDENT_NUMBER_PATTERN = r'^\d{2}-\d{4}$'  # XX-XXXX format

MIN_PASSWORD_LENGTH = 8
PASSWORD_SPECIAL_CHARS = '!@#$%^&*()_+-=[]{}|;:,.<>?'
```

These can be easily adjusted if requirements change.

## 13. Future Enhancements

Potential improvements:
- Email verification (send confirmation email)
- Phone number validation for staff
- Birthdate validation
- Address validation
- Department validation
- More granular role-based validation
- API rate limiting for import operations
- Bulk validation error reports
- Validation webhooks for external systems

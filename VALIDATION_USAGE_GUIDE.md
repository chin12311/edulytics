# Validation System - Implementation Guide

## Overview
This guide explains how the new comprehensive validation system works and how to use it in your Django application.

---

## Part 1: Architecture Overview

### Three-Layer Validation Architecture

```
┌─────────────────────────────────────────────────────┐
│ PRESENTATION LAYER (Views)                          │
│ - UpdateUser, ImportAccountsView                    │
│ - Receives user input                               │
└────────────────────┬────────────────────────────────┘
                     │ Uses
                     ▼
┌─────────────────────────────────────────────────────┐
│ VALIDATION LAYER (AccountValidator)                 │
│ - Centralized validation logic                      │
│ - Reusable across application                       │
│ - Consistent error messages                         │
└────────────────────┬────────────────────────────────┘
                     │ Updates
                     ▼
┌─────────────────────────────────────────────────────┐
│ DATA LAYER (Django Models)                          │
│ - User, UserProfile, Section models                │
│ - Database constraints                              │
└─────────────────────────────────────────────────────┘
```

---

## Part 2: Validation Workflow

### Account Update Flow

```
User Input (Form)
      ↓
UpdateUser.post()
      ↓
AccountValidator.validate_account_update()
      ↓
    Is Valid?
     ↙      ↘
   YES      NO
    ↓        ↓
Update DB  Render Form
           with Errors
```

### Import Account Flow

```
Excel File
    ↓
ImportAccountsView.post()
    ↓
AccountImportExportService.import_accounts_from_excel()
    ↓
For Each Row:
    ↓
Validate using AccountValidator
    ↓
    Is Valid?
    ↙      ↘
   YES      NO
    ↓        ↓
 Create/   Add to
 Update    Error List
    ↓
Summary Report
```

---

## Part 3: Core Validators

### 1. Basic Field Validators

#### Username Validator
**Purpose**: Ensure valid, unique usernames

**Method**: `AccountValidator.validate_username(username, exclude_user_id=None)`

**Returns**: `(is_valid: bool, error_message: str)`

**Example**:
```python
is_valid, msg = AccountValidator.validate_username("john_doe")
if not is_valid:
    print(f"Error: {msg}")
```

#### Email Validator
**Purpose**: Ensure valid, unique emails (case-insensitive)

**Method**: `AccountValidator.validate_email(email, exclude_user_id=None)`

**Returns**: `(is_valid: bool, error_message: str)`

**Example**:
```python
is_valid, msg = AccountValidator.validate_email("john@example.com")
if not is_valid:
    print(f"Error: {msg}")
```

#### Password Validator
**Purpose**: Ensure strong password with complexity requirements

**Method**: `AccountValidator.validate_password(password, confirm_password=None)`

**Returns**: `(is_valid: bool, error_message: str)`

**Example**:
```python
is_valid, msg = AccountValidator.validate_password("MyPass123!", "MyPass123!")
if not is_valid:
    print(f"Error: {msg}")
```

### 2. Role-Specific Validators

#### Student Validators
```python
# Student Number (XX-XXXX format)
is_valid, msg = AccountValidator.validate_student_number("21-1766")

# Course
is_valid, msg = AccountValidator.validate_course("Computer Science")

# Section (must exist in DB)
is_valid, msg, section = AccountValidator.validate_section(section_id)
```

#### Staff Validators
```python
# Institute
is_valid, msg = AccountValidator.validate_institute("School of Engineering")
```

### 3. Complex Validators

#### Account Creation Validator
**Purpose**: Validate entire account data for creation

**Method**: `AccountValidator.validate_account_create(data)`

**Returns**: `{'valid': bool, 'errors': {field: error_message}}`

**Example**:
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
    'section': 1
}

result = AccountValidator.validate_account_create(data)
if result['valid']:
    # Create account
else:
    for field, error in result['errors'].items():
        print(f"{field}: {error}")
```

#### Account Update Validator
**Purpose**: Validate account update with optional fields

**Method**: `AccountValidator.validate_account_update(data, exclude_user_id)`

**Returns**: `{'valid': bool, 'errors': {field: error_message}}`

**Example**:
```python
# Only validate fields being updated
data = {
    'username': 'new_username',
    'email': 'new@example.com'
}

result = AccountValidator.validate_account_update(data, exclude_user_id=user_id)
if result['valid']:
    # Update account
else:
    for field, error in result['errors'].items():
        print(f"{field}: {error}")
```

---

## Part 4: Integration Examples

### Example 1: Simple Field Validation in View

```python
from main.validation_utils import AccountValidator
from django.shortcuts import render

def update_email(request):
    new_email = request.POST.get('email')
    
    # Validate email
    is_valid, error_msg = AccountValidator.validate_email(
        new_email,
        exclude_user_id=request.user.id
    )
    
    if is_valid:
        request.user.email = new_email
        request.user.save()
        return render(request, 'success.html')
    else:
        context = {'error': error_msg}
        return render(request, 'update_email.html', context)
```

### Example 2: Complete Form Validation in View

```python
from main.validation_utils import AccountValidator

def update_user(request):
    if request.method == 'POST':
        # Get form data
        data = {
            'username': request.POST.get('username', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'password': request.POST.get('password', '').strip(),
            'confirm_password': request.POST.get('confirm_password', '').strip(),
            'display_name': request.POST.get('display_name', '').strip()
        }
        
        # Remove empty fields (optional on update)
        data = {k: v for k, v in data.items() if v}
        
        # Validate all fields
        result = AccountValidator.validate_account_update(data, exclude_user_id=request.user.id)
        
        if result['valid']:
            # Update database
            user = request.user
            if 'username' in data:
                user.username = data['username']
            if 'email' in data:
                user.email = data['email']
            if 'password' in data:
                user.set_password(data['password'])
            user.save()
            
            return redirect('success')
        else:
            # Show form with errors
            context = {
                'user': request.user,
                'errors': result['errors']
            }
            return render(request, 'update_user.html', context)
    
    return render(request, 'update_user.html')
```

### Example 3: Batch Import with Validation

```python
from main.validation_utils import AccountValidator
from django.contrib.auth.models import User

def import_users_from_csv(csv_data):
    created = 0
    failed = 0
    errors = []
    
    for row_num, row in enumerate(csv_data, 1):
        # Validate each field
        result = AccountValidator.validate_account_create({
            'username': row['username'],
            'email': row['email'],
            'password': row['password'],
            'confirm_password': row['password'],
            'display_name': row['display_name'],
            'role': row['role']
        })
        
        if result['valid']:
            try:
                # Create user
                user = User.objects.create_user(
                    username=row['username'],
                    email=row['email'],
                    password=row['password']
                )
                created += 1
            except Exception as e:
                failed += 1
                errors.append(f"Row {row_num}: Failed to create - {str(e)}")
        else:
            failed += 1
            field_errors = ", ".join(result['errors'].values())
            errors.append(f"Row {row_num}: {field_errors}")
    
    return {
        'created': created,
        'failed': failed,
        'errors': errors
    }
```

### Example 4: API Endpoint Validation

```python
from django.http import JsonResponse
from main.validation_utils import AccountValidator

def api_create_user(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    import json
    data = json.loads(request.body)
    
    # Validate
    result = AccountValidator.validate_account_create(data)
    
    if not result['valid']:
        return JsonResponse({
            'success': False,
            'errors': result['errors']
        }, status=400)
    
    try:
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )
        return JsonResponse({
            'success': True,
            'user_id': user.id
        }, status=201)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
```

---

## Part 5: Error Handling

### Handling Validation Results

```python
# Single field validation
is_valid, error_msg = AccountValidator.validate_username(username)

if is_valid:
    # Proceed with valid data
    process_username(username)
else:
    # Handle error
    logger.warning(f"Invalid username: {error_msg}")
    show_error_to_user(error_msg)

# Complex validation
result = AccountValidator.validate_account_create(data)

if result['valid']:
    # All fields valid, proceed
    create_account(data)
else:
    # Multiple field errors
    for field, error in result['errors'].items():
        log_validation_error(field, error)
        show_field_error(field, error)
```

### Error Patterns

**Field-level errors**:
```python
result['errors'] = {
    'username': 'Username must be at least 3 characters long',
    'email': 'Invalid email format'
}
```

**Handling in template**:
```html
<form method="post">
    {% csrf_token %}
    
    <div class="form-group">
        <label>Username:</label>
        <input type="text" name="username" value="{{ form.username }}">
        {% if errors.username %}
            <span class="error">{{ errors.username }}</span>
        {% endif %}
    </div>
    
    <div class="form-group">
        <label>Email:</label>
        <input type="email" name="email" value="{{ form.email }}">
        {% if errors.email %}
            <span class="error">{{ errors.email }}</span>
        {% endif %}
    </div>
</form>
```

---

## Part 6: Testing

### Unit Test Example

```python
from django.test import TestCase
from main.validation_utils import AccountValidator

class UsernameValidationTest(TestCase):
    def test_valid_username(self):
        is_valid, msg = AccountValidator.validate_username("john_doe")
        self.assertTrue(is_valid)
    
    def test_username_too_short(self):
        is_valid, msg = AccountValidator.validate_username("ab")
        self.assertFalse(is_valid)
        self.assertIn("at least 3 characters", msg)
    
    def test_duplicate_username(self):
        User.objects.create_user(username="john", email="john@test.com", password="Pass123!")
        is_valid, msg = AccountValidator.validate_username("john")
        self.assertFalse(is_valid)
        self.assertIn("already taken", msg)
```

### Integration Test Example

```python
class AccountUpdateTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="Pass123!"
        )
    
    def test_update_username(self):
        data = {'username': 'newname'}
        result = AccountValidator.validate_account_update(data, self.user.id)
        self.assertTrue(result['valid'])
    
    def test_update_duplicate_username(self):
        User.objects.create_user(username="taken", email="taken@example.com", password="Pass123!")
        data = {'username': 'taken'}
        result = AccountValidator.validate_account_update(data, self.user.id)
        self.assertFalse(result['valid'])
```

---

## Part 7: Best Practices

### DO ✓

1. **Always check validation result**
```python
result = AccountValidator.validate_account_create(data)
if result['valid']:
    create_user(data)
```

2. **Exclude user on updates**
```python
result = AccountValidator.validate_account_update(data, exclude_user_id=user.id)
```

3. **Use specific validators for specific fields**
```python
is_valid, msg = AccountValidator.validate_email(email)
```

4. **Handle all fields in result**
```python
for field, error in result['errors'].items():
    log_error(field, error)
```

5. **Strip and normalize input**
```python
username = request.POST.get('username', '').strip()
```

### DON'T ✗

1. **Don't skip validation**
```python
# BAD
user = User.objects.create_user(username=request.POST['username'])

# GOOD
is_valid, msg = AccountValidator.validate_username(request.POST['username'])
if is_valid:
    user = User.objects.create_user(username=request.POST['username'])
```

2. **Don't forget to exclude user on updates**
```python
# BAD
result = AccountValidator.validate_account_update({'username': user.username})

# GOOD
result = AccountValidator.validate_account_update(
    {'username': user.username},
    exclude_user_id=user.id
)
```

3. **Don't ignore validation errors**
```python
# BAD
is_valid, msg = AccountValidator.validate_password(password)
user.set_password(password)

# GOOD
is_valid, msg = AccountValidator.validate_password(password)
if is_valid:
    user.set_password(password)
```

---

## Part 8: Troubleshooting

### Common Issues

**Issue**: "Module not found" error
**Solution**: Ensure import statement is correct
```python
from main.validation_utils import AccountValidator
```

**Issue**: Validation passes but database error occurs
**Solution**: Validation doesn't guarantee database write succeeds. Handle exceptions:
```python
result = AccountValidator.validate_account_create(data)
if result['valid']:
    try:
        create_user(data)
    except IntegrityError as e:
        handle_database_error(e)
```

**Issue**: Email validation says "already registered" but it's not in database
**Solution**: Check for case sensitivity - emails are normalized to lowercase:
```python
is_valid, msg = AccountValidator.validate_email("JOHN@EXAMPLE.COM")
# Will check against "john@example.com" in database
```

**Issue**: Username update fails validation but it's the user's current username
**Solution**: Always pass `exclude_user_id` on updates:
```python
result = AccountValidator.validate_account_update(
    {'username': current_username},
    exclude_user_id=user_id  # <- Don't forget this!
)
```

---

## Part 9: Performance Tips

1. **Validate before database operations** - Catch errors early
2. **Use exclude_user_id on updates** - Prevents unnecessary database check
3. **Batch validation for imports** - Process in transactions
4. **Cache validation patterns** - Regex patterns are compiled

---

## Part 10: Configuration

### Changing Validation Rules

Edit constants in `AccountValidator` class:

```python
# Change minimum username length
USERNAME_MIN = 3  # Default

# Change password length requirement
MIN_PASSWORD_LENGTH = 8  # Default

# Add more special characters to password
PASSWORD_SPECIAL_CHARS = '!@#$%^&*()_+-=[]{}|;:,.<>?'  # Default
```

Then run tests to ensure nothing breaks:
```bash
python manage.py test test_validation
```

---

## Summary

The validation system provides:
- ✅ Centralized, reusable validation logic
- ✅ Comprehensive error messages
- ✅ Duplicate prevention
- ✅ Role-based validation
- ✅ Input sanitization
- ✅ Extensive test coverage
- ✅ Easy to maintain and extend

Use it consistently across your application to ensure data quality and security.


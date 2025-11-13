# Email Notification Configuration Update

## Change Made
**Date:** November 10, 2025

### What was changed:
The `cibituonon@cca.edu.ph` account has been **excluded** from receiving email notifications when evaluations are released or unreleased.

### Where it was changed:
**File:** `main/email_service.py`

**Changes:**
1. **Line 38-39** - `send_evaluation_released_notification()` method:
   ```python
   # BEFORE:
   users = User.objects.filter(is_active=True).exclude(email='')
   
   # AFTER:
   users = User.objects.filter(is_active=True).exclude(email='').exclude(email='cibituonon@cca.edu.ph')
   ```

2. **Line 114** - `send_evaluation_unreleased_notification()` method:
   ```python
   # BEFORE:
   users = User.objects.filter(is_active=True).exclude(email='')
   
   # AFTER:
   users = User.objects.filter(is_active=True).exclude(email='').exclude(email='cibituonon@cca.edu.ph')
   ```

### Effect:
- **Before:** When you released an evaluation, ALL 58 active users received an email, including `cibituonon@cca.edu.ph`
- **After:** When you release an evaluation, **57 users** receive the email notification (everyone except `cibituonon@cca.edu.ph`)

### Testing:
To verify this works correctly:
1. Release an evaluation in your admin panel
2. The system will send emails to 57 users instead of 58
3. You should see `"sent_count": 57` in the response

---

## Email Recipients Still Receiving Notifications:
✅ All active students (except cibituonon@cca.edu.ph)
✅ All active teachers/evaluators
✅ All other system users with email addresses

## Email Recipients Excluded:
❌ cibituonon@cca.edu.ph (School Head / Admin account)

---

## Future Modifications:
If you need to exclude additional accounts in the future, simply add more `.exclude(email='email@address.com')` calls to those same two lines:
```python
users = User.objects.filter(is_active=True).exclude(email='').exclude(email='cibituonon@cca.edu.ph').exclude(email='another@email.com')
```

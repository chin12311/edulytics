# 📧 Email Notifications - Quick Reference

## What Was Added

Your Edulytics system now automatically sends email notifications when evaluations are released or closed.

---

## ⚙️ Quick Setup (3 Steps)

### Step 1: Get Gmail App Password

1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and your device
3. Copy the 16-character password

### Step 2: Add to `.env` File

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
SERVER_EMAIL=your-email@gmail.com
```

### Step 3: Test It Works

```bash
python test_email_notifications.py
```

---

## 🎯 How It Works

```
Admin Releases Evaluation
           ↓
System Automatically:
  1. Updates evaluation status
  2. Fetches all active users
  3. Sends personalized emails to each user
  4. Logs results
           ↓
Users Receive Email:
  - Professional HTML format
  - Clear action required
  - Link to system
           ↓
Admin Sees Confirmation:
  - "Emails sent: 58"
  - "Failed: 0"
```

---

## 📮 Email Notifications Sent

### ✅ When Evaluation Is Released
- **To:** All active users
- **Subject:** 🎓 Evaluation Form Released
- **Content:** Instructions to complete evaluation

### ✅ When Evaluation Is Closed
- **To:** All active users  
- **Subject:** 📋 Evaluation Period Closed
- **Content:** Notification period has ended

---

## 🧪 Test Email Notifications

### Full Test Suite
```bash
python test_email_notifications.py
```

### Quick Test (Send to yourself)
```bash
python manage.py shell
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    subject='Test',
    message='If you got this, email works!',
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=['your@email.com'],
    fail_silently=False,
)
```

---

## 📊 Email Service Details

### Files Added/Modified

1. **`main/email_service.py`** - NEW
   - EvaluationEmailService class
   - send_evaluation_released_notification()
   - send_evaluation_unreleased_notification()

2. **`main/views.py`** - MODIFIED
   - Added import for EvaluationEmailService
   - Updated release_student_evaluation()
   - Updated unrelease_student_evaluation()
   - Updated release_peer_evaluation()
   - Updated unrelease_peer_evaluation()

### Functions Available

```python
# Send notification when evaluation is released
EvaluationEmailService.send_evaluation_released_notification('student')
EvaluationEmailService.send_evaluation_released_notification('peer')

# Send notification when evaluation is closed
EvaluationEmailService.send_evaluation_unreleased_notification('student')
EvaluationEmailService.send_evaluation_unreleased_notification('peer')
```

---

## 🔍 Verify Setup

Check your `.env` file contains:
```
✅ EMAIL_HOST=smtp.gmail.com
✅ EMAIL_PORT=587
✅ EMAIL_USE_TLS=True
✅ EMAIL_HOST_USER=your-email@gmail.com
✅ EMAIL_HOST_PASSWORD=app-password-16-chars
✅ DEFAULT_FROM_EMAIL=your-email@gmail.com
```

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Invalid credentials" | Check EMAIL_HOST_PASSWORD in .env |
| "Connection refused" | Make sure EMAIL_USE_TLS=True and EMAIL_PORT=587 |
| "Emails not sending" | Check Django logs: `tail -f logs/django.log` |
| "No app password" | Go to https://myaccount.google.com/apppasswords and create one |

---

## 📝 Important Notes

⚠️ **Gmail Credentials**
- Always use app password, NOT your Gmail password
- Keep .env file private (never commit to git)
- Requires 2FA enabled on Gmail account

✅ **Email Features**
- Sends to ALL active users
- HTML + plain text format
- Professional templates
- Automatic error handling
- Detailed logging

---

## 🎉 You're Ready!

Once configured:
1. Release an evaluation normally
2. All users automatically get emailed
3. Check email confirmation in admin response
4. Users see professional notification

**That's it! Email notifications are working.**

---

For detailed setup: See `EMAIL_NOTIFICATION_SETUP.md`  
For testing: Run `python test_email_notifications.py`

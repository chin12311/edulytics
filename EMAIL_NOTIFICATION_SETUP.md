# 📧 Email Notification System Setup Guide

## Overview

Your Edulytics system now sends automatic email notifications to all users when evaluations are released or closed. This guide explains how to configure Gmail SMTP for sending these emails.

---

## 🔧 Step 1: Configure Environment Variables

Add the following variables to your `.env` file:

```bash
# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
SERVER_EMAIL=your-email@gmail.com
```

### Important: Creating a Gmail App Password

1. **Enable 2-Factor Authentication on Gmail**
   - Go to https://myaccount.google.com/security
   - Scroll down to "2-Step Verification"
   - Follow the prompts to enable it

2. **Generate App Password**
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer" (or your device)
   - Google will generate a 16-character password
   - Copy this password and paste it as `EMAIL_HOST_PASSWORD` in `.env`

3. **Example `.env` configuration:**
   ```
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=edulytics@gmail.com
   EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop
   DEFAULT_FROM_EMAIL=edulytics@gmail.com
   SERVER_EMAIL=edulytics@gmail.com
   ```

---

## ✅ Step 2: Verify Configuration

### Test Email Service

Run this command to test if emails are working:

```bash
python manage.py shell
```

Then in the Python shell:

```python
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    subject='Test Email',
    message='This is a test email from Edulytics.',
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=['your-test-email@gmail.com'],
    fail_silently=False,
)
```

You should receive an email within seconds if configured correctly.

---

## 📨 Step 3: How Email Notifications Work

### When Evaluations Are Released

When an admin clicks "Release Student Evaluation" or "Release Peer Evaluation":

1. ✅ Evaluation becomes active in the system
2. ✅ Email notifications sent to ALL active users
3. ✅ Each user receives notification in their Gmail account
4. ✅ Admin sees a confirmation showing how many emails were sent

### When Evaluations Are Closed

When an admin clicks "Unrelease/Close Evaluation":

1. ✅ Evaluation period ends
2. ✅ Email notifications sent to ALL active users
3. ✅ Users are informed the evaluation period has closed
4. ✅ Admin sees a confirmation showing how many emails were sent

---

## 📋 Email Contents

### Release Notification Email

**Subject:** 🎓 Student Evaluation Form Released - Action Required

**Contains:**
- Announcement that evaluation is now active
- Instructions to complete the evaluation
- Link to the Edulytics system
- Contact information for support

### Close Notification Email

**Subject:** 📋 Student Evaluation Period Closed

**Contains:**
- Announcement that evaluation period has ended
- Notice that no further submissions are accepted
- Thank you message for participation

---

## 🔍 Monitoring & Logging

### Check Email Service Logs

All email sending attempts are logged. Check the Django logs:

```bash
# View recent logs
tail -f logs/django.log | grep -i email
```

### What Gets Logged

- ✅ Number of emails sent
- ✅ List of failed email addresses
- ✅ Detailed error messages for troubleshooting
- ✅ Timestamp of when notifications were sent

### Example Log Entry

```
2025-11-09 13:30:45 INFO: Sending student evaluation release notification to 58 users
2025-11-09 13:30:48 INFO: Sent student evaluation release notification: 58 successful, 0 failed
```

---

## 🚨 Troubleshooting

### Issue: "SMTPAuthenticationError: Invalid credentials"

**Solution:**
- Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in `.env`
- Make sure 2FA is enabled on your Gmail account
- Regenerate your app password and update `.env`

### Issue: "SMTPException: SMTP AUTH extension not supported by server"

**Solution:**
- Verify EMAIL_USE_TLS=True in `.env`
- Check EMAIL_PORT=587 (not 465)

### Issue: Emails not being sent but no errors

**Solution:**
- Check the Django error logs
- Verify Django actually tried to send (check logs with "email" keyword)
- Make sure EMAIL_BACKEND is set to `django.core.mail.backends.smtp.EmailBackend`

### Issue: "Email send failed" in system logs

**Solution:**
- The email address is likely invalid
- Check user email addresses in the database
- Verify no users have empty email fields

---

## 🎯 Email Sending Process

Here's how emails are sent:

```
Admin clicks "Release Evaluation"
           ↓
System updates evaluation status to "released"
           ↓
Email service fetches all active users from database
           ↓
For each user:
  - Generate email content
  - Connect to Gmail SMTP server
  - Send email
  - Log result
           ↓
Return summary:
  - Total sent: 58
  - Failed: 0
  - Message with details
           ↓
Admin sees confirmation in UI
```

---

## 📊 Email Service Features

### Automatic Features

✅ **Batch Processing** - Sends to multiple users efficiently  
✅ **HTML & Text** - Sends both HTML and plain text versions  
✅ **Error Handling** - Gracefully handles failed emails  
✅ **Logging** - All activities logged for debugging  
✅ **Admin Feedback** - Admin sees email status in response  

### Email Personalization

Each email includes:
- User's display name (if available)
- Role-specific information
- Professional HTML formatting
- Clear call-to-action

---

## 📝 System Requirements

- Django 5.1.6+ (already installed)
- Python 3.x (already installed)
- Valid Gmail account with 2FA enabled
- 16-character Gmail app password

---

## 🔐 Security Notes

⚠️ **Never commit `.env` file to git** - Contains sensitive credentials  
⚠️ **Keep app password secret** - Don't share in code or emails  
⚠️ **Use environment variables** - Never hardcode credentials  
✅ **Review permissions** - Ensure only admins can release evaluations  
✅ **Monitor logs** - Check for unusual email activity  

---

## ✨ Summary

Your email notification system is now fully integrated! When admins release or close evaluations, all users automatically receive professional notifications via their Gmail accounts.

**Key Points:**
1. Set up `.env` with Gmail credentials
2. Test with the Python shell command
3. Release/close evaluations as normal
4. Users automatically receive email notifications
5. Admin sees confirmation of how many emails were sent

**Questions?** Check the logs or contact your system administrator.

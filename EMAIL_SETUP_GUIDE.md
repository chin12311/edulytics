# Email Notification Setup Guide

## Overview
Email notifications have been integrated into the evaluation release system. When you release or unrelease evaluations, all active users will receive email notifications automatically.

## Current Status
✅ **Code**: Email notification service implemented and deployed
⚠️ **Configuration**: Email credentials need to be configured on AWS

## What's Been Done
1. Created `EvaluationEmailService` with:
   - `send_evaluation_released_notification()` - Sends emails when evaluation is released
   - `send_evaluation_unreleased_notification()` - Sends emails when evaluation is closed
   - Professional HTML email templates with City College of Angeles branding

2. Integrated email service into these functions:
   - `release_student_evaluation()` - Now sends emails to all active users
   - `release_peer_evaluation()` - Now sends emails to all active users
   - `unrelease_student_evaluation()` - Now sends close notifications
   - `unrelease_peer_evaluation()` - Now sends close notifications

3. Email features:
   - Automatically sends to all active users (excludes cibituonon@cca.edu.ph)
   - HTML formatted emails with proper styling
   - Fallback plain text version
   - Detailed logging for debugging

## Email Configuration Required

To enable email notifications on your AWS server, you need to add email settings to the `.env` file.

### Step 1: Choose Email Service

You have several options:

#### Option A: Gmail (Easiest for testing)
1. Use your Gmail account
2. Enable "App Passwords" in your Google Account settings:
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification
   - Generate an App Password for "Mail"

#### Option B: AWS SES (Recommended for production)
1. Go to AWS SES console
2. Verify your sending email address
3. Request production access if needed
4. Get SMTP credentials

#### Option C: Other SMTP service (SendGrid, Mailgun, etc.)
1. Sign up for the service
2. Get SMTP credentials from their dashboard

### Step 2: Add Configuration to AWS

SSH into your AWS server and edit the `.env` file:

```bash
ssh -i edulytics-key.pem ubuntu@13.211.104.201
cd evaluation
nano .env
```

Add these lines at the end of the file:

#### For Gmail:
```bash
# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password-here
DEFAULT_FROM_EMAIL=your-email@gmail.com
SERVER_EMAIL=your-email@gmail.com
```

#### For AWS SES (Sydney region):
```bash
# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=email-smtp.ap-southeast-2.amazonaws.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-ses-smtp-username
EMAIL_HOST_PASSWORD=your-ses-smtp-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
SERVER_EMAIL=admin@yourdomain.com
```

#### For Other SMTP:
```bash
# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.yourservice.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-username
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
SERVER_EMAIL=admin@yourdomain.com
```

### Step 3: Save and Restart

```bash
# Save the file (Ctrl+X, then Y, then Enter in nano)

# Restart gunicorn to load new environment variables
sudo systemctl restart gunicorn

# Check if it restarted successfully
sudo systemctl status gunicorn
```

### Step 4: Test Email Notifications

1. Log into your admin account on AWS: http://13.211.104.201
2. Go to evaluation management
3. Release a student or peer evaluation
4. Check if users receive email notifications

## Email Template Preview

**Student Evaluation Release:**
- Subject: "🎓 Student Evaluation Form Released - Action Required"
- Content: Professional HTML email with green theme
- Call to action: Log in and complete evaluation

**Peer Evaluation Release:**
- Subject: "🎓 Peer Evaluation Form Released - Action Required"
- Content: Professional HTML email with green theme
- Call to action: Log in and complete evaluation

**Evaluation Close:**
- Subject: "📋 Student/Peer Evaluation Period Closed"
- Content: Professional HTML email with orange theme
- Notice: Evaluation period has ended

## Troubleshooting

### Emails not sending?

1. **Check logs:**
```bash
ssh -i edulytics-key.pem ubuntu@13.211.104.201
cd evaluation
tail -f logs/django.log
```

2. **Test email configuration:**
```bash
cd evaluation
source venv/bin/activate
python manage.py shell

# In Python shell:
from django.core.mail import send_mail
send_mail(
    'Test Email',
    'This is a test message.',
    'your-email@gmail.com',
    ['recipient@example.com'],
    fail_silently=False,
)
```

3. **Common issues:**
   - Wrong credentials → Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
   - Blocked by firewall → Ensure port 587 is open
   - Gmail blocking → Enable "Less secure app access" or use App Password
   - AWS SES sandbox → Request production access if needed

### No errors but emails not received?

1. Check spam folder
2. Verify recipient email addresses in database
3. Check that users have `is_active=True`
4. Check email service logs (Gmail, AWS SES console, etc.)

## Current Email Service Location

The email service code is in:
- `main/email_service.py` - Main email service class
- `main/views.py` - Lines 1845-2020+ (release/unrelease functions with email calls)

## Next Steps

1. Decide which email service to use (Gmail for testing, AWS SES for production)
2. Get credentials from your chosen service
3. Add configuration to `.env` file on AWS
4. Restart gunicorn
5. Test by releasing an evaluation

## Security Notes

- Never commit `.env` file to git (it's already in .gitignore)
- Use App Passwords for Gmail, not your main password
- For production, use AWS SES or professional email service
- Regularly rotate email credentials
- Monitor email sending limits (Gmail: 500/day, AWS SES: depends on tier)

## Questions?

If you encounter any issues during setup, let me know:
1. Which email service you want to use
2. Any error messages from logs
3. Results of the test email command

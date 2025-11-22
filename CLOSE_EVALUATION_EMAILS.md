# Emails Sent When Admin Closes Evaluation

## Email Overview

When admin clicks **"Close Student Evaluation"** or **"Close Peer Evaluation"**, the system sends **ONE email** to:

- **ALL ACTIVE USERS** (excluding admin)
- Recipients: 52 users (all faculty, coordinators, deans, and students)
- Excluded: cibituonon@cca.edu.ph (school head admin)

---

## Close Evaluation Email Details

### Email Type: Unreleased Notification

**Sent From:** `DEFAULT_FROM_EMAIL` (configured in Django settings)

**Sent To:** All active users except admin

**Triggered By:** `unrelease_student_evaluation()` or `unrelease_peer_evaluation()`

**Code Location:** `main/email_service.py`, Line 105-160

---

## Email Subject

### For Student Evaluation Close:
```
📋 Student Evaluation Period Closed
```

### For Peer Evaluation Close:
```
📋 Peer Evaluation Period Closed
```

---

## Email HTML Content

### Header Section:
```
┌─────────────────────────────────┐
│  📋 Student Evaluation Period   │
│           Closed                │
└─────────────────────────────────┘
(Orange background #f39c12)
```

### Main Message:

```
Dear User,

The Student Evaluation Form evaluation period has ended and is now CLOSED.

⚠️ Important Notice:
   No further evaluations can be submitted. The evaluation period has 
   officially closed.

SUMMARY:
- Evaluation Type: Student Evaluation Form
- Status: Closed
- Submissions: No longer accepted

Thank you for your participation. Your feedback has been valuable to our 
institution's evaluation process.

---
City College of Angeles - Edulytics Evaluation System
This is an automated notification. Please do not reply to this email.
```

---

## Email Plain Text Content

For users with plain text email clients:

```
The Student Evaluation Form evaluation period has ended and is now CLOSED.

IMPORTANT NOTICE:
No further evaluations can be submitted. The evaluation period has officially closed.

SUMMARY:
- Evaluation Type: Student Evaluation Form
- Status: Closed
- Submissions: No longer accepted

Thank you for your participation. Your feedback has been valuable to our 
institution's evaluation process.

---
City College of Angeles - Edulytics Evaluation System
This is an automated notification. Please do not reply to this email.
```

---

## Email Styling

### Colors Used:
| Element | Color | Hex |
|---------|-------|-----|
| Header Background | Orange | #f39c12 |
| Header Text | White | #FFFFFF |
| Warning Box Background | Light Red | #ffe7e7 |
| Warning Box Border | Red | #e74c3c |
| Status "Closed" Text | Red | #e74c3c |
| Body Background | White | #FFFFFF |
| Footer Background | Light Gray | #f0f0f0 |

### Design Elements:
- Max width: 600px (mobile-friendly)
- Rounded corners: 8px
- Font: Arial, sans-serif
- Padding: 30px main content, 20px header
- Icons: 📋 (clipboard)

---

## Email Generation Code

### Code Location: `main/email_service.py`

```python
@staticmethod
def send_evaluation_unreleased_notification(evaluation_type='student'):
    """
    Send email notification to all users that an evaluation has been 
    unreleased/closed
    
    Args:
        evaluation_type (str): Type of evaluation ('student' or 'peer')
    
    Returns:
        dict: {
            'success': bool,
            'sent_count': int,
            'failed_emails': list,
            'message': str
        }
    """
    try:
        # Get all active users (exclude admin)
        users = User.objects.filter(
            is_active=True
        ).exclude(
            email=''
        ).exclude(
            email='cibituonon@cca.edu.ph'  # Exclude school head
        )
        
        # Build email content
        subject = _get_unreleased_subject(evaluation_type)
        html_content = _get_unreleased_html_content(evaluation_type)
        text_content = _get_unreleased_text_content(evaluation_type)
        
        # Send to each user
        for user in users:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()  # ← Email sent
        
        return {
            'success': True,
            'sent_count': sent_count,
            'failed_emails': failed_emails,
            'message': f'Successfully sent notification to {sent_count} users'
        }
```

---

## Email Sending Flow

### Step-by-Step Execution:

```
Admin clicks "Close Student Evaluation"
    ↓
unrelease_student_evaluation() function called
    ↓
Set is_released = False (form closed)
    ↓
Call send_evaluation_unreleased_notification('student')
    ↓
Get all active users
    ↓
For each of 52 users:
    ├─ Generate subject line
    ├─ Generate HTML content
    ├─ Generate plain text content
    ├─ Create EmailMultiAlternatives object
    ├─ Attach HTML as alternative
    ├─ Send via SMTP
    └─ Log success/failure
    ↓
Return result:
    ├─ 'success': True
    ├─ 'sent_count': 52 (or number successfully sent)
    ├─ 'failed_emails': [] (list of any failures)
    └─ 'message': "Successfully sent to 52 users"
```

---

## Admin Dashboard Response

### When Close Completes Successfully:

```json
{
  "success": true,
  "message": "Student evaluation form has been unreleased. Evaluation period ended.",
  "processing_results": {
    "success": true,
    "processed_count": 45,
    "total_staff": 50
  },
  "evaluation_period_ended": true,
  "email_notification": {
    "sent": 52,
    "failed": 0,
    "message": "Successfully sent to 52 users"
  }
}
```

**Admin sees:**
```
✅ Student evaluation form has been unreleased. Evaluation period ended.
Successfully processed evaluation results for 45 out of 50 staff members.
Evaluation results are now available in staff history.

Email Notifications:
- Sent: 52 ✅
- Failed: 0 ✅
```

---

## Email Timeline Example

### November 16, 2025 - Admin Closes at 5:00 PM

```
5:00:00 PM - Admin clicks "Close Student Evaluation"
             ↓
5:00:01 PM - System processes evaluation results
             ├─ Calculate scores
             ├─ Archive to history
             └─ Prepare notifications
             ↓
5:00:02 PM - Email service starts
             ├─ Get all 52 users
             └─ Generate email subjects
             ↓
5:00:03 PM - Email generation
             ├─ Build HTML for user 1
             ├─ Build HTML for user 2
             ├─ ... (for all 52 users)
             └─ Prepare SMTP delivery
             ↓
5:00:05 PM - SMTP server sends
             ├─ Email 1 sent → user1@school.edu ✅
             ├─ Email 2 sent → user2@school.edu ✅
             ├─ ... (52 total)
             └─ All emails queued
             ↓
5:00:30 PM - Admin sees response
             └─ "Successfully sent 52 emails"
```

---

## What Each User Receives

### In Their Email Inbox:

**From:** edulytics@system (configured DEFAULT_FROM_EMAIL)

**To:** user@school.edu

**Subject:** 📋 Student Evaluation Period Closed

**Date:** November 16, 2025, 5:00 PM

**Body:**

```
═══════════════════════════════════════════════════════════════════
  📋 STUDENT EVALUATION PERIOD CLOSED
═══════════════════════════════════════════════════════════════════

Dear User,

The Student Evaluation Form evaluation period has ended and is now CLOSED.

⚠️ IMPORTANT NOTICE ⚠️
   No further evaluations can be submitted. The evaluation period has 
   officially closed.

───────────────────────────────────────────────────────────────────
SUMMARY:
───────────────────────────────────────────────────────────────────
• Evaluation Type: Student Evaluation Form
• Status: ❌ CLOSED
• Submissions: No longer accepted

───────────────────────────────────────────────────────────────────

Thank you for your participation. Your feedback has been valuable to our 
institution's evaluation process.

───────────────────────────────────────────────────────────────────
City College of Angeles - Edulytics Evaluation System
This is an automated notification. Please do not reply to this email.
═══════════════════════════════════════════════════════════════════
```

---

## Email Configuration

### Required Django Settings:

```python
# settings.py

# SMTP Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # or your email provider
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'

# Default sender email
DEFAULT_FROM_EMAIL = 'noreply-edulytics@school.edu'
```

---

## Two Email Types in System

### 1. Release Notification (When Admin Opens Evaluation)

**Subject:** 🎓 Student Evaluation Form Released - Action Required

**Purpose:** Alert users that evaluation is open

**Action Requested:** "Please complete your evaluation"

**Status Color:** Green (#28a745)

---

### 2. Unreleased Notification (When Admin Closes Evaluation) ← Current Topic

**Subject:** 📋 Student Evaluation Period Closed

**Purpose:** Inform users that evaluation has closed

**Action Requested:** None - period is over

**Status Color:** Red (#e74c3c)

---

## Error Handling

### What If Email Fails?

```python
try:
    msg.send()  # Send email
    sent_count += 1
    
except Exception as e:
    logger.error(f"Failed to send email to {user.email}: {str(e)}")
    failed_emails.append(user.email)
    # ↑ Email address added to failed list
```

### Final Response Includes:

```json
{
  "success": true,
  "sent_count": 50,
  "failed_emails": [
    "invalid@email.com",
    "bounced@email.com"
  ],
  "message": "Successfully sent 50, but 2 failed"
}
```

**Admin sees:**
```
⚠️ Sent: 50 ✅
⚠️ Failed: 2 ❌
Failed emails:
- invalid@email.com
- bounced@email.com
```

---

## Summary Table

| Aspect | Details |
|--------|---------|
| **Email Type** | Unreleased/Close Notification |
| **Triggered By** | Admin clicks "Close Evaluation" button |
| **Recipients** | All 52 active users (except admin) |
| **Subject (Student)** | 📋 Student Evaluation Period Closed |
| **Subject (Peer)** | 📋 Peer Evaluation Period Closed |
| **Header Color** | Orange (#f39c12) |
| **Status Shown** | Closed (Red #e74c3c) |
| **Main Message** | Evaluation period ended, no more submissions |
| **Call-to-Action** | Thank you message (no action needed) |
| **Email Format** | HTML + Plain Text (multipart) |
| **From Email** | DEFAULT_FROM_EMAIL setting |
| **Mobile Friendly** | Yes (max-width: 600px, responsive) |
| **Code File** | main/email_service.py |
| **Function** | send_evaluation_unreleased_notification() |
| **Return Value** | JSON with sent_count, failed_emails, success |
| **Logging** | Full logging of each email attempt |
| **Error Handling** | Failed emails captured and reported |

---

## What Users See in Their Inbox

### When Student Evaluation Closes:

**Visual Preview:**

```
┌─────────────────────────────────────────────────────┐
│ 📋 Student Evaluation Period Closed                │
│ From: noreply-edulytics@school.edu                 │
│ To: faculty@school.edu                             │
│ Date: Nov 16, 2025, 5:00 PM                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Dear User,                                         │
│                                                     │
│  The Student Evaluation Form evaluation period     │
│  has ended and is now CLOSED.                      │
│                                                     │
│  ⚠️ IMPORTANT NOTICE                               │
│  No further evaluations can be submitted.           │
│  The evaluation period has officially closed.       │
│                                                     │
│  SUMMARY:                                           │
│  • Evaluation Type: Student Evaluation Form         │
│  • Status: ❌ CLOSED                               │
│  • Submissions: No longer accepted                 │
│                                                     │
│  Thank you for your participation. Your feedback    │
│  has been valuable to our institution's evaluation │
│  process.                                           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Complete Process When Closing

### Full Sequence:

1. **Admin Action:**
   - Click "Close Student Evaluation" button
   - System receives POST request

2. **Backend Processing:**
   - Set is_released = False
   - Call process_all_evaluation_results()
   - Call archive_period_results_to_history()
   - **→ Call send_evaluation_unreleased_notification('student')**

3. **Email Service:**
   - Retrieves all active users
   - For each user:
     - Generate email content
     - Send via SMTP
   - Collect results

4. **Response to Admin:**
   - Show success message
   - Display: "Sent 52 emails"
   - Link to view results

5. **User Experience:**
   - Each user receives email in inbox
   - Subject: 📋 Student Evaluation Period Closed
   - Can no longer submit evaluations
   - Can view archived results

---

## Notes

✅ Emails sent to **ALL 52 users** including:
- Faculty
- Coordinators
- Deans
- Students

✅ Excluded:
- School head admin (cibituonon@cca.edu.ph)

✅ Email features:
- Responsive HTML design
- Plain text fallback
- Professional styling
- Clear status indicators
- Mobile-friendly

✅ Tracking:
- All sent/failed emails logged
- Admin dashboard shows results
- Error details available

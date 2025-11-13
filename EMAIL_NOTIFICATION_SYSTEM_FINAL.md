# Email Notification Configuration - Final Summary

## Current Email System Architecture

Your Edulytics system has **TWO separate email notification systems**:

### 1️⃣ Evaluation Release/Unreleased Notifications
**File:** `main/email_service.py`

**When Triggered:**
- When admin **releases** a student or peer evaluation
- When admin **unreleases** (closes) an evaluation

**Recipients:**
- ✅ ALL active users **EXCEPT** `cibituonon@cca.edu.ph`
- This includes: Students, Teachers, Deans, Coordinators

**Status:** ✅ Modified to exclude school head

---

### 2️⃣ Evaluation Failure Alerts
**File:** `main/services/email_service.py`

**When Triggered:**
- When evaluation period **ENDS** and results are **PROCESSED**
- When instructor's evaluation score is **BELOW 70%**
- Sends to school head on **2nd failure or more**

**Recipients:**
- ✅ **School Head Only** (`cibituonon@cca.edu.ph`)
- This is `SCHOOL_HEAD_EMAIL` from your `.env` file

**Status:** ✅ Already configured correctly

---

## Email Flow Diagram

```
┌─────────────────────────────────────────────────────┐
│         EVALUATION MANAGEMENT ACTIONS                │
└─────────────────────────────────────────────────────┘
          │
          ├─ RELEASE EVALUATION
          │  └─→ [main/email_service.py]
          │      └─→ send_evaluation_released_notification()
          │          └─→ Sends to 57 users (excludes cibituonon@cca.edu.ph) ✅
          │
          ├─ UNRELEASED EVALUATION
          │  └─→ [main/email_service.py]
          │      └─→ send_evaluation_unreleased_notification()
          │          └─→ Sends to 57 users (excludes cibituonon@cca.edu.ph) ✅
          │
          └─ PROCESS RESULTS (End of Period)
             └─→ [main/services/evaluation_service.py]
                 └─→ process_evaluation_results()
                     └─→ [main/services/email_service.py]
                         └─→ send_failure_alert_to_school_head()
                             └─→ Sends to cibituonon@cca.edu.ph ✅
```

---

## Summary Table

| Notification Type | Sent When | Sent By | Recipients | Includes School Head? |
|---|---|---|---|---|
| **Evaluation Released** | Admin releases form | `main/email_service.py` | 57 users (everyone except school head) | ❌ NO |
| **Evaluation Unreleased** | Admin closes evaluation | `main/email_service.py` | 57 users (everyone except school head) | ❌ NO |
| **Failure Alert** | Period ends + score < 70% | `main/services/email_service.py` | School head only | ✅ YES |

---

## Configuration Details

### From `.env` file:
```
EMAIL_HOST_USER=ccaedulytics@gmail.com
SCHOOL_HEAD_EMAIL=cibituonon@cca.edu.ph
```

### From `main/email_service.py` (Line 39 & 114):
```python
# Exclude school head from release notifications
users = User.objects.filter(is_active=True).exclude(email='').exclude(email='cibituonon@cca.edu.ph')
```

### From `main/services/email_service.py` (Line 40):
```python
# Send failure alerts to school head
recipient_list=[settings.SCHOOL_HEAD_EMAIL]
```

---

## What This Means For You

✅ **cibituonon@cca.edu.ph will:**
- ❌ NOT get emails when evaluations are released
- ❌ NOT get emails when evaluations are closed  
- ✅ **GET emails when instructors fail their evaluations**

✅ **All other 57 users will:**
- ✅ GET emails when evaluations are released
- ✅ GET emails when evaluations are closed
- ❌ NOT get failure alerts (only school head gets those)

---

## Next Steps

The system is already configured correctly! Just:

1. ✅ Release an evaluation in your admin panel
2. ✅ Verify that 57 users receive the email (not 58)
3. ✅ Wait until evaluation period ends
4. ✅ Process results to trigger failure alerts to school head

No further configuration needed! 🚀

# 🔔 How Your System Knows When Evaluation Ends

## Overview

Your system uses **TWO mechanisms** to determine when an evaluation ends:

1. **Manual Trigger** - Admin clicks "Unrelease" button (Primary)
2. **Date-Based Detection** - Checking `end_date` field (Available for enhancement)

---

## 🎛️ Mechanism 1: Manual Trigger (Current Implementation)

### How It Works

The evaluation period ends when **the admin explicitly clicks the "Unrelease" button** in the admin control panel.

### The Flow

```
Admin Control Panel
        ↓
   [Unrelease Button] ← Admin clicks this
        ↓
unrelease_student_evaluation() function called
        ↓
Step 1: Mark Evaluation as Not Released
├─ Set: is_released = False
├─ All Evaluation records updated
└─ Evaluation form becomes unavailable to students

Step 2: Process Results from Last Period
├─ Get active evaluation period
├─ Calculate scores for all staff
├─ Store in EvaluationResult table
└─ Archive to EvaluationHistory table

Step 3: Send Notifications
├─ Email all users: "Evaluation period ended"
├─ Log admin activity
└─ Return success response

Step 4: Deactivate Period
├─ Set: is_active = False
├─ Set: end_date = timezone.now() (current timestamp)
└─ EvaluationPeriod marked as complete
```

### Code Location

File: `main/views.py` (Line 911-965)

```python
def unrelease_student_evaluation(request):
    """Called when admin clicks 'Unrelease' button"""
    if request.method == 'POST':
        # Mark all student evaluations as not released
        evaluations = Evaluation.objects.filter(
            is_released=True, 
            evaluation_type='student'
        )
        updated_count = evaluations.update(is_released=False)

        if updated_count > 0:
            # 1️⃣ Process all evaluation results
            processing_results = process_all_evaluation_results()
            
            # 2️⃣ Send emails to notify users
            email_result = EvaluationEmailService.send_evaluation_unreleased_notification('student')
            
            # 3️⃣ Log the action
            log_admin_activity(
                request=request,
                action='unrelease_evaluation',
                description=f"Unreleased student evaluation form - {updated_count} evaluation(s) deactivated. Evaluation period ended."
            )
            
            # 4️⃣ Return success
            return JsonResponse({
                'success': True,
                'message': message,
                'evaluation_period_ended': True,
                'student_evaluation_released': False,
            })
```

### When This Happens

1. **Admin navigates to** `/admin-control/`
2. **Admin sees** "Unrelease Student Evaluation" button
3. **Admin clicks** the button
4. **System executes** unrelease_student_evaluation()
5. **Evaluation ends**

### What Changes in Database

```
BEFORE Unrelease:
┌──────────────────────────────────────────────────────────┐
│ Evaluation Table                                         │
├──────────────────────────────────────────────────────────┤
│ ID │ Type    │ is_released │ evaluation_period        │
├────┼─────────┼─────────────┼──────────────────────────┤
│ 1  │ student │ True        │ 1st Semester 2024 (ID:5) │
│ 2  │ student │ True        │ 1st Semester 2024 (ID:5) │
└──────────────────────────────────────────────────────────┘

EvaluationPeriod Table:
┌──────────────────────────────────────────────────────────┐
│ ID │ Name               │ is_active │ end_date        │
├────┼────────────────────┼───────────┼─────────────────┤
│ 5  │ 1st Semester 2024  │ True ✅   │ 2024-12-31      │
└──────────────────────────────────────────────────────────┘

AFTER Unrelease:
┌──────────────────────────────────────────────────────────┐
│ Evaluation Table                                         │
├──────────────────────────────────────────────────────────┤
│ ID │ Type    │ is_released │ evaluation_period        │
├────┼─────────┼─────────────┼──────────────────────────┤
│ 1  │ student │ False ❌    │ 1st Semester 2024 (ID:5) │
│ 2  │ student │ False ❌    │ 1st Semester 2024 (ID:5) │
└──────────────────────────────────────────────────────────┘

EvaluationPeriod Table:
┌──────────────────────────────────────────────────────────┐
│ ID │ Name               │ is_active │ end_date        │
├────┼────────────────────┼───────────┼─────────────────┤
│ 5  │ 1st Semester 2024  │ False ❌  │ Nov 11, 2025    │
└──────────────────────────────────────────────────────────┘
```

---

## 📅 Mechanism 2: End Date Detection (Available)

### Current State

Your system **stores end dates** but doesn't automatically check them. You could enhance it to:

### How It Could Work

```python
# Example: Automatic detection on page load
from django.utils import timezone
from main.models import EvaluationPeriod, Evaluation

def check_evaluation_period_expired(evaluation_type='student'):
    """Check if any evaluation period has passed its end date"""
    now = timezone.now()
    
    # Find active periods that have passed their end date
    expired_periods = EvaluationPeriod.objects.filter(
        evaluation_type=evaluation_type,
        is_active=True,
        end_date__lt=now  # end_date is in the past
    )
    
    if expired_periods.exists():
        # Auto-deactivate expired periods
        for period in expired_periods:
            # Unrelease all evaluations for this period
            Evaluation.objects.filter(
                evaluation_period=period,
                is_released=True
            ).update(is_released=False)
            
            # Deactivate the period
            period.is_active = False
            period.save()
            
            return True  # Period was expired
    
    return False  # Period is still active
```

### Available Data for Detection

Each EvaluationPeriod has:

```python
class EvaluationPeriod(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateTimeField()      # ← When period starts
    end_date = models.DateTimeField()        # ← When period SHOULD end
    is_active = models.BooleanField()        # ← Currently active?
```

---

## 🔄 Complete End-to-End Process

### 1st Semester Timeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                    1ST SEMESTER FLOW                               │
└─────────────────────────────────────────────────────────────────────┘

SEPT 1, 2024
├─ Admin creates EvaluationPeriod
│  ├─ name: "1st Semester 2024"
│  ├─ start_date: 2024-09-01
│  ├─ end_date: 2024-12-31
│  └─ is_active: False
└─ System ready, waiting for release

SEPT 15, 2024 (Admin clicks "Release")
├─ Admin goes to /admin-control/
├─ Admin clicks "Release Student Evaluation" button
├─ System calls: release_student_evaluation()
│  ├─ Deactivates any old active periods
│  ├─ Activates current period (is_active = True)
│  ├─ Creates Evaluation records (is_released = True)
│  └─ Students can now evaluate
├─ Email sent: "Evaluation period opened"
└─ Evaluation Window OPEN ✅

DEC 20-31, 2024
├─ Students submitting evaluations
├─ Responses stored in EvaluationResponse table
├─ Each response linked to this period
└─ Everything normal

JAN 1, 2025 (Admin clicks "Unrelease")
├─ Admin goes to /admin-control/
├─ Admin clicks "Unrelease Student Evaluation" button
├─ System calls: unrelease_student_evaluation()
│  ├─ Step 1: Mark all evaluations as not released
│  │  └─ Evaluation.is_released = False
│  ├─ Step 2: Process results from period
│  │  ├─ Calculate scores for all faculty
│  │  ├─ Store in EvaluationResult
│  │  └─ Archive to EvaluationHistory
│  ├─ Step 3: Send notifications
│  │  ├─ Email all users: "Period closed"
│  │  └─ Update activity log
│  ├─ Step 4: Deactivate period
│  │  ├─ EvaluationPeriod.is_active = False
│  │  └─ EvaluationPeriod.end_date = NOW
│  └─ Return success message
├─ Email sent: "Evaluation period closed"
└─ Evaluation Window CLOSED ✌️

DATABASE STATE AFTER UNRELEASE:
┌───────────────────────────────────────────────────────────┐
│ EvaluationPeriod                                         │
│ ┌───────────────────────────────────────────────────────┐│
│ │ ID: 5                                                 ││
│ │ Name: 1st Semester 2024                              ││
│ │ is_active: False                                      ││
│ │ end_date: Jan 1, 2025 11:45 AM (when admin released) ││
│ └───────────────────────────────────────────────────────┘│
│                                                           │
│ EvaluationResponse (285 total)                           │
│ ┌───────────────────────────────────────────────────────┐│
│ │ All linked to Period ID 5                            ││
│ │ Cannot be edited (period closed)                      ││
│ └───────────────────────────────────────────────────────┘│
│                                                           │
│ EvaluationHistory (NEW)                                  │
│ ┌───────────────────────────────────────────────────────┐│
│ │ Faculty 1: 78.5% average from 15 responses          ││
│ │ Faculty 2: 82.3% average from 12 responses          ││
│ │ Faculty 3: 76.8% average from 18 responses          ││
│ │ ... (one record per faculty per period)              ││
│ └───────────────────────────────────────────────────────┘│
└───────────────────────────────────────────────────────────┘

JAN 15, 2025 (Admin releases NEW period)
├─ Admin creates EvaluationPeriod for 2nd Semester
│  ├─ name: "2nd Semester 2024-2025"
│  ├─ start_date: 2025-01-15
│  ├─ end_date: 2025-05-31
│  └─ is_active: False
├─ Admin clicks "Release Student Evaluation"
├─ System activates 2nd Semester period
├─ Students CAN re-evaluate same faculty again!
│  └─ NEW responses stored for 2nd Semester
├─ Email sent: "New evaluation period opened"
└─ New Evaluation Window OPEN ✅
```

---

## 📊 Key Tables and Their States

### During Evaluation (is_active=True)

```
EvaluationPeriod:
  is_active = True           ← Students can evaluate
  end_date = 2024-12-31      ← When it SHOULD end (informational)

Evaluation:
  is_released = True         ← Form is available
  evaluation_period = Period ← Linked to this period

EvaluationResponse:
  Can be created            ← Students can submit
  evaluation_period = Period ← Stored for this period
```

### After Evaluation Ends (is_active=False)

```
EvaluationPeriod:
  is_active = False          ← No more evaluations
  end_date = <updated>       ← Set to when admin clicked unrelease

Evaluation:
  is_released = False        ← Form is NOT available
  evaluation_period = Period ← Still linked

EvaluationResponse:
  Cannot be created          ← Period closed
  evaluation_period = Period ← Preserved

EvaluationHistory:
  NEW records created        ← Archive of results
  evaluation_period = Period ← Reference to period
```

---

## 🎯 Answer to Your Question

### "How does your system know when evaluation ends?"

**Current Method (In Production):**
- ✅ **Admin clicks "Unrelease" button**
- ✅ **System processes and archives results**
- ✅ **System marks period as inactive**
- ✅ **Students cannot evaluate anymore**
- ✅ **Results available in history**

**What Gets Checked:**
- `Evaluation.is_released` flag (FALSE = period ended)
- `EvaluationPeriod.is_active` flag (FALSE = period ended)
- `end_date` field (informational, not auto-checked)

**Enhancement Options:**
1. **Automatic end date checking** - Check if current date > end_date, auto-unrelease
2. **Scheduled task** - Cron job to check expired periods hourly
3. **User notification** - Warn admin when period is close to end_date
4. **Automatic archival** - Auto-archive on end_date without waiting for admin click

---

## 💻 Admin Control Panel

Location: `/admin-control/`

### UI Elements

```
┌─────────────────────────────────────────────────────────────┐
│           ADMIN CONTROL PANEL                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📊 STUDENT EVALUATION                                     │
│  ├─ Current Period: 1st Semester 2024                      │
│  ├─ Status: ACTIVE ✅                                      │
│  ├─ Started: Sept 1, 2024                                 │
│  ├─ Should End: Dec 31, 2024                              │
│  └─ [Release] [Unrelease] ← Admin clicks these            │
│                                                             │
│  📊 PEER EVALUATION                                        │
│  ├─ Current Period: 1st Semester 2024                      │
│  ├─ Status: ACTIVE ✅                                      │
│  ├─ Started: Sept 1, 2024                                 │
│  ├─ Should End: Dec 31, 2024                              │
│  └─ [Release] [Unrelease] ← Admin clicks these            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### What Each Button Does

**[Release] Button:**
1. Checks if already released (prevents double-release)
2. Processes results from OLD period
3. Deactivates OLD period
4. Activates NEW period
5. Creates Evaluation records (is_released=True)
6. Sends emails
7. Students can now evaluate ✅

**[Unrelease] Button:**
1. Marks evaluations as not released
2. Processes all staff results
3. Sends notifications
4. Updates is_released to False
5. Deactivates period
6. Students cannot evaluate anymore ❌

---

## 📊 Checking End Date Status

### SQL Queries to Check End Status

```sql
-- Check if evaluation is still active
SELECT id, name, is_active, end_date 
FROM main_evaluationperiod 
WHERE evaluation_type = 'student' 
AND is_active = True;

-- Check if period has passed end date
SELECT id, name, end_date, 
       CASE 
           WHEN end_date < NOW() THEN 'EXPIRED ⏰'
           ELSE 'ACTIVE ✅'
       END as status
FROM main_evaluationperiod 
WHERE evaluation_type = 'student';

-- Check evaluation status
SELECT e.id, e.is_released, ep.name, ep.end_date
FROM main_evaluation e
JOIN main_evaluationperiod ep ON e.evaluation_period_id = ep.id
WHERE e.evaluation_type = 'student';
```

### Python Check

```python
from django.utils import timezone
from main.models import EvaluationPeriod, Evaluation

# Check current status
active_period = EvaluationPeriod.objects.get(
    evaluation_type='student',
    is_active=True
)

print(f"Period: {active_period.name}")
print(f"Ends: {active_period.end_date}")
print(f"Days until end: {(active_period.end_date - timezone.now()).days}")

# Check if evaluation is open
is_open = Evaluation.objects.filter(
    is_released=True,
    evaluation_type='student'
).exists()

print(f"Evaluation open: {is_open}")
```

---

## 🎯 Summary Table

| Aspect | Method | Current | Potential Enhancement |
|--------|--------|---------|----------------------|
| **Detection** | Manual | Admin clicks Unrelease | Auto-check end_date |
| **Timing** | Event-based | When admin acts | Scheduled/automatic |
| **Status Flag** | is_released | FALSE = closed | - |
| **Period Flag** | is_active | FALSE = closed | - |
| **Data** | end_date | Stored, not checked | Use for validation |
| **Notification** | Email | Sent on unrelease | Send before end_date too |
| **Archival** | Manual trigger | On unrelease | On end_date reached |

---

## 🚀 Optional: Auto-Detection Enhancement

If you want the system to **automatically detect** when evaluation ends (without admin clicking):

```python
# Add this to your view or create a management command

from django.core.management.base import BaseCommand
from main.models import EvaluationPeriod, Evaluation
from django.utils import timezone

class Command(BaseCommand):
    help = 'Auto-unrelease expired evaluation periods'
    
    def handle(self, *args, **options):
        now = timezone.now()
        
        # Find active periods that have passed their end date
        expired = EvaluationPeriod.objects.filter(
            is_active=True,
            end_date__lt=now
        )
        
        for period in expired:
            # Call unrelease function for each expired period
            Evaluation.objects.filter(
                evaluation_period=period,
                is_released=True
            ).update(is_released=False)
            
            period.is_active = False
            period.save()
            
            self.stdout.write(f"Auto-unreleased period: {period.name}")
```

Then run via cron:
```bash
# Run daily to auto-close expired periods
0 0 * * * cd /path/to/project && python manage.py auto_unrelease_evaluations
```

---

## 📝 Final Answer

**Your system knows when evaluation ends through:**

1. ✅ **Admin Manual Control** (Primary - Current)
   - Admin clicks "Unrelease" button
   - System marks is_released=False
   - Period becomes inactive

2. ✅ **End Date Storage** (Secondary - Available)
   - end_date field exists on EvaluationPeriod
   - Not auto-checked currently
   - Could enable automatic detection

3. ✅ **State Flags** (Indicators)
   - is_released flag on Evaluation model
   - is_active flag on EvaluationPeriod model
   - False values = period ended

**The system is flexible!** You control when periods end via the admin panel, but the infrastructure supports automatic end-date based closure if desired.

---

**Status:** ✅ Production Ready  
**Date:** November 11, 2025  
**Document Type:** System Behavior Analysis

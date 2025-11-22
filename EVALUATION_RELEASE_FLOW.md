# Evaluation Release Flow - Step by Step

## YES! Every Release Creates an Active Period with Dates

Here's EXACTLY what happens when admin clicks "Release Evaluation":

---

## Step-by-Step Process

### Step 1: Admin Clicks "Release Student Evaluation"

**Button Location:** Admin Dashboard
```
Release Student Evaluation button
        ↓ (Admin clicks)
        ↓ (Form submitted)
```

### Step 2: System Archives Previous Period

```python
# views.py, line 1100+
previous_periods = EvaluationPeriod.objects.filter(
    evaluation_type='student',
    is_active=True
)

for period in previous_periods:
    archive_period_results_to_history(period)
    # Convert all EvaluationResult → EvaluationHistory

# Mark old period as inactive
previous_periods.update(is_active=False, end_date=timezone.now())
```

**Before Release:**
```
EvaluationPeriod table:
- Student Evaluation October 2025
  - is_active: False (from last cycle)
  - start_date: Oct 1
  - end_date: Oct 31
```

### Step 3: System Creates NEW Period with Current Dates

```python
# views.py, line 1125-1131
evaluation_period = EvaluationPeriod.objects.create(
    name=f"Student Evaluation {timezone.now().strftime('%B %Y')}",
    # ↑ Uses CURRENT month/year
    # Example: "Student Evaluation November 2025"
    
    evaluation_type='student',
    start_date=timezone.now(),           # TODAY (now)
    end_date=timezone.now() + timedelta(days=30),  # TODAY + 30 days
    is_active=True  # ← ACTIVE IMMEDIATELY!
)
```

**Example with Today's Date (November 16, 2025):**

```
NEW EvaluationPeriod created:
{
    name: "Student Evaluation November 2025"
    evaluation_type: "student"
    start_date: November 16, 2025 9:00 AM (timezone.now())
    end_date: December 16, 2025 9:00 AM (30 days later)
    is_active: True  ✅ ACTIVE NOW!
    created_at: November 16, 2025 9:00 AM
}
```

### Step 4: System Links Evaluation Form to Period

```python
# views.py, line 1135-1137
evaluations = Evaluation.objects.filter(
    is_released=False, 
    evaluation_type='student'
)

updated_count = evaluations.update(
    is_released=True,  # ← Form is now open!
    evaluation_period=evaluation_period  # ← Links to NEW period
)
```

**Result:**
```
Evaluation form updated:
{
    evaluation_type: "student"
    is_released: True  ✅ FORM OPEN!
    evaluation_period: Student Evaluation November 2025
}
```

### Step 5: System Sends Notifications

```python
EvaluationEmailService.send_evaluation_released_notification('student')
# Sends email to ALL users:
# "Evaluation period has started!"
```

---

## Timeline Example

### November 1, 2025 (Last Period)

```
EvaluationPeriod table:
- Student Evaluation October 2025
  - is_active: True ✅
  - start_date: Oct 1
  - end_date: Oct 31
  - created_at: Oct 1

Evaluation form:
  - is_released: True ✅ (form was open)
  - evaluation_period: Student Evaluation October 2025
```

**Students doing:** Submitting evaluations for October

---

### November 16, 2025 (Admin Clicks "Release Student Evaluation")

**BEFORE:**
```
Database before release:
- OLD: Student Evaluation October 2025 (is_active: True)
  - 500 EvaluationResult records
  - Results showing Oct scores for all staff
```

**AFTER (Automatically triggered):**

```
Database after release:
Step 1: Archive old results
        October results → EvaluationHistory table
        (500 records become permanent)

Step 2: Deactivate old period
        Student Evaluation October 2025
        - is_active: False ← CLOSED
        - end_date: Nov 16, 2025 (updated)

Step 3: Create NEW period
        Student Evaluation November 2025
        - is_active: True ✅ ACTIVE NOW!
        - start_date: Nov 16, 2025 9:00 AM
        - end_date: Dec 16, 2025 9:00 AM ← 30 days
        - created_at: Nov 16, 2025 9:00 AM

Step 4: Open evaluation form
        Evaluation form
        - is_released: True ✅ NOW OPEN!
        - evaluation_period: Student Evaluation November 2025

Step 5: Notify users
        Email sent: "New evaluation period started!"
```

---

## Key Points

### 1. **Automatic Period Creation**
- Admin never manually creates periods
- Just clicks "Release"
- System creates with current dates

### 2. **Period Name = Current Month**
```python
name=f"Student Evaluation {timezone.now().strftime('%B %Y')}"

Examples:
- Click release on Nov 16 → "Student Evaluation November 2025"
- Click release on Dec 5 → "Student Evaluation December 2025"
- Click release on Jan 20 → "Student Evaluation January 2026"
```

### 3. **Standard Duration = 30 Days**
```python
end_date = timezone.now() + timedelta(days=30)

Release on Nov 16 → Closes Dec 16
Release on Dec 5 → Closes Jan 4
```

### 4. **Dates Are Flexible**
If you wanted custom dates, you could modify:
```python
# Would need code change, but possible:
end_date = timezone.now() + timedelta(days=5)  # Only 5 days
# or
end_date = datetime(2025, 12, 25)  # Specific date
```

### 5. **Period is Immediately Active**
```python
is_active=True  # ← Set immediately when created
# NOT some future date
# Students can submit RIGHT NOW
```

---

## Visual Timeline

```
┌─────────────────────────────────────────────────────────────────┐
│                   Evaluation Release Timeline                   │
└─────────────────────────────────────────────────────────────────┘

November 2025
├─ Oct 31  ├─────────────────────────────────┤
│          │ Oct Period (30 days running)    │ is_active: True ✅
│          │ 500 evaluations submitted       │
│
├─ Nov 1   │
│          │ Oct Period still open (students can still submit)
│
├─ Nov 16  ├─────────────────────────────────┤
│  (TODAY) │ ADMIN CLICKS "RELEASE"          │
│          │                                 │
│          ├─ ARCHIVE Oct results            │
│          ├─ CLOSE Oct period (is_active: False)
│          │
│          ├─ CREATE Nov period (is_active: True)
│          │  start: Nov 16 9:00 AM
│          │  end:   Dec 16 9:00 AM
│          │
│          ├─ OPEN evaluation form
│          │
│          └─ SEND notifications
│
├─ Nov 17  ├─────────────────────────────────┤
│          │ Nov Period (NEW, 30 days)       │ is_active: True ✅
│          │ 0 evaluations yet (just opened) │
│
├─ Dec 16  │
│          ├─────────────────────────────────┤
│          │ Nov Period ends (auto-closes)   │ is_active: False ✅
│          │ Results archived automatically  │
│
└─────────────────────────────────────────────────────────────────┘
```

---

## Database State Comparison

### BEFORE Release (Nov 16, 9:00 AM)

```sql
-- EvaluationPeriod table
SELECT * FROM main_evaluationperiod 
WHERE evaluation_type='student' 
ORDER BY created_at DESC;

┌─────┬─────────────────────────────┬──────────┬─────────┬─────────┬────────────┐
│ id  │ name                        │ type     │ active  │ start   │ end        │
├─────┼─────────────────────────────┼──────────┼─────────┼─────────┼────────────┤
│  3  │ Student Evaluation Oct 2025 │ student  │ True ✅ │ Oct 1   │ Oct 31     │
│  2  │ Student Evaluation Sep 2025 │ student  │ False   │ Sep 1   │ Sep 30     │
│  1  │ Student Evaluation Aug 2025 │ student  │ False   │ Aug 1   │ Aug 31     │
└─────┴─────────────────────────────┴──────────┴─────────┴─────────┴────────────┘

-- Evaluation form
SELECT * FROM main_evaluation WHERE evaluation_type='student';

┌─────┬──────────┬──────────┬────────────────────┐
│ id  │ type     │ released │ evaluation_period  │
├─────┼──────────┼──────────┼────────────────────┤
│  4  │ student  │ True ✅  │ 3 (Oct 2025)       │
└─────┴──────────┴──────────┴────────────────────┘
```

### AFTER Release (Nov 16, 9:01 AM)

```sql
-- EvaluationPeriod table
SELECT * FROM main_evaluationperiod 
WHERE evaluation_type='student' 
ORDER BY created_at DESC;

┌─────┬─────────────────────────────┬──────────┬─────────┬─────────┬────────────┐
│ id  │ name                        │ type     │ active  │ start   │ end        │
├─────┼─────────────────────────────┼──────────┼─────────┼─────────┼────────────┤
│  4  │ Student Evaluation Nov 2025 │ student  │ True ✅ │ Nov 16  │ Dec 16     │
│  3  │ Student Evaluation Oct 2025 │ student  │ False   │ Oct 1   │ Nov 16     │
│  2  │ Student Evaluation Sep 2025 │ student  │ False   │ Sep 1   │ Sep 30     │
│  1  │ Student Evaluation Aug 2025 │ student  │ False   │ Aug 1   │ Aug 31     │
└─────┴─────────────────────────────┴──────────┴─────────┴─────────┴────────────┘

-- Evaluation form
SELECT * FROM main_evaluation WHERE evaluation_type='student';

┌─────┬──────────┬──────────┬────────────────────┐
│ id  │ type     │ released │ evaluation_period  │
├─────┼──────────┼──────────┼────────────────────┤
│  4  │ student  │ True ✅  │ 4 (Nov 2025) ← UPDATED!
└─────┴──────────┴──────────┴────────────────────┘

-- Old results now in history
SELECT * FROM main_evaluationhistory 
WHERE evaluation_period_id = 3;  -- Oct 2025

Result: 500+ records with archived Oct scores
```

---

## Code Proof (Exact Lines)

**File: `main/views.py`**

```python
# Line 1100-1135: Archive old period
previous_periods = EvaluationPeriod.objects.filter(
    evaluation_type='student',
    is_active=True
)

for period in previous_periods:
    archive_period_results_to_history(period)

previous_periods.update(is_active=False, end_date=timezone.now())

# Line 1125-1131: Create NEW period with dates
evaluation_period = EvaluationPeriod.objects.create(
    name=f"Student Evaluation {timezone.now().strftime('%B %Y')}",
    evaluation_type='student',
    start_date=timezone.now(),
    end_date=timezone.now() + timezone.timedelta(days=30),
    is_active=True  # ← ACTIVE IMMEDIATELY
)

# Line 1135-1137: Link form to period
evaluations = Evaluation.objects.filter(
    is_released=False, 
    evaluation_type='student'
)
updated_count = evaluations.update(
    is_released=True,
    evaluation_period=evaluation_period
)
```

---

## Summary

✅ **Yes, every time admin releases:**
- NEW EvaluationPeriod created with current dates
- name = Month + Year (auto-generated)
- start_date = NOW (when admin clicks)
- end_date = NOW + 30 days
- is_active = True (immediately open)
- Form = is_released True (immediately open)
- Previous period archived and closed

✅ **All automatic - no manual creation needed**

✅ **Dates are current - matches when release happened**

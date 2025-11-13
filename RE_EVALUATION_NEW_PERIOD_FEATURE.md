# Re-Evaluation in New Periods - Feature Implementation

## Overview

Students and instructors can now evaluate the same instructor/colleague multiple times, but only **once per evaluation period**. When a new evaluation period is released, users can re-evaluate the same instructor with fresh responses.

## Problem Statement

**Before:** 
- Unique constraint: `(evaluator, evaluatee)` 
- User evaluated instructor once → Could never evaluate again, even in new periods
- Results from multiple periods mixed together

**After:**
- Unique constraint: `(evaluator, evaluatee, evaluation_period)`
- User can evaluate same instructor in each new period
- Results properly separated by period

## Database Changes

### Model: EvaluationResponse

**Added Field:**
```python
evaluation_period = models.ForeignKey(
    EvaluationPeriod, 
    on_delete=models.CASCADE, 
    null=True, 
    blank=True, 
    db_index=True
)
```

**Updated Constraint:**
```python
# Old (Line 248):
unique_together = ('evaluator', 'evaluatee')

# New (Line 248):
unique_together = ('evaluator', 'evaluatee', 'evaluation_period')
```

**Migration:** `0013_add_evaluation_period_to_responses.py`
- ✅ Applied to MySQL
- ✅ Database verified

### Table Structure

```
main_evaluationresponse:
  ├─ id (PK)
  ├─ evaluator_id (FK → User)
  ├─ evaluatee_id (FK → User)
  ├─ evaluation_period_id (FK → EvaluationPeriod) ← NEW
  ├─ student_number
  ├─ student_section
  ├─ submitted_at
  ├─ question1-15 (ratings)
  ├─ comments
  └─ UNIQUE(evaluator_id, evaluatee_id, evaluation_period_id) ← UPDATED
```

## Code Changes

### 1. Student Evaluation Form (`main/views.py` - Line ~1655)

**Before:**
```python
# Prevent duplicate evaluation (forever)
if EvaluationResponse.objects.filter(evaluator=request.user, evaluatee=evaluatee).exists():
    messages.error(request, 'You have already evaluated this instructor.')
    return redirect('main:evaluationform')
```

**After:**
```python
# Get the current active evaluation period
try:
    current_period = EvaluationPeriod.objects.get(
        evaluation_type='student',
        is_active=True
    )
except EvaluationPeriod.DoesNotExist:
    messages.error(request, 'No active evaluation period found.')
    return redirect('main:evaluationform')

# Prevent duplicate evaluation IN THE SAME PERIOD ONLY
if EvaluationResponse.objects.filter(
    evaluator=request.user, 
    evaluatee=evaluatee,
    evaluation_period=current_period
).exists():
    messages.error(request, 'You have already evaluated this instructor in this evaluation period.')
    return redirect('main:evaluationform')
```

### 2. Student Evaluation Response Creation (`main/views.py` - Line ~1727)

**Before:**
```python
evaluation_response = EvaluationResponse(
    evaluator=request.user,
    evaluatee=evaluatee,
    student_number=student_number,
    student_section=student_section,
    comments=comments,
    **questions
)
```

**After:**
```python
evaluation_response = EvaluationResponse(
    evaluator=request.user,
    evaluatee=evaluatee,
    evaluation_period=current_period,  # ← ADDED
    student_number=student_number,
    student_section=student_section,
    comments=comments,
    **questions
)
```

### 3. Staff Evaluation Form (`main/views.py` - Line ~2167)

**Before:**
```python
# Get already evaluated staff members (all time)
evaluated_ids = EvaluationResponse.objects.filter(
    evaluator=request.user
).values_list('evaluatee_id', flat=True)

# Check if already evaluated (all time)
if EvaluationResponse.objects.filter(evaluator=request.user, evaluatee=evaluatee).exists():
    messages.error(request, f"You have already evaluated {evaluatee.username}.")
    return redirect('main:evaluationform_staffs')
```

**After:**
```python
# Get current peer evaluation period
try:
    current_peer_period = EvaluationPeriod.objects.get(
        evaluation_type='peer',
        is_active=True
    )
except EvaluationPeriod.DoesNotExist:
    # Handle error...
    return render(request, 'main/no_active_evaluation.html', {...})

# Get already evaluated staff members FOR THIS PERIOD ONLY
evaluated_ids = EvaluationResponse.objects.filter(
    evaluator=request.user,
    evaluation_period=current_peer_period  # ← ADDED
).values_list('evaluatee_id', flat=True)

# Check if already evaluated IN THIS PERIOD ONLY
if EvaluationResponse.objects.filter(
    evaluator=request.user, 
    evaluatee=evaluatee,
    evaluation_period=current_peer_period  # ← ADDED
).exists():
    messages.error(request, f"You have already evaluated {evaluatee.username} in this evaluation period.")
    return redirect('main:evaluationform_staffs')
```

### 4. Staff Evaluation Response Creation (`main/views.py` - Line ~2210)

**Before:**
```python
response = EvaluationResponse.objects.create(
    evaluator=request.user,
    evaluatee=evaluatee,
    student_section=f"{user_profile.institute} Staff",
    comments=request.POST.get('comments', ''),
    question1=request.POST.get('question1'),
    # ... questions 2-15
)
```

**After:**
```python
response = EvaluationResponse.objects.create(
    evaluator=request.user,
    evaluatee=evaluatee,
    evaluation_period=current_peer_period,  # ← ADDED
    student_section=f"{user_profile.institute} Staff",
    comments=request.POST.get('comments', ''),
    question1=request.POST.get('question1'),
    # ... questions 2-15
)
```

## User Flow

### Timeline Example

#### November 2025 - First Evaluation Period Released

```
Admin releases "Student Evaluation November 2025"
├─ is_active = TRUE
├─ current_period = "Student Evaluation November 2025"
│
Student John evaluates Instructor Smith
├─ Creates EvaluationResponse:
│  ├─ evaluator: John
│  ├─ evaluatee: Smith
│  ├─ evaluation_period: Student Evaluation November 2025 ← LINKED
│  ├─ ratings: 4, 5, 3, 4, 5, ...
│  └─ submitted_at: 2025-11-15
│
✓ Result stored and visible in profile settings
✓ Unique constraint enforced: (John, Smith, Nov 2025) = OK
✓ Unique constraint enforced: (John, Smith, Dec 2025) = BLOCKED (same period)
```

#### One Year Later - November 2026 - New Evaluation Period Released

```
Admin releases "Student Evaluation November 2026"
├─ Deactivate: Student Evaluation November 2025 (is_active=FALSE)
├─ Archive: Results from Nov 2025 → EvaluationHistory
├─ Create: Student Evaluation November 2026 (is_active=TRUE)
│
Student John evaluates Instructor Smith (again)
├─ System checks unique constraint:
│  └─ (John, Smith, Nov 2026) = NOT IN DATABASE ✓ ALLOWED
│
├─ Creates NEW EvaluationResponse:
│  ├─ evaluator: John
│  ├─ evaluatee: Smith
│  ├─ evaluation_period: Student Evaluation November 2026 ← NEW PERIOD
│  ├─ ratings: 5, 4, 4, 5, 4, ...  (different ratings allowed)
│  └─ submitted_at: 2026-11-18
│
✓ NEW evaluation can be submitted
✓ Nov 2025 results in history (separate from Nov 2026)
✓ Each period has independent responses
```

## Query Examples

### Get Evaluations for Current Period Only

```python
from main.models import EvaluationResponse, EvaluationPeriod

current_period = EvaluationPeriod.objects.get(
    evaluation_type='student',
    is_active=True
)

# Get all responses for this period
responses = EvaluationResponse.objects.filter(
    evaluation_period=current_period
)

# Get responses for specific instructor
responses = EvaluationResponse.objects.filter(
    evaluatee=instructor,
    evaluation_period=current_period
)

# Check if user has evaluated someone THIS PERIOD
has_evaluated = EvaluationResponse.objects.filter(
    evaluator=user,
    evaluatee=instructor,
    evaluation_period=current_period
).exists()
```

### Get All Evaluations (Historical)

```python
# Get all evaluations of an instructor (all periods)
all_evaluations = EvaluationResponse.objects.filter(
    evaluatee=instructor
)

# Group by period
from django.db.models import Count
by_period = all_evaluations.values('evaluation_period').annotate(
    count=Count('id')
)
```

## Error Handling

### Scenario 1: User Evaluates Same Person in Same Period

```
User attempts to evaluate Instructor Smith in Nov 2026 (second time)
↓
System queries: EvaluationResponse.objects.filter(
    evaluator=user, 
    evaluatee=Smith,
    evaluation_period=Nov2026_period
)
↓
Query returns: 1 record (already exists)
↓
Error message: "You have already evaluated Smith in this evaluation period."
↓
Redirect to form (no submission)
```

### Scenario 2: New Period Released, User Can Re-Evaluate

```
Admin releases new evaluation (Nov 2026)
↓
User attempts to evaluate same person
↓
System queries: EvaluationResponse.objects.filter(
    evaluator=user, 
    evaluatee=Smith,
    evaluation_period=Nov2026_period  ← Different period!
)
↓
Query returns: 0 records (allowed!)
↓
Response saved successfully
↓
Success message: "Evaluation submitted successfully!"
```

## Result Separation

### EvaluationResult Calculation

The `get_user_evaluation_result()` function already filters by period:

```python
# From main/views.py - Line ~4484
responses = EvaluationResponse.objects.filter(
    evaluatee=user
)

# Filter by period if provided
if evaluation_period:
    responses = responses.filter(
        submitted_at__gte=evaluation_period.start_date,
        submitted_at__lte=evaluation_period.end_date
    )

# Calculate scores for THIS period only
```

**Result:**
- ✅ Nov 2025 results calculated separately
- ✅ Nov 2026 results calculated separately
- ✅ Each period has independent scores/percentages
- ✅ Archiving moves Nov 2025 to history
- ✅ Profile settings shows only active period (Nov 2026)

## Testing Checklist

- [ ] **Create response with evaluation_period**
  - Student evaluation form submission
  - Staff evaluation form submission
  - Verify `evaluation_period` field populated in DB

- [ ] **Prevent duplicate in same period**
  - Submit evaluation for instructor A
  - Try to submit again for same instructor in same period
  - Verify error message
  - Verify no duplicate record created

- [ ] **Allow re-evaluation in different period**
  - Submit evaluation for instructor A in Nov 2025
  - Release new evaluation (Nov 2026)
  - Submit evaluation for same instructor in Nov 2026
  - Verify: 2 separate records in EvaluationResponse
  - Verify: Different periods linked to each

- [ ] **Result separation by period**
  - Calculate results for Nov 2025 only
  - Verify correct scores for period
  - Calculate results for Nov 2026 only
  - Verify correct scores for period (independent)

- [ ] **History archival**
  - Release new period
  - Verify Nov 2025 results → EvaluationHistory
  - Verify Nov 2026 results still in EvaluationResult
  - Profile shows Nov 2026 only

- [ ] **Backward compatibility**
  - Old responses without evaluation_period = NULL
  - Should not break queries
  - Admin can manually set period if needed

## SQL Verification

```sql
-- Verify unique constraint exists
SHOW CREATE TABLE main_evaluationresponse\G

-- Check constraint with evaluation_period
ALTER TABLE main_evaluationresponse 
ADD UNIQUE(evaluator_id, evaluatee_id, evaluation_period_id);

-- Verify index on evaluation_period
SHOW INDEXES FROM main_evaluationresponse;

-- Sample data (should see same evaluator-evaluatee in different periods)
SELECT evaluator_id, evaluatee_id, evaluation_period_id, submitted_at 
FROM main_evaluationresponse 
WHERE evaluator_id = 1 AND evaluatee_id = 5 
ORDER BY evaluation_period_id;
```

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Duplicate Check** | `(evaluator, evaluatee)` | `(evaluator, evaluatee, evaluation_period)` |
| **Same Person, Same Period** | ❌ Cannot evaluate | ❌ Cannot evaluate (maintained) |
| **Same Person, Different Period** | ❌ Cannot evaluate | ✅ CAN evaluate (NEW) |
| **Results Separation** | Mixed across periods | Separated by period (with queries) |
| **Historical Data** | Lost | Preserved in EvaluationHistory |
| **Profile Settings** | Shows all results | Shows only active period |
| **Re-evaluation** | Not possible | Possible each new period |

## Migration Info

- **Migration File:** `main/migrations/0013_add_evaluation_period_to_responses.py`
- **Migration Status:** ✅ Applied
- **Database:** MySQL
- **Fields Modified:**
  - Added: `evaluation_period` (ForeignKey)
  - Updated: `unique_together` constraint

## Code Locations

| Task | File | Line(s) |
|------|------|---------|
| Model definition | `main/models.py` | 215-250 |
| Student eval duplicate check | `main/views.py` | ~1656-1672 |
| Student eval response create | `main/views.py` | ~1727-1735 |
| Staff eval duplicate check | `main/views.py` | ~2184-2195 |
| Staff eval response create | `main/views.py` | ~2210-2228 |
| Archiving function | `main/views.py` | ~4570-4591 |


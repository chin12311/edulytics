# Implementation & Testing Guide

## What Was Implemented

The evaluation system now properly manages the complete lifecycle of evaluation periods to prevent result accumulation and ensure clean historical data.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    EVALUATION LIFECYCLE                      │
└─────────────────────────────────────────────────────────────┘

1. RELEASE NEW EVALUATION
   ↓
   Archive previous active periods (is_active: True → False)
   ↓
   Create new active period (is_active: True, start_date: now)
   ↓
   Users can now submit responses

2. SUBMIT RESPONSES (During Period)
   ↓
   Each response timestamped (submitted_at: now)
   ↓
   Responses stored in database
   ↓
   Users see building results in Profile Settings

3. UNRELEASE EVALUATION (End Period)
   ↓
   Current active period marked inactive (is_active: False)
   ↓
   For each staff member:
   └─ Filter responses by period date range
   └─ Calculate scores from ONLY those responses
   └─ Store results linked to specific period

4. RESULTS AVAILABLE
   ↓
   Current: Profile Settings (active periods only)
   ↓
   Historical: Evaluation History (archived periods only)
```

---

## How to Test the Fix

### Test Scenario 1: Basic Period Archival

**Objective:** Verify that releasing a new evaluation archives the previous one.

**Steps:**
```
1. Access Django Admin: /admin
2. Check EvaluationPeriod table
   - Note: No periods exist initially
3. Release Student Evaluation
   - Navigate to Admin → Release Evaluation
   - Click "Release Student Evaluation"
   - Observe: "Archived 0 previous evaluation period(s)"
   - Observe: New period created "Student Evaluation November 2024"
   - Check EvaluationPeriod table → One period with is_active=True
4. Submit 2-3 test responses as students
5. Release Student Evaluation Again
   - Click "Release Student Evaluation"
   - Observe: "Archived 1 previous evaluation period(s)"
   - Observe: New period created "Student Evaluation November 2024" (different timestamp)
   - Check EvaluationPeriod table → Now shows 2 periods:
     * First one: is_active=False (archived)
     * Second one: is_active=True (current)
```

**Expected Result:** ✅ Previous period archived when new evaluation released

---

### Test Scenario 2: Results Isolation

**Objective:** Verify that results from different periods don't mix.

**Setup:**
```sql
-- In Django Shell or direct DB access
# Check existing periods and results
SELECT * FROM main_evaluationperiod WHERE evaluation_type='student';
SELECT * FROM main_evaluationresult;
```

**Steps:**
```
1. Release Evaluation 1 (Period 1)
   - Time: T0 (e.g., Nov 1, 2024)
   
2. Submit responses for Faculty A (3 evaluations)
   - Times: T5, T10, T15 minutes later
   
3. Admin unreleases → process_all_evaluation_results() runs
   - Period 1 marked is_active=False
   - Results calculated from responses with submitted_at between T0-T0+30days
   - EvaluationResult created for Faculty A, Period 1
   - Check: Total percentage should match the 3 responses
   
4. Release Evaluation 2 (Period 2)
   - Period 1 archived: is_active=False ✓
   - Period 2 created: is_active=True ✓
   
5. Submit NEW responses for Faculty A (2 evaluations)
   - Times: T0+32 days, T0+35 days (new period)
   
6. Admin unreleases → process_all_evaluation_results() runs
   - Period 2 marked is_active=False
   - Results calculated from responses with submitted_at between T0+30days-T0+60days
   - EvaluationResult created for Faculty A, Period 2
   - Check: Total percentage should only reflect the 2 new responses
```

**Verification Query:**
```sql
SELECT ep.name, ep.is_active, er.total_percentage, er.total_responses
FROM main_evaluationresult er
JOIN main_evaluationperiod ep ON er.evaluation_period_id = ep.id
WHERE er.user_id = <faculty_id>
ORDER BY ep.start_date;

-- Expected:
-- Period 1 (Nov):  is_active=0  total_responses=3
-- Period 2 (Dec):  is_active=0  total_responses=2
```

**Expected Result:** ✅ Each period has isolated results, no mixing

---

### Test Scenario 3: Profile Settings vs History

**Objective:** Verify that current and historical results display correctly.

**Steps:**
```
1. Login as Faculty A
2. Navigate to Profile Settings
   - Check Evaluation Results section
   - Should be EMPTY (no active periods with responses yet)

3. Release Evaluation 1
   - Submit 5 responses from different students
   
4. View Profile Settings
   - Should see results building (from Period 1)
   
5. Unrelease → Period 1 archived
   - Profile Settings should be EMPTY again (Period 1 no longer active)
   
6. Navigate to Evaluation History (sidebar "📜 History")
   - Should see Period 1 with the 5 results
   - Results should match what was shown in Profile Settings
   
7. Release Evaluation 2
   - Period 1 still in History (is_active=False)
   - Profile Settings empty (no Period 2 responses yet)
   
8. Submit 3 NEW responses in Period 2
   
9. View Profile Settings
   - Should see 3 results (from Period 2 only)
   
10. Unrelease → Period 2 archived
    - Navigate to Evaluation History
    - Should see BOTH Period 1 (5 results) and Period 2 (3 results)
    - Completely separate data
```

**Expected Result:** ✅ Current and historical results properly separated

---

### Test Scenario 4: Section-Based Results

**Objective:** Verify that section-specific results also respect period boundaries.

**Steps:**
```
1. Release Evaluation 1
   
2. Submit responses for Faculty A from:
   - Section A (2 responses)
   - Section B (3 responses)
   
3. Check Profile Settings → Section dropdown
   - Overall Results: 5 responses ✓
   - Section A: 2 responses ✓
   - Section B: 3 responses ✓
   
4. Unrelease → Period 1 archived
   
5. Release Evaluation 2
   
6. Submit NEW responses for Faculty A from:
   - Section A (1 response)
   - Section C (2 responses)
   
7. Check Profile Settings → Section dropdown
   - Overall Results: 3 responses (from Period 2 only) ✓
   - Section A: 1 response (not 3!) ✓
   - Section B: 0 responses (not in Period 2) ✓
   - Section C: 2 responses ✓
   
8. Check Evaluation History
   - Period 1: Section A=2, Section B=3
   - Period 2: Section A=1, Section C=2
```

**Expected Result:** ✅ Section-based filtering also respects period boundaries

---

## Database Verification Queries

### Check Period Archival
```sql
SELECT 
    id,
    name,
    evaluation_type,
    is_active,
    start_date,
    end_date,
    created_at
FROM main_evaluationperiod
ORDER BY start_date DESC;

-- Expected after multiple releases:
-- Period 1: is_active=0 (archived)
-- Period 2: is_active=0 (archived)
-- Period 3: is_active=1 (current)
```

### Check Results Isolation
```sql
SELECT 
    er.id,
    u.username,
    ep.name,
    ep.start_date,
    ep.end_date,
    er.total_percentage,
    er.total_responses
FROM main_evaluationresult er
JOIN auth_user u ON er.user_id = u.id
JOIN main_evaluationperiod ep ON er.evaluation_period_id = ep.id
ORDER BY ep.start_date, u.username;

-- Each (user, period) combination should have exactly ONE result
-- Results should only include responses submitted in that period
```

### Verify Unique Constraint
```sql
-- Test that unique_together is enforced
-- Try creating duplicate (should fail):
SELECT 
    CONCAT(user_id, '-', evaluation_period_id, '-', COALESCE(section_id, 'NULL')) as unique_key,
    COUNT(*) as count
FROM main_evaluationresult
GROUP BY CONCAT(user_id, '-', evaluation_period_id, '-', COALESCE(section_id, 'NULL'))
HAVING count > 1;

-- Expected: 0 rows (no duplicates)
```

### Check Response Timestamps
```sql
SELECT 
    er.id,
    u.username,
    ep.name,
    ep.start_date,
    ep.end_date,
    COUNT(DISTINCT evr.id) as response_count,
    MIN(evr.submitted_at) as first_response,
    MAX(evr.submitted_at) as last_response
FROM main_evaluationresult er
JOIN auth_user u ON er.user_id = u.id
JOIN main_evaluationperiod ep ON er.evaluation_period_id = ep.id
LEFT JOIN main_evaluationresponse evr ON (
    evr.evaluatee_id = u.id 
    AND evr.submitted_at >= ep.start_date 
    AND evr.submitted_at <= ep.end_date
)
GROUP BY er.id, u.username, ep.name, ep.start_date, ep.end_date
ORDER BY ep.start_date, u.username;

-- Verify: response times fall within period boundaries
```

---

## Performance Validation

### Query Performance Check
```python
# In Django Shell

from main.models import EvaluationPeriod, EvaluationResponse, EvaluationResult
from django.contrib.auth.models import User
from django.utils import timezone
import time

# Get a test period
period = EvaluationPeriod.objects.filter(is_active=False).first()
user = User.objects.filter(userprofile__role='FACULTY').first()

# Benchmark response filtering
start = time.time()
responses = EvaluationResponse.objects.filter(
    evaluatee=user,
    submitted_at__gte=period.start_date,
    submitted_at__lte=period.end_date
)
count = responses.count()
elapsed = time.time() - start

print(f"Period query: {count} responses in {elapsed:.3f}s")
# Expected: < 0.1s for typical data

# Check index usage
print(responses.query)  # Review SQL plan
```

---

## Admin Dashboard Testing

### What to Look For

1. **Release Student Evaluation Button**
   - Should show message: "Archived X previous evaluation period(s)"
   - Should show: "New period created: Student Evaluation [Month] [Year]"

2. **Unrelease Student Evaluation Button**
   - Should show: "Successfully processed evaluation results for X out of Y staff"
   - Should show: "X/Y staff members processed"

3. **Email Notifications**
   - Release: All users should receive notification (except excluded school head)
   - Unrelease: All users should receive notification

---

## Troubleshooting

### Issue: Results still accumulating

**Check:**
```sql
-- 1. Verify periods are being created
SELECT * FROM main_evaluationperiod WHERE evaluation_type='student' ORDER BY start_date DESC LIMIT 5;

-- 2. Verify old periods are marked inactive
SELECT * FROM main_evaluationperiod WHERE evaluation_type='student' AND is_active=1;
-- Should return only 1 period (current)

-- 3. Check response timestamps
SELECT er.id, er.user_id, er.evaluation_period_id, 
       COUNT(*) as response_count
FROM main_evaluationresult er
LEFT JOIN main_evaluationresponse evr ON evr.evaluatee_id = er.user_id
GROUP BY er.id
HAVING response_count > 100;  -- Alert if unexpectedly high
```

**Fix:**
- Check `release_student_evaluation()` is being called
- Check `process_all_evaluation_results()` is processing correctly
- Verify `submitted_at` timestamps on EvaluationResponse

### Issue: History shows incorrect results

**Check:**
```python
# In Django Shell
from main.views import process_evaluation_results_for_user

user = User.objects.get(username='faculty_name')
period = EvaluationPeriod.objects.filter(is_active=False).first()

# Debug result processing
result = process_evaluation_results_for_user(user, period)
print(f"User: {user}")
print(f"Period: {period.name} ({period.start_date} to {period.end_date})")
print(f"Result: {result.total_responses} responses, {result.total_percentage}%")
```

### Issue: Period boundaries not respected

**Check:**
```python
# Verify compute_category_scores filters correctly
from main.views import compute_category_scores

user = User.objects.get(username='faculty_name')
period = EvaluationPeriod.objects.filter(is_active=False).first()

# This should work with evaluation_period parameter
scores = compute_category_scores(user, evaluation_period=period)
print(f"Scores: {scores}")
```

---

## Rollback Plan (If Needed)

If critical issues arise, the changes are backward compatible:

1. **Old code still works:** Functions default to previous behavior if `evaluation_period=None`
2. **No schema changes:** Database structure unchanged
3. **No data loss:** All existing data preserved

---

## Sign-Off Checklist

- [ ] Django system check passes: `python manage.py check`
- [ ] No syntax errors in updated views.py
- [ ] Test Scenario 1: Period archival works
- [ ] Test Scenario 2: Results isolation verified
- [ ] Test Scenario 3: Profile settings vs history separate
- [ ] Test Scenario 4: Section-based results correct
- [ ] Database queries show expected structure
- [ ] Email notifications working
- [ ] Admin activity logging functional
- [ ] No performance regression observed

---

## Success Criteria

✅ When releasing a new evaluation:
- Previous period archived (is_active=False)
- New period created (is_active=True)
- Responses properly separated by period

✅ When viewing results:
- Profile Settings: Only shows active period results
- Evaluation History: Shows archived period results
- Results never mix between periods

✅ Data integrity:
- No duplicate results per (user, period, section)
- Each period has clean, isolated response data
- Historical data properly archived


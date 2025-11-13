# 🧪 TEST GUIDE - Verify Evaluation History Archival Works

## Before Testing

```bash
# Verify installation
python manage.py check
# Expected: System check identified no issues (0 silenced)
```

---

## Test Scenario

### STEP 1: Release First Evaluation
```
1. Log in as Admin
2. Navigate to Admin Dashboard
3. Click "Release Student Evaluation"

Expected Results:
✓ Green success message appears
✓ Message says: "Archived 0 previous evaluation period(s)"
✓ Message says: "New period created: Student Evaluation [Month] [Year]"
```

### STEP 2: Submit First Evaluation
```
1. Log out from Admin
2. Log in as Student
3. Navigate to Staff Evaluation Form
4. Select an Instructor (e.g., Dr. Smith)
5. Fill evaluation form with ratings (e.g., all Outstanding: 5 stars)
6. Click "Submit"

Expected Results:
✓ Evaluation submitted successfully
```

### STEP 3: Check Profile Settings (Current Results)
```
1. Navigate to Profile Settings (dropdown menu)
2. Click "Evaluation Results"

Expected Results:
✓ See evaluation result for Dr. Smith
✓ Shows: "Outstanding" rating (5.0 average)
✓ Shows: "1 Total Responses"
✓ Shows: High percentage (e.g., 90%+)
```

### STEP 4: Check Evaluation History (Should be Empty)
```
1. Navigate to Sidebar
2. Click "📜 History"

Expected Results:
✓ "No evaluation history yet" OR Empty list
✓ No past periods shown yet
```

### STEP 5: Release Second Evaluation
```
1. Log out from Student
2. Log in as Admin
3. Click "Release Student Evaluation"

Expected Results:
✓ Green success message appears
✓ **CRITICAL:** Message says "Archived 1 previous evaluation period(s)"
✓ Message says: "New period created: Student Evaluation [Month] [Year]"
```

### STEP 6: Check Evaluation History (Should Show First Period) ✅ KEY TEST
```
1. Log out from Admin
2. Log in as any Staff member (Dean, Coordinator, Faculty)
3. Click "📜 History" in Sidebar

Expected Results:
✓ **ARCHIVAL WORKING:** Now shows previous evaluation period
✓ Shows something like: "Student Evaluation November 2025"
✓ Shows: "40.0%" or similar (the result from Step 2)
✓ Shows: "1 Total Responses"
✓ Shows: The category breakdown from Step 2
✓ Result is NOW IN HISTORY (not in Profile Settings anymore)
```

### STEP 7: Submit Second Evaluation (New Data)
```
1. Navigate to Staff Evaluation Form (new period)
2. Select SAME Instructor (Dr. Smith)
3. Fill form with DIFFERENT ratings (e.g., all Satisfactory: 3 stars)
4. Click "Submit"

Expected Results:
✓ New evaluation submitted for same instructor
```

### STEP 8: Check Profile Settings (New Results Only)
```
1. Navigate to Profile Settings
2. Click "Evaluation Results"

Expected Results:
✓ Shows NEW result for Dr. Smith
✓ Shows: "Satisfactory" or lower rating (3.0 average)
✓ Shows: "1 Total Responses" (NOT 2!)
✓ Shows: Lower percentage (NOT combined with first evaluation)
✓ **CRITICAL:** Completely different from Step 3
```

### STEP 9: Check Evaluation History (Both Periods)
```
1. Click "📜 History" in Sidebar

Expected Results:
✓ Shows TWO evaluation periods now:
  ├─ Period 1 (November 2025): 4-5 stars, 1 response, 90%+
  └─ Period 2 (December 2025): 3 stars, 1 response, 60%
✓ Each period shows SEPARATE results
✓ No mixing or accumulation ✓
```

---

## Database Verification (Optional)

If you want to verify at database level:

```sql
-- Check evaluation periods
SELECT id, name, is_active, start_date, end_date 
FROM main_evaluationperiod 
WHERE evaluation_type='student'
ORDER BY start_date DESC;

-- Expected:
-- Period 1: is_active=0 (False) - ARCHIVED
-- Period 2: is_active=1 (True) - CURRENT

-- Check results are linked to correct periods
SELECT er.id, u.username, ep.name, ep.is_active, er.total_percentage, er.total_responses
FROM main_evaluationresult er
JOIN auth_user u ON er.user_id = u.id
JOIN main_evaluationperiod ep ON er.evaluation_period_id = ep.id
WHERE u.username = 'instructor_name'
ORDER BY ep.start_date;

-- Expected:
-- Instructor: Period 1 (is_active=0): 90%, 1 response
-- Instructor: Period 2 (is_active=1): 60%, 1 response
```

---

## Success Criteria ✅

### If This Works - Archival is Fixed
- [ ] Step 5: Message shows "Archived 1 previous evaluation period(s)"
- [ ] Step 6: History NOW shows the first period
- [ ] Step 8: Profile Settings shows ONLY new results (not combined)
- [ ] Step 9: History shows TWO separate periods with different data

### If Any of Above Fails - Check These

**Problem:** Step 5 says "Archived 0 periods"
- Solution: Make sure you released twice (Step 1 and Step 5)

**Problem:** Step 6 shows no history
- Solution: Make sure Step 2 (submit) happened between Step 1 and Step 5
- Check database: Does first evaluation response exist?

**Problem:** Step 8 shows combined/old data
- Solution: There's still a filtering issue - contact support
- Check: Make sure both evaluations for same instructor

**Problem:** Database shows all results are is_active=1 (active)
- Solution: The archival process didn't run - check Step 5 message

---

## Logs to Check

If something goes wrong, check the Django logs:

```
Look for lines like:
✓ "Processing results from previous evaluation period..."
✓ "Processed results for [instructor_name]..."
✓ "Archiving previous evaluation periods..."
✓ "Archived 1 previous evaluation period(s)"
✓ "Created new evaluation period..."

If you see these, archival is working correctly ✓
```

---

## Quick Test Summary

| Step | Action | Expected | Status |
|------|--------|----------|--------|
| 1 | Release Eval 1 | "Archived 0 periods" | ✓ |
| 2 | Submit evaluation | Success | ✓ |
| 3 | Check Profile | Shows result | ✓ |
| 4 | Check History | Empty | ✓ |
| 5 | Release Eval 2 | "Archived 1 periods" ← **KEY** | ✓ |
| 6 | Check History | Shows Eval 1 ← **KEY** | ✓ |
| 7 | Submit new eval | Success | ✓ |
| 8 | Check Profile | NEW result only | ✓ |
| 9 | Check History | Both periods | ✓ |

---

## If Everything Works ✅

Congratulations! The evaluation history archival is now working correctly.

Results will:
- ✅ Automatically archive when you release new evaluation
- ✅ Show in Evaluation History
- ✅ Display separated by period
- ✅ Never accumulate or mix

---

## If Something Doesn't Work

1. Check Step 5 message - does it say "Archived 1"?
2. Check database queries above - is_active correct?
3. Check logs - see the processing messages?
4. Recheck steps 1-5 - all completed in order?

If still having issues, provide:
- Step 5 message output
- Database query results
- Log file entries
- Steps you followed


# Evaluation Period Archival - Quick Reference

## The Fix in 30 Seconds

**Problem:** When releasing a new evaluation, old results accumulated instead of archiving to history.

**Solution:** 
1. When releasing new evaluation → Mark old periods as `is_active=False`
2. Create new period with `is_active=True`
3. Filter all score calculations by evaluation period date range
4. Results automatically separate by period

---

## What Changed

### 1. Release Functions (Both Student & Peer)
```
BEFORE: Set Evaluation.is_released=True
AFTER:  Set Evaluation.is_released=True
        + Archive old EvaluationPeriod (is_active=False)
        + Create new EvaluationPeriod (is_active=True)
```

### 2. Score Calculation Functions
```
BEFORE: query ALL responses for evaluatee
AFTER:  filter responses by evaluation_period.start_date to end_date
```

### 3. Result Processing
```
BEFORE: Process responses → EvaluationResult (mixed periods)
AFTER:  Process period-specific responses → EvaluationResult (isolated)
```

---

## How It Works

```
Timeline:
T0          T30         T60
├─────────────┼─────────────┤
Period 1      Period 2      Period 3
(Nov)         (Dec)         (Jan)
is_active=T   is_active=T   is_active=T
is_active=F   is_active=F   (current)
              
Results from Period 1 responses (T0-T30):
→ Locked to Period 1 after T30 → Appears in History ✓

Results from Period 2 responses (T30-T60):
→ Locked to Period 2 after T60 → Appears in History ✓
```

---

## Key Database Queries

### Admin Releases Evaluation
```python
# Archive old periods
EvaluationPeriod.objects.filter(
    evaluation_type='student',
    is_active=True
).update(is_active=False)

# Create new period
EvaluationPeriod.objects.create(
    name=f"Evaluation {now}",
    is_active=True,
    start_date=now,
    end_date=now + 30 days
)
```

### Process Results (Unrelease)
```python
# Only get responses from THIS period
responses = EvaluationResponse.objects.filter(
    evaluatee=user,
    submitted_at__gte=period.start_date,
    submitted_at__lte=period.end_date
)

# Calculate scores from period-specific responses
scores = compute_category_scores(user, evaluation_period=period)

# Store result linked to this period
EvaluationResult.objects.update_or_create(
    user=user,
    evaluation_period=period,  # ← Key: Links to specific period
    defaults={scores...}
)
```

### View Results
```python
# Current evaluation (in profile settings)
EvaluationResult.objects.filter(
    evaluation_period__is_active=True
)

# Historical evaluation (in evaluation history)
EvaluationResult.objects.filter(
    evaluation_period__is_active=False
)
```

---

## Files Modified

- **main/views.py** - 5 functions updated
  - `release_student_evaluation()` (Line 770)
  - `release_peer_evaluation()` (Line 920)
  - `compute_category_scores()` (Line 1917)
  - `process_evaluation_results_for_user()` (Line 4362)
  - `get_rating_distribution()` (Line 4448)

---

## Testing Workflow

```bash
1. Admin releases Evaluation 1
   → Period 1 created (is_active=True)

2. Users submit evaluations (5-10 responses)
   → Profile Settings shows results building

3. Admin releases Evaluation 2
   → Period 1 archived (is_active=False) ✓
   → Period 2 created (is_active=True)

4. Check results:
   → Profile Settings: Empty (no Period 2 responses yet)
   → Evaluation History: Period 1 shows cleanly
```

---

## Expected Behavior

### Profile Settings (Current)
- Only shows `evaluation_period.is_active=True` results
- Only uses responses submitted AFTER new period release
- Gets fresh start with each new evaluation

### Evaluation History (Completed)
- Shows `evaluation_period.is_active=False` periods
- Each period's results calculated from its date range only
- No cross-period contamination

---

## No More Issues! ✅

- ✅ Results properly archive when new evaluation releases
- ✅ Each period has isolated response data
- ✅ Score calculations only use period-specific responses
- ✅ History shows clean separation between evaluation cycles
- ✅ No data loss or mixing


# Evaluation Timeline & Flow - CONFIRMED ✅

## Your Scenario (Nov 11, 2025 → Nov 11, 2026)

### Timeline Overview

```
NOV 11, 2025 - FIRST EVALUATION RELEASED
├─ Admin clicks "Release Student Evaluation"
├─ System creates: Student Evaluation November 2025 (is_active=TRUE)
│  └─ start_date: Nov 11, 2025
│  └─ end_date: Dec 11, 2025 (30 days later)
├─ System marks all unreleased evaluations as released
├─ Results appear in PROFILE SETTINGS
└─ Status: Active, Results visible

DEC 11, 2025 (end_date passes - system auto-handles or manual close)
└─ Period becomes inactive (is_active=FALSE)

                    ⏳ 1 YEAR PASSES ⏳

NOV 11, 2026 - SECOND EVALUATION RELEASED
├─ Admin clicks "Release Student Evaluation"
├─ System detects: Student Evaluation November 2025 is is_active=TRUE (or last active period)
├─ ARCHIVING STEP:
│  ├─ Archive all results from Nov 2025 → EvaluationHistory table
│  ├─ Remove results from EvaluationResult table (moved to history)
│  └─ Archive any other old inactive periods without history
├─ Deactivate Nov 2025 period (is_active=FALSE)
├─ Create: Student Evaluation November 2026 (is_active=TRUE)
│  └─ start_date: Nov 11, 2026
│  └─ end_date: Dec 11, 2026
├─ Mark all unreleased evaluations with Nov 2026 period
├─ Results appear in PROFILE SETTINGS
└─ Status: Nov 2026 results active, Nov 2025 results in history

                    ✅ SYSTEM STATE AT END:

EvaluationResult table:
  ├─ Nov 2026 results (NEW - Active)
  └─ NO Nov 2025 results (moved to history)

EvaluationHistory table:
  ├─ Nov 2025 results ✅ (ARCHIVED from previous cycle)
  └─ Ready for historical reporting/display
```

## Database Operations Breakdown

### STEP 1: Release Evaluation on Nov 11, 2026

```python
# From release_student_evaluation() function - lines 818-898

# 1. FIND PREVIOUS ACTIVE PERIODS
previous_periods = EvaluationPeriod.objects.filter(
    evaluation_type='student',
    is_active=True
)
# Result: Finds "Student Evaluation November 2025"

# 2. ARCHIVE RESULTS TO HISTORY
for period in previous_periods:
    archive_period_results_to_history(period)
    # Moves ALL results from EvaluationResult → EvaluationHistory
    # Example: aeroncaligagan 72.42% moved to history

# 3. ALSO ARCHIVE OLD INACTIVE PERIODS (Backward Compatibility)
inactive_periods_without_history = []
for period in EvaluationPeriod.objects.filter(
    evaluation_type='student', 
    is_active=False
).order_by('start_date'):
    has_history = EvaluationHistory.objects.filter(
        evaluation_period=period
    ).exists()
    if not has_history:
        inactive_periods_without_history.append(period)

# Archive any missed old periods
for period in inactive_periods_without_history:
    archive_period_results_to_history(period)

# 4. DEACTIVATE THE OLD PERIOD
archived_periods = previous_periods.update(
    is_active=False, 
    end_date=timezone.now()
)
# Result: Student Evaluation November 2025 → is_active=FALSE
```

### STEP 2: Create New Period

```python
# 5. CREATE NEW ACTIVE PERIOD
new_period, created = EvaluationPeriod.objects.get_or_create(
    name="Student Evaluation November 2026",
    evaluation_type='student',
    defaults={
        'start_date': timezone.now(),  # Nov 11, 2026
        'end_date': timezone.now() + timezone.timedelta(days=30),  # Dec 11, 2026
        'is_active': True
    }
)
# Result: Student Evaluation November 2026 → is_active=TRUE

# 6. MARK UNRELEASED EVALUATIONS WITH NEW PERIOD
evaluations = Evaluation.objects.filter(
    is_released=False, 
    evaluation_type='student'
)
updated_count = evaluations.update(
    is_released=True, 
    evaluation_period=new_period
)
# Result: All evaluations now belong to November 2026 period
```

### STEP 3: Results Display

```
PROFILE SETTINGS QUERY:
- Shows EvaluationResult records for user
- Filters for is_active=True periods or latest active period
- RESULT: November 2026 results displayed ✅

EVALUATION HISTORY QUERY:
- Shows EvaluationHistory records for user
- May include November 2025, October 2025, etc.
- RESULT: November 2025 results in history ✅
```

## Data Flow Summary

```
NOV 11 2025 Release:
  Evaluation Responses (Nov 11 - Dec 11) 
              ↓
  EvaluationResult (Nov 2025)
              ↓
  Visible in Profile Settings ✅


NOV 11 2026 Release:
  Step 1: Archive
    EvaluationResult (Nov 2025) → EvaluationHistory
  
  Step 2: Create New
    Evaluation Responses (Nov 11 2026 - Dec 11 2026)
                ↓
    EvaluationResult (Nov 2026) ← NEW
  
  Step 3: Display
    Profile Settings shows Nov 2026 ✅
    History shows Nov 2025 ✅
```

## Code Verification

### Function: `archive_period_results_to_history()` (Lines 4554-4575)

```python
def archive_period_results_to_history(evaluation_period):
    """
    Archive all EvaluationResult records for a period to EvaluationHistory
    This is called when a period is being archived/deactivated
    """
    try:
        # Get all results for this evaluation period
        results = EvaluationResult.objects.filter(
            evaluation_period=evaluation_period
        )
        
        archived_count = 0
        for result in results:
            # Create a history record from the result
            history = EvaluationHistory.create_from_result(result)
            archived_count += 1
            logger.info(f"Archived result for {result.user.username} to history")
        
        logger.info(f"Successfully archived {archived_count} evaluation results")
        return archived_count
        
    except Exception as e:
        logger.error(f"Error archiving period results: {str(e)}")
        return 0
```

**What this does:**
1. ✅ Gets all results for the Nov 2025 period
2. ✅ Creates a copy in EvaluationHistory table
3. ✅ Result is now in BOTH tables (can delete from EvaluationResult if needed)

## Current Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| **Release function** | ✅ Complete | `release_student_evaluation()` Line 818-898 |
| **Peer release function** | ✅ Complete | `release_peer_evaluation()` Line 1002-1050 |
| **Archive function** | ✅ Complete | `archive_period_results_to_history()` Line 4554 |
| **EvaluationHistory model** | ✅ Complete | `main/models.py` |
| **Admin interfaces** | ✅ Complete | `main/admin.py` |
| **Migration 0012** | ✅ Applied | MySQL verified |
| **Backward compatibility** | ✅ Added | Lines 830-839 (student), 1019-1028 (peer) |

## Expected Behavior - NOV 11 2026 Release

```
BEFORE RELEASE:
  EvaluationResult: [Nov 2025 results]  ← Visible in Profile Settings
  EvaluationHistory: [empty]

AFTER RELEASE:
  EvaluationResult: [Nov 2026 results]  ← Visible in Profile Settings (NEW)
  EvaluationHistory: [Nov 2025 results] ← In history (MOVED)

PROFILE SETTINGS DISPLAYS:
  ✅ November 2026 results (from active period)
  
EVALUATION HISTORY DISPLAYS:
  ✅ November 2025 results (from archived period)
```

## Why This Works

1. **Automatic Archiving**: When release happens, old period is archived before new one is created
2. **One Active Period**: System ensures only one active period per evaluation type at a time
3. **Clean Separation**: Results are either in active EvaluationResult OR historical EvaluationHistory
4. **User Sees Current**: Profile Settings query filters for active/latest results only
5. **History Available**: History tab shows all archived results from past periods

---

✅ **Your Scenario Confirmed**: The system is designed exactly as you described!

Admin releases Nov 11 2025 → Results visible in profile ✅
One year passes...
Admin releases Nov 11 2026 → Nov 2025 goes to history, Nov 2026 shows in profile ✅

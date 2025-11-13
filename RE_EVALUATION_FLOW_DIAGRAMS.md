# Re-Evaluation Flow Diagram

## System Architecture Before → After

### BEFORE Implementation
```
┌─────────────────────────────────────────────────────────────┐
│ EvaluationResponse Table                                     │
├─────────────────────────────────────────────────────────────┤
│ Columns:                                                     │
│  - id (PK)                                                   │
│  - evaluator_id (FK)                                         │
│  - evaluatee_id (FK)                                         │
│  - submitted_at                                              │
│  - question1-15 (ratings)                                    │
│  - comments                                                  │
│                                                              │
│ UNIQUE CONSTRAINT: (evaluator_id, evaluatee_id)             │
│ Problem: Once John evaluates Smith, NEVER again!            │
└─────────────────────────────────────────────────────────────┘

Example:
  John evaluates Smith in Nov 2025 → Record 1
  John tries to evaluate Smith in Nov 2026 → BLOCKED! ✗
  John stuck forever
```

### AFTER Implementation
```
┌─────────────────────────────────────────────────────────────┐
│ EvaluationResponse Table (UPDATED)                           │
├─────────────────────────────────────────────────────────────┤
│ Columns:                                                     │
│  - id (PK)                                                   │
│  - evaluator_id (FK)                                         │
│  - evaluatee_id (FK)                                         │
│  ★ evaluation_period_id (FK) ← NEW!                         │
│  - submitted_at                                              │
│  - question1-15 (ratings)                                    │
│  - comments                                                  │
│                                                              │
│ UNIQUE CONSTRAINT: (evaluator_id, evaluatee_id, period_id)  │
│ Benefit: Different periods = different evaluations!         │
└─────────────────────────────────────────────────────────────┘

Example:
  John evaluates Smith in Nov 2025 → Record 1 (period=Nov2025)
  John evaluates Smith in Nov 2026 → Record 2 (period=Nov2026) ✓
  Both allowed! Different periods.
```

## Timeline Flow Diagram

```
NOVEMBER 2025 EVALUATION CYCLE
┌─────────────────────────────────┐
│ Admin: Release Student Evaluation│
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ System Actions:                             │
│ ├─ Create "Student Evaluation Nov 2025"     │
│ ├─ is_active = TRUE                         │
│ ├─ start_date = 2025-11-11                  │
│ └─ end_date = 2025-12-11                    │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ Student John: Fill Evaluation Form          │
│ ├─ Select: Instructor Smith                 │
│ ├─ Answer 15 questions                      │
│ └─ Click: Submit                            │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ System Validation:                          │
│ ├─ Get current period = "Nov 2025"          │
│ ├─ Check: (John, Smith, Nov2025) exists?    │
│ │         → NO ✓ Proceed                    │
│ └─ Create EvaluationResponse                │
│    ├─ evaluator: John                       │
│    ├─ evaluatee: Smith                      │
│    ├─ evaluation_period: Nov 2025 ← KEY     │
│    └─ ratings: 4,5,3,4,5,...                │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ Database State:                      │
│ EvaluationResponse:                  │
│  ├─ Record 1: (John, Smith, Nov25)   │
│  └─ Active: YES                      │
│                                      │
│ Profile Settings:                    │
│  └─ Shows: Smith's Nov 25 results    │
└──────────────────────────────────────┘


                    ▼ TIME PASSES: 1 YEAR ▼


NOVEMBER 2026 EVALUATION CYCLE
┌─────────────────────────────────┐
│ Admin: Release Student Evaluation│
│ (New Annual Cycle)              │
└──────────────┬──────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│ System Archival (Automatic):                 │
│ ├─ Find active periods = "Nov 2025"          │
│ ├─ Copy all Nov 2025 results → EvaluationHistory
│ ├─ Set Nov 2025: is_active = FALSE           │
│ └─ Result: (John, Smith, Nov25) now archived │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│ System Creates New Period:                   │
│ ├─ Create "Student Evaluation Nov 2026"      │
│ ├─ is_active = TRUE ← NOW ACTIVE             │
│ ├─ start_date = 2026-11-11                   │
│ └─ end_date = 2026-12-11                     │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│ Student John: Fill Evaluation Form (AGAIN!)  │
│ ├─ Select: Instructor Smith (SAME PERSON!)  │
│ ├─ Answer 15 questions (fresh feedback)     │
│ └─ Click: Submit                            │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│ System Validation:                           │
│ ├─ Get current period = "Nov 2026"           │
│ ├─ Check: (John, Smith, Nov2026) exists?     │
│ │         → NO ✓ Allowed! (different period)│
│ └─ Create NEW EvaluationResponse             │
│    ├─ evaluator: John                        │
│    ├─ evaluatee: Smith (SAME)                │
│    ├─ evaluation_period: Nov 2026 ← DIFFERENT
│    └─ ratings: 5,4,4,5,4,...  (new ratings) │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ Database State:                             │
│ EvaluationResponse:                         │
│  ├─ Record 1: (John, Smith, Nov25) ✗       │
│  │            (Archived to history)         │
│  └─ Record 2: (John, Smith, Nov26) ✓       │
│              (Active - current)             │
│                                             │
│ EvaluationHistory:                          │
│  └─ Record 1: (John, Smith, Nov25) ✓       │
│              (Permanent archive)            │
│                                             │
│ Profile Settings:                           │
│  └─ Shows: Smith's Nov 26 results (NEW)     │
│                                             │
│ Evaluation History Tab:                     │
│  └─ Shows: Smith's Nov 25 results (OLD)     │
└─────────────────────────────────────────────┘
```

## Database Query Flow

### Scenario 1: User Tries to Submit Evaluation (Same Period)

```
USER SUBMISSION FLOW
│
├─► Get Active Period
│   └─► EvaluationPeriod.objects.get(type='student', is_active=TRUE)
│       Result: "Student Evaluation November 2026"
│
├─► Check Duplicate
│   └─► EvaluationResponse.objects.filter(
│       ├─ evaluator=John
│       ├─ evaluatee=Smith
│       └─ evaluation_period="Nov2026"
│       )
│       Result: 1 record found ✗ EXISTS
│
└─► Return Error
    └─► "You have already evaluated Smith in this evaluation period"
```

### Scenario 2: User Tries to Submit Evaluation (Different Period)

```
USER SUBMISSION FLOW
│
├─► Get Active Period
│   └─► EvaluationPeriod.objects.get(type='student', is_active=TRUE)
│       Result: "Student Evaluation November 2026"
│
├─► Check Duplicate
│   └─► EvaluationResponse.objects.filter(
│       ├─ evaluator=John
│       ├─ evaluatee=Smith
│       └─ evaluation_period="Nov2026"
│       )
│       Result: 0 records ✓ DOESN'T EXIST
│
├─► Create Response
│   └─► EvaluationResponse.objects.create(
│       ├─ evaluator=John
│       ├─ evaluatee=Smith
│       ├─ evaluation_period="Nov2026"  ← KEY LINKING
│       ├─ question1=5
│       ├─ question2=4
│       └─ ...
│       )
│
└─► Return Success
    └─► "Evaluation submitted successfully!"
```

## Data Separation Example

### Across Multiple Years

```
┌──────────────────────────────────────────────────────────────┐
│ STUDENT: John | INSTRUCTOR: Prof Smith                       │
└──────────────────────────────────────────────────────────────┘

YEAR 1 (November 2024):
┌─────────────────────────────────────────────────────────────┐
│ Evaluation Period: Student Evaluation November 2024          │
│ Period Status: ARCHIVED (is_active=FALSE)                    │
│                                                              │
│ EvaluationResponse:                                          │
│  └─ Removed (moved to history)                               │
│                                                              │
│ EvaluationHistory:                                           │
│  └─ ID: 101 | Evaluator: John | Evaluatee: Smith            │
│     Ratings: 3, 3, 2, 3, 3, ...  (Nov 2024)                 │
│     Total %: 65.2%                                           │
│     Archived Date: 2024-11-12                                │
└─────────────────────────────────────────────────────────────┘

YEAR 2 (November 2025):
┌─────────────────────────────────────────────────────────────┐
│ Evaluation Period: Student Evaluation November 2025          │
│ Period Status: ARCHIVED (is_active=FALSE)                    │
│                                                              │
│ EvaluationResponse:                                          │
│  └─ Removed (moved to history)                               │
│                                                              │
│ EvaluationHistory:                                           │
│  └─ ID: 102 | Evaluator: John | Evaluatee: Smith            │
│     Ratings: 4, 5, 3, 4, 5, ...  (Nov 2025)                 │
│     Total %: 72.5%  ← IMPROVED!                              │
│     Archived Date: 2025-11-11                                │
└─────────────────────────────────────────────────────────────┘

YEAR 3 (November 2026 - CURRENT):
┌─────────────────────────────────────────────────────────────┐
│ Evaluation Period: Student Evaluation November 2026          │
│ Period Status: ACTIVE (is_active=TRUE)                       │
│                                                              │
│ EvaluationResponse:                                          │
│  └─ ID: 103 | Evaluator: John | Evaluatee: Smith            │
│     Ratings: 5, 4, 4, 5, 4, ...  (Nov 2026)                 │
│     Total %: 78.3%  ← BEST YET!                              │
│     Submitted: 2026-11-18                                    │
│                                                              │
│ EvaluationHistory:                                           │
│  ├─ ID: 101 (Nov 2024: 65.2%)                               │
│  └─ ID: 102 (Nov 2025: 72.5%)                               │
└─────────────────────────────────────────────────────────────┘

INSIGHTS:
  Nov 2024 → Nov 2025: +7.3% improvement
  Nov 2025 → Nov 2026: +5.8% improvement
  Over 2 years: +13.1% improvement ✓
```

## UI/UX Impact

### Before Implementation
```
Student tries to evaluate same instructor twice:
┌────────────────────────────────────┐
│ Evaluation Form                     │
├────────────────────────────────────┤
│ Select Instructor: [Smith ▼]        │
│ [Submit]                            │
└────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ ✗ ERROR                             │
│ You have already evaluated this     │
│ instructor.                         │
│                                    │
│ (No way forward - blocked forever) │
└────────────────────────────────────┘
```

### After Implementation
```
FIRST PERIOD (Nov 2025):
┌────────────────────────────────────┐
│ Evaluation Form                     │
├────────────────────────────────────┤
│ Period: Nov 2025 (Active)           │
│ Select Instructor: [Smith ▼]        │
│ [Submit]                            │
└────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ ✓ SUCCESS                           │
│ Evaluation submitted!               │
│ You can view it in Profile Settings │
└────────────────────────────────────┘

SECOND PERIOD (Nov 2026 - NEW):
┌────────────────────────────────────┐
│ Evaluation Form                     │
├────────────────────────────────────┤
│ Period: Nov 2026 (NEW - Active)     │
│ Select Instructor: [Smith ▼]        │
│ [Submit]                            │
└────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ ✓ SUCCESS                           │
│ Evaluation submitted!               │
│ You can update your feedback yearly │
│ Old evaluations in History tab      │
└────────────────────────────────────┘
```

## Code Change Summary

### Change Type 1: Duplicate Check

```python
# BEFORE (Line 1655)
if EvaluationResponse.objects.filter(
    evaluator=request.user, 
    evaluatee=evaluatee
).exists():
    # BLOCKS ALL FUTURE ATTEMPTS

# AFTER (Line 1656-1666)
current_period = EvaluationPeriod.objects.get(
    evaluation_type='student',
    is_active=True
)
if EvaluationResponse.objects.filter(
    evaluator=request.user, 
    evaluatee=evaluatee,
    evaluation_period=current_period  # ← PERIOD-SPECIFIC
).exists():
    # BLOCKS ONLY IN SAME PERIOD
```

### Change Type 2: Response Creation

```python
# BEFORE (Line 1711)
response = EvaluationResponse(
    evaluator=request.user,
    evaluatee=evaluatee,
    student_number=student_number,
    student_section=student_section,
    comments=comments,
    **questions
)

# AFTER (Line 1727)
response = EvaluationResponse(
    evaluator=request.user,
    evaluatee=evaluatee,
    evaluation_period=current_period,  # ← NEW FIELD
    student_number=student_number,
    student_section=student_section,
    comments=comments,
    **questions
)
```

## Success Flow Chart

```
YEAR 1 EVALUATION (Nov 2025)
│
├─ Student submits evaluation → ALLOWED ✓
├─ Result stored with period link
├─ Visible in profile settings
└─ User cannot re-submit in same period ✓

                    ▼ 1 YEAR ▼

NEW EVALUATION RELEASE (Nov 2026)
│
├─ Admin releases new period
├─ Old results auto-archived ✓
├─ New period activated ✓
│
└─ Student submits evaluation (AGAIN) → ALLOWED ✓ (DIFFERENT PERIOD)
   ├─ NEW record created
   ├─ Linked to Nov 2026 period
   ├─ Visible in profile settings
   ├─ Old evaluation visible in history
   └─ Independent scores calculated

RESULT:
  ✓ User can evaluate same person yearly
  ✓ Results properly separated
  ✓ History preserved
  ✓ No data loss
  ✓ Fresh feedback each period
```

---

**Implementation Status: ✅ COMPLETE**

All diagrams represent actual system behavior after migration 0013 is applied.

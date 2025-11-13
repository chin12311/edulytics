# Where the 40% Results Are Stored

## The 40% Result Location

**Database:** `db.sqlite3`
**Table:** `main_evaluationresult`
**Record:** ID 2

**Details:**
- User: `jadepuno` (your instructor)
- Period: "Student Evaluation November 2025"
- Status: Archived (is_active=0)
- Score: 40.0%
- Responses: 1

---

## Why It's Still Showing

The system stores evaluation results in two ways:

### 1. **EvaluationResult Table** (Permanent Storage)
- Stores calculated/aggregated scores
- Linked to specific evaluation periods
- **This is where the 40% is stored** ✓

### 2. **EvaluationResponse Table** (Raw Data)
- Stores individual evaluation responses
- Has timestamps for each response
- Results are calculated from this

---

## How Results are Created

1. **During Release Evaluation:**
   - System looks at all EvaluationResponse records
   - Calculates aggregate score
   - Stores in EvaluationResult table
   - Links to evaluation period

2. **Once Stored:**
   - EvaluationResult record persists even if you delete responses
   - It's independent data
   - Must be deleted separately

---

## To Delete the 40% Result

You can delete it using Django admin or directly via command:

### Option 1: Via Django Shell
```python
from main.models import EvaluationResult
from django.contrib.auth.models import User

# Get the instructor
user = User.objects.get(username='jadepuno')

# Delete all results for this user
EvaluationResult.objects.filter(user=user).delete()
```

### Option 2: Delete All Old Results
```python
from main.models import EvaluationResult, EvaluationPeriod

# Delete all results from archived periods
archived_periods = EvaluationPeriod.objects.filter(is_active=False)
EvaluationResult.objects.filter(evaluation_period__in=archived_periods).delete()
```

### Option 3: Delete Specific Result
```python
from main.models import EvaluationResult

# Delete by ID
EvaluationResult.objects.filter(id=2).delete()
```

---

## Current Database State

**Evaluation Results:**
- Record 1: aeroncaligagan (jadepuno) - 72.42% - Archived Period
- Record 2: jadepuno - **40.0%** - Archived Period ← THIS ONE
- Record 3: aeroncaligagan (peer) - 72.42% - Archived Period

**All 3 records are from archived periods (is_active=0)**

---

## To Clean Up Everything

Delete all evaluation results:

```python
from main.models import EvaluationResult
count = EvaluationResult.objects.count()
EvaluationResult.objects.all().delete()
print(f"Deleted {count} evaluation results")
```

---

## After Deletion

Once deleted:
- ✅ Profile Settings will show empty
- ✅ Evaluation History will show empty
- ✅ Next time you release evaluation, fresh results will start


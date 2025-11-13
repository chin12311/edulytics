# ✅ FOUND IT! - Where Your 40% Results Are Stored

## The Answer

Your 40% evaluation results are stored in the **database table: `main_evaluationresult`**

It's **NOT** an EvaluationResponse that you deleted - it's the **calculated/stored result**.

---

## Here's Why It's Still There

### What Happens When You Delete Evaluations

When you delete EvaluationResponse records (the individual evaluations):
- ✅ Individual responses deleted
- ❌ EvaluationResult record STILL EXISTS (not deleted)

**Why?** Because EvaluationResult is a **separate table** that stores the calculated aggregate scores.

---

## The Two Separate Tables

### 1. **EvaluationResponse** (Individual Data)
```
Table: main_evaluationresponse
Stores: Each individual evaluation
├─ evaluator: Who filled it out
├─ evaluatee: Who was evaluated
├─ submitted_at: When submitted
├─ question1-15: Individual ratings
└─ Other data...

When you "delete responses" - you delete these
```

### 2. **EvaluationResult** (Aggregate Data)
```
Table: main_evaluationresult  ← 40% IS HERE!
Stores: Calculated aggregate scores
├─ user: The person evaluated
├─ evaluation_period: Which period
├─ total_percentage: The score (40.0%)
├─ total_responses: How many responses (1)
├─ category_a_score: Category breakdown
└─ Other calculations...

When you delete this - the 40% disappears
```

---

## How Results Get Created

```
Step 1: Release Evaluation
    ↓
Step 2: Submit EvaluationResponse
    └─ Stored in: main_evaluationresponse table
    └─ Stores individual ratings
    ↓
Step 3: System Processes Results
    └─ Calculates: 40.0% from responses
    └─ Stores in: main_evaluationresult table
    └─ Creates: Permanent record
    ↓
Step 4: You Delete EvaluationResponse
    └─ Deletes: Individual responses ✓
    └─ Does NOT delete: EvaluationResult ✗
    ↓
Result: 40% still shows because the result record still exists
```

---

## Your Database Right Now

**EvaluationResult Table:**
```
ID | User       | Percentage | Period
---+------------+------------+---------------------------
1  | aeroncaligagan | 72.42%   | Student Evaluation November
2  | jadepuno   | 40.0%      | Student Evaluation November  ← THIS ONE!
3  | aeroncaligagan | 72.42%   | Peer Evaluation November
```

**All 3 are from ARCHIVED periods (is_active=False)**

---

## How to Delete It

### Option 1: Django Admin (Easiest)
```
1. Go to /admin
2. Click "Evaluation results"
3. Check all results
4. Delete
```

### Option 2: Django Shell
```bash
python manage.py shell
```

```python
from main.models import EvaluationResult

# Delete all results
EvaluationResult.objects.all().delete()
print("✅ Deleted!")
```

### Option 3: Direct SQL
```bash
sqlite3 db.sqlite3
DELETE FROM main_evaluationresult;
.quit
```

---

## Why This Design?

**Two separate tables exist for good reason:**

1. **Responses are raw data** - Individual evaluations, never changed
2. **Results are calculated data** - Aggregates, can be recomputed

This separation allows:
- ✅ Keep historical responses as audit trail
- ✅ Recalculate results if needed
- ✅ Store results efficiently (1 record per person per period)
- ✅ Keep raw data separate from processed data

---

## What to Do Now

### To Clean Up Completely

Delete the EvaluationResult records:

```python
from main.models import EvaluationResult
EvaluationResult.objects.all().delete()
```

Then:
1. ✅ 40% disappears from everywhere
2. ✅ Profile Settings empty
3. ✅ History empty
4. ✅ Fresh start for next evaluation

---

## The Flow Going Forward

```
Release Evaluation 1
    ↓
Submit responses
    ├─ Stored in: main_evaluationresponse
    └─ Visible in: Profile Settings
    ↓
Release Evaluation 2
    ├─ Process results from Evaluation 1
    │  └─ Stores in: main_evaluationresult
    ├─ Archive Evaluation 1
    └─ Results now in history
    ↓
Submit new responses for Evaluation 2
    ├─ Stored in: main_evaluationresponse (new)
    └─ Visible in: Profile Settings (fresh)
```

---

## Summary

| Item | Stores | Deletes With | Status |
|------|--------|--------------|--------|
| **EvaluationResponse** | Individual responses | When you delete responses | ✓ You already did this |
| **EvaluationResult** | Calculated scores (40%) | When you delete results | ✗ Still exists! |

**To make 40% disappear: Delete the EvaluationResult record!**


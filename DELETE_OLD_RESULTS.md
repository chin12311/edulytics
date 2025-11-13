# 🗑️ HOW TO DELETE THE OLD 40% RESULTS

## Quick Answer

The 40% results are stored in the database in the `EvaluationResult` table.

**Location:**
- User: `jadepuno`
- Score: 40.0%
- Period: Student Evaluation November 2025 (archived)
- Table: `main_evaluationresult`

---

## Delete via Django Admin (Easiest)

1. Go to `/admin`
2. Click "Evaluation results"
3. Find and select all results
4. Delete action → Delete

---

## Delete via Django Shell (Recommended)

Run these commands:

```bash
python manage.py shell
```

Then copy/paste this code:

```python
from main.models import EvaluationResult

# Show what's there
print("Before:", EvaluationResult.objects.count())

# Delete ALL results
EvaluationResult.objects.all().delete()

# Confirm deleted
print("After:", EvaluationResult.objects.count())

# Exit
exit()
```

---

## Delete via SQL (Direct Database)

If you want to delete directly from database:

```bash
sqlite3 db.sqlite3
```

Then run:

```sql
DELETE FROM main_evaluationresult;
SELECT COUNT(*) FROM main_evaluationresult;  -- Should show 0
.quit
```

---

## Delete Specific Results Only

If you only want to delete the 40% result:

```python
from main.models import EvaluationResult
from django.contrib.auth.models import User

# Delete for specific user
user = User.objects.get(username='jadepuno')
EvaluationResult.objects.filter(user=user).delete()
```

---

## After Deletion

✅ Profile Settings: Will be empty
✅ Evaluation History: Will be empty
✅ Next evaluation: Starts fresh with no old data

---

## Current Database Contents

**3 Records exist:**
1. aeroncaligagan - 72.42% - Student Evaluation - Archived
2. jadepuno - **40.0%** ← The one you see - Archived
3. aeroncaligagan - 72.42% - Peer Evaluation - Archived

All are from archived periods, so they won't show unless viewing history.

**But if they're showing in your profile,** you can delete them all.


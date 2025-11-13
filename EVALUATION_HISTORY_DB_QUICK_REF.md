# ⚡ Evaluation History Database - Quick Reference

## TL;DR

✅ **New Table:** `main_evaluationhistory` - Stores archived evaluation results
✅ **Auto-Archiving:** Results automatically copied when new evaluation released
✅ **Admin Interface:** View at `/admin/main/evaluationhistory/`
✅ **Status:** Live and working

---

## Database Tables

| Table | Purpose | When Used |
|-------|---------|-----------|
| `main_evaluationresult` | **Current** evaluation results | View current scores |
| `main_evaluationhistory` | **Archived** evaluation results | View past scores |

---

## The Flow

```
Release Evaluation
    ↓
Process Results (stored in EvaluationResult)
    ↓
Archive Previous Period
    ├─ Copy to EvaluationHistory ✨ NEW!
    ├─ Deactivate old period
    └─ Create new active period
    ↓
Users see current results in EvaluationResult
Users see past results in EvaluationHistory
```

---

## Quick SQL Queries

### View All History
```sql
SELECT * FROM main_evaluationhistory ORDER BY archived_at DESC;
```

### History by User
```sql
SELECT * FROM main_evaluationhistory 
WHERE user_id = 15
ORDER BY archived_at DESC;
```

### History by Period Type
```sql
SELECT * FROM main_evaluationhistory 
WHERE evaluation_type = 'student'
ORDER BY period_start_date DESC;
```

### Count Records
```sql
SELECT COUNT(*) FROM main_evaluationhistory;
```

---

## Quick Python Queries

### Get User History
```python
from main.models import EvaluationHistory
history = EvaluationHistory.objects.filter(
    user__username='aeroncaligagan'
).order_by('-archived_at')
```

### Get Recent Archived
```python
recent = EvaluationHistory.objects.order_by('-archived_at')[:10]
for record in recent:
    print(f"{record.user.username}: {record.total_percentage}%")
```

### Get Period Average
```python
from django.db.models import Avg
avg = EvaluationHistory.objects.filter(
    evaluation_period__name="Student Evaluation November 2025"
).aggregate(avg=Avg('total_percentage'))
```

---

## Admin Access

**Current Results:** 
- http://localhost:8000/admin/main/evaluationresult/

**Archived Results:** 
- http://localhost:8000/admin/main/evaluationhistory/

**Features:**
- View ✓
- Filter by type, period, date
- Search by user name/email
- Export data
- View detailed breakdowns

---

## Model Fields

### EvaluationHistory Fields

```
id                          BigInt (PK)
user_id                     Int (FK to User)
evaluation_period_id        BigInt (FK to Period)
evaluation_type             VARCHAR 'student'/'peer'
section_id                  BigInt (FK to Section, nullable)

category_a_score            Double
category_b_score            Double
category_c_score            Double
category_d_score            Double

total_percentage            Double  (0-100)
average_rating              Double  (0-5)

total_responses             Int
total_questions             Int

poor_count                  Int
unsatisfactory_count        Int
satisfactory_count          Int
very_satisfactory_count     Int
outstanding_count           Int

archived_at                 DateTime (auto)
period_start_date           DateTime (snapshot)
period_end_date             DateTime (snapshot)
```

---

## Key Features

✅ **Auto-Archiving** - Happens on release
✅ **Immutable** - Cannot edit records
✅ **Indexed** - Fast queries
✅ **Timestamped** - Know when archived
✅ **Complete** - All scores captured
✅ **Admin UI** - Easy to browse

---

## Files Modified

1. **main/models.py**
   - Added `EvaluationHistory` model
   - Added `create_from_result()` classmethod

2. **main/views.py**
   - Imported `EvaluationHistory`
   - Added `archive_period_results_to_history()` function
   - Integrated into student evaluation release
   - Integrated into peer evaluation release

3. **main/admin.py**
   - Registered `EvaluationResult` for admin
   - Registered `EvaluationHistory` for admin

4. **main/migrations/0012_***
   - Created new table
   - Created indexes

---

## Use Cases

### 📊 Show Historical Dashboard
```python
history = EvaluationHistory.objects.filter(user=staff_member)
return render(request, 'history.html', {'history': history})
```

### 📈 Track Performance Over Time
```python
history = EvaluationHistory.objects.filter(
    user=staff_member,
    evaluation_type='student'
).order_by('archived_at')

percentages = [h.total_percentage for h in history]
# [65.0, 70.5, 72.42, 75.0]  ← improvement!
```

### 📋 Generate Report
```python
history = EvaluationHistory.objects.filter(
    evaluation_period=period
)
total_avg = history.aggregate(Avg('total_percentage'))
```

### 🔍 Audit Trail
```python
# See exactly when this result was archived
record = EvaluationHistory.objects.get(id=1)
print(f"Archived: {record.archived_at}")
print(f"Period: {record.period_start_date} to {record.period_end_date}")
```

---

## Migration Status

✅ **Migration Created:** `0012_alter_userprofile_options_evaluationhistory.py`
✅ **Migration Applied:** OK
✅ **Table Exists:** YES
✅ **Ready to Use:** YES

---

## Next: Frontend Integration

Now you can:
1. Display history on staff profile page
2. Show performance trends
3. Compare periods side-by-side
4. Generate historical reports
5. Track improvement over time

Example:
```html
<!-- Show user's evaluation history -->
{% for record in history %}
  <div class="history-card">
    <h3>{{ record.evaluation_period.name }}</h3>
    <p>Score: {{ record.total_percentage }}%</p>
    <p>Responses: {{ record.total_responses }}</p>
    <p>Archived: {{ record.archived_at|date:"F d, Y" }}</p>
  </div>
{% endfor %}
```

---

## Troubleshooting

**Q: I don't see EvaluationHistory in admin**
- A: Make sure you're logged in as superuser
- A: Check that migration 0012 was applied

**Q: History table is empty**
- A: Archive history only created when releasing new evaluation
- A: Release an evaluation to populate it

**Q: Can I delete history?**
- A: Only superusers can delete
- A: Strongly NOT recommended - keeps audit trail

---

✨ **You're all set! Your evaluation history database is live.**

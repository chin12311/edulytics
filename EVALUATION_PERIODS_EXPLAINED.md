# How Evaluation Periods Are Created

## Overview
Evaluation periods are **automatically created** when evaluations are **released** through specific admin buttons in the application.

## Where They're Created

### 1. **Via Django Admin Interface** (Easiest for Users)
The 5 evaluation periods you see were likely created through admin buttons like:
- **"Release Student Evaluation"** button
- **"Release Peer Evaluation"** button

When clicked, the code:
1. Finds old evaluation periods → marks them as `is_active=False`
2. Creates a NEW period with:
   - `name`: e.g., "Student Evaluation November 2025"
   - `evaluation_type`: 'student' or 'peer'
   - `start_date`: Today
   - `end_date`: 30 days from now
   - `is_active`: True

### 2. **Code Location**
The evaluation period creation happens in `main/views.py` in functions like:
- `release_student_evaluation()` - line 1232
- `release_peer_evaluation()` - line 1129

Example code:
```python
evaluation_period = EvaluationPeriod.objects.create(
    name=f"Peer Evaluation {timezone.now().strftime('%B %Y')}",
    evaluation_type='peer',
    start_date=timezone.now(),
    end_date=timezone.now() + timezone.timedelta(days=30),
    is_active=True
)
```

### 3. **Your Current Periods**
Based on the data, someone created these periods by clicking "Release" multiple times:
- October 2025 (student) - Created in Oct, now inactive
- October 2025 (peer) - Created in Oct, now inactive  
- November 2025 (student) - Created in Nov, **now ACTIVE (I enabled it)**
- November 2025 (peer) - Created in Nov, already active
- January 2026 (student) - Created in Jan?, not active yet

## How to View/Manage Them

### Option 1: Django Admin (Best Way)
Since `EvaluationPeriod` is NOT registered in admin.py, you need to either:

**Add it to admin.py:**
```python
from django.contrib import admin
from .models import EvaluationPeriod

@admin.register(EvaluationPeriod)
class EvaluationPeriodAdmin(admin.ModelAdmin):
    list_display = ('name', 'evaluation_type', 'is_active', 'start_date', 'end_date')
    list_filter = ('evaluation_type', 'is_active')
    list_editable = ('is_active',)  # Can toggle on/off directly

admin.site.register(EvaluationPeriod, EvaluationPeriodAdmin)
```

Then go to: http://localhost:8000/admin/main/evaluationperiod/

### Option 2: Django Shell
```bash
python manage.py shell
from main.models import EvaluationPeriod
EvaluationPeriod.objects.all().values('name', 'evaluation_type', 'is_active', 'start_date', 'end_date')
```

### Option 3: Database Query
```sql
SELECT name, evaluation_type, is_active, start_date, end_date 
FROM main_evaluationperiod 
ORDER BY start_date DESC;
```

## Summary
- **Created by**: Clicking "Release Evaluation" button in admin or views
- **Automatic naming**: Uses current date → "November 2025"
- **30-day duration**: Lasts for 30 days by default
- **Only one active per type**: Student + Peer (only ONE of each type can be active)
- **Auto-archive**: When you create a new one, the old one becomes `is_active=False`

---

**To manage them better, I recommend adding EvaluationPeriod to Django Admin!**

# Architecture Issue: Dual View Problem

## Issue Discovered

The system has **TWO separate views** for accessing the peer evaluation form:

1. **`EvaluationView` (Class-Based)** - Lines 685-815
   - Handles: GET request to `/evaluation/`
   - Purpose: Show overview page saying "evaluation is available"
   - Also handles: POST submission (old code, may not be used)

2. **`evaluation_form_staffs` (Function-Based)** - Lines 2200-2283
   - Handles: GET request to `/evaluationform_staffs/`
   - Purpose: Display actual evaluation form with questions

## Why This Causes Problems

### Scenario: Asynchronous Release

```
Admin Release Process:
┌─ release_student_evaluation() 
│  └─ Creates Period(type='student', active=True)
│  └─ Creates Evaluation(type='student', released=True, period=...)
│
└─ release_peer_evaluation()
   └─ Creates Period(type='peer', active=True)
   └─ Creates Evaluation(type='peer', released=True, period=...)
   └─ Verification check
```

### User Navigation

```
Dean visits /evaluation/:
│
├─ EvaluationView.get()
│  ├─ Searches for ANY released evaluation (original bug)
│  ├─ Finds: Student evaluation exists
│  └─ Shows: "Start Evaluation" button (not specific to type!)
│
└─ Dean clicks button
   ├─ Redirects to /evaluationform_staffs/
   │
   ├─ evaluation_form_staffs() expects:
   │  ├─ Peer evaluation exists
   │  ├─ Peer evaluation released=True
   │  └─ Peer evaluation.evaluation_period_id matches active period
   │
   ├─ But finds:
   │  ├─ Only Student evaluation exists (or)
   │  ├─ Peer eval has evaluation_period=NULL (or)
   │  └─ Peer eval linked to OLD archived period
   │
   └─ BOOM! Error: "No active peer evaluation period found"
```

## Why `evaluation_form_staffs` Must Verify Period Linkage

The form function cannot assume:
- That an evaluation record exists just because `/evaluation/` showed the button
- That if an evaluation exists, it's linked to the current active period
- That the period is still active (hasn't been archived)

### Example of Linkage Problem:

```
Time T1: Admin creates peer eval in Period A (active=True)
         Period A: ID=1, is_active=True
         Evaluation: ID=50, period_id=1, released=True

Time T2: Admin clicks Release again
         Old Period A: is_active=False (archived)
         New Period B: ID=2, is_active=True
         New Evaluation: ID=51, period_id=2, released=True
         
         BUT: Old Evaluation still exists!
         ID=50, period_id=1 (now archived), released=True

Time T3: Dean visits /evaluation/ → See form available ✅
Time T4: Dean clicks start
         evaluation_form_staffs() queries:
         - Active period: Gets Period B (ID=2) ✅
         - Evaluation linked to B: Should find ID=51
         - BUT if query is wrong, might find ID=50 instead
           (old record linked to archived period)
```

## Solution Applied

### 1. Type-Specific Checking in EvaluationView
Ensures button only shows when CORRECT type is available:

```python
if user_profile.role == Role.STUDENT:
    eval_type = 'student'
else:
    eval_type = 'peer'

evaluation = Evaluation.objects.filter(
    is_released=True,
    evaluation_type=eval_type  # ← CRITICAL
).order_by('-created_at').first()
```

### 2. Period-Linked Verification in evaluation_form_staffs
Ensures evaluation is linked to current active period:

```python
# Step 1: Get ACTIVE period (fail fast if missing)
active_period = EvaluationPeriod.objects.get(
    type='peer',
    is_active=True
)

# Step 2: Get evaluation linked to THAT period
evaluation = Evaluation.objects.filter(
    is_released=True,
    evaluation_type='peer',
    evaluation_period=active_period  # ← CRITICAL linkage check
).first()
```

## Why Both Views Can't Just Use EvaluationFormView

Looking at `EvaluationFormView` (the student form):

```python
# Student form (in EvaluationFormView):
evaluation = Evaluation.objects.filter(
    is_released=True,
    evaluation_type='student'
).order_by('-created_at').first()
```

It also **doesn't verify period linkage** in the GET handler!

But why doesn't it fail?

1. Students get a fresh eval each term (old periods archivesd)
2. There's usually only ONE active student period
3. If linkage breaks, students would fail too (same bug)

**Both need fixing** - but student form hasn't caused issues yet because:
- Only one active student period typically exists
- No re-release during evaluation period
- Fewer edge cases trigger the bug

## Proper Architecture Would Be:

```python
# Single unified form view that handles both types
class EvaluationFormView(TemplateView):
    def get_context(self, type='student'):
        # Get active period for type
        period = EvaluationPeriod.objects.get(type=type, is_active=True)
        
        # Get evaluation linked to period
        evaluation = Evaluation.objects.filter(
            type=type,
            released=True,
            period=period
        ).first()
        
        # Get template based on type
        template = 'form_student.html' if type=='student' else 'form_peer.html'
        
        return context, template
```

Instead of having:
- EvaluationView (for showing availability)
- EvaluationFormView (for student form)
- evaluation_form_staffs (for peer form)

## Current Status

**Temporary Fix Applied:** ✅
- EvaluationView now checks correct type
- evaluation_form_staffs now verifies period linkage
- Works correctly in current setup

**Long-term Refactoring Recommended:** 🔄
- Consolidate to single unified form view
- Share common validation logic
- Reduce code duplication
- Easier to maintain

But for now, the two-view setup works with the fixes applied.

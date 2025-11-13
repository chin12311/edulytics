# 🔄 Evaluation Flow - Complete Walkthrough

## The Two Different Workflows

### ❌ INCORRECT UNDERSTANDING (What you asked)
"Unrelease → History, Release → Current"

### ✅ CORRECT UNDERSTANDING (What actually happens)
"Release NEW evaluation → Archive old to History, Current becomes new"

---

## Detailed Flow Comparison

## Scenario 1: Release New Evaluation (CORRECT)

```
CYCLE 1: Evaluation 1 (September)
│
├─ Step 1: ADMIN RELEASES Evaluation 1
│  └─ is_released = True
│  └─ Status: Open for responses
│
├─ Step 2: STUDENTS SUBMIT EVALUATIONS
│  └─ Responses stored in: main_evaluationresponse
│
├─ Step 3: STUDENTS CAN SEE RESULTS
│  ├─ Results calculated and stored in: main_evaluationresult
│  ├─ Displayed in: Profile Settings
│  └─ Score: 72.42% (CURRENT)
│
└─ Evaluation 1 STAYS ACTIVE (is_released=True)


CYCLE 2: Release NEW Evaluation (October)
│
├─ Step 1: ADMIN RELEASES NEW Evaluation 2 ← KEY STEP
│  │
│  ├─ System PROCESSES previous period (Sept)
│  │  └─ Get all staff scores: [72.42%, 70.5%, 68.0%]
│  │
│  ├─ System ARCHIVES previous results ✨
│  │  └─ Copy 72.42% → main_evaluationhistory
│  │  └─ Copy 70.5% → main_evaluationhistory
│  │  └─ Copy 68.0% → main_evaluationhistory
│  │
│  ├─ System DEACTIVATES old period
│  │  └─ Evaluation 1: is_released = False (now closed)
│  │
│  └─ System CREATES new period (October)
│     └─ Evaluation 2: is_released = True (newly open)
│
├─ Step 2: STUDENTS SUBMIT NEW EVALUATIONS
│  └─ New responses stored in: main_evaluationresponse
│
├─ Step 3: STUDENTS CAN SEE NEW RESULTS
│  ├─ NEW results calculated: 75.5%
│  ├─ Stored in: main_evaluationresult (NOW EMPTY, NEW SCORES)
│  ├─ Displayed in: Profile Settings (FRESH)
│  └─ OLD results: 72.42% → in main_evaluationhistory (HISTORY)
│
└─ Database state:
   ├─ main_evaluationresult: [75.5%, 71.2%, 69.3%] ← CURRENT
   └─ main_evaluationhistory: [72.42%, 70.5%, 68.0%] ← PREVIOUS


CYCLE 3: Release NEW Evaluation (November)
│
├─ Repeat same process
├─ October's 75.5% moves to history
├─ November's 78.3% shows in Profile Settings
│
└─ Database state:
   ├─ main_evaluationresult: [78.3%, 72.1%, 70.5%] ← CURRENT
   ├─ main_evaluationhistory:
   │  ├─ [72.42%, 70.5%, 68.0%] ← September
   │  └─ [75.5%, 71.2%, 69.3%] ← October (now added)
```

---

## What "UNRELEASE" Does (Different from Release New)

```
DURING AN ACTIVE EVALUATION:

Step 1: Evaluation is RELEASED
├─ is_released = True
├─ Students can see and submit
└─ Results visible in Profile Settings

Step 2: ADMIN CLICKS "UNRELEASE"
├─ is_released = False
├─ Evaluation CLOSES (no more responses)
├─ Results STAY in: main_evaluationresult
├─ Results STILL visible in: Profile Settings
└─ ⚠️ Results do NOT go to history (just closed)

Step 3: System waits for admin to Release NEW evaluation
├─ While unreleased, results stay visible
└─ NOT in history yet
```

---

## The KEY Difference

### ❌ UNRELEASE (Just Closes Current)
```
Unrelease Eval 1
    ↓
Results: 72.42%
├─ Stay in: main_evaluationresult
├─ Still visible in: Profile Settings
└─ NOT moved to history
```

### ✅ RELEASE NEW EVALUATION (Closes Old + Archives + Opens New)
```
Release NEW Eval 2
    ↓
OLD Results (from Eval 1): 72.42%
├─ Copied to: main_evaluationhistory ✓
├─ Removed from: main_evaluationresult
└─ No longer visible in: Profile Settings
    ↓
NEW Results (from Eval 2): [empty, waiting for responses]
├─ Stored in: main_evaluationresult (fresh)
└─ Ready for new evaluation cycle
```

---

## Your Question - Corrected

### What You Asked:
> "When admin ends evaluation → results in profile settings
> When admin releases NEW evaluation → results in profile settings
> When admin unreleases → first result goes to history?"

### What ACTUALLY Happens:
> "When releasing NEW evaluation → old results automatically go to history, NEW results in profile settings"

---

## Timeline Example

```
SEPT 1 - 15
│
├─ Release Evaluation 1
├─ Students evaluate
└─ Result: 72.42% in Profile Settings

OCT 1
│
├─ Release NEW Evaluation 2 ← THIS IS THE KEY ACTION
│  └─ AUTOMATIC ARCHIVING HAPPENS:
│     ├─ 72.42% moves to history
│     ├─ Evaluation 1 closes
│     └─ Evaluation 2 opens (fresh)
│
├─ Students evaluate (new)
└─ Result: 75.5% in Profile Settings (FRESH, replaces old)

NOV 1
│
├─ Release NEW Evaluation 3
│  └─ AUTOMATIC ARCHIVING HAPPENS:
│     ├─ 75.5% moves to history
│     ├─ Evaluation 2 closes
│     └─ Evaluation 3 opens
│
├─ Students evaluate (new)
└─ Result: 78.3% in Profile Settings (FRESH)


PROFILE SETTINGS OVER TIME:
│
├─ Sept-Oct: 72.42% ← shown during Eval 1
├─ Oct-Nov: 75.5% ← shown during Eval 2
└─ Nov-Dec: 78.3% ← shown during Eval 3


HISTORY TABLE OVER TIME:
│
├─ After Oct 1: [72.42%] ← Sept eval archived
├─ After Nov 1: [72.42%, 75.5%] ← Oct eval archived
└─ After Dec 1: [72.42%, 75.5%, 78.3%] ← Nov eval archived
```

---

## What Does NOT Cause Archiving

### ❌ Unreleasing (just closes, doesn't archive)
```
Unrelease Evaluation
    ├─ Closes the evaluation (is_released = False)
    ├─ Results stay in main_evaluationresult
    ├─ Results still visible in Profile Settings
    └─ NO archiving happens ✗
```

### ❌ Deleting Responses (doesn't create history)
```
Delete EvaluationResponse records
    ├─ Removes individual responses
    ├─ Results recalculated (or deleted if no responses left)
    └─ No automatic history entry ✗
```

### ❌ Manually Clearing Results
```
Delete from main_evaluationresult
    ├─ Results disappear
    ├─ Nothing archived (you deleted it!)
    └─ No history entry ✗
```

---

## What DOES Cause Archiving

### ✅ Releasing NEW Evaluation (Only this!)
```
Release NEW Evaluation (when one is already active)
    ├─ System detects active evaluation
    ├─ Processes results from active period
    ├─ ARCHIVES all results to history
    ├─ Deactivates old period
    ├─ Creates new active period
    └─ History automatically populated ✓
```

---

## The Complete State Diagram

```
                    RELEASE EVAL 1
                         │
                         ↓
    ┌─────────────────────────────────────┐
    │ STATE: Evaluation 1 Active          │
    ├─────────────────────────────────────┤
    │ Current Results: [72.42%]           │
    │ Displayed in: Profile Settings      │
    │ In main_evaluationresult: ✓         │
    │ In main_evaluationhistory: ✗        │
    └────────────┬────────────────────────┘
                 │
                 │ RELEASE NEW EVAL 2
                 ↓
    ┌─────────────────────────────────────┐
    │ AUTOMATIC ARCHIVING:                │
    │ 1. Copy 72.42% to history           │
    │ 2. Close Evaluation 1               │
    │ 3. Clear main_evaluationresult      │
    │ 4. Open Evaluation 2 (fresh)        │
    └────────────┬────────────────────────┘
                 │
                 ↓
    ┌─────────────────────────────────────┐
    │ STATE: Evaluation 2 Active          │
    ├─────────────────────────────────────┤
    │ Current Results: [75.5%]            │
    │ Displayed in: Profile Settings      │
    │ In main_evaluationresult: ✓         │
    │ In main_evaluationhistory:          │
    │   └─ [72.42%] from Sept ✓           │
    └────────────┬────────────────────────┘
                 │
                 │ RELEASE NEW EVAL 3
                 ↓
    ┌─────────────────────────────────────┐
    │ AUTOMATIC ARCHIVING:                │
    │ 1. Copy 75.5% to history            │
    │ 2. Close Evaluation 2               │
    │ 3. Clear main_evaluationresult      │
    │ 4. Open Evaluation 3 (fresh)        │
    └────────────┬────────────────────────┘
                 │
                 ↓
    ┌─────────────────────────────────────┐
    │ STATE: Evaluation 3 Active          │
    ├─────────────────────────────────────┤
    │ Current Results: [78.3%]            │
    │ Displayed in: Profile Settings      │
    │ In main_evaluationresult: ✓         │
    │ In main_evaluationhistory:          │
    │   ├─ [72.42%] from Sept ✓           │
    │   └─ [75.5%] from Oct ✓             │
    └─────────────────────────────────────┘
```

---

## Key Points to Remember

| Concept | Details |
|---------|---------|
| **Release NEW Eval** | ARCHIVES old results, opens new evaluation |
| **Unrelease** | Just closes current (doesn't archive) |
| **Delete Responses** | Clears evaluation (doesn't trigger history) |
| **Profile Settings** | Shows CURRENT evaluation results only |
| **Evaluation History** | Shows ALL PAST evaluation results |
| **Automatic** | Archiving happens when releasing NEW eval |
| **One at a Time** | Only ONE evaluation can be active |
| **History Grows** | Adds records every time you release NEW eval |

---

## Real Example

### Month 1: September Evaluation
```
Release Sept Eval
    ↓
Students evaluate Prof. Smith
    ├─ 5 students submit
    └─ Score: 72.42%
    ↓
Visible: Profile Settings shows 72.42%
History: Empty
```

### Month 2: October Evaluation
```
Release OCT Eval (NEW one)
    ├─ AUTOMATICALLY:
    │  ├─ Move 72.42% to history
    │  ├─ Close Sept eval
    │  └─ Open Oct eval
    ↓
Students evaluate Prof. Smith (NEW responses)
    ├─ 6 students submit (fresh batch)
    └─ Score: 75.5%
    ↓
Visible: Profile Settings shows 75.5% (NEW)
History: Contains 72.42% (OLD)
```

### Month 3: November Evaluation
```
Release NOV Eval (NEW one)
    ├─ AUTOMATICALLY:
    │  ├─ Move 75.5% to history
    │  ├─ Close Oct eval
    │  └─ Open Nov eval
    ↓
Students evaluate Prof. Smith (NEW responses)
    ├─ 7 students submit (fresh batch)
    └─ Score: 78.3%
    ↓
Visible: Profile Settings shows 78.3% (LATEST)
History: Contains [72.42%, 75.5%] (ALL PAST)
```

---

## Database State Summary

### After Release Oct Eval:
```
main_evaluationresult (CURRENT):
├─ Prof. Smith: 75.5% ← October (NEW)

main_evaluationhistory (PAST):
├─ Prof. Smith: 72.42% ← September (ARCHIVED)
```

### After Release Nov Eval:
```
main_evaluationresult (CURRENT):
├─ Prof. Smith: 78.3% ← November (NEW)

main_evaluationhistory (PAST):
├─ Prof. Smith: 72.42% ← September (ARCHIVED FIRST)
├─ Prof. Smith: 75.5% ← October (ARCHIVED SECOND)
```

---

## Answer to Your Question

> "When admin releases NEW evaluation, first result goes to history and second shows in Profile Settings?"

✅ **YES, EXACTLY!**

When you **Release a NEW Evaluation**:
1. ✅ OLD results automatically move to history
2. ✅ OLD evaluation closes
3. ✅ NEW evaluation opens
4. ✅ NEW results display in Profile Settings
5. ✅ History grows with each cycle

**This is the NORMAL workflow and it's automatic!**

---

## What UNRELEASE Does (For Reference)

```
Unrelease (During Active Eval)
    ├─ Closes the evaluation
    ├─ Results stay visible
    ├─ NO archiving
    └─ Used only to stop collecting responses
    
When to use Unrelease:
├─ Need to pause evaluation
├─ Want to close early
└─ Will release SAME evaluation again later
```

---

✅ **Your understanding is correct!**
The flow is: **Release NEW → Auto-Archive OLD → Show NEW in Profile**


# Evaluation History UI - Visual Guide

## What You're Building

### Current UI (During Evaluation Period)
```
┌─────────────────────────────────────────────────────────────────┐
│ Evaluation Results | AI Recommendations | Students Comments    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                                                                 │
│     📊 Evaluation Results Temporarily Unavailable             │
│                                                                 │
│     Results will be available after evaluation period ends     │
│                                                                 │
│     Assigned Sections: 3                                       │
│     Total Evaluations: 120                                     │
│     Active Sections: 3                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### New UI (After Period Ends)
```
┌────────────────────────────────────────────────────────────────────────┐
│ Eval Results | AI Recommendations | Students Comments | 📜 History   │◄ NEW TAB
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│ 📜 Evaluation History                                                 │
│ View your past evaluation periods and archived results               │
│                                                                        │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ 📅 👨‍🎓 Student Evaluation                                        │ │
│ │ Oct 1 - Oct 31                                                   │ │
│ │ 87.5% Score • 50 Responses • Archived: Oct 31                   │ │
│ │ ────────────────────────────────────────────────────────────── │◄Click
│ │ This item is clickable!                                          │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ 📅 👨‍🎓 Student Evaluation                                        │ │
│ │ Sep 1 - Sep 30                                                   │ │
│ │ 85.2% Score • 48 Responses • Archived: Sep 30                   │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ 📅 👥 Peer Evaluation                                            │ │
│ │ Aug 15 - Aug 31                                                  │ │
│ │ 84.8% Score • 45 Responses • Archived: Aug 31                   │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### When User Clicks a History Entry
```
┌────────────────────────────────────────────────────────────────────────┐
│ Eval Results | AI Recommendations | Students Comments | 📜 History   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│ 📊 Evaluation Results Overview - Student Evaluation October 2025      │
│                                                                        │
│ ┌────────────────────────────────────────────────────────────────────┐
│ │                    Total Score: 87.5%                             │
│ │            Based on 50 evaluations                                │
│ ├────────────────────────────────────────────────────────────────────┤
│ │ 📚 Subject Mastery        32.5 / 35     92.86%                   │
│ │ 🎯 Classroom Management   24.0 / 25     96.00%                   │
│ │ 📋 Policy Compliance      19.5 / 20     97.50%                   │
│ │ 😊 Personality            19.0 / 20     95.00%                   │
│ ├────────────────────────────────────────────────────────────────────┤
│ │ 50 Total Responses • 4.2 Avg Rating • Oct 31 Archived            │
│ └────────────────────────────────────────────────────────────────────┘
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## UI Components Breakdown

### History Tab Button
**Location:** Top navigation tabs
```html
<button class="tab" onclick="switchTab('history')">📜 Evaluation History</button>
```

**Appearance:**
- Green text when active: #47682c
- Gray when inactive: #7f8c8d
- Underline appears when selected

---

### History Timeline Item

**HTML Structure:**
```html
<div class="history-item" onclick="selectHistoryPeriod(...)">
  <div class="history-title">📅 👨‍🎓 Student Evaluation</div>
  <div class="history-period">Oct 1 - Oct 31</div>
  <div class="history-stats">
    <span>87.5%</span> | <span>50 Responses</span> | <span>Archived: Oct 31</span>
  </div>
</div>
```

**Styling:**
- Left border: 5px green (#47682c)
- Hover: Slides right, darker shadow
- Selected: Light green background

**Stats Shown:**
- 📅 Calendar icon + date range
- 📊 Percentage score
- 👥 Number of responses
- 📦 Archived date

---

### Timeline Loading States

**Loading:**
```
⏳ Loading evaluation history...
(spinner animation)
```

**No History:**
```
📭 No evaluation history available
```

**Loaded:**
```
[History items list]
```

---

### Results Display

**When Clicked, Shows:**

1. **Header**
   ```
   📊 Evaluation Results Overview - Period Name
   ```

2. **Total Score Box**
   ```
   Total Score: 87.5%
   Based on 50 evaluations
   ```

3. **Score Breakdown** (4 categories)
   ```
   📚 Subject Mastery        32.5 / 35     92.86%
   🎯 Classroom Management   24.0 / 25     96.00%
   📋 Policy Compliance      19.5 / 20     97.50%
   😊 Personality            19.0 / 20     95.00%
   ```

4. **Stats Summary**
   ```
   50 Total Responses | 4.2 Avg Rating | Oct 31 Archived
   ```

---

## Color Scheme

| Element | Color | Hex | Usage |
|---------|-------|-----|-------|
| Primary Green | Green | #47682c | Headers, active states, borders |
| Light Green | Light Green | #5a8537 | Hover states |
| Background | Light Green | #f0f8f0 | Selected state background |
| Border | Gray | #e0e0e0 | Item borders |
| Text | Dark Gray | #2c3e50 | Main text |
| Secondary Text | Medium Gray | #666 | Dates, descriptions |
| Stats | Light Gray | #95a5a6 | Archived label |

---

## Icons Used

| Icon | Purpose |
|------|---------|
| 📜 | Evaluation History tab |
| 📅 | History item, date/period |
| 👨‍🎓 | Student evaluation |
| 👥 | Peer evaluation |
| 📊 | Evaluation results |
| 📚 | Subject Mastery category |
| 🎯 | Classroom Management |
| 📋 | Policy Compliance |
| 😊 | Personality |
| 📭 | Empty state (no history) |
| ⏳ | Loading state |

---

## Interactions

### Timeline Item
- **Hover:** Slides right, shadow increases
- **Click:** Becomes highlighted with green background
- **Selected:** Shows green border, light background

### View Results
- **Click Period:** Automatically switches to "Evaluation Results" tab
- **Display:** Shows detailed scores and stats
- **Reference:** Uses same layout as current evaluation results

---

## Responsive Design

### Desktop (>768px)
- Timeline items full width
- Stats on one line
- Two columns for score categories

### Mobile (<768px)
- Timeline items responsive
- Stats wrap to multiple lines
- Single column for scores
- Larger touch targets

---

## Data Flow

```
User clicks "📜 Evaluation History" tab
         ↓
loadHistoryTab() called
         ↓
Fetch /api/evaluation-history/
         ↓
displayEvaluationHistory(data)
         ↓
Render timeline items
         ↓
User clicks a history item
         ↓
selectHistoryPeriod(element, id)
         ↓
Fetch /api/evaluation-history/{id}/
         ↓
loadHistoryResults(data)
         ↓
switchTab('evaluation')
         ↓
Display detailed results
```

---

## Performance Considerations

1. **Lazy Loading:** History loads only when tab clicked
2. **Caching:** Details load on-demand when clicked
3. **Sorting:** Most recent periods first
4. **Filtering:** Only shows user's own history

---

## Accessibility

- ✅ Semantic HTML (button, div with roles)
- ✅ Color not only indicator (text + icons)
- ✅ Keyboard accessible (tab navigation)
- ✅ Loading states clearly indicated
- ✅ Error messages displayed

---

## Summary

Your new Evaluation History feature:
1. ✅ Shows all past evaluation periods in timeline
2. ✅ Displays key metrics at a glance
3. ✅ Clickable to view full details
4. ✅ Uses same styling as profile results
5. ✅ Mobile responsive
6. ✅ Smooth animations and transitions

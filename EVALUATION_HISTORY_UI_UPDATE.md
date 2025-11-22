# Evaluation History UI - Implementation Guide

## Overview

This guide shows how to add an "Evaluation History" tab that displays:
1. **Timeline/List View**: Shows all past evaluation periods with their date ranges
2. **Detail View**: When user clicks a period, displays results in same format as current profile settings

---

## What You'll Add

### New Tab: "Evaluation History"
```
Tabs:
├─ Evaluation Results (current)
├─ AI Recommendations (current)
├─ Students Comments (current)
└─ Evaluation History (NEW!) ← Click to see past evaluations
```

### History Timeline
Shows entries like:
```
┌─────────────────────────────────────────────────┐
│  📅 Student Evaluation October 2025             │
│     Oct 1, 2025 - Oct 31, 2025                 │
│     Archived: Oct 31, 2025 3:45 PM             │
│     Average: 87.5% • 50 responses              │
│     [Click to view details]                    │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  📅 Student Evaluation September 2025           │
│     Sep 1, 2025 - Sep 30, 2025                │
│     Archived: Sep 30, 2025 2:15 PM            │
│     Average: 85.2% • 48 responses              │
│     [Click to view details]                    │
└─────────────────────────────────────────────────┘
```

### When User Clicks a History Entry
- Shows same evaluation results view as profile settings
- Displays section dropdown to view by section
- Shows scores, charts, stats
- Can switch between tabs (evaluation results, recommendations, comments)

---

## Implementation Steps

### Step 1: Add New Tab Button

**Location:** Lines 568-570 in template

**Add:**
```html
<div id="tabs-navigation" class="tabs hidden-content">
    <button class="tab active" onclick="switchTab('evaluation')">Evaluation Results</button>
    <button class="tab" onclick="switchTab('recommendations')">AI Recommendations</button>
    <button class="tab" onclick="switchTab('comments')">Students Comments</button>
    <button class="tab" onclick="switchTab('history')">📜 Evaluation History</button>
</div>
```

### Step 2: Add History Tab Content

**Add new HTML section for history tab:**
```html
<!-- Evaluation History Tab -->
<div id="history-tab" class="tab-content hidden-content">
    <div class="form-card">
        <h4>📜 Evaluation History</h4>
        
        <!-- History Timeline List -->
        <div id="history-list" class="history-timeline">
            <!-- Content will load dynamically via JavaScript -->
        </div>
    </div>
</div>
```

### Step 3: Add CSS Styles for History

```css
/* History Timeline Styles */
.history-timeline {
    display: flex;
    flex-direction: column;
    gap: 15px;
    margin: 20px 0;
}

.history-item {
    background: white;
    border: 2px solid #e0e0e0;
    border-left: 5px solid #47682c;
    border-radius: 8px;
    padding: 20px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.history-item:hover {
    border-left-color: #5a8537;
    box-shadow: 0 4px 12px rgba(71, 104, 44, 0.2);
    transform: translateX(5px);
}

.history-item.selected {
    background: linear-gradient(135deg, #f0f8f0, #e8f5e8);
    border-left-color: #47682c;
    box-shadow: 0 6px 15px rgba(71, 104, 44, 0.3);
}

.history-header {
    display: flex;
    justify-content: space-between;
    align-items: start;
    margin-bottom: 12px;
}

.history-title {
    font-weight: 600;
    font-size: 16px;
    color: #2c3e50;
    display: flex;
    align-items: center;
    gap: 8px;
}

.history-period {
    font-size: 14px;
    color: #666;
    margin: 8px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}

.history-stats {
    display: flex;
    gap: 15px;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #f0f0f0;
}

.history-stat {
    font-size: 13px;
    color: #7f8c8d;
}

.history-stat-value {
    font-weight: 600;
    color: #47682c;
}

.history-badge {
    display: inline-block;
    background: #e8f5e8;
    color: #47682c;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}

.history-empty {
    text-align: center;
    padding: 40px 20px;
    color: #95a5a6;
}

.history-empty i {
    font-size: 48px;
    color: #bdc3c7;
    margin-bottom: 15px;
    display: block;
}

/* Timeline line effect */
.history-timeline::before {
    content: '';
    position: absolute;
    left: 20px;
    top: 0;
    bottom: 0;
    width: 2px;
    background: linear-gradient(to bottom, #47682c, #bdc3c7);
    z-index: -1;
}
```

### Step 4: Add JavaScript Functions

**Add these functions to your script section:**

```javascript
// Load evaluation history
function loadHistoryTab() {
    console.log('Loading evaluation history...');
    const historyList = document.getElementById('history-list');
    
    // Show loading state
    historyList.innerHTML = `
        <div class="text-center" style="padding: 40px;">
            <div class="spinner-border text-success" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3">Loading evaluation history...</p>
        </div>
    `;
    
    // Fetch history data from API
    fetch('/api/evaluation-history/', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('History data received:', data);
        displayEvaluationHistory(data.history_records || []);
    })
    .catch(error => {
        console.error('Error loading history:', error);
        historyList.innerHTML = `
            <div class="history-empty">
                <i class="fas fa-inbox"></i>
                <p>Unable to load evaluation history</p>
            </div>
        `;
    });
}

// Display history records
function displayEvaluationHistory(historyRecords) {
    const historyList = document.getElementById('history-list');
    
    if (!historyRecords || historyRecords.length === 0) {
        historyList.innerHTML = `
            <div class="history-empty">
                <i class="fas fa-inbox"></i>
                <p>No evaluation history available</p>
            </div>
        `;
        return;
    }
    
    let historyHTML = '<div class="history-timeline">';
    
    historyRecords.forEach((record, index) => {
        const startDate = new Date(record.period_start_date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
        
        const endDate = new Date(record.period_end_date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
        
        const archivedDate = new Date(record.archived_at).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        const percentage = parseFloat(record.total_percentage).toFixed(2);
        const evaluationType = record.evaluation_type === 'student' ? '👨‍🎓 Student' : '👥 Peer';
        
        historyHTML += `
            <div class="history-item" onclick="selectHistoryPeriod(this, ${record.id}, '${record.evaluation_type}')">
                <div class="history-header">
                    <div class="history-title">
                        <span>📅</span>
                        <span>${evaluationType} Evaluation</span>
                    </div>
                </div>
                
                <div class="history-period">
                    <i class="fas fa-calendar-alt" style="color: #47682c;"></i>
                    ${startDate} - ${endDate}
                </div>
                
                <div class="history-stats">
                    <div class="history-stat">
                        <i class="fas fa-check-circle" style="color: #47682c;"></i>
                        <span class="history-stat-value">${percentage}%</span>
                        <span>Overall Score</span>
                    </div>
                    <div class="history-stat">
                        <i class="fas fa-users" style="color: #47682c;"></i>
                        <span class="history-stat-value">${record.total_responses || 0}</span>
                        <span>Responses</span>
                    </div>
                    <div class="history-stat">
                        <i class="fas fa-archive" style="color: #47682c;"></i>
                        <span class="history-badge">${archivedDate}</span>
                    </div>
                </div>
            </div>
        `;
    });
    
    historyHTML += '</div>';
    historyList.innerHTML = historyHTML;
}

// Select history period and load its data
function selectHistoryPeriod(element, periodId, evaluationType) {
    console.log(`Loading history period ${periodId} (${evaluationType})`);
    
    // Update UI - mark as selected
    document.querySelectorAll('.history-item').forEach(item => {
        item.classList.remove('selected');
    });
    element.classList.add('selected');
    
    // Load the detailed data for this period
    fetch(`/api/evaluation-history/${periodId}/`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('Period data:', data);
        // Display the results using existing functions
        loadHistoryResults(data);
    })
    .catch(error => {
        console.error('Error loading period data:', error);
    });
}

// Load and display history results
function loadHistoryResults(periodData) {
    // Show evaluation results tab
    switchTab('evaluation');
    
    // Update section name
    const periodName = periodData.evaluation_period_name || 'Archived Period';
    document.getElementById('selected-section-name').textContent = periodName;
    
    // Display the historical scores
    const evaluationContent = document.getElementById('evaluation-content');
    
    const totalPercentage = parseFloat(periodData.total_percentage || 0).toFixed(2);
    const category1Score = parseFloat(periodData.category_a_score || 0).toFixed(2);
    const category2Score = parseFloat(periodData.category_b_score || 0).toFixed(2);
    const category3Score = parseFloat(periodData.category_c_score || 0).toFixed(2);
    const category4Score = parseFloat(periodData.category_d_score || 0).toFixed(2);
    
    const categoryMaxScores = [35, 25, 20, 20];
    const category1Percentage = ((category1Score / categoryMaxScores[0]) * 100).toFixed(2);
    const category2Percentage = ((category2Score / categoryMaxScores[1]) * 100).toFixed(2);
    const category3Percentage = ((category3Score / categoryMaxScores[2]) * 100).toFixed(2);
    const category4Percentage = ((category4Score / categoryMaxScores[3]) * 100).toFixed(2);
    
    const content = `
        <div class="evaluation-summary">
            <div class="max-score-info">
                <h5>Total Score: <span style="color: #47682c; font-size: 28px;">${totalPercentage}%</span></h5>
                <p style="font-size: 13px; color: #666; margin-bottom: 0;">
                    Based on ${periodData.total_responses || 0} evaluations
                </p>
            </div>
            
            <div class="score-breakdown">
                <div class="score-item">
                    <div class="score-category">📚 Subject Mastery</div>
                    <div class="score-value">
                        ${category1Score} <span class="score-max">/ 35</span>
                        <div class="score-percentage">${category1Percentage}%</div>
                    </div>
                </div>
                <div class="score-item">
                    <div class="score-category">🎯 Classroom Management</div>
                    <div class="score-value">
                        ${category2Score} <span class="score-max">/ 25</span>
                        <div class="score-percentage">${category2Percentage}%</div>
                    </div>
                </div>
                <div class="score-item">
                    <div class="score-category">📋 Policy Compliance</div>
                    <div class="score-value">
                        ${category3Score} <span class="score-max">/ 20</span>
                        <div class="score-percentage">${category3Percentage}%</div>
                    </div>
                </div>
                <div class="score-item">
                    <div class="score-category">😊 Personality</div>
                    <div class="score-value">
                        ${category4Score} <span class="score-max">/ 20</span>
                        <div class="score-percentage">${category4Percentage}%</div>
                    </div>
                </div>
            </div>
            
            <div class="stats-summary" style="margin-top: 20px;">
                <div class="stat-item">
                    <span class="stat-value">${periodData.total_responses || 0}</span>
                    <span class="stat-label">Total Responses</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${(periodData.average_rating || 0).toFixed(1)}</span>
                    <span class="stat-label">Average Rating</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${new Date(periodData.archived_at).toLocaleDateString()}</span>
                    <span class="stat-label">Archived Date</span>
                </div>
            </div>
        </div>
    `;
    
    evaluationContent.innerHTML = content;
}
```

### Step 5: Update Tab Switch Function

**Modify your existing `switchTab` function to handle history:**

```javascript
function switchTab(tabName) {
    console.log('Switching to tab:', tabName);
    
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab content
    const tabElement = document.getElementById(tabName + '-tab');
    if (tabElement) {
        tabElement.classList.add('active');
    }
    
    // Add active class to clicked tab
    event.target.classList.add('active');

    // Load content for the selected tab
    if (tabName === 'history') {
        loadHistoryTab();  // ← NEW
    } else {
        loadTabContent(tabName);
    }
}
```

---

## Backend API Endpoints Needed

### 1. GET `/api/evaluation-history/`

**Returns:** List of all evaluation history records for logged-in user

```json
{
  "history_records": [
    {
      "id": 1,
      "evaluation_period_name": "Student Evaluation October 2025",
      "evaluation_type": "student",
      "period_start_date": "2025-10-01T00:00:00Z",
      "period_end_date": "2025-10-31T23:59:59Z",
      "archived_at": "2025-10-31T15:45:00Z",
      "total_percentage": 87.5,
      "total_responses": 50,
      "average_rating": 4.2
    }
  ]
}
```

### 2. GET `/api/evaluation-history/{id}/`

**Returns:** Detailed data for specific history record

```json
{
  "id": 1,
  "evaluation_period_name": "Student Evaluation October 2025",
  "evaluation_type": "student",
  "period_start_date": "2025-10-01T00:00:00Z",
  "period_end_date": "2025-10-31T23:59:59Z",
  "archived_at": "2025-10-31T15:45:00Z",
  "total_percentage": 87.5,
  "category_a_score": 32.5,
  "category_b_score": 24.0,
  "category_c_score": 19.5,
  "category_d_score": 19.0,
  "total_responses": 50,
  "average_rating": 4.2,
  "poor_count": 2,
  "unsatisfactory_count": 5,
  "satisfactory_count": 15,
  "very_satisfactory_count": 18,
  "outstanding_count": 10
}
```

---

## File Changes Summary

### Files to Modify:
1. **dean_profile_settings.html** - Add new tab and tab content
2. **main/views.py** - Create API endpoints
3. **main/urls.py** - Add routes for new API endpoints

### What the User Sees:

**Current State (During Evaluation):**
```
Tabs: [Evaluation Results] [AI Recommendations] [Students Comments]
Content: "Results will be available after period ends"
```

**New State (After Period Ends):**
```
Tabs: [Evaluation Results] [AI Recommendations] [Students Comments] [📜 Evaluation History]
Content: Shows current evaluation results
```

**When User Clicks History Tab:**
```
Tabs: [Evaluation Results] [AI Recommendations] [Students Comments] [📜 Evaluation History]
Content: 
  📅 Student Evaluation October 2025
  Oct 1 - Oct 31 | 87.5% | 50 responses | [Click to view]
  
  📅 Student Evaluation September 2025
  Sep 1 - Sep 30 | 85.2% | 48 responses | [Click to view]
```

**When User Clicks a History Entry:**
```
Same view as current evaluation results, but showing archived data
- Shows all scores, charts, stats
- Same dropdown to select section
- Can switch to recommendations/comments tabs for that period
```

---

## Implementation Priority

1. ✅ Add HTML for history tab (easy)
2. ✅ Add CSS for timeline styling (easy)
3. ✅ Add JavaScript for history tab switching (medium)
4. ⏳ Create backend API endpoints (medium)
5. ⏳ Test and refine UI/UX (medium)

---

## Notes

- History data comes from `EvaluationHistory` model (already exists)
- Same styling/structure as current evaluation results for consistency
- Timeline view makes it easy to browse past periods
- Click to view details for any period
- Can extend to show period-specific sections later

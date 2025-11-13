# 3 Algorithms in Your System - Source Code Analysis

## Algorithm 1: Weighted Category Scoring Algorithm

**Purpose**: Calculate overall evaluation scores by weighting 4 different teaching competency categories

**Source File**: `main/views.py` - Function `compute_category_scores()` (Lines 1790-1880)

**How It Works**:
```python
# Step 1: Collect ratings for 4 categories from evaluation responses
- Category A: Questions 1-4   (Mastery of Subject Matter)     → Weight: 35%
- Category B: Questions 5-8   (Classroom Management)          → Weight: 25%
- Category C: Questions 9-12  (Compliance to Policies)        → Weight: 20%
- Category D: Questions 13-15 (Personality)                   → Weight: 20%

# Step 2: Convert text ratings to numeric scores
rating_to_numeric = {
    'Poor': 1,
    'Unsatisfactory': 2,
    'Satisfactory': 3,
    'Very Satisfactory': 4,
    'Outstanding': 5
}

# Step 3: Calculate weighted average for each category
def scaled_avg(total, count, weight):
    if count == 0:
        return 0
    average_score = total / count          # Average out of 5
    result = (average_score / 5) * weight * 100  # Scale to weight percentage
    return result

# Step 4: Apply weights
a_avg = scaled_avg(category_a_total, count_a, 0.35)  # 35% of total
b_avg = scaled_avg(category_b_total, count_b, 0.25)  # 25% of total
c_avg = scaled_avg(category_c_total, count_c, 0.20)  # 20% of total
d_avg = scaled_avg(category_d_total, count_d, 0.20)  # 20% of total

# Step 5: Calculate final overall percentage
total_percentage = a_avg + b_avg + c_avg + d_avg  # Ranges from 0-100%
```

**Example Calculation**:
- If all responses are "Very Satisfactory" (4 out of 5):
  - Category A: (4/5) × 0.35 × 100 = 28%
  - Category B: (4/5) × 0.25 × 100 = 20%
  - Category C: (4/5) × 0.20 × 100 = 16%
  - Category D: (4/5) × 0.20 × 100 = 16%
  - **Total Score: 80%**

**Where It's Used**:
- `main/views.py` - DeanProfileSettingsView, CoordinatorProfileSettingsView, FacultyProfileSettingsView
- `main/services/evaluation_service.py` - `calculate_overall_score()`
- All profile display pages (dean_profile_settings.html, coordinator_profile_settings.html, faculty_profile_settings.html)

---

## Algorithm 2: Rating Distribution Analysis Algorithm

**Purpose**: Analyze how many evaluations fall into each rating category (Poor, Unsatisfactory, Satisfactory, Very Satisfactory, Outstanding)

**Source File**: `main/views.py` - Multiple profile views (Lines 2000-3500+)

**How It Works**:
```python
# Step 1: Initialize array to count ratings
overall_rating_distribution = [0, 0, 0, 0, 0]
# Index:    0    1            2              3                4
# Rating:  Poor  Unsatisfactory  Satisfactory  Very Satisfactory  Outstanding

# Step 2: For each evaluation response, convert text rating to numeric
# Step 3: Increment the corresponding count
rating_to_numeric_reverse = {
    1: 'Poor',                    # Index 0
    2: 'Unsatisfactory',          # Index 1
    3: 'Satisfactory',            # Index 2
    4: 'Very Satisfactory',       # Index 3
    5: 'Outstanding'              # Index 4
}

# Step 4: For each response, count rating in distribution
for response in responses:
    for question_num in range(1, 16):  # 15 questions
        rating = getattr(response, f'question{question_num}')
        index = rating_to_numeric.get(rating, 1) - 1
        overall_rating_distribution[index] += 1

# Step 5: Generate visual representation
# Final result: [poor_count, unsatisfactory_count, satisfactory_count, 
#               very_satisfactory_count, outstanding_count]
```

**Example Result**:
- overall_rating_distribution = [2, 5, 15, 30, 48]
- Meaning: Out of 100 total ratings:
  - 2 were "Poor"
  - 5 were "Unsatisfactory"
  - 15 were "Satisfactory"
  - 30 were "Very Satisfactory"
  - 48 were "Outstanding"

**Where It's Used**:
- Profile settings pages display rating distribution as bar charts
- Used in faculty_profile_settings.html, dean_profile_settings.html, coordinator_profile_settings.html
- Provides visual feedback about consistency of evaluations

---

## Algorithm 3: Adaptive Recommendation Sorting Algorithm with Performance Ranking

**Purpose**: Automatically generate prioritized recommendations based on which categories have the weakest performance

**Source File**: `main/ai_service.py` - TeachingAIRecommendationService class (Lines 333-450+)

**How It Works**:

### Step 1: Define Categories with Performance Targets
```python
# For faculty/student evaluations:
categories = [
    ("Mastery of Subject Matter", category_a_score, 35),     # 35% max
    ("Classroom Management", category_b_score, 25),          # 25% max
    ("Compliance to Policies", category_c_score, 20),        # 20% max
    ("Personality", category_d_score, 20)                    # 20% max
]

# For peer evaluations:
peer_categories = [
    ("Communication and Collaboration", score, 25),
    ("Responsibility and Professionalism", score, 25),
    ("Leadership and Work Ethic", score, 25),
    ("Overall Professional Impact", score, 25)
]
```

### Step 2: Calculate Performance Percentage for Each Category
```python
performances = []
for i, (name, score, max_score) in enumerate(categories):
    performance = (score / max_score * 100) if max_score > 0 else 0
    performances.append({
        'index': i, 
        'name': name, 
        'score': score, 
        'performance': performance  # 0-100%
    })
```

### Step 3: Sort Categories by Performance (Weakest First)
```python
performances.sort(key=lambda x: x['performance'])
# Result: Categories ordered from lowest performance to highest
```

### Step 4: Filter Weak Categories (Below 80% Threshold)
```python
weak_categories = [p for p in performances if p['performance'] < 80]
# Only include categories performing below 80% of maximum
```

### Step 5: Generate Prioritized Recommendations
```python
recommendations = []

# 1st Recommendation: Strongest weak category (primary focus)
if weak_categories:
    weakest = weak_categories[0]
    recommendations.append({
        'title': f'Improve {weakest["name"]}',
        'description': f'Your {weakest["name"].lower()} score is {weakest["performance"]:.1f}% of maximum...',
        'priority': 'High'  # Highest priority for weakest
    })

# 2nd Recommendation: Second weakest (secondary focus)
if len(weak_categories) > 1:
    second_weakest = weak_categories[1]
    recommendations.append({
        'title': f'Enhance {second_weakest["name"]}',
        'description': f'Focus on improving {second_weakest["name"].lower()}...',
        'priority': 'Medium'
    })

# 3rd Recommendation: General strategy based on overall score
if total_percentage < 75:
    recommendations.append({
        'title': 'Comprehensive Teaching Strategy Review',
        'description': f'With an overall score of {total_percentage}%...',
        'priority': 'High'
    })
else:
    recommendations.append({
        'title': 'Maintain Teaching Excellence',
        'description': f'All categories performing well ({total_percentage}%)...',
        'priority': 'Low'
    })
```

### Step 6: Display Recommendations Sorted by Priority
```javascript
// In template (faculty_profile_settings.html, coordinator_profile_settings.html):
recommendations.sort((a, b) => {
    const priorityOrder = { 'High': 0, 'Medium': 1, 'Low': 2 };
    return priorityOrder[a.priority] - priorityOrder[b.priority];
});
// High priority recommendations appear first
```

**Example Workflow**:
1. Faculty has scores: [28%, 20%, 12%, 18%] (out of [35%, 25%, 20%, 20%])
2. Performance calculation: [80%, 80%, 60%, 90%]
3. Sort by weakest: [60% (Compliance), 80% (Classroom), 80% (Subject), 90% (Personality)]
4. Weak categories (< 80%): [Compliance]
5. Generate recommendations:
   - **High Priority**: "Improve Compliance to Policies" (60%)
   - **Medium Priority**: Consider general improvement strategies
6. Display to user in dashboard

**Where It's Used**:
- `main/ai_service.py` - TeachingAIRecommendationService._get_student_fallback_recommendations()
- `main/ai_service.py` - TeachingAIRecommendationService._get_peer_fallback_recommendations()
- Profile settings pages (faculty_profile_settings.html, dean_profile_settings.html, coordinator_profile_settings.html)
- Generates personalized improvement suggestions for each faculty member

---

## Key Characteristics

### Algorithm Type Analysis:
- **Algorithm 1**: **Deterministic Weighted Averaging** - Uses fixed weights, no randomness
- **Algorithm 2**: **Frequency Distribution Counting** - Tallies occurrence of each rating
- **Algorithm 3**: **Adaptive Ranking & Prioritization** - Uses thresholds (80%) to identify weak areas and prioritize recommendations

### Why NO Fuzzy Logic:
Your system uses **crisp logic** with hard thresholds:
- Performance < 80% → Weak category (needs improvement)
- Performance ≥ 80% → Acceptable performance
- Performance ≥ 90% → Excellent (maintenance mode)

Fuzzy logic would use membership degrees (e.g., 0.6 membership in "weak", 0.4 membership in "acceptable"), but your system uses binary classifications.

---

## Integration Points:

```
Evaluation Response → Algorithm 1: Calculate Scores
                   ↓
              Algorithm 2: Analyze Distribution
                   ↓
              Algorithm 3: Generate Recommendations
                   ↓
            Display in Profile Dashboard
```

All three algorithms work together to provide comprehensive faculty evaluation analysis and personalized improvement recommendations.

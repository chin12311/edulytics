from django.contrib.auth.models import User
from main.models import (EvaluationResponse, EvaluationResult, EvaluationPeriod, 
                         SectionAssignment, UserProfile)
from django.utils import timezone

user = User.objects.get(username='jzapata')

print("=" * 80)
print("PROCESSING EVALUATION RESULTS FOR JZAPATA")
print("=" * 80)

# Get all responses for this user
responses = EvaluationResponse.objects.filter(evaluatee=user)
print(f"\nFound {responses.count()} evaluation responses")

# Group by section and period
sections_dict = {}
for response in responses:
    key = (response.student_section, response.evaluation_period_id)
    if key not in sections_dict:
        sections_dict[key] = []
    sections_dict[key].append(response)

print(f"Grouped into {len(sections_dict)} section-period combinations\n")

# Process each section
created_count = 0
for (section_code, period_id), section_responses in sections_dict.items():
    period = EvaluationPeriod.objects.get(id=period_id)
    print(f"Processing: {section_code} - {period.name}")
    print(f"  Responses: {len(section_responses)}")
    
    # Find the section object
    section_assignment = SectionAssignment.objects.filter(
        user=user,
        section__code=section_code
    ).first()
    
    if not section_assignment:
        print(f"  ⚠️ Section assignment not found for {section_code}")
        continue
    
    section = section_assignment.section
    
    # Calculate scores (19 questions, 4 categories)
    rating_map = {'Poor': 1, 'Unsatisfactory': 2, 'Satisfactory': 3, 'Very Satisfactory': 4, 'Outstanding': 5}
    
    category_a = category_b = category_c = category_d = 0
    for resp in section_responses:
        # Category A: Q1-4 (35%)
        for i in range(1, 5):
            category_a += rating_map.get(getattr(resp, f'question{i}'), 1)
        # Category B: Q5-8 (25%)
        for i in range(5, 9):
            category_b += rating_map.get(getattr(resp, f'question{i}'), 1)
        # Category C: Q9-12 (20%)
        for i in range(9, 13):
            category_c += rating_map.get(getattr(resp, f'question{i}'), 1)
        # Category D: Q13-19 (20%)
        for i in range(13, 20):
            category_d += rating_map.get(getattr(resp, f'question{i}'), 1)
    
    # Calculate averages and weighted percentages
    num_responses = len(section_responses)
    max_score = 5
    
    a_avg = (category_a / (num_responses * 4)) / max_score
    b_avg = (category_b / (num_responses * 4)) / max_score
    c_avg = (category_c / (num_responses * 4)) / max_score
    d_avg = (category_d / (num_responses * 7)) / max_score
    
    a_score = round(a_avg * 35, 2)
    b_score = round(b_avg * 25, 2)
    c_score = round(c_avg * 20, 2)
    d_score = round(d_avg * 20, 2)
    total = round(a_score + b_score + c_score + d_score, 2)
    
    # Create EvaluationResult
    result, created = EvaluationResult.objects.get_or_create(
        user=user,
        section=section,
        evaluation_period=period,
        defaults={
            'category_a_score': a_score,
            'category_b_score': b_score,
            'category_c_score': c_score,
            'category_d_score': d_score,
            'total_percentage': total,
            'total_responses': num_responses,
            'created_at': timezone.now()
        }
    )
    
    if created:
        created_count += 1
        print(f"  ✅ Created result: {total}% ({num_responses} responses)")
        print(f"     A={a_score}%, B={b_score}%, C={c_score}%, D={d_score}%")
    else:
        print(f"  ℹ️ Result already exists")

print(f"\n✅ Created {created_count} new evaluation results")
print("=" * 80)

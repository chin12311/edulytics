"""
Script to add peer evaluation filtering to overall calculations
"""

with open('main/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern 1: Add active_student_period variable after "total_responses = 0"
old_pattern1 = '''        total_responses = 0
        
        for section_assignment in assigned_sections:'''

new_pattern1 = '''        total_responses = 0
        
        # Get active student evaluation period (NOT peer evaluation)
        active_student_period = EvaluationPeriod.objects.filter(
            is_active=True,
            evaluation_type='student'
        ).first()
        
        for section_assignment in assigned_sections:'''

content = content.replace(old_pattern1, new_pattern1)

# Pattern 2: Add filtering to section_responses query
old_pattern2 = '''                section_responses = EvaluationResponse.objects.filter(
                    evaluatee=user,
                    student_section=section_code
                )
                
                if section_responses.exists():'''

new_pattern2 = '''                section_responses = EvaluationResponse.objects.filter(
                    evaluatee=user,
                    student_section=section_code
                )
                
                # Filter by active student period to exclude peer evaluations
                if active_student_period:
                    section_responses = section_responses.filter(evaluation_period=active_student_period)
                
                if section_responses.exists():'''

content = content.replace(old_pattern2, new_pattern2)

# Pattern 3: Add filtering to comments query  
old_pattern3 = '''        # FETCH COMMENTS FROM ALL SECTIONS FOR OVERALL VIEW
        all_comments = EvaluationResponse.objects.filter(
            evaluatee=user,
            comments__isnull=False
        ).exclude(comments='').values_list('comments', flat=True)'''

new_pattern3 = '''        # FETCH COMMENTS FROM ALL SECTIONS FOR OVERALL VIEW
        # IMPORTANT: Only student evaluation comments, NOT peer evaluation comments
        comments_query = EvaluationResponse.objects.filter(
            evaluatee=user,
            comments__isnull=False
        ).exclude(comments='')
        
        # Filter by active student period to exclude peer evaluations
        if active_student_period:
            comments_query = comments_query.filter(evaluation_period=active_student_period)
        
        all_comments = comments_query.values_list('comments', flat=True)'''

content = content.replace(old_pattern3, new_pattern3)

# Write back
with open('main/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Updated overall evaluation calculations to exclude peer evaluations")
print("   - Added active_student_period filtering")
print("   - Updated section_responses queries")
print("   - Updated comments queries")

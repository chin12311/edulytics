"""
Script to update get_section_scores methods in profile views
to read from EvaluationResult table instead of computing from responses
"""

import re

# Read the views.py file
with open('main/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The new method implementation
new_method = '''    def get_section_scores(self, user, assigned_sections):
        """Get scores for each assigned section from EvaluationResult table"""
        from main.models import EvaluationResult
        section_scores = {}
        
        # Get the most recent INACTIVE period (last completed evaluation)
        # Results are stored in EvaluationResult when period ends (unrelease)
        latest_period = EvaluationPeriod.objects.filter(
            evaluation_type='student',
            is_active=False
        ).order_by('-end_date').first()
        
        for section_assignment in assigned_sections:
            section = section_assignment.section
            section_code = section.code
            
            # Try to get pre-computed result from EvaluationResult table
            result = None
            if latest_period:
                try:
                    result = EvaluationResult.objects.get(
                        user=user,
                        section=section,
                        evaluation_period=latest_period
                    )
                except EvaluationResult.DoesNotExist:
                    pass
            
            if result:
                # Use pre-computed results from EvaluationResult table
                a_avg = result.category_a_score
                b_avg = result.category_b_score
                c_avg = result.category_c_score
                d_avg = result.category_d_score
                total_percentage = result.total_percentage
                evaluation_count = result.total_responses
                has_data = True
                
                # Get comments from the responses in this period
                comments_queryset = EvaluationResponse.objects.filter(
                    evaluatee=user,
                    student_section=section_code,
                    submitted_at__gte=latest_period.start_date,
                    submitted_at__lte=latest_period.end_date,
                    comments__isnull=False
                ).exclude(comments='').values_list('comments', flat=True)
            else:
                # No results yet - section has no data
                a_avg = b_avg = c_avg = d_avg = total_percentage = 0
                evaluation_count = 0
                has_data = False
                comments_queryset = []
            
            # Categorize comments using sentiment analysis
            positive_comments = []
            negative_comments = []
            mixed_comments = []
            
            for comment in comments_queryset:
                sentiment = TeachingAIRecommendationService.analyze_comment_sentiment(comment)
                if sentiment == 'positive':
                    positive_comments.append(comment)
                elif sentiment == 'negative':
                    negative_comments.append(comment)
                elif sentiment == 'mixed':
                    mixed_comments.append(comment)
            
            section_scores[section_code] = {
                'category_scores': [
                    round(a_avg, 2),
                    round(b_avg, 2),
                    round(c_avg, 2),
                    round(d_avg, 2)
                ],
                'total_percentage': round(total_percentage, 2),
                'has_data': has_data,
                'evaluation_count': evaluation_count,
                'section_name': section.code,
                'positive_comments': positive_comments,
                'negative_comments': negative_comments,
                'mixed_comments': mixed_comments
            }
        
        return section_scores'''

# Pattern to match the old get_section_scores methods
# We need to match from the method definition to the return statement
pattern = r'(    def get_section_scores\(self, user, assigned_sections\):.*?)(        return section_scores)'

# Function to replace each occurrence
def replace_method(match):
    # Return the new method implementation
    return new_method + '\n'

# Replace all occurrences (should be 3: Dean, Coordinator, Faculty)
new_content, count = re.subn(pattern, replace_method, content, flags=re.DOTALL)

print(f"Found and replaced {count} get_section_scores methods")

if count > 0:
    # Write the updated content back
    with open('main/views.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✅ Successfully updated views.py")
else:
    print("❌ No methods found to replace")

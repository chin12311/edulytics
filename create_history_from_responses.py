"""
Create EvaluationHistory records from existing EvaluationResponse data
This will process all responses and create proper history records with user details and period dates
"""
import os
import sys
import django

sys.path.append('/home/ubuntu/edulytics')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import EvaluationResponse, EvaluationPeriod, EvaluationHistory, User
from django.db.models import Count

def create_history_records():
    """
    Create EvaluationHistory records from evaluation responses
    Groups responses by user and evaluation period
    """
    print("=" * 80)
    print("Creating Evaluation History from Responses")
    print("=" * 80)
    
    # Get all evaluation periods
    periods = EvaluationPeriod.objects.all().order_by('start_date')
    
    print(f"\nFound {periods.count()} evaluation periods:")
    for period in periods:
        print(f"  - {period.name} ({period.evaluation_type})")
        print(f"    Start: {period.start_date}")
        print(f"    End: {period.end_date}")
        print(f"    Active: {period.is_active}")
    
    # Get all responses grouped by evaluatee and period
    responses_by_user_period = {}
    all_responses = EvaluationResponse.objects.select_related(
        'evaluatee', 'evaluation_period'
    ).all()
    
    print(f"\nProcessing {all_responses.count()} evaluation responses...")
    
    for response in all_responses:
        if not response.evaluation_period:
            print(f"  ⚠️  Skipping response {response.id} - no evaluation period")
            continue
            
        key = (response.evaluatee.id, response.evaluation_period.id)
        if key not in responses_by_user_period:
            responses_by_user_period[key] = []
        responses_by_user_period[key].append(response)
    
    print(f"\nGrouped into {len(responses_by_user_period)} user-period combinations")
    
    # Process each user-period combination
    created_count = 0
    skipped_count = 0
    
    for (user_id, period_id), responses in responses_by_user_period.items():
        user = User.objects.get(id=user_id)
        period = EvaluationPeriod.objects.get(id=period_id)
        
        print(f"\n--- Processing: {user.username} - {period.name} ---")
        print(f"    Responses: {len(responses)}")
        
        # Check if history already exists
        existing = EvaluationHistory.objects.filter(
            user=user,
            evaluation_period=period,
            section__isnull=True  # Overall history (not section-specific)
        ).first()
        
        if existing:
            print(f"    ✓ History already exists (ID: {existing.id})")
            skipped_count += 1
            continue
        
        # Calculate scores based on evaluation type
        if period.evaluation_type == 'peer':
            # Peer evaluation - simple average
            rating_to_numeric = {
                'Poor': 1,
                'Unsatisfactory': 2,
                'Satisfactory': 3,
                'Very Satisfactory': 4,
                'Outstanding': 5
            }
            
            total_score = 0
            total_questions = 0
            rating_counts = [0, 0, 0, 0, 0]  # Poor, Unsat, Sat, Very Sat, Outstanding
            
            for response in responses:
                for i in range(1, 16):  # 15 questions for peer
                    question_key = f'question{i}'
                    rating_text = getattr(response, question_key, 'Poor')
                    score = rating_to_numeric.get(rating_text, 1)
                    total_score += score
                    total_questions += 1
                    rating_counts[score - 1] += 1
            
            average_rating = total_score / total_questions if total_questions > 0 else 0
            total_percentage = (average_rating / 5) * 100
            
            # Create history record
            history = EvaluationHistory.objects.create(
                user=user,
                evaluation_period=period,
                evaluation_type='peer',
                section=None,
                category_a_score=0,
                category_b_score=0,
                category_c_score=0,
                category_d_score=0,
                total_percentage=round(total_percentage, 2),
                average_rating=round(average_rating, 2),
                total_responses=len(responses),
                total_questions=15,
                poor_count=rating_counts[0],
                unsatisfactory_count=rating_counts[1],
                satisfactory_count=rating_counts[2],
                very_satisfactory_count=rating_counts[3],
                outstanding_count=rating_counts[4],
                period_start_date=period.start_date,
                period_end_date=period.end_date
            )
            
            print(f"    ✅ Created PEER history: {total_percentage:.2f}%")
            
        else:  # Student evaluation
            # Student evaluation - 4 categories with weights
            rating_to_numeric = {
                'Poor': 1,
                'Unsatisfactory': 2,
                'Satisfactory': 3,
                'Very Satisfactory': 4,
                'Outstanding': 5
            }
            
            total_a = total_b = total_c = total_d = 0
            count_a = count_b = count_c = count_d = 0
            rating_counts = [0, 0, 0, 0, 0]
            
            for response in responses:
                # Category A: Questions 1-4 (35%)
                for i in range(1, 5):
                    rating_text = getattr(response, f'question{i}', 'Poor')
                    score = rating_to_numeric.get(rating_text, 1)
                    total_a += score
                    count_a += 1
                    rating_counts[score - 1] += 1
                
                # Category B: Questions 5-8 (25%)
                for i in range(5, 9):
                    rating_text = getattr(response, f'question{i}', 'Poor')
                    score = rating_to_numeric.get(rating_text, 1)
                    total_b += score
                    count_b += 1
                    rating_counts[score - 1] += 1
                
                # Category C: Questions 9-12 (20%)
                for i in range(9, 13):
                    rating_text = getattr(response, f'question{i}', 'Poor')
                    score = rating_to_numeric.get(rating_text, 1)
                    total_c += score
                    count_c += 1
                    rating_counts[score - 1] += 1
                
                # Category D: Questions 13-15 (20%)
                for i in range(13, 16):
                    rating_text = getattr(response, f'question{i}', 'Poor')
                    score = rating_to_numeric.get(rating_text, 1)
                    total_d += score
                    count_d += 1
                    rating_counts[score - 1] += 1
            
            # Calculate weighted scores
            def scaled_avg(total, count, weight):
                if count == 0:
                    return 0
                avg = total / count
                return (avg / 5) * weight * 100
            
            a_score = scaled_avg(total_a, count_a, 0.35)
            b_score = scaled_avg(total_b, count_b, 0.25)
            c_score = scaled_avg(total_c, count_c, 0.20)
            d_score = scaled_avg(total_d, count_d, 0.20)
            total_percentage = a_score + b_score + c_score + d_score
            
            total_ratings = total_a + total_b + total_c + total_d
            total_count = count_a + count_b + count_c + count_d
            average_rating = (total_ratings / total_count) if total_count > 0 else 0
            
            # Create history record
            history = EvaluationHistory.objects.create(
                user=user,
                evaluation_period=period,
                evaluation_type='student',
                section=None,
                category_a_score=round(a_score, 2),
                category_b_score=round(b_score, 2),
                category_c_score=round(c_score, 2),
                category_d_score=round(d_score, 2),
                total_percentage=round(total_percentage, 2),
                average_rating=round(average_rating, 2),
                total_responses=len(responses),
                total_questions=19,
                poor_count=rating_counts[0],
                unsatisfactory_count=rating_counts[1],
                satisfactory_count=rating_counts[2],
                very_satisfactory_count=rating_counts[3],
                outstanding_count=rating_counts[4],
                period_start_date=period.start_date,
                period_end_date=period.end_date
            )
            
            print(f"    ✅ Created STUDENT history: {total_percentage:.2f}%")
            print(f"       Categories: A={a_score:.1f}%, B={b_score:.1f}%, C={c_score:.1f}%, D={d_score:.1f}%")
        
        created_count += 1
    
    print("\n" + "=" * 80)
    print(f"SUMMARY:")
    print(f"  Created: {created_count} new history records")
    print(f"  Skipped: {skipped_count} existing records")
    print(f"  Total history records now: {EvaluationHistory.objects.count()}")
    print("=" * 80)

if __name__ == '__main__':
    create_history_records()

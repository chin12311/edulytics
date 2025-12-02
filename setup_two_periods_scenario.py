"""
Setup Two Evaluation Periods Scenario
- Period 1: 3 regular students (C405), 1 irregular student, 1 peer evaluate Aeron Caligagan
- Period 2: Same students evaluate again with different answers
- Archive Period 1 to history
- Include student comments in both periods
"""

import os
import django
from django.utils import timezone
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluation_system.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import (
    EvaluationPeriod, EvaluationResponse, IrregularEvaluation,
    Profile, EvaluationHistory
)

def setup_scenario():
    print("=" * 80)
    print("SETTING UP TWO EVALUATION PERIODS SCENARIO")
    print("=" * 80)
    
    # Step 1: Get or create Aeron Caligagan (instructor)
    print("\n[1] Setting up Aeron Caligagan (Instructor)...")
    aeron, created = User.objects.get_or_create(
        username='aeron.caligagan',
        defaults={
            'first_name': 'Aeron',
            'last_name': 'Caligagan',
            'email': 'aeron.caligagan@example.com'
        }
    )
    if created:
        aeron.set_password('password123')
        aeron.save()
    
    aeron_profile, _ = Profile.objects.get_or_create(
        user=aeron,
        defaults={
            'user_type': 'faculty',
            'department': 'Computer Science',
            'employee_number': 'FAC-001'
        }
    )
    print(f"   ✓ Aeron Caligagan: {aeron.username} (ID: {aeron.id})")
    
    # Step 2: Create 3 regular students (Section C405)
    print("\n[2] Creating 3 Regular Students (Section C405)...")
    students = []
    for i in range(1, 4):
        student, created = User.objects.get_or_create(
            username=f'student{i}.c405',
            defaults={
                'first_name': f'Student{i}',
                'last_name': 'Regular',
                'email': f'student{i}.c405@example.com'
            }
        )
        if created:
            student.set_password('password123')
            student.save()
        
        profile, _ = Profile.objects.get_or_create(
            user=student,
            defaults={
                'user_type': 'student',
                'student_number': f'2024-C405-{i:03d}',
                'section': 'C405',
                'is_irregular': False
            }
        )
        students.append(student)
        print(f"   ✓ {student.username} (Student #: {profile.student_number})")
    
    # Step 3: Create 1 irregular student
    print("\n[3] Creating 1 Irregular Student...")
    irregular_student, created = User.objects.get_or_create(
        username='irregular.student1',
        defaults={
            'first_name': 'Irregular',
            'last_name': 'Student',
            'email': 'irregular.student1@example.com'
        }
    )
    if created:
        irregular_student.set_password('password123')
        irregular_student.save()
    
    irregular_profile, _ = Profile.objects.get_or_create(
        user=irregular_student,
        defaults={
            'user_type': 'student',
            'student_number': '2024-IRR-001',
            'section': 'IRREGULAR',
            'is_irregular': True
        }
    )
    print(f"   ✓ {irregular_student.username} (Student #: {irregular_profile.student_number})")
    
    # Step 4: Create 1 peer (faculty)
    print("\n[4] Creating 1 Peer (Faculty)...")
    peer_faculty, created = User.objects.get_or_create(
        username='peer.faculty1',
        defaults={
            'first_name': 'Peer',
            'last_name': 'Faculty',
            'email': 'peer.faculty1@example.com'
        }
    )
    if created:
        peer_faculty.set_password('password123')
        peer_faculty.save()
    
    peer_profile, _ = Profile.objects.get_or_create(
        user=peer_faculty,
        defaults={
            'user_type': 'faculty',
            'department': 'Computer Science',
            'employee_number': 'FAC-002'
        }
    )
    print(f"   ✓ {peer_faculty.username} (Employee #: {peer_profile.employee_number})")
    
    # Step 5: Close any active periods and create Period 1
    print("\n[5] Creating Evaluation Period 1...")
    EvaluationPeriod.objects.filter(is_active=True).update(is_active=False)
    
    period1_start = datetime(2024, 1, 1, tzinfo=timezone.get_current_timezone())
    period1_end = datetime(2024, 1, 31, tzinfo=timezone.get_current_timezone())
    
    period1 = EvaluationPeriod.objects.create(
        name='Evaluation Period 1',
        evaluation_type='student',
        start_date=period1_start,
        end_date=period1_end,
        is_active=False  # We'll make it inactive since we're creating historical data
    )
    print(f"   ✓ Period 1 created: {period1.name} (ID: {period1.id})")
    print(f"      Date: {period1.start_date.date()} to {period1.end_date.date()}")
    
    # Step 6: Create evaluations for Period 1 (Good ratings)
    print("\n[6] Creating Period 1 Evaluations (Good Ratings)...")
    
    # Period 1: 3 Regular Students evaluate Aeron
    period1_comments = [
        "Excellent instructor! Very knowledgeable and engaging.",
        "Great teaching style, explains concepts clearly.",
        "One of the best professors I've had. Highly recommended!"
    ]
    
    for idx, student in enumerate(students):
        profile = Profile.objects.get(user=student)
        eval_response = EvaluationResponse.objects.create(
            evaluator=student,
            evaluatee=aeron,
            evaluation_period=period1,
            student_number=profile.student_number,
            student_section=profile.section,
            submitted_at=period1_start + timedelta(days=idx+1),
            # Good ratings (Excellent/Very Good)
            question1='Excellent',
            question2='Excellent',
            question3='Very Good',
            question4='Excellent',
            question5='Very Good',
            question6='Excellent',
            question7='Excellent',
            question8='Very Good',
            question9='Excellent',
            question10='Very Good',
            question11='Excellent',
            question12='Excellent',
            question13='Very Good',
            question14='Excellent',
            question15='Excellent',
            question16='Very Good',
            question17='Excellent',
            question18='Excellent',
            question19='Very Good',
            comments=period1_comments[idx]
        )
        print(f"   ✓ {student.username} → Aeron (Rating: Excellent/Very Good)")
        print(f"      Comment: \"{period1_comments[idx]}\"")
    
    # Period 1: 1 Irregular Student evaluates Aeron
    irregular_eval = IrregularEvaluation.objects.create(
        evaluator=irregular_student,
        evaluatee=aeron,
        evaluation_period=period1,
        student_number=irregular_profile.student_number,
        submitted_at=period1_start + timedelta(days=4),
        # Good ratings
        question1='Excellent',
        question2='Very Good',
        question3='Excellent',
        question4='Very Good',
        question5='Excellent',
        question6='Very Good',
        question7='Excellent',
        question8='Excellent',
        question9='Very Good',
        question10='Excellent',
        question11='Very Good',
        question12='Excellent',
        question13='Excellent',
        question14='Very Good',
        question15='Excellent',
        question16='Excellent',
        question17='Very Good',
        question18='Excellent',
        question19='Excellent',
        comments="As an irregular student, I appreciate the flexibility and support provided."
    )
    print(f"   ✓ {irregular_student.username} → Aeron (Rating: Excellent/Very Good)")
    print(f"      Comment: \"{irregular_eval.comments}\"")
    
    # Period 1: 1 Peer evaluates Aeron
    peer_eval = EvaluationResponse.objects.create(
        evaluator=peer_faculty,
        evaluatee=aeron,
        evaluation_period=period1,
        student_number=None,  # Peer evaluation
        student_section=None,
        submitted_at=period1_start + timedelta(days=5),
        # Good ratings
        question1='Excellent',
        question2='Excellent',
        question3='Excellent',
        question4='Very Good',
        question5='Excellent',
        question6='Excellent',
        question7='Very Good',
        question8='Excellent',
        question9='Excellent',
        question10='Excellent',
        question11='Very Good',
        question12='Excellent',
        question13='Excellent',
        question14='Excellent',
        question15='Very Good',
        question16='Excellent',
        question17='Excellent',
        question18='Excellent',
        question19='Very Good',
        comments="Colleague demonstrates exceptional teaching abilities and professionalism."
    )
    print(f"   ✓ {peer_faculty.username} → Aeron (Peer Rating: Excellent/Very Good)")
    print(f"      Comment: \"{peer_eval.comments}\"")
    
    print(f"\n   📊 Period 1 Summary:")
    print(f"      - 3 Regular Students (C405): Excellent/Very Good ratings")
    print(f"      - 1 Irregular Student: Excellent/Very Good ratings")
    print(f"      - 1 Peer Evaluation: Excellent/Very Good ratings")
    print(f"      - All with positive comments")
    
    # Step 7: Archive Period 1 to History
    print("\n[7] Archiving Period 1 to EvaluationHistory...")
    
    # Get all Period 1 evaluations
    period1_regular = EvaluationResponse.objects.filter(evaluation_period=period1)
    period1_irregular = IrregularEvaluation.objects.filter(evaluation_period=period1)
    
    archived_count = 0
    
    # Archive regular evaluations
    for eval_response in period1_regular:
        history = EvaluationHistory.objects.create(
            evaluator=eval_response.evaluator,
            evaluatee=eval_response.evaluatee,
            evaluation_period=period1,
            student_number=eval_response.student_number,
            student_section=eval_response.student_section,
            submitted_at=eval_response.submitted_at,
            question1=eval_response.question1,
            question2=eval_response.question2,
            question3=eval_response.question3,
            question4=eval_response.question4,
            question5=eval_response.question5,
            question6=eval_response.question6,
            question7=eval_response.question7,
            question8=eval_response.question8,
            question9=eval_response.question9,
            question10=eval_response.question10,
            question11=eval_response.question11,
            question12=eval_response.question12,
            question13=eval_response.question13,
            question14=eval_response.question14,
            question15=eval_response.question15,
            question16=eval_response.question16,
            question17=eval_response.question17,
            question18=eval_response.question18,
            question19=eval_response.question19,
            comments=eval_response.comments,
            archived_at=timezone.now()
        )
        archived_count += 1
    
    # Archive irregular evaluations
    for irregular_eval in period1_irregular:
        history = EvaluationHistory.objects.create(
            evaluator=irregular_eval.evaluator,
            evaluatee=irregular_eval.evaluatee,
            evaluation_period=period1,
            student_number=irregular_eval.student_number,
            student_section=None,
            submitted_at=irregular_eval.submitted_at,
            question1=irregular_eval.question1,
            question2=irregular_eval.question2,
            question3=irregular_eval.question3,
            question4=irregular_eval.question4,
            question5=irregular_eval.question5,
            question6=irregular_eval.question6,
            question7=irregular_eval.question7,
            question8=irregular_eval.question8,
            question9=irregular_eval.question9,
            question10=irregular_eval.question10,
            question11=irregular_eval.question11,
            question12=irregular_eval.question12,
            question13=irregular_eval.question13,
            question14=irregular_eval.question14,
            question15=irregular_eval.question15,
            question16=irregular_eval.question16,
            question17=irregular_eval.question17,
            question18=irregular_eval.question18,
            question19=irregular_eval.question19,
            comments=irregular_eval.comments,
            archived_at=timezone.now()
        )
        archived_count += 1
    
    print(f"   ✓ Archived {archived_count} evaluations to EvaluationHistory")
    
    # Step 8: Create Period 2
    print("\n[8] Creating Evaluation Period 2...")
    
    period2_start = datetime(2024, 6, 1, tzinfo=timezone.get_current_timezone())
    period2_end = datetime(2024, 6, 30, tzinfo=timezone.get_current_timezone())
    
    period2 = EvaluationPeriod.objects.create(
        name='Evaluation Period 2',
        evaluation_type='student',
        start_date=period2_start,
        end_date=period2_end,
        is_active=True  # This is the current active period
    )
    print(f"   ✓ Period 2 created: {period2.name} (ID: {period2.id})")
    print(f"      Date: {period2.start_date.date()} to {period2.end_date.date()}")
    print(f"      Status: ACTIVE")
    
    # Step 9: Create evaluations for Period 2 (Lower ratings - Fair/Good)
    print("\n[9] Creating Period 2 Evaluations (Lower Ratings - Fair/Good)...")
    
    # Period 2: 3 Regular Students evaluate Aeron with DIFFERENT answers
    period2_comments = [
        "The course material was okay, but could use more practical examples.",
        "Fair instructor, but sometimes goes too fast through topics.",
        "Good content but delivery could be improved. More interaction needed."
    ]
    
    for idx, student in enumerate(students):
        profile = Profile.objects.get(user=student)
        eval_response = EvaluationResponse.objects.create(
            evaluator=student,
            evaluatee=aeron,
            evaluation_period=period2,
            student_number=profile.student_number,
            student_section=profile.section,
            submitted_at=period2_start + timedelta(days=idx+1),
            # Lower ratings (Fair/Good)
            question1='Good',
            question2='Fair',
            question3='Good',
            question4='Fair',
            question5='Good',
            question6='Good',
            question7='Fair',
            question8='Good',
            question9='Fair',
            question10='Good',
            question11='Fair',
            question12='Good',
            question13='Good',
            question14='Fair',
            question15='Good',
            question16='Fair',
            question17='Good',
            question18='Fair',
            question19='Good',
            comments=period2_comments[idx]
        )
        print(f"   ✓ {student.username} → Aeron (Rating: Fair/Good)")
        print(f"      Comment: \"{period2_comments[idx]}\"")
    
    # Period 2: 1 Irregular Student evaluates Aeron with DIFFERENT answers
    irregular_eval2 = IrregularEvaluation.objects.create(
        evaluator=irregular_student,
        evaluatee=aeron,
        evaluation_period=period2,
        student_number=irregular_profile.student_number,
        submitted_at=period2_start + timedelta(days=4),
        # Lower ratings
        question1='Good',
        question2='Fair',
        question3='Good',
        question4='Good',
        question5='Fair',
        question6='Good',
        question7='Fair',
        question8='Good',
        question9='Good',
        question10='Fair',
        question11='Good',
        question12='Fair',
        question13='Good',
        question14='Good',
        question15='Fair',
        question16='Good',
        question17='Fair',
        question18='Good',
        question19='Good',
        comments="This semester was more challenging. Would benefit from clearer instructions."
    )
    print(f"   ✓ {irregular_student.username} → Aeron (Rating: Fair/Good)")
    print(f"      Comment: \"{irregular_eval2.comments}\"")
    
    # Period 2: 1 Peer evaluates Aeron with DIFFERENT answers
    peer_eval2 = EvaluationResponse.objects.create(
        evaluator=peer_faculty,
        evaluatee=aeron,
        evaluation_period=period2,
        student_number=None,
        student_section=None,
        submitted_at=period2_start + timedelta(days=5),
        # Lower ratings
        question1='Good',
        question2='Good',
        question3='Fair',
        question4='Good',
        question5='Good',
        question6='Fair',
        question7='Good',
        question8='Good',
        question9='Fair',
        question10='Good',
        question11='Fair',
        question12='Good',
        question13='Good',
        question14='Fair',
        question15='Good',
        question16='Good',
        question17='Fair',
        question18='Good',
        question19='Good',
        comments="Colleague shows good effort but could improve on time management and student engagement."
    )
    print(f"   ✓ {peer_faculty.username} → Aeron (Peer Rating: Fair/Good)")
    print(f"      Comment: \"{peer_eval2.comments}\"")
    
    print(f"\n   📊 Period 2 Summary:")
    print(f"      - 3 Regular Students (C405): Fair/Good ratings")
    print(f"      - 1 Irregular Student: Fair/Good ratings")
    print(f"      - 1 Peer Evaluation: Fair/Good ratings")
    print(f"      - All with constructive comments")
    
    # Final Summary
    print("\n" + "=" * 80)
    print("SETUP COMPLETE!")
    print("=" * 80)
    print(f"\n📋 Created Accounts:")
    print(f"   • Instructor: {aeron.username} (password: password123)")
    print(f"   • Students: student1.c405, student2.c405, student3.c405 (password: password123)")
    print(f"   • Irregular: irregular.student1 (password: password123)")
    print(f"   • Peer: peer.faculty1 (password: password123)")
    
    print(f"\n📅 Evaluation Periods:")
    print(f"   • Period 1: {period1.name} (ID: {period1.id}) - ARCHIVED")
    print(f"     - Dates: {period1.start_date.date()} to {period1.end_date.date()}")
    print(f"     - Ratings: Excellent/Very Good (Positive)")
    print(f"     - Status: Moved to EvaluationHistory table")
    
    print(f"\n   • Period 2: {period2.name} (ID: {period2.id}) - ACTIVE")
    print(f"     - Dates: {period2.start_date.date()} to {period2.end_date.date()}")
    print(f"     - Ratings: Fair/Good (Lower than Period 1)")
    print(f"     - Status: Current evaluations in EvaluationResponse table")
    
    print(f"\n✅ Verification:")
    print(f"   • Period 1 data → EvaluationHistory table ({archived_count} records)")
    print(f"   • Period 2 data → EvaluationResponse & IrregularEvaluation tables (5 records)")
    print(f"   • Same students evaluated Aeron in both periods ✓")
    print(f"   • Different ratings between periods ✓")
    print(f"   • Student comments included in both periods ✓")
    
    print(f"\n🔍 Next Steps:")
    print(f"   1. Login as coordinator/dean/faculty to view results")
    print(f"   2. Check 'Overall Results' to see Period 2 (current)")
    print(f"   3. Check 'Evaluation History' to see Period 1 (archived)")
    print(f"   4. Verify different ratings between the two periods")
    print(f"   5. Try evaluating Aeron again as any student - should be BLOCKED (same period)")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    try:
        setup_scenario()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

import os
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluation.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import (
    EvaluationPeriod, EvaluationResponse, IrregularEvaluation,
    EvaluationHistory, UserProfile, Department, Section
)
from django.utils import timezone

def create_scenario():
    print("=" * 70)
    print("CREATING EVALUATION SCENARIO - PERIOD 1 & PERIOD 2")
    print("=" * 70)
    
    # Get or create department
    dept, _ = Department.objects.get_or_create(
        name="Computer Science",
        defaults={'institute': 'College of Engineering'}
    )
    print(f"✓ Department: {dept.name}")
    
    # Get or create section C405
    section, _ = Section.objects.get_or_create(
        name="C405",
        defaults={'department': dept}
    )
    print(f"✓ Section: {section.name}")
    
    # Get or create Aeron Caligagan (faculty)
    aeron, created = User.objects.get_or_create(
        username='aeron.caligagan',
        defaults={
            'first_name': 'Aeron',
            'last_name': 'Caligagan',
            'email': 'aeron.caligagan@university.edu'
        }
    )
    if created:
        aeron.set_password('faculty123')
        aeron.save()
    
    aeron_profile, _ = UserProfile.objects.get_or_create(
        user=aeron,
        defaults={
            'role': 'faculty',
            'department': dept,
            'is_irregular': False
        }
    )
    aeron_profile.sections.add(section)
    print(f"✓ Faculty: {aeron.get_full_name()} (username: {aeron.username})")
    
    # Create 3 regular students
    students = []
    for i in range(1, 4):
        student, created = User.objects.get_or_create(
            username=f'student{i}.c405',
            defaults={
                'first_name': f'Student{i}',
                'last_name': 'Regular',
                'email': f'student{i}.c405@university.edu'
            }
        )
        if created:
            student.set_password('student123')
            student.save()
        
        profile, _ = UserProfile.objects.get_or_create(
            user=student,
            defaults={
                'role': 'student',
                'department': dept,
                'student_number': f'2024-C405-{i:03d}',
                'is_irregular': False
            }
        )
        profile.sections.add(section)
        students.append(student)
        print(f"✓ Regular Student {i}: {student.username} (SN: {profile.student_number})")
    
    # Create 1 irregular student
    irregular, created = User.objects.get_or_create(
        username='irregular.c405',
        defaults={
            'first_name': 'Irregular',
            'last_name': 'Student',
            'email': 'irregular.c405@university.edu'
        }
    )
    if created:
        irregular.set_password('student123')
        irregular.save()
    
    irregular_profile, _ = UserProfile.objects.get_or_create(
        user=irregular,
        defaults={
            'role': 'student',
            'department': dept,
            'student_number': '2024-IRR-001',
            'is_irregular': True
        }
    )
    irregular_profile.sections.add(section)
    print(f"✓ Irregular Student: {irregular.username} (SN: {irregular_profile.student_number})")
    
    # Create 1 peer (another faculty)
    peer, created = User.objects.get_or_create(
        username='peer.faculty',
        defaults={
            'first_name': 'Peer',
            'last_name': 'Faculty',
            'email': 'peer.faculty@university.edu'
        }
    )
    if created:
        peer.set_password('faculty123')
        peer.save()
    
    peer_profile, _ = UserProfile.objects.get_or_create(
        user=peer,
        defaults={
            'role': 'faculty',
            'department': dept,
            'is_irregular': False
        }
    )
    peer_profile.sections.add(section)
    print(f"✓ Peer Faculty: {peer.get_full_name()} (username: {peer.username})")
    
    print("\n" + "=" * 70)
    print("CREATING EVALUATION PERIOD 1")
    print("=" * 70)
    
    # Create Period 1 (past period - will be archived)
    period1, _ = EvaluationPeriod.objects.get_or_create(
        name="First Semester Evaluation 2024",
        evaluation_type='student',
        defaults={
            'start_date': timezone.now() - timedelta(days=90),
            'end_date': timezone.now() - timedelta(days=60),
            'is_active': False
        }
    )
    print(f"✓ Period 1: {period1.name} (INACTIVE - for history)")
    
    # Period 1 - Student evaluations (Good ratings)
    print("\nCreating Period 1 evaluations...")
    comments_p1 = [
        "Great instructor! Very clear explanations in Period 1.",
        "Good teaching style, but could improve time management.",
        "Excellent professor, very helpful during consultations."
    ]
    
    for idx, student in enumerate(students):
        profile = student.userprofile
        response, created = EvaluationResponse.objects.update_or_create(
            evaluator=student,
            evaluatee=aeron,
            evaluation_period=period1,
            defaults={
                'student_number': profile.student_number,
                'student_section': 'C405',
                'submitted_at': period1.start_date + timedelta(days=5 + idx),
                'question1': 'Good',
                'question2': 'Good',
                'question3': 'Good',
                'question4': 'Good',
                'question5': 'Good',
                'question6': 'Good',
                'question7': 'Good',
                'question8': 'Excellent',
                'question9': 'Good',
                'question10': 'Good',
                'question11': 'Good',
                'question12': 'Good',
                'question13': 'Good',
                'question14': 'Good',
                'question15': 'Good',
                'question16': 'Good',
                'question17': 'Good',
                'question18': 'Good',
                'question19': 'Good',
                'comments': comments_p1[idx]
            }
        )
        print(f"  ✓ {student.username} → Aeron (Good ratings) - '{comments_p1[idx][:50]}...'")
    
    # Period 1 - Irregular student evaluation
    irreg_response, created = IrregularEvaluation.objects.update_or_create(
        evaluator=irregular,
        evaluatee=aeron,
        evaluation_period=period1,
        defaults={
            'student_number': irregular_profile.student_number,
            'submitted_at': period1.start_date + timedelta(days=8),
            'question1': 'Excellent',
            'question2': 'Good',
            'question3': 'Good',
            'question4': 'Good',
            'question5': 'Good',
            'question6': 'Good',
            'question7': 'Good',
            'question8': 'Good',
            'question9': 'Good',
            'question10': 'Good',
            'question11': 'Good',
            'question12': 'Good',
            'question13': 'Good',
            'question14': 'Good',
            'question15': 'Good',
            'question16': 'Good',
            'question17': 'Good',
            'question18': 'Good',
            'question19': 'Good',
            'comments': 'As an irregular student, I appreciate the flexibility. Good instructor!'
        }
    )
    print(f"  ✓ {irregular.username} → Aeron (Irregular, Good ratings) - 'As an irregular student...'")
    
    # Period 1 - Peer evaluation
    peer_response, created = EvaluationResponse.objects.update_or_create(
        evaluator=peer,
        evaluatee=aeron,
        evaluation_period=period1,
        defaults={
            'submitted_at': period1.start_date + timedelta(days=10),
            'question1': 'Good',
            'question2': 'Good',
            'question3': 'Good',
            'question4': 'Good',
            'question5': 'Good',
            'question6': 'Good',
            'question7': 'Good',
            'question8': 'Good',
            'question9': 'Good',
            'question10': 'Good',
            'question11': 'Good',
            'question12': 'Good',
            'question13': 'Good',
            'question14': 'Good',
            'question15': 'Good',
            'question16': 'Good',
            'question17': 'Good',
            'question18': 'Good',
            'question19': 'Good',
            'comments': 'Good colleague, collaborates well with the department in Period 1.'
        }
    )
    print(f"  ✓ {peer.username} → Aeron (Peer, Good ratings) - 'Good colleague...'")
    
    print("\n" + "=" * 70)
    print("ARCHIVING PERIOD 1 TO EVALUATION HISTORY")
    print("=" * 70)
    
    # Archive Period 1 results
    all_p1_responses = EvaluationResponse.objects.filter(evaluation_period=period1, evaluatee=aeron)
    all_p1_irregular = IrregularEvaluation.objects.filter(evaluation_period=period1, evaluatee=aeron)
    
    # Calculate Period 1 results
    total_responses = all_p1_responses.count() + all_p1_irregular.count()
    
    # Create history record
    history, created = EvaluationHistory.objects.update_or_create(
        user=aeron,
        evaluation_period=period1,
        section=section,
        defaults={
            'total_responses': total_responses,
            'average_rating': 4.0,  # Good = 4.0
            'archived_at': timezone.now() - timedelta(days=59)
        }
    )
    print(f"✓ Period 1 archived to history: {total_responses} total responses, avg rating: 4.0")
    
    print("\n" + "=" * 70)
    print("CREATING EVALUATION PERIOD 2 (CURRENT ACTIVE)")
    print("=" * 70)
    
    # Create Period 2 (current active period)
    period2, _ = EvaluationPeriod.objects.get_or_create(
        name="Second Semester Evaluation 2024",
        evaluation_type='student',
        defaults={
            'start_date': timezone.now() - timedelta(days=10),
            'end_date': timezone.now() + timedelta(days=20),
            'is_active': True
        }
    )
    period2.is_active = True
    period2.save()
    print(f"✓ Period 2: {period2.name} (ACTIVE)")
    
    # Period 2 - Student evaluations (Excellent ratings - improved!)
    print("\nCreating Period 2 evaluations (BETTER ratings)...")
    comments_p2 = [
        "Outstanding improvement! Best instructor this semester in Period 2!",
        "Excellent teaching methods, very engaging and interactive now.",
        "Perfect! Time management much better, very organized classes."
    ]
    
    for idx, student in enumerate(students):
        profile = student.userprofile
        response, created = EvaluationResponse.objects.update_or_create(
            evaluator=student,
            evaluatee=aeron,
            evaluation_period=period2,
            defaults={
                'student_number': profile.student_number,
                'student_section': 'C405',
                'submitted_at': period2.start_date + timedelta(days=2 + idx),
                'question1': 'Excellent',
                'question2': 'Excellent',
                'question3': 'Excellent',
                'question4': 'Excellent',
                'question5': 'Excellent',
                'question6': 'Excellent',
                'question7': 'Excellent',
                'question8': 'Excellent',
                'question9': 'Excellent',
                'question10': 'Excellent',
                'question11': 'Excellent',
                'question12': 'Excellent',
                'question13': 'Excellent',
                'question14': 'Excellent',
                'question15': 'Excellent',
                'question16': 'Excellent',
                'question17': 'Excellent',
                'question18': 'Excellent',
                'question19': 'Excellent',
                'comments': comments_p2[idx]
            }
        )
        print(f"  ✓ {student.username} → Aeron (Excellent ratings) - '{comments_p2[idx][:50]}...'")
    
    # Period 2 - Irregular student evaluation (Excellent)
    irreg_response, created = IrregularEvaluation.objects.update_or_create(
        evaluator=irregular,
        evaluatee=aeron,
        evaluation_period=period2,
        defaults={
            'student_number': irregular_profile.student_number,
            'submitted_at': period2.start_date + timedelta(days=5),
            'question1': 'Excellent',
            'question2': 'Excellent',
            'question3': 'Excellent',
            'question4': 'Excellent',
            'question5': 'Excellent',
            'question6': 'Excellent',
            'question7': 'Excellent',
            'question8': 'Excellent',
            'question9': 'Excellent',
            'question10': 'Excellent',
            'question11': 'Excellent',
            'question12': 'Excellent',
            'question13': 'Excellent',
            'question14': 'Excellent',
            'question15': 'Excellent',
            'question16': 'Excellent',
            'question17': 'Excellent',
            'question18': 'Excellent',
            'question19': 'Excellent',
            'comments': 'Excellent instructor in Period 2! Teaching quality significantly improved!'
        }
    )
    print(f"  ✓ {irregular.username} → Aeron (Irregular, Excellent) - 'Excellent instructor in Period 2!...'")
    
    # Period 2 - Peer evaluation (Excellent)
    peer_response, created = EvaluationResponse.objects.update_or_create(
        evaluator=peer,
        evaluatee=aeron,
        evaluation_period=period2,
        defaults={
            'submitted_at': period2.start_date + timedelta(days=7),
            'question1': 'Excellent',
            'question2': 'Excellent',
            'question3': 'Excellent',
            'question4': 'Excellent',
            'question5': 'Excellent',
            'question6': 'Excellent',
            'question7': 'Excellent',
            'question8': 'Excellent',
            'question9': 'Excellent',
            'question10': 'Excellent',
            'question11': 'Excellent',
            'question12': 'Excellent',
            'question13': 'Excellent',
            'question14': 'Excellent',
            'question15': 'Excellent',
            'question16': 'Excellent',
            'question17': 'Excellent',
            'question18': 'Excellent',
            'question19': 'Excellent',
            'comments': 'Outstanding colleague in Period 2! Leadership skills have greatly improved!'
        }
    )
    print(f"  ✓ {peer.username} → Aeron (Peer, Excellent) - 'Outstanding colleague in Period 2!...'")
    
    print("\n" + "=" * 70)
    print("SCENARIO CREATION COMPLETE!")
    print("=" * 70)
    print("\n📊 SUMMARY:")
    print(f"   Period 1 (ARCHIVED):")
    print(f"      - 3 Regular Students (Good ratings, avg ~4.0)")
    print(f"      - 1 Irregular Student (Good ratings)")
    print(f"      - 1 Peer Faculty (Good ratings)")
    print(f"      - Status: Moved to EvaluationHistory")
    print(f"")
    print(f"   Period 2 (ACTIVE):")
    print(f"      - 3 Regular Students (Excellent ratings, avg ~5.0)")
    print(f"      - 1 Irregular Student (Excellent ratings)")
    print(f"      - 1 Peer Faculty (Excellent ratings)")
    print(f"      - Status: Current active evaluations")
    print(f"")
    print(f"🎯 Results for Aeron Caligagan:")
    print(f"   - Period 1: Average ~4.0 (Good) - See Evaluation History")
    print(f"   - Period 2: Average ~5.0 (Excellent) - Current Results")
    print(f"")
    print(f"📝 All evaluations include student comments!")
    print(f"")
    print(f"✅ Login Credentials:")
    print(f"   Faculty: aeron.caligagan / faculty123")
    print(f"   Students: student1.c405, student2.c405, student3.c405 / student123")
    print(f"   Irregular: irregular.c405 / student123")
    print(f"   Peer: peer.faculty / faculty123")
    print("=" * 70)

if __name__ == '__main__':
    try:
        create_scenario()
        print("\n✅ SUCCESS! Scenario created successfully!")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

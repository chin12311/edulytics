from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import (
    EvaluationPeriod, EvaluationResponse, IrregularEvaluation,
    EvaluationHistory, UserProfile, Section, Institute, Course
)
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Creates evaluation scenario with Period 1 (archived) and Period 2 (active)'

    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write("CREATING EVALUATION SCENARIO - PERIOD 1 & PERIOD 2")
        self.stdout.write("=" * 70)
        
        # Get or create institute
        institute, _ = Institute.objects.get_or_create(
            name="College of Engineering",
            defaults={'code': 'COE'}
        )
        self.stdout.write(f"✓ Institute: {institute.name}")
        
        # Get or create course
        course, _ = Course.objects.get_or_create(
            name="Computer Science",
            institute=institute,
            defaults={'code': 'CS'}
        )
        self.stdout.write(f"✓ Course: {course.name}")
        
        # Get or create section C405
        section, _ = Section.objects.get_or_create(
            code="C405",
            defaults={'year_level': 4}
        )
        self.stdout.write(f"✓ Section: {section.code}")
        
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
                'institute': institute.name,
                'course': course.name,
                'is_irregular': False
            }
        )
        self.stdout.write(f"✓ Faculty: {aeron.get_full_name()} (username: {aeron.username})")
        
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
                    'institute': institute.name,
                    'course': course.name,
                    'studentnumber': f'24-{1000+i}',  # Format: XX-XXXX
                    'section': section,
                    'is_irregular': False
                }
            )
            students.append(student)
            self.stdout.write(f"✓ Regular Student {i}: {student.username} (SN: {profile.studentnumber})")
        
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
                'institute': institute.name,
                'course': course.name,
                'studentnumber': '24-9999',  # Format: XX-XXXX
                'section': None,  # Irregular students don't have section
                'is_irregular': True
            }
        )
        self.stdout.write(f"✓ Irregular Student: {irregular.username} (SN: {irregular_profile.studentnumber})")
        
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
                'institute': institute.name,
                'course': course.name,
                'is_irregular': False
            }
        )
        self.stdout.write(f"✓ Peer Faculty: {peer.get_full_name()} (username: {peer.username})")
        
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("CREATING EVALUATION PERIOD 1")
        self.stdout.write("=" * 70)
        
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
        self.stdout.write(f"✓ Period 1: {period1.name} (INACTIVE - for history)")
        
        # Period 1 - Student evaluations (Good ratings)
        self.stdout.write("\nCreating Period 1 evaluations...")
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
                    'student_number': profile.studentnumber,
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
            self.stdout.write(f"  ✓ {student.username} → Aeron (Good ratings) - '{comments_p1[idx][:50]}...'")
        
        # Period 1 - Irregular student evaluation
        irreg_response, created = IrregularEvaluation.objects.update_or_create(
            evaluator=irregular,
            evaluatee=aeron,
            evaluation_period=period1,
            defaults={
                'student_number': irregular_profile.studentnumber,
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
        self.stdout.write(f"  ✓ {irregular.username} → Aeron (Irregular, Good ratings) - 'As an irregular student...'")
        
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
        self.stdout.write(f"  ✓ {peer.username} → Aeron (Peer, Good ratings) - 'Good colleague...'")
        
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("ARCHIVING PERIOD 1 TO EVALUATION HISTORY")
        self.stdout.write("=" * 70)
        
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
        self.stdout.write(f"✓ Period 1 archived to history: {total_responses} total responses, avg rating: 4.0")
        
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("CREATING EVALUATION PERIOD 2 (CURRENT ACTIVE)")
        self.stdout.write("=" * 70)
        
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
        self.stdout.write(f"✓ Period 2: {period2.name} (ACTIVE)")
        
        # Period 2 - Student evaluations (Excellent ratings - improved!)
        self.stdout.write("\nCreating Period 2 evaluations (BETTER ratings)...")
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
                    'student_number': profile.studentnumber,
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
            self.stdout.write(f"  ✓ {student.username} → Aeron (Excellent ratings) - '{comments_p2[idx][:50]}...'")
        
        # Period 2 - Irregular student evaluation (Excellent)
        irreg_response, created = IrregularEvaluation.objects.update_or_create(
            evaluator=irregular,
            evaluatee=aeron,
            evaluation_period=period2,
            defaults={
                'student_number': irregular_profile.studentnumber,
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
        self.stdout.write(f"  ✓ {irregular.username} → Aeron (Irregular, Excellent) - 'Excellent instructor in Period 2!...'")
        
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
        self.stdout.write(f"  ✓ {peer.username} → Aeron (Peer, Excellent) - 'Outstanding colleague in Period 2!...'")
        
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("SCENARIO CREATION COMPLETE!")
        self.stdout.write("=" * 70)
        self.stdout.write("\n📊 SUMMARY:")
        self.stdout.write(f"   Period 1 (ARCHIVED):")
        self.stdout.write(f"      - 3 Regular Students (Good ratings, avg ~4.0)")
        self.stdout.write(f"      - 1 Irregular Student (Good ratings)")
        self.stdout.write(f"      - 1 Peer Faculty (Good ratings)")
        self.stdout.write(f"      - Status: Moved to EvaluationHistory")
        self.stdout.write(f"")
        self.stdout.write(f"   Period 2 (ACTIVE):")
        self.stdout.write(f"      - 3 Regular Students (Excellent ratings, avg ~5.0)")
        self.stdout.write(f"      - 1 Irregular Student (Excellent ratings)")
        self.stdout.write(f"      - 1 Peer Faculty (Excellent ratings)")
        self.stdout.write(f"      - Status: Current active evaluations")
        self.stdout.write(f"")
        self.stdout.write(f"🎯 Results for Aeron Caligagan:")
        self.stdout.write(f"   - Period 1: Average ~4.0 (Good) - See Evaluation History")
        self.stdout.write(f"   - Period 2: Average ~5.0 (Excellent) - Current Results")
        self.stdout.write(f"")
        self.stdout.write(f"📝 All evaluations include student comments!")
        self.stdout.write(f"")
        self.stdout.write(self.style.SUCCESS("✅ Login Credentials:"))
        self.stdout.write(f"   Faculty: aeron.caligagan / faculty123")
        self.stdout.write(f"   Students: student1.c405, student2.c405, student3.c405 / student123")
        self.stdout.write(f"   Irregular: irregular.c405 / student123")
        self.stdout.write(f"   Peer: peer.faculty / faculty123")
        self.stdout.write("=" * 70)
        
        self.stdout.write(self.style.SUCCESS('\n✅ SUCCESS! Scenario created successfully!'))

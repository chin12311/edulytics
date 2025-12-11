from django.core.management.base import BaseCommand
from main.models import EvaluationQuestion, PeerEvaluationQuestion, UpwardEvaluationQuestion

class Command(BaseCommand):
    help = 'Initialize evaluation questions in the database'
    
    def handle(self, *args, **options):
        # Student evaluation questions (19 questions)
        student_questions = [
            "Demonstrates mastery of the subject and the ability to translate competencies into meaningful lessons.",
            "Shows ability to stimulate independent and critical thinking",
            "Is focused and explains the lesson clearly",
            "Knowledgable and uses a variety of teaching strategies.",
            "Demonstrates enthusiasm for the subject matter",
            "Establishes and communicates clearly parameters for student classroom behaviour based on student handbook and OVPAA Guidelines for the conduct of Flexible Learning Modalities.",
            "Promote self-discipline, respect and treats all students in fair and equitable manner.",
            "Keeps accurate accounting of student's attendance and records",
            "Demonstrates fairness and consistency in handling student's problems.",
            "Maintains harmonious relations with students characterized by mutual respect and understanding.",
            "Reports to class regularly.",
            "Demonstrates exceptional punctuality in observing work hours and college official functions.",
            "Returns quizzes, examination results, assignments and other activities on time.",
            "Informs the students on their academic performances and grades.",
            "Uses Google Meet and Classroom as the official platform for online classes.",
            "Commands respect by example in appearance, manners and behaviour and language.",
            "Maintains a good disposition.",
            "Relates well with students in a pleasing manner.",
            "Possesses a sense of balance that combines good humor, sincerity and fairness when confronted with difficulties in the classroom",
        ]
        
        # Peer evaluation questions (11 questions)
        peer_questions = [
            "Conducts himself/herself in a manner that is consistent to CCA vision and mission.",
            "Shows willingness to help colleagues in the performance of tasks and other assignments.",
            "Complies with the college's policies and procedures.",
            "Demonstrates professionalism and courtesy in relating with colleagues",
            "Exhibits willingness to grow personally and professionally",
            "Shows appreciation and respect for the output and ideas of colleagues",
            "Shows willingness to accept responsibility for his/her actions",
            "Demonstrates willingness to listen to colleague's ideas",
            "Demonstrates good interpersonal relationships with colleagues",
            "Shows willingness to share his/her expertise to colleagues",
            "Exhibits leadership potentials and abilities",
        ]
        
        # Upward evaluation questions (15 questions) - Faculty → Coordinator
        upward_questions = [
            "Provides clear direction and vision for the department/program",
            "Makes informed decisions that benefit faculty and students",
            "Demonstrates effective leadership in managing department initiatives",
            "Encourages innovation and continuous improvement in teaching practices",
            "Builds a collaborative team environment among faculty members",
            "Provides adequate resources and support for teaching effectiveness",
            "Facilitates professional development opportunities for faculty growth",
            "Offers constructive feedback and mentorship when needed",
            "Advocates for faculty interests and welfare with higher administration",
            "Communicates policies, decisions, and expectations clearly and transparently",
            "Is accessible and approachable for faculty concerns and questions",
            "Listens actively and responds appropriately to faculty input and feedback",
            "Manages workload distribution fairly and equitably among faculty",
            "Handles conflicts and problems in a timely and professional manner",
            "Demonstrates efficiency in administrative tasks and departmental operations",
        ]
        
        # Create or update student evaluation questions
        created_count = 0
        updated_count = 0
        for i, question in enumerate(student_questions, 1):
            obj, created = EvaluationQuestion.objects.update_or_create(
                evaluation_type='student',
                question_number=i,
                defaults={'question_text': question, 'is_active': True}
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Student Questions: {created_count} created, {updated_count} updated'
            )
        )
        
        # Create or update peer evaluation questions
        created_count = 0
        updated_count = 0
        for i, question in enumerate(peer_questions, 1):
            obj, created = PeerEvaluationQuestion.objects.update_or_create(
                question_number=i,
                defaults={'question_text': question, 'is_active': True}
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Peer Questions: {created_count} created, {updated_count} updated'
            )
        )
        
        # Create or update upward evaluation questions
        created_count = 0
        updated_count = 0
        for i, question in enumerate(upward_questions, 1):
            obj, created = UpwardEvaluationQuestion.objects.update_or_create(
                question_number=i,
                defaults={'question_text': question, 'is_active': True}
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Upward Questions: {created_count} created, {updated_count} updated'
            )
        )
        
        self.stdout.write(self.style.SUCCESS('✅ Evaluation questions initialized successfully!'))

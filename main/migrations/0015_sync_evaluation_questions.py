from django.db import migrations

STUDENT_QUESTIONS = [
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

PEER_QUESTIONS = [
    "Effectively communicates with others in the workplace",
    "Listens actively and values others' opinions and perspectives",
    "Shows respect in all professional interactions",
    "Contributes actively to team discussions and collaborative efforts",
    "Completes assigned duties and responsibilities on time",
    "Demonstrates reliability and accountability in work",
    "Takes initiative when appropriate and needed",
    "Makes valuable contributions to institutional goals and objectives",
    "Shows leadership qualities when needed or appropriate",
    "Helps resolve conflicts constructively when they arise",
    "Accepts and applies feedback for personal and professional improvement",
    "Maintains focus and engagement in professional duties",
    "Is prepared and organized in carrying out responsibilities",
    "Demonstrates strong work ethic and professional integrity",
    "Would you want to work with this colleague again in future projects?",
]


def sync_questions(apps, schema_editor):
    EvaluationQuestion = apps.get_model('main', 'EvaluationQuestion')
    PeerEvaluationQuestion = apps.get_model('main', 'PeerEvaluationQuestion')

    student_numbers = []
    for idx, question in enumerate(STUDENT_QUESTIONS, start=1):
        EvaluationQuestion.objects.update_or_create(
            evaluation_type='student',
            question_number=idx,
            defaults={'question_text': question, 'is_active': True}
        )
        student_numbers.append(idx)

    EvaluationQuestion.objects.filter(evaluation_type='student').exclude(
        question_number__in=student_numbers
    ).delete()

    peer_numbers = []
    for idx, question in enumerate(PEER_QUESTIONS, start=1):
        PeerEvaluationQuestion.objects.update_or_create(
            question_number=idx,
            defaults={'question_text': question, 'is_active': True}
        )
        peer_numbers.append(idx)

    PeerEvaluationQuestion.objects.exclude(question_number__in=peer_numbers).delete()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_airecommendation_description_and_more'),
    ]

    operations = [
        migrations.RunPython(sync_questions, noop),
    ]

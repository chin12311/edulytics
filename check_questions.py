import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import EvaluationQuestion, PeerEvaluationQuestion

print("=" * 80)
print("STUDENT EVALUATION QUESTIONS (from database)")
print("=" * 80)

student_questions = EvaluationQuestion.objects.filter(
    evaluation_type='student',
    is_active=True
).order_by('question_number')

print(f"Total questions: {student_questions.count()}\n")

for q in student_questions:
    print(f"Q{q.question_number}: {q.question_text[:80]}...")
    print(f"  Updated: {q.updated_at}")
    print()

print("\n" + "=" * 80)
print("PEER EVALUATION QUESTIONS (from database)")
print("=" * 80)

peer_questions = PeerEvaluationQuestion.objects.filter(
    is_active=True
).order_by('question_number')

print(f"Total questions: {peer_questions.count()}\n")

for q in peer_questions:
    print(f"Q{q.question_number}: {q.question_text[:80]}...")
    print(f"  Updated: {q.updated_at}")
    print()

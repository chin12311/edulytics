from main.models import EvaluationQuestion

questions = EvaluationQuestion.objects.filter(
    evaluation_type='student',
    is_active=True
).order_by('question_number')

print(f'Total questions: {questions.count()}')
print()
for q in questions:
    print(f'Q{q.question_number}: {q.question_text[:70]}...')

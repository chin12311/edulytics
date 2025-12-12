from main.models import EvaluationPeriod, Evaluation

print('=== EVALUATION PERIODS ===')
periods = EvaluationPeriod.objects.filter(evaluation_type='upward')
print(f'Total upward periods: {periods.count()}')
for p in periods:
    print(f'ID: {p.id}, Name: {p.name}, Active: {p.is_active}, Type: {p.evaluation_type}')

print('\n=== EVALUATIONS ===')
evals = Evaluation.objects.filter(evaluation_type='upward')
print(f'Total upward evaluations: {evals.count()}')
for e in evals:
    print(f'ID: {e.id}, Released: {e.is_released}, Period: {e.evaluation_period_id}, Type: {e.evaluation_type}')

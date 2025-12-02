from main.models import EvaluationResponse
from django.db import connection

print("=== Checking for Evaluation ID 31 ===\n")

# Try to get evaluation ID 31
try:
    eval_31 = EvaluationResponse.objects.get(id=31)
    print(f"✓ Evaluation ID 31 EXISTS!")
    print(f"  Evaluator: {eval_31.evaluator.username}")
    print(f"  Evaluatee: {eval_31.evaluatee.username}")
    print(f"  Period: {eval_31.evaluation_period.name}")
    print(f"  Submitted: {eval_31.submitted_at}")
except EvaluationResponse.DoesNotExist:
    print("✗ Evaluation ID 31 NOT FOUND")

# Check what IDs exist
print(f"\n=== All Evaluation IDs ===")
all_evals = EvaluationResponse.objects.all().values_list('id', 'evaluator__username', 'evaluatee__username')
print(f"Total evaluations: {len(all_evals)}")
for eval_id, evaluator, evaluatee in all_evals:
    print(f"  ID {eval_id}: {evaluator} -> {evaluatee}")

# Check with raw SQL
print(f"\n=== Raw SQL Check ===")
with connection.cursor() as cursor:
    cursor.execute("SELECT id, evaluator_id, evaluatee_id, submitted_at FROM main_evaluationresponse WHERE id = 31")
    result = cursor.fetchone()
    if result:
        print(f"✓ Raw SQL found ID 31: {result}")
    else:
        print("✗ Raw SQL found nothing for ID 31")
    
    # Check max ID
    cursor.execute("SELECT MAX(id) FROM main_evaluationresponse")
    max_id = cursor.fetchone()[0]
    print(f"\nMax evaluation ID in database: {max_id}")
    
    # Check auto_increment value
    cursor.execute("SHOW TABLE STATUS LIKE 'main_evaluationresponse'")
    table_status = cursor.fetchone()
    print(f"Table auto_increment value: {table_status[10]}")  # Auto_increment is column 11

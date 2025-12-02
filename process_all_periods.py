from main.models import EvaluationPeriod
from main.views import process_evaluation_period_to_results

print("=== PROCESSING UNPROCESSED EVALUATIONS ===\n")

# Get the December 2025 periods
student_period = EvaluationPeriod.objects.get(
    name="Student Evaluation December 2025",
    evaluation_type='student'
)

peer_period = EvaluationPeriod.objects.get(
    name="Peer Evaluation December 2025",
    evaluation_type='peer'
)

print("Processing Student Evaluation Period...")
student_count = process_evaluation_period_to_results(student_period)
print(f"✓ Processed {student_count} student evaluation results\n")

print("Processing Peer Evaluation Period...")
peer_count = process_evaluation_period_to_results(peer_period)
print(f"✓ Processed {peer_count} peer evaluation results\n")

# Verify results
from main.models import EvaluationResult
results = EvaluationResult.objects.all()
print(f"=== Total Results After Processing: {results.count()} ===")
for result in results:
    print(f"  {result.user.username} - Section: {result.section.code if result.section else 'None'} - Score: {result.total_percentage:.2f}%")

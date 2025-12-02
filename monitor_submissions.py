import time
from django.db import connection
from main.models import EvaluationResponse, IrregularEvaluation

print("=== MONITORING DATABASE FOR NEW SUBMISSIONS ===")
print("Checking every 2 seconds for new evaluations...")
print("Press Ctrl+C to stop\n")

initial_regular = EvaluationResponse.objects.count()
initial_irregular = IrregularEvaluation.objects.count()

print(f"Initial counts:")
print(f"  Regular: {initial_regular}")
print(f"  Irregular: {initial_irregular}")
print("\nWaiting for new submissions...\n")

try:
    for i in range(30):  # Monitor for 60 seconds
        time.sleep(2)
        
        current_regular = EvaluationResponse.objects.count()
        current_irregular = IrregularEvaluation.objects.count()
        
        if current_regular > initial_regular:
            print(f"\n✓ NEW REGULAR EVALUATION DETECTED!")
            new_evals = EvaluationResponse.objects.all().order_by('-id')[:1]
            for eval in new_evals:
                print(f"  ID: {eval.id}")
                print(f"  Evaluator: {eval.evaluator.username}")
                print(f"  Evaluatee: {eval.evaluatee.username}")
                print(f"  Period: {eval.evaluation_period.name}")
                print(f"  Submitted: {eval.submitted_at}")
            break
            
        if current_irregular > initial_irregular:
            print(f"\n✓ NEW IRREGULAR EVALUATION DETECTED!")
            new_evals = IrregularEvaluation.objects.all().order_by('-id')[:1]
            for eval in new_evals:
                print(f"  ID: {eval.id}")
                print(f"  Evaluator: {eval.evaluator.username}")
                print(f"  Evaluatee: {eval.evaluatee.username}")
                print(f"  Period: {eval.evaluation_period.name}")
                print(f"  Submitted: {eval.submitted_at}")
            break
        
        print(f"Check #{i+1}: No new submissions yet...")
        
except KeyboardInterrupt:
    print("\n\nMonitoring stopped.")

print(f"\nFinal counts:")
print(f"  Regular: {EvaluationResponse.objects.count()}")
print(f"  Irregular: {IrregularEvaluation.objects.count()}")

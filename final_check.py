from main.models import EvaluationResponse, IrregularEvaluation, EvaluationResult
from django.contrib.auth.models import User

print("=== FINAL DATABASE CHECK ===\n")

print(f"Total Users in DB: {User.objects.count()}")
print(f"Total Evaluation Responses: {EvaluationResponse.objects.count()}")
print(f"Total Irregular Evaluations: {IrregularEvaluation.objects.count()}")
print(f"Total Evaluation Results: {EvaluationResult.objects.count()}")

print("\n=== Checking for specific usernames ===")
usernames_to_check = ['jowardclaudio', 'jadepuno', 'zyrahmastelero', 'aeroncaligagan']
for username in usernames_to_check:
    exists = User.objects.filter(username=username).exists()
    print(f"{username}: {'EXISTS' if exists else 'NOT FOUND'}")

print("\n=== CONCLUSION ===")
if EvaluationResponse.objects.count() == 0 and IrregularEvaluation.objects.count() == 0:
    print("✗ NO EVALUATIONS IN AWS DATABASE")
    print("✗ The admin panel screenshots you showed are from LOCAL database, not AWS")
    print("✗ To see results on AWS production, you must:")
    print("  1. Go to https://edulytics.uk")
    print("  2. Create accounts for jadepuno, zyrahmastelero, aeroncaligagan")
    print("  3. Submit evaluations through the production website")
    print("  4. Click 'Unrelease' as coordinator/dean")
else:
    print("✓ Data found in AWS database")

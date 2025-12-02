"""
Check current evaluation submissions and results after cleanup
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import (
    EvaluationResponse, IrregularEvaluation, EvaluationResult, 
    EvaluationPeriod, UserProfile, User
)
from django.utils import timezone

print("\n" + "=" * 80)
print("CURRENT EVALUATION STATE")
print("=" * 80)

# Check active period
print("\n1️⃣ ACTIVE EVALUATION PERIOD:")
print("-" * 80)
try:
    active_period = EvaluationPeriod.objects.get(is_active=True)
    print(f"✅ {active_period.name} (ID: {active_period.id})")
    print(f"   Type: {active_period.evaluation_type}")
    print(f"   Start: {active_period.start_date}")
    print(f"   End: {active_period.end_date}")
except EvaluationPeriod.DoesNotExist:
    print("❌ No active period!")
    active_period = None

# Check completed periods
print("\n2️⃣ COMPLETED PERIODS:")
print("-" * 80)
completed = EvaluationPeriod.objects.filter(
    is_active=False,
    end_date__lte=timezone.now()
).order_by('-end_date')[:3]
if completed.exists():
    for period in completed:
        print(f"   - {period.name} (ID: {period.id}) - Ended: {period.end_date}")
else:
    print("   No completed periods")

# Check evaluation responses
print("\n3️⃣ EVALUATION RESPONSES:")
print("-" * 80)
responses = EvaluationResponse.objects.all().order_by('-submitted_at')
if responses.exists():
    print(f"Found {responses.count()} response(s):")
    for resp in responses:
        print(f"\n   ID {resp.id}:")
        print(f"   - Evaluator: {resp.evaluator.username} (Section: {resp.student_section})")
        print(f"   - Evaluatee: {resp.evaluatee.username}")
        print(f"   - Period: {resp.evaluation_period.name}")
        print(f"   - Submitted: {resp.submitted_at}")
else:
    print("   ❌ No responses found")

# Check irregular evaluations
print("\n4️⃣ IRREGULAR EVALUATIONS:")
print("-" * 80)
irregulars = IrregularEvaluation.objects.all().order_by('-submitted_at')
if irregulars.exists():
    print(f"Found {irregulars.count()} irregular evaluation(s):")
    for irreg in irregulars:
        print(f"\n   ID {irreg.id}:")
        print(f"   - Evaluator: {irreg.evaluator.username}")
        print(f"   - Evaluatee: {irreg.evaluatee.username}")
        print(f"   - Period: {irreg.evaluation_period.name}")
        print(f"   - Submitted: {irreg.submitted_at}")
else:
    print("   ❌ No irregular evaluations found")

# Check evaluation results
print("\n5️⃣ EVALUATION RESULTS:")
print("-" * 80)
results = EvaluationResult.objects.all().order_by('-calculated_at')
if results.exists():
    print(f"Found {results.count()} result(s):")
    for result in results:
        section_name = result.section.code if result.section else "No Section"
        print(f"\n   ID {result.id}:")
        print(f"   - Evaluatee: {result.user.username}")
        print(f"   - Section: {section_name}")
        print(f"   - Period: {result.evaluation_period.name}")
        print(f"   - Score: {result.total_percentage}%")
        print(f"   - Responses: {result.total_responses}")
        print(f"   - Calculated: {result.calculated_at}")
else:
    print("   ❌ No results found")

# Check C405 section students
print("\n6️⃣ C405 SECTION STUDENTS:")
print("-" * 80)
c405_students = User.objects.filter(
    userprofile__section__code='C405',
    userprofile__role='Student'
)
if c405_students.exists():
    print(f"Found {c405_students.count()} C405 student(s):")
    for user in c405_students:
        profile = user.userprofile
        print(f"   - {user.username} (Student #{profile.studentnumber}, Irregular: {profile.is_irregular})")
else:
    print("   ❌ No C405 students found")

print("\n" + "=" * 80)
print("DIAGNOSTIC SUMMARY")
print("=" * 80)

if not responses.exists() and not irregulars.exists():
    print("\n⚠️ NO EVALUATIONS SUBMITTED YET")
    print("   Please submit evaluations first before checking results.")
elif not results.exists():
    print("\n⚠️ EVALUATIONS EXIST BUT NOT PROCESSED")
    print("   You need to click 'Unrelease Student Evaluation' to process them into results.")
else:
    print("\n✅ System has evaluations and results")

print("=" * 80 + "\n")

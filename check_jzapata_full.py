from django.contrib.auth.models import User
from main.models import (EvaluationResponse, IrregularEvaluation, EvaluationResult, 
                         UserProfile, SectionAssignment, EvaluationPeriod)

user = User.objects.get(username='jzapata')

print("=" * 80)
print(f"EVALUATION DATA FOR: {user.username}")
print("=" * 80)

profile = user.userprofile
print(f"\nRole: {profile.role}")
print(f"Institute: {profile.institute}")

# Check assigned sections
print(f"\n📚 ASSIGNED SECTIONS:")
sections = SectionAssignment.objects.filter(user=user)
print(f"Total: {sections.count()}")
for sec in sections:
    print(f"  - {sec.section.code} (Year {sec.section.year_level})")

# Check evaluation responses received
print(f"\n📊 EVALUATION RESPONSES RECEIVED (as evaluatee):")
responses = EvaluationResponse.objects.filter(evaluatee=user)
print(f"Total: {responses.count()}")
for resp in responses:
    print(f"  - From: {resp.evaluator.username} | Section: {resp.student_section} | Period: {resp.evaluation_period} | Date: {resp.submitted_at}")

# Check irregular evaluations
print(f"\n📊 IRREGULAR EVALUATIONS RECEIVED:")
irregular = IrregularEvaluation.objects.filter(evaluatee=user)
print(f"Total: {irregular.count()}")

# Check processed results (what shows in profile settings)
print(f"\n📈 EVALUATION RESULTS (processed for profile display):")
results = EvaluationResult.objects.filter(user=user)
print(f"Total: {results.count()}")
if results.exists():
    for result in results:
        section = result.section.code if result.section else "No Section"
        print(f"  - Section: {section}")
        print(f"    Total: {result.total_percentage}%")
        print(f"    Responses: {result.total_responses}")
        print(f"    Period: {result.evaluation_period}")
        print(f"    Categories: A={result.category_a_score}%, B={result.category_b_score}%, C={result.category_c_score}%, D={result.category_d_score}%")
else:
    print("  ❌ No processed results found")
    print("\n  💡 Results are only visible after:")
    print("     1. Students submit evaluations")
    print("     2. Admin clicks 'Unrelease' to close the evaluation period")
    print("     3. System processes responses into EvaluationResult table")

# Check active periods
print(f"\n📅 CURRENT EVALUATION PERIODS:")
student_period = EvaluationPeriod.objects.filter(evaluation_type='student', is_active=True).first()
peer_period = EvaluationPeriod.objects.filter(evaluation_type='peer', is_active=True).first()
print(f"Student Evaluation: {'🟢 Active - ' + student_period.name if student_period else '🔴 Inactive'}")
print(f"Peer Evaluation: {'🟢 Active - ' + peer_period.name if peer_period else '🔴 Inactive'}")

print("\n" + "=" * 80)

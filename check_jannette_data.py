from django.contrib.auth.models import User
from main.models import EvaluationResponse, IrregularEvaluation, EvaluationResult, UserProfile

# Find Jannette Zapata
users = User.objects.filter(username__icontains='jannette')
if not users.exists():
    users = User.objects.filter(first_name__icontains='jannette')
if not users.exists():
    users = User.objects.filter(last_name__icontains='zapata')

print("=" * 80)
print("JANNETTE ZAPATA - EVALUATION DATA CHECK")
print("=" * 80)

if users.exists():
    user = users.first()
    print(f"\n✅ Found user: {user.username} (ID: {user.id})")
    print(f"   Name: {user.first_name} {user.last_name}")
    print(f"   Email: {user.email}")
    
    try:
        profile = user.userprofile
        print(f"   Role: {profile.role}")
        print(f"   Institute: {profile.institute}")
    except:
        print("   ⚠️ No profile found")
    
    # Check EvaluationResponse (regular student evaluations)
    print(f"\n📊 EVALUATION RESPONSES (as evaluatee):")
    responses = EvaluationResponse.objects.filter(evaluatee=user)
    print(f"   Total: {responses.count()}")
    for resp in responses[:5]:
        print(f"   - From: {resp.evaluator.username} | Section: {resp.student_section} | Date: {resp.submitted_at}")
    
    # Check IrregularEvaluation
    print(f"\n📊 IRREGULAR EVALUATIONS (as evaluatee):")
    irregular = IrregularEvaluation.objects.filter(evaluatee=user)
    print(f"   Total: {irregular.count()}")
    for irr in irregular[:5]:
        print(f"   - From: {irr.evaluator.username} | Date: {irr.submitted_at}")
    
    # Check EvaluationResult (processed results visible in profile)
    print(f"\n📈 EVALUATION RESULTS (processed for profile view):")
    results = EvaluationResult.objects.filter(user=user)
    print(f"   Total: {results.count()}")
    for result in results[:5]:
        section = result.section.code if result.section else "N/A"
        print(f"   - Section: {section} | Total: {result.total_percentage}% | Responses: {result.total_responses} | Period: {result.evaluation_period}")
    
    # Check peer evaluation responses
    print(f"\n👥 PEER EVALUATION RESPONSES (staff evaluating this user):")
    peer_responses = EvaluationResponse.objects.filter(
        evaluatee=user,
        student_section__icontains="Staff"
    )
    print(f"   Total: {peer_responses.count()}")
    for resp in peer_responses[:5]:
        print(f"   - From: {resp.evaluator.username} | Date: {resp.submitted_at}")
    
else:
    print("\n❌ User not found. Searching all users with 'zapata':")
    all_users = User.objects.filter(last_name__icontains='zapata')
    for u in all_users:
        print(f"   - {u.username} | {u.first_name} {u.last_name}")

print("\n" + "=" * 80)

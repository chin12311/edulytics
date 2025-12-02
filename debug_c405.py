"""
Debug script to check C405 section evaluation data
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import (
    EvaluationResponse, EvaluationResult, EvaluationPeriod, 
    Section, SectionAssignment, User
)

print("=" * 70)
print("DEBUGGING C405 SECTION EVALUATIONS")
print("=" * 70)

# Check if C405 section exists
print("\n1️⃣ CHECKING SECTION C405:")
try:
    section_c405 = Section.objects.get(code='C405')
    print(f"   ✅ Section found: {section_c405.code}")
    print(f"      ID: {section_c405.id}")
    print(f"      Year Level: {section_c405.year_level}")
except Section.DoesNotExist:
    print("   ❌ Section C405 not found in database!")
    section_c405 = None

# Check for evaluation responses with C405
print("\n2️⃣ CHECKING EVALUATION RESPONSES:")
c405_responses = EvaluationResponse.objects.filter(student_section='C405')
print(f"   Total responses for C405: {c405_responses.count()}")

if c405_responses.exists():
    # Group by evaluatee (instructor)
    evaluatees = c405_responses.values_list('evaluatee__username', flat=True).distinct()
    print(f"   Instructors evaluated: {list(evaluatees)}")
    
    for username in evaluatees:
        count = c405_responses.filter(evaluatee__username=username).count()
        latest = c405_responses.filter(evaluatee__username=username).order_by('-submitted_at').first()
        print(f"      - {username}: {count} responses (latest: {latest.submitted_at})")

# Check evaluation periods
print("\n3️⃣ CHECKING EVALUATION PERIODS:")
latest_inactive = EvaluationPeriod.objects.filter(
    evaluation_type='student',
    is_active=False
).order_by('-end_date').first()

if latest_inactive:
    print(f"   Latest inactive period: {latest_inactive.name}")
    print(f"      Start: {latest_inactive.start_date}")
    print(f"      End: {latest_inactive.end_date}")
    
    # Check responses in this period
    responses_in_period = c405_responses.filter(
        submitted_at__gte=latest_inactive.start_date,
        submitted_at__lte=latest_inactive.end_date
    )
    print(f"      C405 responses in this period: {responses_in_period.count()}")
else:
    print("   ❌ No inactive periods found")

# Check EvaluationResult table
print("\n4️⃣ CHECKING EVALUATION RESULT TABLE:")
if section_c405:
    c405_results = EvaluationResult.objects.filter(section=section_c405)
    print(f"   Results for C405: {c405_results.count()}")
    
    if c405_results.exists():
        for result in c405_results:
            print(f"      - {result.user.username}: {result.total_percentage}% ({result.total_responses} responses)")
            print(f"        Period: {result.evaluation_period.name}")
    else:
        print("   ⚠️  No results found in EvaluationResult table")
        
        # Check if there should be results
        if c405_responses.exists():
            print("\n   🔍 INVESTIGATION: Responses exist but no results")
            print("      This means responses haven't been processed yet")
            print("      Action needed: Admin should click UNRELEASE to process results")

# Check section assignments
print("\n5️⃣ CHECKING SECTION ASSIGNMENTS:")
if section_c405:
    assignments = SectionAssignment.objects.filter(section=section_c405)
    print(f"   Instructors assigned to C405: {assignments.count()}")
    
    for assignment in assignments:
        print(f"      - {assignment.user.username} ({assignment.user.userprofile.role})")
        
        # Check if they have responses
        user_c405_responses = c405_responses.filter(evaluatee=assignment.user)
        print(f"        Responses: {user_c405_responses.count()}")
        
        # Check if they have results
        user_c405_results = EvaluationResult.objects.filter(
            user=assignment.user,
            section=section_c405
        )
        print(f"        Results in table: {user_c405_results.count()}")

# Summary and recommendations
print("\n" + "=" * 70)
print("💡 DIAGNOSIS:")
print("=" * 70)

if not section_c405:
    print("❌ ISSUE: Section C405 doesn't exist in database")
    print("   FIX: Create the section first")
elif c405_responses.exists() and not EvaluationResult.objects.filter(section=section_c405).exists():
    print("⚠️  ISSUE: Responses exist but haven't been processed")
    print("   FIX: Admin needs to click UNRELEASE button to process results")
    print("        This will create EvaluationResult records that appear in profile")
elif not c405_responses.exists():
    print("⚠️  ISSUE: No evaluation responses for C405")
    print("   FIX: Students need to submit evaluations for this section")
elif EvaluationResult.objects.filter(section=section_c405).exists():
    print("✅ Results exist - Check profile settings implementation")
    print("   Possible issues:")
    print("   - Instructor not viewing correct section")
    print("   - Section assignment missing")
    print("   - Profile view filtering issue")
else:
    print("🤔 Unknown issue - need more investigation")

print("=" * 70)

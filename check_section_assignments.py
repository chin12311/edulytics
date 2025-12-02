"""
Check if C405 students have proper section assignments for evaluation submission
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import User, UserProfile, Section, SectionAssignment
from django.contrib.auth.models import User

print("\n" + "=" * 80)
print("SECTION ASSIGNMENT CHECK FOR C405 STUDENTS")
print("=" * 80)

# Get C405 section
try:
    c405_section = Section.objects.get(code='C405')
    print(f"\n✅ Found Section: {c405_section.code} (ID: {c405_section.id})")
except Section.DoesNotExist:
    print(f"\n❌ Section C405 not found!")
    c405_section = None

if c405_section:
    # Check students
    students = User.objects.filter(
        userprofile__section=c405_section,
        userprofile__role='Student'
    )
    
    print(f"\n📚 C405 STUDENTS ({students.count()} total):")
    print("-" * 80)
    
    for user in students[:5]:  # Show first 5
        profile = user.userprofile
        print(f"\n   Username: {user.username}")
        print(f"   - Profile Section: {profile.section.code if profile.section else 'None'}")
        print(f"   - Student Number: {profile.studentnumber}")
        print(f"   - Is Irregular: {profile.is_irregular}")
        print(f"   - Role: {profile.role}")
        
        # Check if they have SectionAssignment
        assignments = SectionAssignment.objects.filter(
            user=user,
            section=c405_section
        )
        if assignments.exists():
            print(f"   - ✅ Has SectionAssignment (Count: {assignments.count()})")
            for assignment in assignments:
                print(f"      Assignment ID: {assignment.id}, Period: {assignment.evaluation_period}")
        else:
            print(f"   - ⚠️ NO SectionAssignment found")

# Check faculty members they can evaluate
print(f"\n\n👨‍🏫 FACULTY MEMBERS AVAILABLE TO EVALUATE:")
print("-" * 80)
faculty = User.objects.filter(
    userprofile__role__in=['Faculty', 'Coordinator', 'Dean']
)[:5]

for fac in faculty:
    profile = fac.userprofile
    print(f"   - {fac.username} ({profile.role}, Institute: {profile.institute})")

print("\n" + "=" * 80)

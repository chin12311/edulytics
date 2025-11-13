"""
Debug script to diagnose student account creation issue.
Run: python manage.py shell < debug_account_creation.py
"""

from django.contrib.auth.models import User
from main.models import UserProfile, Role, Section

print("\n" + "="*80)
print("STUDENT ACCOUNT CREATION DEBUG")
print("="*80)

# Check all students in database
print("\n1. All Students in Database:")
print("-" * 80)
students = UserProfile.objects.filter(role=Role.STUDENT)
print(f"Total students found: {students.count()}")
for student in students:
    print(f"  - {student.user.username} ({student.user.email})")
    print(f"    Display Name: {student.display_name}")
    print(f"    Student Number: {student.studentnumber}")
    print(f"    Course: {student.course}")
    print(f"    Section: {student.section}")
    print(f"    Role: {student.role}")
    print()

# Check database constraints
print("\n2. Checking Database Constraints:")
print("-" * 80)
try:
    # Try to find any student without proper fields
    invalid_students = UserProfile.objects.filter(
        role=Role.STUDENT
    ).filter(
        studentnumber__isnull=True
    ) | UserProfile.objects.filter(
        role=Role.STUDENT
    ).filter(
        course__isnull=True
    )
    
    if invalid_students.exists():
        print("⚠️ WARNING: Found students with missing required fields:")
        for student in invalid_students:
            print(f"  - {student.user.username}: StudentNum={student.studentnumber}, Course={student.course}")
    else:
        print("✅ All students have required fields (studentnumber and course)")
except Exception as e:
    print(f"❌ Error checking constraints: {e}")

# Check non-students with student fields
print("\n3. Checking Non-Students with Student Fields:")
print("-" * 80)
try:
    non_students_with_fields = UserProfile.objects.exclude(
        role=Role.STUDENT
    ).filter(
        studentnumber__isnull=False
    ) | UserProfile.objects.exclude(
        role=Role.STUDENT
    ).filter(
        course__isnull=False
    ) | UserProfile.objects.exclude(
        role=Role.STUDENT
    ).filter(
        section__isnull=False
    )
    
    if non_students_with_fields.exists():
        print("⚠️ WARNING: Found non-students with student fields:")
        for profile in non_students_with_fields:
            print(f"  - {profile.user.username} ({profile.role})")
            print(f"    StudentNum={profile.studentnumber}, Course={profile.course}, Section={profile.section}")
    else:
        print("✅ All non-students correctly have no student fields")
except Exception as e:
    print(f"❌ Error checking non-students: {e}")

# Test creating a new student
print("\n4. Testing Student Account Creation:")
print("-" * 80)
try:
    test_user = User.objects.create_user(
        username=f"test_student_{User.objects.count()}",
        email="test.student@cca.edu.ph",
        password="TestPass123!"
    )
    print(f"✅ Created test user: {test_user.username}")
    
    section = Section.objects.first()
    if not section:
        print("⚠️ No sections in database - creating test section")
        section = Section.objects.create(code="TEST101", year_level="1st Year")
    
    test_profile = UserProfile(
        user=test_user,
        display_name="Test Student",
        studentnumber="21-9999",
        course="Test Course",
        section=section,
        role=Role.STUDENT
    )
    
    print(f"Created profile object (not saved yet)")
    test_profile.full_clean()
    print(f"✅ Validation passed")
    
    test_profile.save(skip_validation=True)
    print(f"✅ Profile saved successfully")
    
    # Verify it appears in the list
    verify = UserProfile.objects.filter(user=test_user).first()
    if verify:
        print(f"✅ Profile retrieved from database: {verify}")
    else:
        print(f"❌ Profile NOT found in database after saving!")
    
    # Cleanup
    test_user.delete()
    print(f"✅ Cleaned up test data")
    
except Exception as e:
    print(f"❌ Error during test creation: {e}")
    import traceback
    traceback.print_exc()
    if test_user:
        test_user.delete()

print("\n" + "="*80)
print("DEBUG COMPLETE")
print("="*80 + "\n")

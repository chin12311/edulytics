import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import Institute, Course

def seed_data():
    """Seed the database with institutes and courses from CCA"""
    
    # Clear existing data
    print("🗑️ Clearing existing institutes and courses...")
    Course.objects.all().delete()
    Institute.objects.all().delete()
    
    # Institute 1: Business and Management
    print("➕ Creating Institute of Business and Management...")
    ibm = Institute.objects.create(
        name="Institute of Business and Management",
        code="IBM"
    )
    
    ibm_courses = [
        "Bachelor of Science in Accountancy",
        "Bachelor of Science in Entrepreneurship",
        "Bachelor of Science in Tourism Management"
    ]
    
    for course_name in ibm_courses:
        Course.objects.create(name=course_name, institute=ibm)
        print(f"  ✅ {course_name}")
    
    # Institute 2: Computing Studies and Library Information Science
    print("\n➕ Creating Institute of Computing Studies and Library Information Science...")
    icslis = Institute.objects.create(
        name="Institute of Computing Studies and Library Information Science",
        code="ICSLIS"
    )
    
    icslis_courses = [
        "Associate in Computer Technology (2-year program)",
        "Bachelor of Science in Computer Science",
        "Bachelor of Science in Information Systems",
        "Bachelor of Library and Information Science"
    ]
    
    for course_name in icslis_courses:
        Course.objects.create(name=course_name, institute=icslis)
        print(f"  ✅ {course_name}")
    
    # Institute 3: Education, Arts and Sciences
    print("\n➕ Creating Institute of Education, Arts and Sciences...")
    ieas = Institute.objects.create(
        name="Institute of Education, Arts and Sciences",
        code="IEAS"
    )
    
    ieas_courses = [
        "Bachelor of Physical Education",
        "Bachelor of Technical-Vocational Teacher Education",
        "Bachelor of Arts in English Language Studies",
        "Bachelor in Special Needs Education",
        "Bachelor of Science in Psychology",
        "Bachelor of Science in Mathematics"
    ]
    
    for course_name in ieas_courses:
        Course.objects.create(name=course_name, institute=ieas)
        print(f"  ✅ {course_name}")
    
    print("\n✅ Successfully seeded 3 institutes and 13 courses!")
    
    # Summary
    print("\n📊 Summary:")
    print(f"Total Institutes: {Institute.objects.count()}")
    print(f"Total Courses: {Course.objects.count()}")
    
    for institute in Institute.objects.all():
        print(f"\n{institute.name} ({institute.code}):")
        for course in institute.courses.all():
            print(f"  - {course.name}")

if __name__ == '__main__':
    seed_data()

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import Course, Institute

# Get institutes
icslis = Institute.objects.get(code='ICSLIS')
ibm = Institute.objects.get(code='IBM')
ieas = Institute.objects.get(code='IEAS')

# New courses to add
new_courses = [
    {
        'name': 'Bachelor of Science in Accountancy',
        'code': 'BSA',
        'institute': ibm
    },
    {
        'name': 'Bachelor of Science in Business Administration',
        'code': 'BSBA',
        'institute': ibm
    },
    {
        'name': 'Bachelor of Secondary Education',
        'code': 'BSED',
        'institute': ieas
    },
    {
        'name': 'Bachelor of Elementary Education',
        'code': 'BEED',
        'institute': ieas
    }
]

print("Adding new courses to database...")
for course_data in new_courses:
    course, created = Course.objects.get_or_create(
        name=course_data['name'],
        institute=course_data['institute'],
        defaults={'code': course_data['code']}
    )
    if created:
        print(f"✓ Created: {course.name} ({course.code}) - {course.institute.name}")
    else:
        print(f"• Already exists: {course.name} ({course.code}) - {course.institute.name}")

print("\nDone! New courses added to database.")
print("\nAll courses in database:")
for course in Course.objects.all().order_by('institute__name', 'name'):
    print(f"  - {course.name} ({course.code}) - {course.institute.name}")

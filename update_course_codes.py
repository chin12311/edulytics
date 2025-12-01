import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import Course

# Update courses with their codes
course_code_mapping = {
    'Bachelor of Science in Accountancy': 'BSA',
    'Bachelor of Science in Business Administration': 'BSBA',
    'Bachelor of Secondary Education': 'BSED',
    'Bachelor of Elementary Education': 'BEED',
    'Bachelor of Science in Computer Science': 'BSCS',
    'Bachelor of Science in Information Systems': 'BSIS',
    'Associate in Computer Technology (2-year program)': 'ACT',
    'Bachelor of Library and Information Science': 'BLIS',
    'Bachelor of Science in Entrepreneurship': 'BSE',
    'Bachelor of Science in Tourism Management': 'BSTM',
    'Bachelor in Special Needs Education': 'BSNED',
    'Bachelor of Arts in English Language Studies': 'BAELS',
    'Bachelor of Physical Education': 'BPE',
    'Bachelor of Science in Mathematics': 'BSM',
    'Bachelor of Science in Psychology': 'BSP',
    'Bachelor of Technical-Vocational Teacher Education': 'BTVTED'
}

print("Updating course codes...")
for course_name, code in course_code_mapping.items():
    courses = Course.objects.filter(name=course_name)
    for course in courses:
        if not course.code or course.code != code:
            course.code = code
            course.save()
            print(f"✓ Updated: {course.name} → {code}")
        else:
            print(f"• Already set: {course.name} → {code}")

print("\nDone! All course codes updated.")
print("\nCurrent courses in database:")
for course in Course.objects.all().order_by('institute__name', 'name'):
    print(f"  - {course.name} ({course.code}) - {course.institute.name}")

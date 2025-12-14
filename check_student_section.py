from django.contrib.auth.models import User
from main.models import UserProfile, Role, SectionAssignment

student = User.objects.filter(userprofile__role='Student').first()
if student:
    print(f'Student: {student.username}')
    profile = student.userprofile
    if profile.section:
        print(f'Section: {profile.section.name}')
        coords = SectionAssignment.objects.filter(
            section=profile.section, 
            assigned_user__userprofile__role='Coordinator'
        )
        print(f'Coordinators: {coords.count()}')
        for c in coords:
            print(f'  - {c.assigned_user.username}')
    else:
        print('ERROR: Student has no section assigned!')
else:
    print('No student found')

from django.contrib.auth.models import User
from main.models import UserProfile, Role, SectionAssignment, Section

# Get C405 section
section = Section.objects.get(code='C405')
print(f'Section: {section}')

# Check all section assignments
print('\n=== All Section Assignments for C405 ===')
assignments = SectionAssignment.objects.filter(section=section)
print(f'Total: {assignments.count()}')
for a in assignments:
    role = a.assigned_user.userprofile.role if hasattr(a.assigned_user, 'userprofile') else 'No profile'
    print(f'  - {a.assigned_user.username} ({role})')

# Check coordinators specifically
print('\n=== Checking Coordinator Query ===')
print(f'Role.COORDINATOR value: {Role.COORDINATOR}')

# Try with Role enum
coord_assignments = SectionAssignment.objects.filter(
    section=section,
    assigned_user__userprofile__role=Role.COORDINATOR
)
print(f'Coordinators (using Role.COORDINATOR): {coord_assignments.count()}')
for ca in coord_assignments:
    print(f'  - {ca.assigned_user.username}')

# Try with string
coord_assignments2 = SectionAssignment.objects.filter(
    section=section,
    assigned_user__userprofile__role='Coordinator'
)
print(f'Coordinators (using string): {coord_assignments2.count()}')
for ca in coord_assignments2:
    print(f'  - {ca.assigned_user.username}')

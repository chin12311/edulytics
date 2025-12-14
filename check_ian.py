from django.contrib.auth.models import User
from main.models import UserProfile, Role, SectionAssignment, Section

# Check Ian's account
ian = User.objects.filter(username__icontains='ian').first()
if ian:
    print(f'User: {ian.username}')
    profile = ian.userprofile
    print(f'Role: {profile.role}')
    print(f'Section: {profile.section}')
    
    if profile.section:
        print(f'Section code: {profile.section.code}')
        
        # Check section assignments
        print('\nChecking SectionAssignment...')
        assignments = SectionAssignment.objects.filter(section=profile.section)
        print(f'Total assignments in section: {assignments.count()}')
        
        # Try the exact query from the view
        print('\nTrying exact query from view...')
        try:
            coord_assignments = SectionAssignment.objects.filter(
                section=profile.section,
                assigned_user__userprofile__role=Role.COORDINATOR
            )
            print(f'Coordinator assignments: {coord_assignments.count()}')
            for ca in coord_assignments:
                print(f'  - {ca.assigned_user.username}')
        except Exception as e:
            print(f'Error in coordinator query: {e}')
            import traceback
            traceback.print_exc()
            
        # Try alternative query
        print('\nTrying alternative query...')
        coord_assignments2 = SectionAssignment.objects.filter(
            section=profile.section,
            assigned_user__userprofile__role='Coordinator'
        )
        print(f'Coordinator assignments (string): {coord_assignments2.count()}')
else:
    print('Ian not found')

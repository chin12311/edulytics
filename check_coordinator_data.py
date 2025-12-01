import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import SectionAssignment, IrregularEvaluation, UserProfile

# Find coordinators
coordinators = UserProfile.objects.filter(role='coordinator')
print(f"\n=== Found {coordinators.count()} Coordinators ===")

for profile in coordinators:
    user = profile.user
    print(f"\nCoordinator: {user.username}")
    
    # Check sections
    assignments = SectionAssignment.objects.filter(user=user)
    print(f"  Assigned Sections: {assignments.count()}")
    for assignment in assignments:
        print(f"    - {assignment.section.code}")
    
    # Check irregular evaluations
    irregular = IrregularEvaluation.objects.filter(evaluatee=user)
    print(f"  Irregular Evaluations received: {irregular.count()}")
    if irregular.count() > 0:
        for ie in irregular:
            print(f"    - From: {ie.evaluator.username}")

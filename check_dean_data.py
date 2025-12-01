#!/usr/bin/env python3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import SectionAssignment, EvaluationResponse, IrregularEvaluation

print("=" * 60)
print("DEAN ACCOUNT CHECK")
print("=" * 60)

# Find dean users
deans = User.objects.filter(userprofile__role='Dean')
print(f"\nTotal Dean accounts: {deans.count()}")

for dean in deans:
    print(f"\n{'=' * 60}")
    print(f"Dean: {dean.username} ({dean.email})")
    print(f"{'=' * 60}")
    
    # Check section assignments
    assignments = SectionAssignment.objects.filter(user=dean)
    print(f"\nAssigned Sections: {assignments.count()}")
    for assignment in assignments[:5]:
        print(f"  - {assignment.section.code} ({assignment.section.get_year_level_display()} Year)")
    
    # Check evaluations
    print(f"\nEvaluation Data:")
    print(f"  Regular Evaluations: {EvaluationResponse.objects.filter(evaluatee=dean).count()}")
    print(f"  Irregular Evaluations: {IrregularEvaluation.objects.filter(evaluatee=dean).count()}")
    
    # Show irregular details if any
    irregulars = IrregularEvaluation.objects.filter(evaluatee=dean)
    if irregulars.exists():
        print("\n  Irregular Evaluation Details:")
        for irr in irregulars:
            print(f"    - From {irr.evaluator.username} (Period: {irr.evaluation_period.name})")

print("\n" + "=" * 60)

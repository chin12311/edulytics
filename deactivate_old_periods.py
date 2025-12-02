import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import EvaluationPeriod
from django.utils import timezone

print("Deactivating old active periods...")

# Deactivate all active student periods
student_active = EvaluationPeriod.objects.filter(
    evaluation_type='student',
    is_active=True
)
print(f"\nFound {student_active.count()} active student period(s):")
for p in student_active:
    print(f"  - {p.name} (ID: {p.id}, Created: {p.created_at})")

if student_active.exists():
    student_active.update(is_active=False, end_date=timezone.now())
    print("✅ Deactivated all student periods")

# Deactivate all active peer periods
peer_active = EvaluationPeriod.objects.filter(
    evaluation_type='peer',
    is_active=True
)
print(f"\nFound {peer_active.count()} active peer period(s):")
for p in peer_active:
    print(f"  - {p.name} (ID: {p.id}, Created: {p.created_at})")

if peer_active.exists():
    peer_active.update(is_active=False, end_date=timezone.now())
    print("✅ Deactivated all peer periods")

print("\n✅ Done! Now click Release on edulytics.uk to create a new period with timestamp.")

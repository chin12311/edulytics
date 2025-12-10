import os
import django

os.chdir(r'c:\Users\ADMIN\eval\evaluation')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edulytics.settings')
django.setup()

from main.models import EvaluationPeriod

print("=" * 60)
print("PEER EVALUATION PERIODS CHECK")
print("=" * 60)

peer_periods = EvaluationPeriod.objects.filter(evaluation_type='peer')
print(f"\nTotal peer evaluation periods: {peer_periods.count()}\n")

if peer_periods.exists():
    for period in peer_periods:
        print(f"ID: {period.id}")
        print(f"Name: {period.name}")
        print(f"Active: {period.is_active}")
        print(f"Start Date: {period.start_date}")
        print(f"End Date: {period.end_date}")
        print("-" * 60)
else:
    print("❌ NO PEER EVALUATION PERIODS FOUND!")
    print("\nTo create one, you need to:")
    print("1. Go to the admin panel as a Dean")
    print("2. Navigate to Evaluation Management")
    print("3. Create a new period with evaluation_type='peer'")

print("\n" + "=" * 60)
print("ALL EVALUATION PERIODS")
print("=" * 60)

all_periods = EvaluationPeriod.objects.all()
print(f"\nTotal evaluation periods: {all_periods.count()}\n")

for period in all_periods:
    print(f"ID: {period.id} | Name: {period.name} | Type: {period.evaluation_type} | Active: {period.is_active}")

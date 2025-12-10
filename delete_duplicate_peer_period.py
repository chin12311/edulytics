from main.models import EvaluationPeriod

# Find and delete the duplicate peer period
duplicate = EvaluationPeriod.objects.filter(
    name="Peer Evaluation December 2025",
    evaluation_type='peer'
).first()

if duplicate:
    print(f"Found duplicate period: {duplicate.name} (ID: {duplicate.id})")
    duplicate.delete()
    print("✅ Deleted duplicate peer evaluation period")
else:
    print("No duplicate period found")

# Show current peer periods
print("\n📅 Current Peer Evaluation Periods:")
peer_periods = EvaluationPeriod.objects.filter(evaluation_type='peer').order_by('-start_date')[:5]
for period in peer_periods:
    status = "🟢 ACTIVE" if period.is_active else "🔴 INACTIVE"
    print(f"  {status} | {period.name} | ID: {period.id}")

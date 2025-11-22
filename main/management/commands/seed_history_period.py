from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone

from main.models import EvaluationPeriod, EvaluationResult


class Command(BaseCommand):
    help = "Create an extra completed evaluation period and seed results so the history page shows multiple entries."

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Seed only for this username (optional).')
        parser.add_argument('--name', type=str, help='Custom period name (optional).')
        parser.add_argument('--month-offset', type=int, default=2, help='Months back for start/end dates (default: 2).')

    def handle(self, *args, **options):
        User = get_user_model()

        username = options.get('username')
        custom_name = options.get('name')
        month_offset = options.get('month_offset') or 2

        now = timezone.now()

        # Compute a past month window for the period
        # Approximate months by 30 days
        start = now - timezone.timedelta(days=(month_offset * 30 + 30))
        end = now - timezone.timedelta(days=(month_offset * 30))

        period_name = custom_name or f"Evaluation {start.strftime('%Y-%m')}"

        period, created = EvaluationPeriod.objects.get_or_create(
            name=period_name,
            defaults={
                'evaluation_type': 'student',
                'start_date': start,
                'end_date': end,
                'is_active': False
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created evaluation period: {period.name} ({period.start_date.date()} - {period.end_date.date()})"))
        else:
            self.stdout.write(self.style.WARNING(f"Using existing period: {period.name}"))

        # Determine target users
        targets = []
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError(f"User '{username}' not found")
            targets = [user]
        else:
            # Users who already have at least one EvaluationResult (ensures the page will show multiple entries)
            user_ids = (EvaluationResult.objects
                        .values_list('user_id', flat=True)
                        .distinct())
            targets = list(User.objects.filter(id__in=user_ids))

        if not targets:
            self.stdout.write(self.style.WARNING("No target users with existing results. Nothing to seed."))
            return

        created_count = 0
        skipped = 0

        for user in targets:
            # Skip if this user already has a result for this period
            if EvaluationResult.objects.filter(user=user, evaluation_period=period).exists():
                skipped += 1
                continue

            # Seed a plausible result without requiring raw responses
            # Values are illustrative; the history page will display them and the by-period API will show no-data for sections/peer if absent
            seeded = EvaluationResult.objects.create(
                user=user,
                evaluation_period=period,
                section=None,
                category_a_score=88.0,
                category_b_score=82.0,
                category_c_score=86.0,
                category_d_score=90.0,
                total_percentage=86.5,
                average_rating=round(86.5/20, 2),
                total_responses=12,
                poor_count=0,
                unsatisfactory_count=1,
                satisfactory_count=2,
                very_satisfactory_count=5,
                outstanding_count=4,
                calculated_at=timezone.now()
            )

            created_count += 1
            self.stdout.write(self.style.SUCCESS(f"Seeded result for {user.username}: {seeded.total_percentage}%"))

        self.stdout.write(self.style.SUCCESS(f"Done. Created {created_count} result(s), skipped {skipped}."))

from django.core.management.base import BaseCommand
from main.models import AdminActivityLog
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Deletes admin activity logs older than 7 days.'

    def handle(self, *args, **kwargs):
        cutoff = timezone.now() - timedelta(days=7)
        deleted, _ = AdminActivityLog.objects.filter(timestamp__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted} old admin activity logs.'))

from django.core.management.base import BaseCommand
from main.services.evaluation_service import EvaluationService

class Command(BaseCommand):
    help = 'Process evaluation failures after evaluation period ends'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--evaluation-type',
            default='student',
            help='Evaluation type to process (student or peer)'
        )
    
    def handle(self, *args, **options):
        evaluation_type = options['evaluation_type']
        
        self.stdout.write(f"🔄 Processing evaluation failures for {evaluation_type} evaluations...")
        
        EvaluationService.process_failures_after_evaluation_period(evaluation_type)
        
        self.stdout.write(
            self.style.SUCCESS('✅ Evaluation failures processed successfully!')
        )
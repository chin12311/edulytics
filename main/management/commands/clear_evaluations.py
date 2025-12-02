"""
Management command to clear all evaluation data and start fresh
Usage: python manage.py clear_evaluations
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import (
    EvaluationHistory, EvaluationResponse, EvaluationResult, 
    IrregularEvaluation, AiRecommendation, EvaluationPeriod
)


class Command(BaseCommand):
    help = 'Clear all evaluation data to start fresh'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-periods',
            action='store_true',
            help='Keep evaluation periods (only delete responses and results)',
        )
        parser.add_argument(
            '--yes',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        keep_periods = options['keep_periods']
        skip_confirm = options['yes']
        
        # Show what will be deleted
        self.stdout.write(self.style.WARNING('\n=== EVALUATION DATA TO BE DELETED ==='))
        self.stdout.write(f'Evaluation Histories: {EvaluationHistory.objects.count()}')
        self.stdout.write(f'Evaluation Responses: {EvaluationResponse.objects.count()}')
        self.stdout.write(f'Evaluation Results: {EvaluationResult.objects.count()}')
        self.stdout.write(f'Irregular Evaluations: {IrregularEvaluation.objects.count()}')
        self.stdout.write(f'AI Recommendations: {AiRecommendation.objects.count()}')
        
        if not keep_periods:
            self.stdout.write(f'Evaluation Periods: {EvaluationPeriod.objects.count()}')
        else:
            self.stdout.write(self.style.NOTICE('Evaluation Periods: WILL BE KEPT'))
        
        # Confirmation
        if not skip_confirm:
            self.stdout.write(self.style.ERROR('\n⚠️  WARNING: This action cannot be undone!'))
            confirm = input('\nType "DELETE" to confirm: ')
            if confirm != 'DELETE':
                self.stdout.write(self.style.ERROR('Cancelled.'))
                return
        
        # Delete data
        try:
            with transaction.atomic():
                self.stdout.write('\n=== DELETING DATA ===')
                
                # Delete evaluation histories
                history_count = EvaluationHistory.objects.count()
                EvaluationHistory.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Deleted {history_count} evaluation histories'))
                
                # Delete evaluation responses
                response_count = EvaluationResponse.objects.count()
                EvaluationResponse.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Deleted {response_count} evaluation responses'))
                
                # Delete evaluation results
                result_count = EvaluationResult.objects.count()
                EvaluationResult.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Deleted {result_count} evaluation results'))
                
                # Delete irregular evaluations
                irregular_count = IrregularEvaluation.objects.count()
                IrregularEvaluation.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Deleted {irregular_count} irregular evaluations'))
                
                # Delete AI recommendations
                ai_count = AiRecommendation.objects.count()
                AiRecommendation.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Deleted {ai_count} AI recommendations'))
                
                # Delete evaluation periods (optional)
                if not keep_periods:
                    period_count = EvaluationPeriod.objects.count()
                    EvaluationPeriod.objects.all().delete()
                    self.stdout.write(self.style.SUCCESS(f'✓ Deleted {period_count} evaluation periods'))
                
                self.stdout.write(self.style.SUCCESS('\n✅ All evaluation data cleared successfully!'))
                self.stdout.write(self.style.NOTICE('\nYou can now start fresh with new evaluations.'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error: {str(e)}'))
            raise

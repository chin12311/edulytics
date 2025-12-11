from main.models import EvaluationPeriod

def evaluation_context(request):
    """
    Context processor to make evaluation status available in all templates
    """
    upward_evaluation_active = EvaluationPeriod.objects.filter(
        evaluation_type='upward',
        is_active=True
    ).exists()
    
    return {
        'upward_evaluation_active': upward_evaluation_active
    }

from main.models import EvaluationPeriod, Evaluation

def evaluation_context(request):
    """
    Context processor to make evaluation status available in all templates
    """
    # Check if there's both an active upward evaluation period AND a released evaluation
    upward_evaluation_active = False
    
    active_period = EvaluationPeriod.objects.filter(
        evaluation_type='upward',
        is_active=True
    ).first()
    
    if active_period:
        # Check if there's a released evaluation linked to this period
        upward_evaluation_active = Evaluation.objects.filter(
            evaluation_type='upward',
            evaluation_period=active_period,
            is_released=True
        ).exists()
    
    return {
        'upward_evaluation_active': upward_evaluation_active
    }

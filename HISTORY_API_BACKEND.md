# Backend API Endpoints for Evaluation History

## File: main/views.py

Add these functions to your views.py file:

```python
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import EvaluationHistory, UserProfile, Role
from django.utils import timezone
import json

@login_required
@require_http_methods(["GET"])
def api_evaluation_history(request):
    """
    API endpoint to get all evaluation history records for logged-in user
    GET /api/evaluation-history/
    
    Returns: List of evaluation history periods with summary data
    """
    try:
        user = request.user
        
        # Get all evaluation history records for this user
        history_records = EvaluationHistory.objects.filter(
            user=user
        ).select_related(
            'evaluation_period'
        ).order_by(
            '-archived_at'  # Most recent first
        )
        
        # Serialize the data
        history_data = []
        for record in history_records:
            history_data.append({
                'id': record.id,
                'evaluation_period_id': record.evaluation_period.id,
                'evaluation_period_name': record.evaluation_period.name,
                'evaluation_type': record.evaluation_period.evaluation_type,
                'period_start_date': record.period_start_date.isoformat(),
                'period_end_date': record.period_end_date.isoformat(),
                'archived_at': record.archived_at.isoformat(),
                'total_percentage': float(record.total_percentage or 0),
                'total_responses': record.total_responses or 0,
                'average_rating': float(record.average_rating or 0),
            })
        
        return JsonResponse({
            'success': True,
            'history_records': history_data,
            'count': len(history_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching evaluation history: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_evaluation_history_detail(request, history_id):
    """
    API endpoint to get detailed data for a specific evaluation history record
    GET /api/evaluation-history/{id}/
    
    Returns: Detailed evaluation results for that period
    """
    try:
        user = request.user
        
        # Get the specific history record
        history_record = EvaluationHistory.objects.select_related(
            'evaluation_period',
            'user'
        ).get(
            id=history_id,
            user=user
        )
        
        # Serialize detailed data
        detail_data = {
            'id': history_record.id,
            'evaluation_period_name': history_record.evaluation_period.name,
            'evaluation_period_id': history_record.evaluation_period.id,
            'evaluation_type': history_record.evaluation_period.evaluation_type,
            'period_start_date': history_record.period_start_date.isoformat(),
            'period_end_date': history_record.period_end_date.isoformat(),
            'archived_at': history_record.archived_at.isoformat(),
            
            # Scores
            'total_percentage': float(history_record.total_percentage or 0),
            'category_a_score': float(history_record.category_a_score or 0),
            'category_b_score': float(history_record.category_b_score or 0),
            'category_c_score': float(history_record.category_c_score or 0),
            'category_d_score': float(history_record.category_d_score or 0),
            
            # Response counts
            'total_responses': history_record.total_responses or 0,
            'average_rating': float(history_record.average_rating or 0),
            
            # Rating distribution
            'poor_count': history_record.poor_count or 0,
            'unsatisfactory_count': history_record.unsatisfactory_count or 0,
            'satisfactory_count': history_record.satisfactory_count or 0,
            'very_satisfactory_count': history_record.very_satisfactory_count or 0,
            'outstanding_count': history_record.outstanding_count or 0,
        }
        
        return JsonResponse({
            'success': True,
            'data': detail_data
        })
        
    except EvaluationHistory.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Evaluation history record not found'
        }, status=404)
        
    except Exception as e:
        logger.error(f"Error fetching evaluation history detail: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
```

---

## File: main/urls.py

Add these URL patterns to your urls.py:

```python
# Add to your urlpatterns list:

path('api/evaluation-history/', api_evaluation_history, name='api_evaluation_history'),
path('api/evaluation-history/<int:history_id>/', api_evaluation_history_detail, name='api_evaluation_history_detail'),
```

---

## Full Context Example

In your main/urls.py, it should look like:

```python
from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    # ... existing patterns ...
    
    # Evaluation History API endpoints
    path('api/evaluation-history/', views.api_evaluation_history, name='api_evaluation_history'),
    path('api/evaluation-history/<int:history_id>/', views.api_evaluation_history_detail, name='api_evaluation_history_detail'),
    
    # ... other patterns ...
]
```

---

## API Response Examples

### GET /api/evaluation-history/

```json
{
  "success": true,
  "history_records": [
    {
      "id": 1,
      "evaluation_period_id": 3,
      "evaluation_period_name": "Student Evaluation October 2025",
      "evaluation_type": "student",
      "period_start_date": "2025-10-01T00:00:00Z",
      "period_end_date": "2025-10-31T23:59:59Z",
      "archived_at": "2025-10-31T15:45:00Z",
      "total_percentage": 87.5,
      "total_responses": 50,
      "average_rating": 4.2
    },
    {
      "id": 2,
      "evaluation_period_id": 2,
      "evaluation_period_name": "Student Evaluation September 2025",
      "evaluation_type": "student",
      "period_start_date": "2025-09-01T00:00:00Z",
      "period_end_date": "2025-09-30T23:59:59Z",
      "archived_at": "2025-09-30T14:30:00Z",
      "total_percentage": 85.2,
      "total_responses": 48,
      "average_rating": 4.1
    }
  ],
  "count": 2
}
```

### GET /api/evaluation-history/1/

```json
{
  "success": true,
  "data": {
    "id": 1,
    "evaluation_period_name": "Student Evaluation October 2025",
    "evaluation_period_id": 3,
    "evaluation_type": "student",
    "period_start_date": "2025-10-01T00:00:00Z",
    "period_end_date": "2025-10-31T23:59:59Z",
    "archived_at": "2025-10-31T15:45:00Z",
    "total_percentage": 87.5,
    "category_a_score": 32.5,
    "category_b_score": 24.0,
    "category_c_score": 19.5,
    "category_d_score": 19.0,
    "total_responses": 50,
    "average_rating": 4.2,
    "poor_count": 2,
    "unsatisfactory_count": 5,
    "satisfactory_count": 15,
    "very_satisfactory_count": 18,
    "outstanding_count": 10
  }
}
```

---

## Testing the APIs

### Using curl:

```bash
# Get all history records
curl -X GET http://localhost:8000/api/evaluation-history/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID"

# Get specific record
curl -X GET http://localhost:8000/api/evaluation-history/1/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

### Using browser:

Just navigate to:
- `http://localhost:8000/api/evaluation-history/`
- `http://localhost:8000/api/evaluation-history/1/`

(You must be logged in)

---

## Notes

- Both endpoints require authentication (`@login_required`)
- User can only see their own evaluation history
- Data is ordered by archived date (most recent first)
- All dates are in ISO 8601 format
- Scores are returned as floats
- Category scores: A=35, B=25, C=20, D=20

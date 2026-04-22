from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone

from data_app.models import Alert, Metric


@login_required
def overview_api(request):
    end_at = timezone.now()
    start_at = end_at - timedelta(hours=24)
    metrics = Metric.objects.filter(user=request.user, timestamp__range=(start_at, end_at))
    alerts = Alert.objects.filter(user=request.user, timestamp__range=(start_at, end_at))
    return JsonResponse(
        {
            "metrics_count": metrics.count(),
            "alerts_count": alerts.count(),
            "max_ppi": max([m.ppi for m in metrics], default=0),
            "max_contact_area": max([m.contact_area_pct for m in metrics], default=0),
        }
    )

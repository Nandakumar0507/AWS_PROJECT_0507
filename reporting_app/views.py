from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.shortcuts import render
from django.utils import timezone

from data_app.models import Alert, Metric


@login_required
def reports_view(request):
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)

    today_metrics = Metric.objects.filter(user=request.user, timestamp__gte=today_start)
    yesterday_metrics = Metric.objects.filter(user=request.user, timestamp__range=(yesterday_start, today_start))

    context = {
        "today_avg_ppi": today_metrics.aggregate(v=Avg("ppi"))["v"] or 0,
        "yesterday_avg_ppi": yesterday_metrics.aggregate(v=Avg("ppi"))["v"] or 0,
        "today_avg_contact": today_metrics.aggregate(v=Avg("contact_area_pct"))["v"] or 0,
        "yesterday_avg_contact": yesterday_metrics.aggregate(v=Avg("contact_area_pct"))["v"] or 0,
        "today_alerts": Alert.objects.filter(user=request.user, timestamp__gte=today_start)[:20],
    }
    return render(request, "reports.html", context)

import json
import statistics
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from analytics_app.services import contact_area_pct, peak_pressure_index, severity_for_ppi
from auth_app.decorators import roles_required
from auth_app.models import PatientProfile, Role

from .models import Alert, Comment, Metric, Reply, SensorData

User = get_user_model()


def _visible_user_ids(request):
    if request.user.role == Role.ADMIN:
        return None
    if request.user.role == Role.CLINICIAN:
        return list(request.user.assigned_patients.values_list("user_id", flat=True))
    return [request.user.id]


def _resolve_target_user_id(request):
    allowed = _visible_user_ids(request)
    requested = request.GET.get("user_id")
    if not requested:
        return request.user.id, allowed, None
    try:
        target_user_id = int(requested)
    except ValueError:
        return None, allowed, JsonResponse({"error": "Invalid user_id."}, status=400)
    if allowed is not None and target_user_id not in allowed:
        return None, allowed, JsonResponse({"error": "Unauthorized."}, status=403)
    return target_user_id, allowed, None


@login_required
def dashboard_view(request):
    return render(request, "dashboard.html")


@login_required
def dashboard_context_api(request):
    allowed = _visible_user_ids(request)
    if allowed is None:
        patient_profiles = PatientProfile.objects.select_related("user").order_by("user__email")
    else:
        patient_profiles = PatientProfile.objects.select_related("user").filter(user_id__in=allowed).order_by("user__email")

    users = [
        {"id": profile.user.id, "email": profile.user.email, "name": profile.user.display_name or profile.user.username}
        for profile in patient_profiles
    ]
    now = timezone.now()
    recent_window = now - timedelta(hours=24)
    monitored_ids = [u["id"] for u in users]
    context_payload = {
        "role": request.user.role,
        "users": users,
        "default_user_id": users[0]["id"] if users else request.user.id,
        "kpi_total_patients": len(users),
        "kpi_alerts_24h": Alert.objects.filter(user_id__in=monitored_ids, timestamp__gte=recent_window).count()
        if monitored_ids
        else 0,
        "kpi_comments_24h": Comment.objects.filter(user_id__in=monitored_ids, timestamp__gte=recent_window).count()
        if monitored_ids
        else 0,
    }
    return JsonResponse(context_payload)


@login_required
def sensor_summary_api(request):
    user_id, _, error = _resolve_target_user_id(request)
    if error:
        return error

    hours = int(request.GET.get("hours", 1))
    end_at = timezone.now()
    start_at = end_at - timedelta(hours=hours)

    sensor_data = SensorData.objects.filter(user_id=user_id, timestamp__range=(start_at, end_at)).order_by("timestamp")
    metrics = Metric.objects.filter(user_id=user_id, timestamp__range=(start_at, end_at)).order_by("timestamp")
    alerts = Alert.objects.filter(user_id=user_id, timestamp__range=(start_at, end_at)).order_by("-timestamp")[:100]

    using_fallback_window = False
    if not metrics.exists():
        using_fallback_window = True
        metrics = Metric.objects.filter(user_id=user_id).order_by("-timestamp")[:240]
        metrics = sorted(metrics, key=lambda item: item.timestamp)
    if not sensor_data.exists():
        sensor_data = SensorData.objects.filter(user_id=user_id).order_by("-timestamp")[:1]
    if not alerts:
        alerts = Alert.objects.filter(user_id=user_id).order_by("-timestamp")[:100]

    latest_matrix = sensor_data[0].matrix_data if sensor_data else [[0] * 32 for _ in range(32)]
    metrics_list = list(metrics)
    ppi_values = [item.ppi for item in metrics_list]
    contact_values = [item.contact_area_pct for item in metrics_list]
    latest_ppi = ppi_values[-1] if ppi_values else 0
    latest_contact = contact_values[-1] if contact_values else 0
    risk_series = []
    for item in metrics_list:
        risk_score = min(100, round((item.ppi / 4095) * 100, 2))
        risk_series.append({"t": item.timestamp.isoformat(), "v": risk_score})
    ppi_stdev = statistics.pstdev(ppi_values) if len(ppi_values) > 1 else 0
    posture_stability_score = round(max(0, 100 - (ppi_stdev / 30)), 2)

    return JsonResponse(
        {
            "heatmap": latest_matrix,
            "ppi_series": [{"t": item.timestamp.isoformat(), "v": item.ppi} for item in metrics_list],
            "contact_series": [{"t": item.timestamp.isoformat(), "v": item.contact_area_pct} for item in metrics_list],
            "risk_series": risk_series,
            "alerts": [{"t": item.timestamp.isoformat(), "severity": item.severity, "message": item.message} for item in alerts],
            "kpis": {
                "latest_ppi": round(latest_ppi, 2),
                "latest_contact": round(latest_contact, 2),
                "avg_ppi": round((sum(ppi_values) / len(ppi_values)), 2) if ppi_values else 0,
                "avg_contact": round((sum(contact_values) / len(contact_values)), 2) if contact_values else 0,
                "alerts_total": len(alerts),
                "alerts_high": sum(1 for item in alerts if item.severity == Alert.Severity.HIGH),
                "posture_stability_score": posture_stability_score,
                "comments_total": Comment.objects.filter(user_id=user_id).count(),
            },
            "using_fallback_window": using_fallback_window,
        }
    )


@login_required
def comments_api(request):
    if request.method == "GET":
        user_id, _, error = _resolve_target_user_id(request)
        if error:
            return error
        comments = Comment.objects.filter(user_id=user_id).select_related("user").prefetch_related("replies")[:200]
        payload = []
        for comment in comments:
            payload.append(
                {
                    "id": comment.id,
                    "timestamp": comment.timestamp.isoformat(),
                    "comment_text": comment.comment_text,
                    "replies": [
                        {"id": reply.id, "reply_text": reply.reply_text, "created_at": reply.created_at.isoformat()}
                        for reply in comment.replies.all()
                    ],
                }
            )
        return JsonResponse({"items": payload})

    data = json.loads(request.body.decode("utf-8"))
    Comment.objects.create(user=request.user, timestamp=timezone.now(), comment_text=data.get("comment_text", "").strip())
    return JsonResponse({"status": "ok"})


@login_required
@roles_required(Role.CLINICIAN, Role.ADMIN)
def reply_api(request, comment_id):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.user.role == Role.CLINICIAN and not PatientProfile.objects.filter(
        user=comment.user, assigned_clinician=request.user
    ).exists():
        return JsonResponse({"error": "Unauthorized."}, status=403)

    data = json.loads(request.body.decode("utf-8"))
    Reply.objects.create(clinician=request.user, comment=comment, reply_text=data.get("reply_text", "").strip())
    return JsonResponse({"status": "ok"})


@login_required
def recalc_latest_metric_api(request):
    sample = SensorData.objects.filter(user=request.user).order_by("-timestamp").first()
    if not sample:
        return JsonResponse({"status": "skipped"})
    ppi = peak_pressure_index(sample.matrix_data)
    contact = contact_area_pct(sample.matrix_data)
    severity = severity_for_ppi(ppi)
    Metric.objects.update_or_create(
        user=request.user, timestamp=sample.timestamp, defaults={"ppi": ppi, "contact_area_pct": contact}
    )
    if severity in {"MEDIUM", "HIGH"}:
        Alert.objects.create(
            user=request.user, timestamp=sample.timestamp, severity=severity, message=f"Pressure risk level: {severity}"
        )
    return JsonResponse({"status": "ok", "ppi": ppi, "contact_area_pct": contact, "severity": severity})

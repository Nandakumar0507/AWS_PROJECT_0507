from django.urls import path

from . import views

app_name = "data_app"

urlpatterns = [
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("api/context/", views.dashboard_context_api, name="context_api"),
    path("api/summary/", views.sensor_summary_api, name="summary_api"),
    path("api/comments/", views.comments_api, name="comments_api"),
    path("api/comments/<int:comment_id>/reply/", views.reply_api, name="reply_api"),
    path("api/recalculate/", views.recalc_latest_metric_api, name="recalculate_api"),
]

from django.urls import path

from .views import reports_view

app_name = "reporting_app"

urlpatterns = [path("", reports_view, name="reports")]

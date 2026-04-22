from django.urls import path

from .views import overview_api

app_name = "analytics_app"

urlpatterns = [path("api/overview/", overview_api, name="overview_api")]

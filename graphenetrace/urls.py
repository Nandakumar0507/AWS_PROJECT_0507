from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("auth_app.urls")),
    path("data/", include("data_app.urls")),
    path("analytics/", include("analytics_app.urls")),
    path("reports/", include("reporting_app.urls")),
]

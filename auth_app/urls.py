from django.urls import path

from . import views

app_name = "auth_app"

urlpatterns = [
    path("landing/", views.landing_view, name="landing"),
    path("", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("users/create/", views.create_user_view, name="create_user"),
    path("patients/<int:patient_id>/assign/", views.assign_patient_view, name="assign_patient"),
]

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import roles_required
from .forms import LoginForm, ProfileUpdateForm, SignUpForm, UserCreateForm
from .models import PatientProfile, Role

User = get_user_model()


def landing_view(request):
    return render(request, "landing.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("data_app:dashboard")

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = authenticate(request, email=form.cleaned_data["email"], password=form.cleaned_data["password"])
        if user:
            login(request, user)
            return redirect("data_app:dashboard")
        messages.error(request, "Invalid login credentials.")
    return render(request, "auth/login.html", {"form": form})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("data_app:dashboard")

    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.role = Role.PATIENT
        user.set_password(form.cleaned_data["password"])
        user.save()
        PatientProfile.objects.get_or_create(user=user)
        messages.success(request, "Account created successfully. Please sign in.")
        return redirect("auth_app:login")
    return render(request, "auth/signup.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("auth_app:login")


@login_required
def profile_view(request):
    form = ProfileUpdateForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("auth_app:profile")
    return render(request, "auth/profile.html", {"form": form})


@login_required
@roles_required(Role.ADMIN)
def create_user_view(request):
    form = UserCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password"])
        user.save()
        if user.role == Role.PATIENT:
            PatientProfile.objects.get_or_create(user=user)
        messages.success(request, "User created successfully.")
        return redirect("auth_app:create_user")
    clinicians = User.objects.filter(role=Role.CLINICIAN).order_by("email")
    patients = PatientProfile.objects.select_related("user", "assigned_clinician").order_by("user__email")
    return render(request, "auth/create_user.html", {"form": form, "clinicians": clinicians, "patients": patients})


@login_required
@roles_required(Role.ADMIN)
def assign_patient_view(request, patient_id):
    patient = get_object_or_404(PatientProfile, pk=patient_id)
    clinician_id = request.POST.get("clinician_id")
    clinician = get_object_or_404(User, pk=clinician_id, role=Role.CLINICIAN)
    patient.assigned_clinician = clinician
    patient.save(update_fields=["assigned_clinician"])
    messages.success(request, "Patient assignment updated.")
    return redirect("auth_app:create_user")

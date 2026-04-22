from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class Role(models.TextChoices):
    PATIENT = "PATIENT", "Patient"
    CLINICIAN = "CLINICIAN", "Clinician"
    ADMIN = "ADMIN", "Admin"


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=16, choices=Role.choices)
    display_name = models.CharField(max_length=120, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.email} ({self.role})"


class ClinicianProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="clinician_profile")
    specialization = models.CharField(max_length=120, blank=True)

    def clean(self):
        if self.user.role != Role.CLINICIAN:
            raise ValidationError("Clinician profile can only be attached to clinician users.")


class PatientProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="patient_profile")
    date_of_birth = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    assigned_clinician = models.ForeignKey(
        CustomUser, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_patients"
    )

    def clean(self):
        if self.user.role != Role.PATIENT:
            raise ValidationError("Patient profile can only be attached to patient users.")
        if self.assigned_clinician and self.assigned_clinician.role != Role.CLINICIAN:
            raise ValidationError("Assigned clinician must have clinician role.")

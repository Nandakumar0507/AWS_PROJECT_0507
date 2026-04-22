import csv
from datetime import timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from analytics_app.services import contact_area_pct, peak_pressure_index
from auth_app.models import PatientProfile, Role
from data_app.models import Alert, Comment, Metric, Reply, SensorData

User = get_user_model()


class Command(BaseCommand):
    help = "Create demo patient/clinician users and populate recent non-zero data from CSV."

    def add_arguments(self, parser):
        parser.add_argument("--data-dir", type=str, default="GTLB-Data")
        parser.add_argument("--max-frames", type=int, default=180)

    def _read_matrices(self, data_dir: Path):
        files = sorted(data_dir.glob("*.csv"))
        if not files:
            files = sorted(data_dir.glob("**/*.csv"))
        if not files:
            raise CommandError(f"No CSV files found under {data_dir}")

        selected_file = files[0]
        with selected_file.open("r", encoding="utf-8") as handle:
            rows = [list(map(int, row)) for row in csv.reader(handle) if row]
        if len(rows) < 32:
            raise CommandError("CSV appears empty or corrupt for 32x32 frame extraction.")

        matrices = []
        for i in range(0, len(rows), 32):
            matrix = rows[i : i + 32]
            if len(matrix) == 32 and all(len(r) == 32 for r in matrix):
                matrices.append(matrix)
        if not matrices:
            raise CommandError("No valid 32x32 frames found in CSV.")
        return selected_file.name, matrices

    def handle(self, *args, **options):
        data_dir = Path(options["data_dir"])
        if not data_dir.exists():
            raise CommandError(f"Data directory not found: {data_dir}")

        filename, matrices = self._read_matrices(data_dir)
        max_frames = max(20, options["max_frames"])
        step = max(1, len(matrices) // max_frames)
        sampled = matrices[::step][:max_frames]

        patient_email = "patient.demo@graphenetrace.local"
        clinician_email = "doctor.demo@graphenetrace.local"
        admin_email = "admin.demo@graphenetrace.local"
        default_password = "Demo@12345"

        patient, _ = User.objects.get_or_create(
            email=patient_email,
            defaults={"username": "patient_demo", "display_name": "Demo Patient", "role": Role.PATIENT},
        )
        patient.role = Role.PATIENT
        patient.username = "patient_demo"
        patient.display_name = "Demo Patient"
        patient.set_password(default_password)
        patient.save()

        clinician, _ = User.objects.get_or_create(
            email=clinician_email,
            defaults={"username": "doctor_demo", "display_name": "Dr. Maya Chen", "role": Role.CLINICIAN},
        )
        clinician.role = Role.CLINICIAN
        clinician.username = "doctor_demo"
        clinician.display_name = "Dr. Maya Chen"
        clinician.set_password(default_password)
        clinician.save()

        admin, _ = User.objects.get_or_create(
            email=admin_email,
            defaults={
                "username": "admin_demo",
                "display_name": "Demo Admin",
                "role": Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.role = Role.ADMIN
        admin.username = "admin_demo"
        admin.display_name = "Demo Admin"
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password(default_password)
        admin.save()

        patient_profile, _ = PatientProfile.objects.get_or_create(user=patient)
        patient_profile.assigned_clinician = clinician
        patient_profile.notes = f"Demo profile seeded from {filename}"
        patient_profile.save()

        # Also assign a few existing patient profiles to demo clinician for richer clinician demo.
        other_profiles = PatientProfile.objects.exclude(user=patient).order_by("id")[:3]
        for profile in other_profiles:
            profile.assigned_clinician = clinician
            profile.save(update_fields=["assigned_clinician"])

        Reply.objects.filter(comment__user=patient).delete()
        Comment.objects.filter(user=patient).delete()
        Alert.objects.filter(user=patient).delete()
        Metric.objects.filter(user=patient).delete()
        SensorData.objects.filter(user=patient).delete()

        start_ts = timezone.now() - timedelta(minutes=len(sampled))
        high_alert_count = 0
        for idx, matrix in enumerate(sampled):
            ts = start_ts + timedelta(minutes=idx)
            SensorData.objects.create(user=patient, timestamp=ts, matrix_data=matrix)
            ppi = peak_pressure_index(matrix)
            contact = contact_area_pct(matrix)
            Metric.objects.create(user=patient, timestamp=ts, ppi=ppi, contact_area_pct=contact)

            if ppi > 2200 and idx % 18 == 0:
                severity = Alert.Severity.HIGH if ppi > 3200 else Alert.Severity.MEDIUM
                Alert.objects.create(
                    user=patient,
                    timestamp=ts,
                    severity=severity,
                    message="Sustained pressure detected in sacral region. Reposition within 20 minutes.",
                )
                if severity == Alert.Severity.HIGH:
                    high_alert_count += 1

        if not Alert.objects.filter(user=patient).exists():
            Alert.objects.create(
                user=patient,
                timestamp=timezone.now() - timedelta(minutes=5),
                severity=Alert.Severity.MEDIUM,
                message="Localized pressure elevated. Increase micro-shifts every 15 minutes.",
            )

        c1 = Comment.objects.create(
            user=patient,
            timestamp=timezone.now() - timedelta(minutes=34),
            comment_text="Lower back discomfort started after a long meeting.",
        )
        c2 = Comment.objects.create(
            user=patient,
            timestamp=timezone.now() - timedelta(minutes=12),
            comment_text="Tried a cushion and pressure felt more balanced.",
        )
        Reply.objects.create(
            clinician=clinician,
            comment=c1,
            reply_text="Thanks for reporting. Please perform a 2-minute posture reset every 25 minutes today.",
        )
        Reply.objects.create(
            clinician=clinician,
            comment=c2,
            reply_text="Great improvement. Keep using the cushion and monitor afternoon trend.",
        )

        self.stdout.write(self.style.SUCCESS("Demo users and patient timeline seeded successfully."))
        self.stdout.write(f"Patient login: {patient_email} / {default_password}")
        self.stdout.write(f"Clinician login: {clinician_email} / {default_password}")
        self.stdout.write(f"Admin login: {admin_email} / {default_password}")

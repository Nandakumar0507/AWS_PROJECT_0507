import csv
from datetime import datetime, timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from analytics_app.services import contact_area_pct, high_pressure_sustained, peak_pressure_index, severity_for_ppi
from auth_app.models import PatientProfile, Role
from data_app.models import Alert, Metric, SensorData

User = get_user_model()


class Command(BaseCommand):
    help = "Load 32x32 pressure CSV files from GTLB-Data folder."

    def add_arguments(self, parser):
        parser.add_argument("--data-dir", type=str, default="GTLB-Data")

    def handle(self, *args, **options):
        data_dir = Path(options["data_dir"])
        if not data_dir.exists():
            raise CommandError(f"Data directory not found: {data_dir}")

        files = sorted(data_dir.glob("*.csv"))
        if not files:
            raise CommandError("No CSV files found.")

        for file_path in files:
            user_token, date_token = file_path.stem.split("_")
            user, _ = User.objects.get_or_create(
                email=f"{user_token}@graphenetrace.local",
                defaults={"username": user_token, "role": Role.PATIENT, "display_name": user_token},
            )
            if user.role != Role.PATIENT:
                continue
            PatientProfile.objects.get_or_create(user=user)
            base_ts = timezone.make_aware(datetime.strptime(date_token, "%Y%m%d"))

            with file_path.open("r", encoding="utf-8") as handle:
                rows = [list(map(int, row)) for row in csv.reader(handle) if row]

            if len(rows) % 32 != 0:
                self.stderr.write(self.style.WARNING(f"Skipping corrupt file {file_path.name}: rows not divisible by 32"))
                continue

            frames = []
            for i in range(0, len(rows), 32):
                matrix = rows[i : i + 32]
                if len(matrix) != 32 or any(len(r) != 32 for r in matrix):
                    continue
                ts = base_ts + timedelta(seconds=(i // 32))
                SensorData.objects.update_or_create(user=user, timestamp=ts, defaults={"matrix_data": matrix})
                ppi = peak_pressure_index(matrix)
                contact = contact_area_pct(matrix)
                Metric.objects.update_or_create(user=user, timestamp=ts, defaults={"ppi": ppi, "contact_area_pct": contact})
                frames.append(matrix)

            if high_pressure_sustained(frames):
                ppi_max = max((peak_pressure_index(frame) for frame in frames), default=0)
                severity = severity_for_ppi(ppi_max)
                Alert.objects.create(
                    user=user,
                    timestamp=base_ts,
                    severity=severity,
                    message="Sustained high pressure detected. You were sitting unevenly for a prolonged period.",
                )
            self.stdout.write(self.style.SUCCESS(f"Imported {file_path.name}"))

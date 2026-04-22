from django.conf import settings
from django.db import models


class SensorData(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sensor_data")
    timestamp = models.DateTimeField(db_index=True)
    matrix_data = models.JSONField()

    class Meta:
        ordering = ["-timestamp"]
        indexes = [models.Index(fields=["user", "timestamp"])]


class Metric(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="metrics")
    timestamp = models.DateTimeField(db_index=True)
    ppi = models.FloatField()
    contact_area_pct = models.FloatField()

    class Meta:
        ordering = ["-timestamp"]
        indexes = [models.Index(fields=["user", "timestamp"])]


class Alert(models.Model):
    class Severity(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alerts")
    timestamp = models.DateTimeField(db_index=True)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    message = models.CharField(max_length=255)

    class Meta:
        ordering = ["-timestamp"]


class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    timestamp = models.DateTimeField(db_index=True)
    comment_text = models.TextField()

    class Meta:
        ordering = ["-timestamp"]


class Reply(models.Model):
    clinician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="replies")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="replies")
    reply_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

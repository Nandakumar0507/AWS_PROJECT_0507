from django.contrib import admin

from .models import Alert, Comment, Metric, Reply, SensorData

admin.site.register(SensorData)
admin.site.register(Metric)
admin.site.register(Alert)
admin.site.register(Comment)
admin.site.register(Reply)

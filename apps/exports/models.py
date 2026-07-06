from django.conf import settings
from django.db import models

class ExportLog(models.Model):
    class Format(models.TextChoices):
        XLSX = 'xlsx', 'Excel'
        PDF = 'pdf', 'PDF'

    created_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    format = models.CharField(max_length=10, choices=Format.choices)
    filters_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

from django.contrib import admin
from .models import NotificationLog

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('application', 'recipient_email', 'type', 'status', 'created_at')
    list_filter = ('type', 'status')

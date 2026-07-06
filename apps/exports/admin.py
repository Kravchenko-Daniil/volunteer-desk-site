from django.contrib import admin
from .models import ExportLog

@admin.register(ExportLog)
class ExportLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'format', 'created_by_user', 'created_at')
    list_filter = ('format',)

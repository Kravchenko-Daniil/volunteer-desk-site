from django.contrib import admin
from .models import Application, ApplicationAction, SubmissionAttempt
from .services import log_action

class ApplicationActionInline(admin.TabularInline):
    model = ApplicationAction
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'applicant_full_name', 'district', 'status', 'assigned_volunteer')
    list_filter = ('status', 'district', 'assigned_volunteer', 'created_from')
    search_fields = ('applicant_full_name', 'applicant_email')
    inlines = [ApplicationActionInline]
    readonly_fields = (
        'status',
        'assigned_volunteer',
        'accepted_at',
        'rejected_at',
        'completed_at',
        'completion_comment',
        'created_at',
        'updated_at',
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by_user = request.user
            obj.created_from = Application.CreatedFrom.ADMIN_PANEL
        super().save_model(request, obj, form, change)
        if not change:
            log_action(obj, ApplicationAction.Action.CREATED, user=request.user, comment='Заявка создана в Django Admin')

@admin.register(ApplicationAction)
class ApplicationActionAdmin(admin.ModelAdmin):
    list_display = ('application', 'action', 'changed_by_user', 'assigned_volunteer', 'created_at')
    list_filter = ('action',)


@admin.register(SubmissionAttempt)
class SubmissionAttemptAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'created_at', 'was_blocked', 'was_honeypot')
    list_filter = ('was_blocked', 'was_honeypot', 'created_at')
    search_fields = ('ip_address', 'user_agent')
    readonly_fields = ('ip_address', 'user_agent', 'was_blocked', 'was_honeypot', 'created_at')

    def has_add_permission(self, request):
        return False

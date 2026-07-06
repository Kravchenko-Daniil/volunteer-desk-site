from .models import ApplicationAction


def log_action(
    application,
    action,
    *,
    user=None,
    old_status='',
    new_status='',
    assigned_volunteer=None,
    comment='',
):
    return ApplicationAction.objects.create(
        application=application,
        action=action,
        changed_by_user=user if getattr(user, 'is_authenticated', False) else None,
        old_status=old_status or '',
        new_status=new_status or '',
        assigned_volunteer=assigned_volunteer,
        comment=comment,
    )


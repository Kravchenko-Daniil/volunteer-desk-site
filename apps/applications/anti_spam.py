from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import SubmissionAttempt


def register_submission_attempt(*, ip_address, user_agent='', honeypot=False):
    now = timezone.now()
    blocked = False

    if ip_address and not honeypot:
        attempts = SubmissionAttempt.objects.filter(ip_address=ip_address)
        blocked = (
            attempts.filter(created_at__gte=now - timedelta(minutes=10)).count()
            >= settings.RATE_LIMIT_10_MINUTES
            or attempts.filter(created_at__gte=now - timedelta(hours=24)).count()
            >= settings.RATE_LIMIT_24_HOURS
        )

    SubmissionAttempt.objects.create(
        ip_address=ip_address,
        user_agent=(user_agent or '')[:500],
        was_blocked=blocked,
        was_honeypot=honeypot,
    )
    return blocked

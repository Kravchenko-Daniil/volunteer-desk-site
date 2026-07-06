from django.db import models

class NotificationLog(models.Model):
    class Type(models.TextChoices):
        ACCEPTED = 'accepted', 'Заявка принята'
        REJECTED = 'rejected', 'Заявка отклонена'
        COMPLETED = 'completed', 'Заявка выполнена'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает'
        SENT = 'sent', 'Отправлено'
        ERROR = 'error', 'Ошибка'

    application = models.ForeignKey('applications.Application', on_delete=models.CASCADE, related_name='notifications')
    recipient_email = models.EmailField()
    type = models.CharField(max_length=20, choices=Type.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

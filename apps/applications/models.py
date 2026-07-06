from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

class Application(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'Новая'
        ACCEPTED = 'accepted', 'Принята'
        REJECTED = 'rejected', 'Отклонена'
        ASSIGNED = 'assigned', 'Назначена'
        COMPLETED = 'completed', 'Выполнена'

    class CreatedFrom(models.TextChoices):
        PUBLIC_FORM = 'public_form', 'Публичная форма'
        ADMIN_PANEL = 'admin_panel', 'Админ-панель'
        VOLUNTEER_SELF = 'volunteer_self', 'Волонтёр для себя'
        VOLUNTEER_FOR_OTHER = 'volunteer_for_other', 'Волонтёр для другого'

    applicant_full_name = models.CharField('ФИО заявителя', max_length=255)
    applicant_email = models.EmailField('Email заявителя', blank=True)
    district = models.ForeignKey('districts.District', on_delete=models.PROTECT, verbose_name='Район')
    help_description = models.TextField('Описание необходимой помощи')
    people_needed = models.PositiveIntegerField('Количество людей', null=True, blank=True)
    comment = models.TextField('Комментарий', blank=True)
    status = models.CharField('Статус', max_length=20, choices=Status.choices, default=Status.NEW)
    created_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_applications', verbose_name='Кем создана')
    assigned_volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_applications', verbose_name='Назначенный волонтёр')
    created_from = models.CharField('Источник создания', max_length=40, choices=CreatedFrom.choices, default=CreatedFrom.PUBLIC_FORM)
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)
    accepted_at = models.DateTimeField('Принята', null=True, blank=True)
    rejected_at = models.DateTimeField('Отклонена', null=True, blank=True)
    completed_at = models.DateTimeField('Выполнена', null=True, blank=True)
    completion_comment = models.TextField('Комментарий выполнения', blank=True)
    personal_data_agreed = models.BooleanField('Согласие на ПДн', default=False)
    personal_data_agreed_at = models.DateTimeField('Дата согласия', null=True, blank=True)
    personal_data_policy_version = models.CharField('Версия политики ПДн', max_length=50, blank=True)
    applicant_ip = models.GenericIPAddressField('IP', null=True, blank=True)
    user_agent = models.TextField('User-Agent', blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'

    def __str__(self):
        return f'Заявка №{self.pk} — {self.applicant_full_name}'

    def can_transition_to(self, new_status):
        allowed = {
            self.Status.NEW: {self.Status.ACCEPTED, self.Status.REJECTED},
            self.Status.ACCEPTED: {self.Status.ASSIGNED},
            self.Status.REJECTED: set(),
            self.Status.ASSIGNED: {self.Status.COMPLETED},
            self.Status.COMPLETED: set(),
        }
        return new_status in allowed.get(self.status, set())

    def transition_to(self, new_status, *, assigned_volunteer=None, completion_comment=''):
        if not self.can_transition_to(new_status):
            raise ValidationError(
                f'Нельзя изменить статус «{self.get_status_display()}» на «{self.Status(new_status).label}».'
            )

        now = timezone.now()
        self.status = new_status
        update_fields = ['status', 'updated_at']

        if new_status == self.Status.ACCEPTED:
            self.accepted_at = now
            update_fields.append('accepted_at')
        elif new_status == self.Status.REJECTED:
            self.rejected_at = now
            update_fields.append('rejected_at')
        elif new_status == self.Status.ASSIGNED:
            if assigned_volunteer is None or not assigned_volunteer.is_volunteer:
                raise ValidationError('Для назначения нужен активный пользователь с ролью волонтёра.')
            self.assigned_volunteer = assigned_volunteer
            update_fields.append('assigned_volunteer')
        elif new_status == self.Status.COMPLETED:
            if self.assigned_volunteer_id is None:
                raise ValidationError('Нельзя выполнить заявку без назначенного волонтёра.')
            self.completed_at = now
            self.completion_comment = completion_comment
            update_fields.extend(['completed_at', 'completion_comment'])

        self.save(update_fields=update_fields)

class ApplicationAction(models.Model):
    class Action(models.TextChoices):
        CREATED = 'created', 'Создана'
        ACCEPTED = 'accepted', 'Принята'
        REJECTED = 'rejected', 'Отклонена'
        ASSIGNED = 'assigned', 'Назначен волонтёр'
        COMPLETED = 'completed', 'Выполнена'
        PDF_GENERATED = 'pdf_generated', 'PDF сформирован'
        EXPORTED = 'exported', 'Экспортирована'

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='actions', verbose_name='Заявка')
    old_status = models.CharField('Старый статус', max_length=20, blank=True)
    new_status = models.CharField('Новый статус', max_length=20, blank=True)
    action = models.CharField('Действие', max_length=30, choices=Action.choices)
    changed_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Кем выполнено')
    assigned_volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assignment_actions', verbose_name='Волонтёр')
    comment = models.TextField('Комментарий', blank=True)
    created_at = models.DateTimeField('Дата', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'История заявки'
        verbose_name_plural = 'История заявок'


class SubmissionAttempt(models.Model):
    ip_address = models.GenericIPAddressField('IP-адрес', null=True, blank=True, db_index=True)
    user_agent = models.CharField('User-Agent', max_length=500, blank=True)
    was_blocked = models.BooleanField('Заблокирована лимитом', default=False)
    was_honeypot = models.BooleanField('Сработал honeypot', default=False)
    created_at = models.DateTimeField('Дата', auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['ip_address', 'created_at'])]
        verbose_name = 'Попытка отправки заявки'
        verbose_name_plural = 'Попытки отправки заявок'

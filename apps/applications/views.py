import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import (
    ApplicationFilterForm,
    PublicApplicationForm,
    VolunteerForOtherApplicationForm,
    VolunteerSelfApplicationForm,
    get_client_ip,
)
from .models import Application, ApplicationAction
from .anti_spam import register_submission_attempt
from .captcha import verify_captcha
from .selectors import filter_applications
from .services import log_action

User = get_user_model()
logger = logging.getLogger(__name__)

def public_application_create(request):
    captcha_context = {
        'captcha_enabled': settings.CAPTCHA_ENABLED,
        'captcha_site_key': settings.CAPTCHA_SITE_KEY,
    }
    if request.method == 'POST':
        ip_address = get_client_ip(request)
        if request.POST.get('honeypot'):
            register_submission_attempt(
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                honeypot=True,
            )
            logger.warning('Honeypot submission blocked from %s', request.META.get('REMOTE_ADDR', 'unknown'))
            messages.success(request, 'Спасибо! Ваша заявка принята и будет рассмотрена администратором.')
            return redirect('applications:thanks')
        if register_submission_attempt(
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        ):
            form = PublicApplicationForm(request.POST)
            form.add_error(None, 'Слишком много отправок. Попробуйте снова через несколько минут.')
            messages.error(request, 'Превышен лимит отправки заявок.')
            return render(request, 'applications/public_form.html', {'form': form, **captcha_context}, status=429)
        form = PublicApplicationForm(request.POST)
        if form.is_valid():
            if not verify_captcha(request.POST.get('h-captcha-response', ''), ip_address):
                form.add_error(None, 'Подтвердите, что вы не робот.')
                messages.error(request, 'Проверка CAPTCHA не пройдена.')
                return render(request, 'applications/public_form.html', {'form': form, **captcha_context})
            application = form.save(request=request)
            log_action(application, ApplicationAction.Action.CREATED)
            messages.success(request, 'Спасибо! Ваша заявка принята и будет рассмотрена администратором.')
            return redirect('applications:thanks')
        messages.error(request, 'Проверьте обязательные поля формы.')
    else:
        form = PublicApplicationForm()
    return render(request, 'applications/public_form.html', {'form': form, **captcha_context})

def application_thanks(request):
    return render(request, 'applications/thanks.html')

def require_admin(user):
    if not user.is_authenticated or not user.is_project_admin:
        raise PermissionDenied

def require_volunteer(user):
    if not user.is_authenticated or not user.is_volunteer:
        raise PermissionDenied

@login_required
def application_list(request):
    require_admin(request.user)
    qs = Application.objects.select_related('district', 'assigned_volunteer', 'created_by_user')
    form = ApplicationFilterForm(request.GET or None, user_model=User)
    if form.is_valid():
        qs = filter_applications(qs, form.cleaned_data)
    return render(request, 'applications/application_list.html', {'applications': qs, 'filter_form': form})

@login_required
def application_detail(request, pk):
    require_admin(request.user)
    application = get_object_or_404(Application.objects.select_related('district', 'assigned_volunteer', 'created_by_user'), pk=pk)
    volunteers = User.objects.filter(role=User.Role.VOLUNTEER, is_active=True)
    return render(request, 'applications/application_detail.html', {'application': application, 'volunteers': volunteers})

@login_required
@require_POST
def application_accept(request, pk):
    require_admin(request.user)
    with transaction.atomic():
        application = get_object_or_404(Application.objects.select_for_update(), pk=pk)
        old_status = application.status
        try:
            application.transition_to(Application.Status.ACCEPTED)
        except ValidationError as error:
            messages.error(request, error.messages[0])
        else:
            log_action(application, ApplicationAction.Action.ACCEPTED, user=request.user, old_status=old_status, new_status=application.status)
            messages.success(request, 'Заявка принята.')
    return redirect('applications:detail', pk=pk)

@login_required
@require_POST
def application_reject(request, pk):
    require_admin(request.user)
    with transaction.atomic():
        application = get_object_or_404(Application.objects.select_for_update(), pk=pk)
        old_status = application.status
        try:
            application.transition_to(Application.Status.REJECTED)
        except ValidationError as error:
            messages.error(request, error.messages[0])
        else:
            log_action(application, ApplicationAction.Action.REJECTED, user=request.user, old_status=old_status, new_status=application.status)
            messages.success(request, 'Заявка отклонена.')
    return redirect('applications:detail', pk=pk)

@login_required
@require_POST
def application_assign(request, pk):
    require_admin(request.user)
    with transaction.atomic():
        application = get_object_or_404(Application.objects.select_for_update(), pk=pk)
        volunteer = get_object_or_404(User, pk=request.POST.get('volunteer_id'), role=User.Role.VOLUNTEER, is_active=True)
        old_status = application.status
        try:
            application.transition_to(Application.Status.ASSIGNED, assigned_volunteer=volunteer)
        except ValidationError as error:
            messages.error(request, error.messages[0])
        else:
            log_action(application, ApplicationAction.Action.ASSIGNED, user=request.user, old_status=old_status, new_status=application.status, assigned_volunteer=volunteer)
            messages.success(request, 'Волонтёр назначен.')
    return redirect('applications:detail', pk=pk)

@login_required
def volunteer_applications(request):
    require_volunteer(request.user)
    qs = Application.objects.select_related('district').filter(Q(assigned_volunteer=request.user) | Q(created_by_user=request.user)).distinct()
    return render(request, 'applications/volunteer_list.html', {'applications': qs})

@login_required
def volunteer_application_detail(request, pk):
    require_volunteer(request.user)
    application = get_object_or_404(Application.objects.select_related('district', 'assigned_volunteer'), pk=pk)
    if application.assigned_volunteer_id != request.user.id and application.created_by_user_id != request.user.id:
        raise PermissionDenied
    return render(request, 'applications/volunteer_detail.html', {'application': application})

@login_required
@require_POST
def application_complete(request, pk):
    require_volunteer(request.user)
    with transaction.atomic():
        application = get_object_or_404(Application.objects.select_for_update(), pk=pk, assigned_volunteer=request.user)
        old_status = application.status
        completion_comment = request.POST.get('completion_comment', '')
        try:
            application.transition_to(Application.Status.COMPLETED, completion_comment=completion_comment)
        except ValidationError as error:
            messages.error(request, error.messages[0])
        else:
            log_action(application, ApplicationAction.Action.COMPLETED, user=request.user, old_status=old_status, new_status=application.status, comment=completion_comment)
            messages.success(request, 'Заявка отмечена как выполненная.')
    return redirect('applications:volunteer_detail', pk=pk)

@login_required
def volunteer_create_self(request):
    require_volunteer(request.user)
    initial = {'applicant_full_name': request.user.full_name, 'applicant_email': request.user.email}
    if request.method == 'POST':
        form = VolunteerSelfApplicationForm(request.POST, initial=initial)
        if form.is_valid():
            application = form.save(request=request, created_from=Application.CreatedFrom.VOLUNTEER_SELF, created_by_user=request.user)
            log_action(application, ApplicationAction.Action.CREATED, user=request.user)
            messages.success(request, 'Заявка создана.')
            return redirect('applications:volunteer_list')
        messages.error(request, 'Проверьте обязательные поля формы.')
    else:
        form = VolunteerSelfApplicationForm(initial=initial)
    return render(request, 'applications/public_form.html', {'form': form, 'title': 'Создать заявку для себя'})

@login_required
def volunteer_create_for_other(request):
    require_volunteer(request.user)
    if request.method == 'POST':
        form = VolunteerForOtherApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(request=request, created_from=Application.CreatedFrom.VOLUNTEER_FOR_OTHER, created_by_user=request.user)
            log_action(application, ApplicationAction.Action.CREATED, user=request.user, comment='Заявка создана волонтёром для другого человека')
            messages.success(request, 'Заявка для другого человека создана.')
            return redirect('applications:volunteer_list')
        messages.error(request, 'Проверьте обязательные поля и подтверждение согласия.')
    else:
        form = VolunteerForOtherApplicationForm()
    return render(request, 'applications/public_form.html', {'form': form, 'title': 'Создать заявку для другого человека'})

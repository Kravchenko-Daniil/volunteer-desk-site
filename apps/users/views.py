from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import VolunteerCreateForm, VolunteerPasswordForm, VolunteerUpdateForm


User = get_user_model()


def require_admin(user):
    if not user.is_authenticated or not user.is_project_admin:
        raise PermissionDenied


@login_required
def post_login_redirect(request):
    if request.user.is_project_admin:
        return redirect('applications:list')
    if request.user.is_volunteer:
        return redirect('applications:volunteer_list')
    return redirect('core:home')


@login_required
def volunteer_list(request):
    require_admin(request.user)
    volunteers = User.objects.filter(role=User.Role.VOLUNTEER).order_by('-is_active', 'full_name', 'email')
    return render(request, 'users/volunteer_list.html', {'volunteers': volunteers})


@login_required
def volunteer_create(request):
    require_admin(request.user)
    if request.method == 'POST':
        form = VolunteerCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Волонтёр создан.')
            return redirect('users:volunteer_list')
        messages.error(request, 'Проверьте ошибки в форме.')
    else:
        form = VolunteerCreateForm()
    return render(request, 'users/volunteer_form.html', {'form': form, 'title': 'Создать волонтёра'})


@login_required
def volunteer_update(request, pk):
    require_admin(request.user)
    volunteer = get_object_or_404(User, pk=pk, role=User.Role.VOLUNTEER)
    if request.method == 'POST':
        form = VolunteerUpdateForm(request.POST, instance=volunteer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Данные волонтёра обновлены.')
            return redirect('users:volunteer_list')
        messages.error(request, 'Проверьте ошибки в форме.')
    else:
        form = VolunteerUpdateForm(instance=volunteer)
    return render(request, 'users/volunteer_form.html', {'form': form, 'title': 'Редактировать волонтёра'})


@login_required
def volunteer_password(request, pk):
    require_admin(request.user)
    volunteer = get_object_or_404(User, pk=pk, role=User.Role.VOLUNTEER)
    if request.method == 'POST':
        form = VolunteerPasswordForm(volunteer, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Пароль волонтёра изменён.')
            return redirect('users:volunteer_list')
        messages.error(request, 'Проверьте требования к паролю.')
    else:
        form = VolunteerPasswordForm(volunteer)
    return render(request, 'users/volunteer_form.html', {'form': form, 'title': 'Сменить пароль'})


@login_required
@require_POST
def volunteer_toggle_active(request, pk):
    require_admin(request.user)
    volunteer = get_object_or_404(User, pk=pk, role=User.Role.VOLUNTEER)
    volunteer.is_active = not volunteer.is_active
    volunteer.save(update_fields=['is_active'])
    message = 'Волонтёр включён.' if volunteer.is_active else 'Волонтёр отключён.'
    messages.success(request, message)
    return redirect('users:volunteer_list')

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DistrictForm
from .models import District


def require_admin(user):
    if not user.is_project_admin:
        raise PermissionDenied


@login_required
def district_list(request):
    require_admin(request.user)
    return render(request, 'districts/district_list.html', {'districts': District.objects.all()})


@login_required
def district_create(request):
    require_admin(request.user)
    form = DistrictForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Район создан.')
        return redirect('districts:list')
    if request.method == 'POST':
        messages.error(request, 'Проверьте ошибки в форме.')
    return render(request, 'districts/district_form.html', {'form': form, 'title': 'Добавить район'})


@login_required
def district_update(request, pk):
    require_admin(request.user)
    district = get_object_or_404(District, pk=pk)
    form = DistrictForm(request.POST or None, instance=district)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Район обновлён.')
        return redirect('districts:list')
    if request.method == 'POST':
        messages.error(request, 'Проверьте ошибки в форме.')
    return render(request, 'districts/district_form.html', {'form': form, 'title': 'Редактировать район'})


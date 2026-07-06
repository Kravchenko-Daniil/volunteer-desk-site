from django.shortcuts import render

def home(request):
    return render(request, 'core/home.html')

def privacy(request):
    return render(request, 'core/privacy.html')

def personal_data_consent(request):
    return render(request, 'core/personal_data_consent.html')


def permission_denied(request, exception=None):
    return render(request, 'errors/403.html', status=403)

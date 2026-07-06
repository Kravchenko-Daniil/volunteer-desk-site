from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

handler403 = 'apps.core.views.permission_denied'

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('applications/', include('apps.applications.urls')),
    path('exports/', include('apps.exports.urls')),
    path('users/', include('apps.users.urls')),
    path('districts/', include('apps.districts.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

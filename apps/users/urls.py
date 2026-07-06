from django.urls import path

from . import views


app_name = 'users'

urlpatterns = [
    path('after-login/', views.post_login_redirect, name='post_login_redirect'),
    path('volunteers/', views.volunteer_list, name='volunteer_list'),
    path('volunteers/new/', views.volunteer_create, name='volunteer_create'),
    path('volunteers/<int:pk>/edit/', views.volunteer_update, name='volunteer_update'),
    path('volunteers/<int:pk>/password/', views.volunteer_password, name='volunteer_password'),
    path('volunteers/<int:pk>/toggle-active/', views.volunteer_toggle_active, name='volunteer_toggle_active'),
]

from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    path('new/', views.public_application_create, name='public_create'),
    path('thanks/', views.application_thanks, name='thanks'),
    path('admin/', views.application_list, name='list'),
    path('admin/<int:pk>/', views.application_detail, name='detail'),
    path('admin/<int:pk>/accept/', views.application_accept, name='accept'),
    path('admin/<int:pk>/reject/', views.application_reject, name='reject'),
    path('admin/<int:pk>/assign/', views.application_assign, name='assign'),
    path('volunteer/', views.volunteer_applications, name='volunteer_list'),
    path('volunteer/new/self/', views.volunteer_create_self, name='volunteer_create_self'),
    path('volunteer/new/other/', views.volunteer_create_for_other, name='volunteer_create_for_other'),
    path('volunteer/<int:pk>/', views.volunteer_application_detail, name='volunteer_detail'),
    path('volunteer/<int:pk>/complete/', views.application_complete, name='complete'),
]

from django.urls import path

from . import views


app_name = 'districts'

urlpatterns = [
    path('', views.district_list, name='list'),
    path('new/', views.district_create, name='create'),
    path('<int:pk>/edit/', views.district_update, name='update'),
]

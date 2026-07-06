from django.urls import path
from . import views

app_name = 'exports'

urlpatterns = [
    path('applications.xlsx', views.export_applications_xlsx, name='applications_xlsx'),
    path('application/<int:pk>.pdf', views.application_pdf, name='application_pdf'),
]

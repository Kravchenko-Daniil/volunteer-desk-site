from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Администратор'
        VOLUNTEER = 'volunteer', 'Волонтёр'

    full_name = models.CharField('ФИО', max_length=255, blank=True)
    email = models.EmailField('Email', unique=True)
    phone = models.CharField('Телефон', max_length=32, blank=True)
    role = models.CharField('Роль', max_length=20, choices=Role.choices, default=Role.VOLUNTEER)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    @property
    def is_project_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_volunteer(self):
        return self.role == self.Role.VOLUNTEER

    def __str__(self):
        return self.full_name or self.email

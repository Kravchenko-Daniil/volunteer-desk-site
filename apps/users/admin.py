from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class ProjectUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'username', 'full_name', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'username', 'full_name')
    fieldsets = UserAdmin.fieldsets + (
        ('Проект', {'fields': ('full_name', 'phone', 'role')}),
    )

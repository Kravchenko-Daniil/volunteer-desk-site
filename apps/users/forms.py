from django import forms
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import User


class VolunteerCreateForm(forms.Form):
    full_name = forms.CharField(label='ФИО', max_length=255)
    email = forms.EmailField(label='Email')
    phone = forms.CharField(label='Телефон', max_length=32, required=False)
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Повторите пароль', widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password1')
        if password and password != cleaned_data.get('password2'):
            self.add_error('password2', 'Пароли не совпадают.')
        if password:
            try:
                validate_password(password)
            except ValidationError as error:
                self.add_error('password1', error)
        return cleaned_data

    def save(self):
        email = self.cleaned_data['email']
        return User.objects.create_user(
            username=email,
            email=email,
            password=self.cleaned_data['password1'],
            full_name=self.cleaned_data['full_name'],
            phone=self.cleaned_data['phone'],
            role=User.Role.VOLUNTEER,
        )


class VolunteerUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone', 'is_active']

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        user.role = User.Role.VOLUNTEER
        if commit:
            user.save()
        return user


class VolunteerPasswordForm(SetPasswordForm):
    pass


from django import forms
from django.conf import settings
from django.utils import timezone
from apps.districts.models import District
from .models import Application

class PublicApplicationForm(forms.ModelForm):
    applicant_email = forms.EmailField(label='Email заявителя', required=True)
    personal_data_agreed = forms.BooleanField(
        label='Я даю согласие на обработку персональных данных',
        required=True,
    )
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Application
        fields = [
            'applicant_full_name',
            'applicant_email',
            'district',
            'help_description',
            'people_needed',
            'comment',
            'personal_data_agreed',
        ]
        widgets = {
            'help_description': forms.Textarea(attrs={'rows': 5}),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['district'].queryset = District.objects.filter(is_active=True)

    def clean_honeypot(self):
        value = self.cleaned_data.get('honeypot')
        if value:
            raise forms.ValidationError('Ошибка отправки формы.')
        return value

    def save(self, commit=True, request=None, created_from=Application.CreatedFrom.PUBLIC_FORM, created_by_user=None):
        obj = super().save(commit=False)
        obj.status = Application.Status.NEW
        obj.created_from = created_from
        obj.created_by_user = created_by_user
        obj.personal_data_agreed_at = timezone.now()
        obj.personal_data_policy_version = getattr(settings, 'PERSONAL_DATA_POLICY_VERSION', 'draft')
        if request:
            obj.applicant_ip = get_client_ip(request)
            obj.user_agent = request.META.get('HTTP_USER_AGENT', '')
        if commit:
            obj.save()
        return obj

class VolunteerSelfApplicationForm(PublicApplicationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['applicant_full_name'].disabled = True
        self.fields['applicant_email'].disabled = True


class VolunteerForOtherApplicationForm(PublicApplicationForm):
    applicant_email = forms.EmailField(label='Email заявителя (если есть)', required=False)
    personal_data_agreed = forms.BooleanField(
        label='Согласие заявителя на передачу и обработку персональных данных получено',
        required=True,
    )

class ApplicationFilterForm(forms.Form):
    q = forms.CharField(label='ФИО или email', required=False)
    status = forms.ChoiceField(label='Статус', required=False, choices=[('', 'Все статусы')] + list(Application.Status.choices))
    district = forms.ModelChoiceField(label='Район', required=False, queryset=District.objects.filter(is_active=True))
    volunteer = forms.ModelChoiceField(label='Волонтёр', required=False, queryset=None)
    date_from = forms.DateField(label='Дата от', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(label='Дата до', required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        user_model = kwargs.pop('user_model')
        super().__init__(*args, **kwargs)
        self.fields['volunteer'].queryset = user_model.objects.filter(role=user_model.Role.VOLUNTEER, is_active=True)

def get_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if settings.TRUST_X_FORWARDED_FOR and forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

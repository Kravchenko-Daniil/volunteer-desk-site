from django import forms

from .models import District


class DistrictForm(forms.ModelForm):
    class Meta:
        model = District
        fields = ['name', 'sort_order', 'is_active']


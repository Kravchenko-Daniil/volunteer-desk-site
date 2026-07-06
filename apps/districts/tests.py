from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import District


User = get_user_model()


class DistrictInterfaceTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='district-admin',
            email='district-admin@test.local',
            password='DistrictAdmin123!',
            role=User.Role.ADMIN,
        )
        self.client.force_login(self.admin)

    def test_admin_can_create_and_edit_district(self):
        response = self.client.post(reverse('districts:create'), {'name': 'Новый', 'sort_order': 10, 'is_active': 'on'})
        self.assertRedirects(response, reverse('districts:list'))
        district = District.objects.get(name='Новый')
        response = self.client.post(reverse('districts:update', args=[district.pk]), {'name': 'Обновлённый', 'sort_order': 20})
        self.assertRedirects(response, reverse('districts:list'))
        district.refresh_from_db()
        self.assertEqual(district.name, 'Обновлённый')
        self.assertFalse(district.is_active)

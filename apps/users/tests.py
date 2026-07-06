from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class VolunteerManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username='admin-users',
            email='admin-users@test.local',
            password='AdminPassword123!',
            role=User.Role.ADMIN,
        )
        cls.volunteer = User.objects.create_user(
            username='volunteer-users',
            email='volunteer-users@test.local',
            password='VolunteerPassword123!',
            role=User.Role.VOLUNTEER,
            full_name='Исходный волонтёр',
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_admin_can_create_and_edit_volunteer(self):
        response = self.client.post(
            reverse('users:volunteer_create'),
            {
                'full_name': 'Новый волонтёр',
                'email': 'new-volunteer@test.local',
                'phone': '+79990000000',
                'password1': 'StrongVolunteerPassword456!',
                'password2': 'StrongVolunteerPassword456!',
            },
        )
        self.assertRedirects(response, reverse('users:volunteer_list'))
        volunteer = User.objects.get(email='new-volunteer@test.local')
        self.assertEqual(volunteer.role, User.Role.VOLUNTEER)
        self.assertTrue(volunteer.check_password('StrongVolunteerPassword456!'))

        response = self.client.post(
            reverse('users:volunteer_update', args=[volunteer.pk]),
            {
                'full_name': 'Обновлённый волонтёр',
                'email': 'updated-volunteer@test.local',
                'phone': '',
                'is_active': 'on',
            },
        )
        self.assertRedirects(response, reverse('users:volunteer_list'))
        volunteer.refresh_from_db()
        self.assertEqual(volunteer.full_name, 'Обновлённый волонтёр')
        self.assertEqual(volunteer.username, volunteer.email)

    def test_admin_can_change_password_and_disable_login(self):
        response = self.client.post(
            reverse('users:volunteer_password', args=[self.volunteer.pk]),
            {
                'new_password1': 'ChangedVolunteerPassword789!',
                'new_password2': 'ChangedVolunteerPassword789!',
            },
        )
        self.assertRedirects(response, reverse('users:volunteer_list'))
        self.volunteer.refresh_from_db()
        self.assertTrue(self.volunteer.check_password('ChangedVolunteerPassword789!'))

        self.client.post(reverse('users:volunteer_toggle_active', args=[self.volunteer.pk]))
        self.volunteer.refresh_from_db()
        self.assertFalse(self.volunteer.is_active)
        self.client.logout()
        # self.client.login() bypasses axes middleware and triggers AxesBackendRequestParameterRequired.
        # Use an HTTP POST to the login view instead — this goes through the full middleware stack.
        login_response = self.client.post(
            '/login/',
            {'username': self.volunteer.email, 'password': 'ChangedVolunteerPassword789!'},
            REMOTE_ADDR='127.0.0.2',
        )
        # An inactive user must NOT be redirected to the dashboard — login is rejected.
        self.assertNotEqual(login_response.status_code, 302)

    def test_volunteer_cannot_manage_volunteers(self):
        self.client.force_login(self.volunteer)
        self.assertEqual(self.client.get(reverse('users:volunteer_list')).status_code, 403)


class AxesBruteForceProtectionTests(TestCase):
    """Verify that django-axes blocks login after AXES_FAILURE_LIMIT failed attempts."""

    LOGIN_URL = '/login/'
    WRONG_PASSWORD = 'WrongPassword!!!'
    CORRECT_PASSWORD = 'CorrectPassword123!'
    FAILURE_LIMIT = 5

    def setUp(self):
        # Reset axes state so every test starts clean
        from axes.utils import reset
        reset()

        self.user = get_user_model().objects.create_user(
            username='bruteforce-target@test.local',
            email='bruteforce-target@test.local',
            password=self.CORRECT_PASSWORD,
        )

    def _post_login(self, password):
        return self.client.post(
            self.LOGIN_URL,
            {'username': self.user.email, 'password': password},
            REMOTE_ADDR='127.0.0.1',
        )

    def test_lockout_after_failure_limit(self):
        """After FAILURE_LIMIT wrong attempts axes blocks the IP (status 429 or 403)."""
        # axes blocks when failures >= FAILURE_LIMIT, so attempts 1..(FAILURE_LIMIT-1) are free
        for i in range(self.FAILURE_LIMIT - 1):
            response = self._post_login(self.WRONG_PASSWORD)
            self.assertNotIn(
                response.status_code,
                [429, 403],
                msg=f'Unexpected lockout on attempt {i + 1} (before limit reached)',
            )

        # The FAILURE_LIMIT-th attempt hits the threshold — axes blocks here
        response = self._post_login(self.WRONG_PASSWORD)
        self.assertIn(
            response.status_code,
            [429, 403],
            msg=(
                f'Expected lockout (429 or 403) on attempt {self.FAILURE_LIMIT}, '
                f'got {response.status_code}'
            ),
        )

    def test_correct_password_blocked_after_lockout(self):
        """Even correct credentials must be rejected (via HTTP POST) while IP is locked out."""
        # Trigger the lockout
        for _ in range(self.FAILURE_LIMIT):
            self._post_login(self.WRONG_PASSWORD)

        # Now even the right password must be blocked at the HTTP layer
        response = self._post_login(self.CORRECT_PASSWORD)
        self.assertIn(
            response.status_code,
            [429, 403],
            msg=(
                f'Expected locked-out response even with correct password, '
                f'got {response.status_code}'
            ),
        )


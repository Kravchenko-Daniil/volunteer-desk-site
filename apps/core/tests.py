from io import StringIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from apps.districts.models import District


User = get_user_model()


class SeedInitialDataTests(TestCase):
    def test_seed_command_is_idempotent(self):
        arguments = [
            '--district',
            'Центральный',
            '--admin',
            'seed-admin@test.local',
            'Тестовый администратор',
            'SeedAdminPassword123!',
            '--volunteer',
            'seed-volunteer@test.local',
            'Тестовый волонтёр',
            'SeedVolunteerPassword123!',
        ]
        call_command('seed_initial_data', *arguments, stdout=StringIO())
        call_command('seed_initial_data', *arguments, stdout=StringIO())
        self.assertEqual(District.objects.filter(name='Центральный').count(), 1)
        self.assertEqual(User.objects.filter(email='seed-admin@test.local').count(), 1)
        self.assertEqual(User.objects.filter(email='seed-volunteer@test.local').count(), 1)


class DockerConfigurationTests(TestCase):
    def test_required_docker_files_exist(self):
        root = Path(__file__).resolve().parents[2]
        for filename in ['Dockerfile', 'docker-compose.yml', 'docker-compose.prod.yml', '.dockerignore']:
            self.assertTrue((root / filename).is_file(), filename)

    def test_compose_uses_postgresql_16(self):
        root = Path(__file__).resolve().parents[2]
        compose = (root / 'docker-compose.yml').read_text()
        self.assertIn('postgres:16', compose)
        self.assertIn('service_healthy', compose)

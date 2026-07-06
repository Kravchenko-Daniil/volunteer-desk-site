from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.districts.models import District


User = get_user_model()


class Command(BaseCommand):
    help = 'Идемпотентно создаёт стартовые районы и рабочие учётные записи.'

    def add_arguments(self, parser):
        parser.add_argument('--district', action='append', default=[], metavar='NAME')
        parser.add_argument('--admin', nargs=3, metavar=('EMAIL', 'FULL_NAME', 'PASSWORD'))
        parser.add_argument(
            '--volunteer',
            action='append',
            nargs=3,
            default=[],
            metavar=('EMAIL', 'FULL_NAME', 'PASSWORD'),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not options['district'] and not options['admin'] and not options['volunteer']:
            raise CommandError('Передайте хотя бы --district, --admin или --volunteer.')

        for index, name in enumerate(options['district'], start=1):
            district, created = District.objects.get_or_create(
                name=name.strip(),
                defaults={'is_active': True, 'sort_order': index * 10},
            )
            self.stdout.write(f'Район: {district.name} ({"создан" if created else "уже существует"})')

        if options['admin']:
            self._create_user(*options['admin'], role=User.Role.ADMIN, is_staff=True)

        for volunteer in options['volunteer']:
            self._create_user(*volunteer, role=User.Role.VOLUNTEER, is_staff=False)

    def _create_user(self, email, full_name, password, *, role, is_staff):
        email = email.strip().lower()
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'full_name': full_name,
                'role': role,
                'is_staff': is_staff,
                'is_active': True,
            },
        )
        if created:
            user.set_password(password)
            user.save(update_fields=['password'])
        self.stdout.write(
            f'{user.get_role_display()}: {user.email} ({"создан" if created else "уже существует, пароль не изменён"})'
        )

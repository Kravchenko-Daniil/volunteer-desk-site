# Развёртывание

Шаблоны в этой папке нельзя копировать вслепую: замените домен, пользователя и пути.

1. Создать системного пользователя и каталог `/srv/help_requests_site`.
2. Установить Python, PostgreSQL, Nginx и системные зависимости WeasyPrint.
3. Создать PostgreSQL-роль и базу без прав суперпользователя.
4. Создать `.venv`, установить `requirements.txt`, заполнить `.env` по `.env.production.example`.
5. Выполнить:

   ```bash
   python manage.py check --deploy
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py createsuperuser
   ```

6. Установить и включить unit Gunicorn из `gunicorn.service.example`.
7. Настроить Nginx по `nginx.conf.example`, проверить `nginx -t`.
8. Выпустить сертификат Let's Encrypt и только после проверки HTTPS включить HSTS.
9. Настроить ежедневный запуск `scripts/backup_postgres.sh` и тест восстановления.

Стартовые данные создаются без помещения паролей в код:

```bash
python manage.py seed_initial_data \
  --district "Первый район" \
  --district "Второй район" \
  --admin "admin@example.ru" "Администратор" "временный-сложный-пароль" \
  --volunteer "volunteer@example.ru" "Волонтёр" "временный-сложный-пароль"
```

Команда повторяемая: существующие аккаунты не дублируются и их пароли не перезаписываются.

До реального запуска нужны утверждённые юридические тексты, домен, рабочие аккаунты и секреты.

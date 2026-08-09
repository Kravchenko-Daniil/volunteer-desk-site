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

## Запуск под доменом по HTTPS

Обвязка для домена `youngnart.ru`: `deploy/nginx.https.conf`, `docker-compose.https.yml`
(override поверх `docker-compose.prod.yml`, добавляет certbot и порт 443) и
`scripts/issue_cert.sh` для первичного выпуска сертификата. Домен ещё не зарегистрирован —
сертификат пока не выпускался, ниже порядок действий на будущее.

1. Прописать у регистратора домена A-запись (и AAAA, если есть IPv6) `youngnart.ru` и
   `www.youngnart.ru` на IP сервера. Дождаться распространения DNS (`getent hosts youngnart.ru`
   должен вернуть IP сервера).
2. Заполнить `.env` по актуальному `.env.production.example`, включая блок
   `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` / `SECURE_*` для `youngnart.ru`.
3. Открыть порты 80 и 443 в файрволе сервера и у облачного провайдера.
4. Поднять обычный HTTP-стек и убедиться, что сайт отвечает по домену:

   ```bash
   docker compose -f docker-compose.prod.yml up -d
   curl -I http://youngnart.ru/health/
   ```

5. Выпустить сертификат (сначала сухим прогоном, затем по-настоящему):

   ```bash
   scripts/issue_cert.sh --dry-run youngnart.ru admin@youngnart.ru
   scripts/issue_cert.sh youngnart.ru admin@youngnart.ru
   ```

   Скрипт сам проверит резолвинг домена и доступность порта 80, временно переключит
   nginx в HTTP-режим для ACME-challenge, запросит сертификат у Let's Encrypt и
   переключит nginx на HTTPS-конфигурацию.

6. Поднять полный стек с HTTPS и автопродлением сертификата:

   ```bash
   docker compose -f docker-compose.prod.yml -f docker-compose.https.yml up -d
   ```

7. Проверить сертификат и редиректы:

   ```bash
   curl -I http://youngnart.ru/health/        # 301 на https
   curl -I https://youngnart.ru/health/       # 200 ok
   curl -I https://www.youngnart.ru/health/   # 301 на https://youngnart.ru
   openssl s_client -connect youngnart.ru:443 -servername youngnart.ru </dev/null 2>/dev/null | openssl x509 -noout -dates
   ```

8. Только после того как HTTPS стабильно проработал и подтверждено автопродление
   (сервис `certbot` в `docker-compose.https.yml` перезапускается и не падает),
   включить HSTS: поднять `SECURE_HSTS_SECONDS` в `.env` с `0` до боевого значения
   (например, `31536000`) и перезапустить `web`. До этого момента HSTS должен
   оставаться выключенным — иначе браузеры закэшируют принудительный HTTPS и
   откатиться в случае проблем с сертификатом будет тяжело.

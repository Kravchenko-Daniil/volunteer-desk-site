# Развёртывание

## DEV — локальный запуск через Docker

Самый быстрый способ запустить проект для разработки.

### Шаги

```bash
cp .env.example .env
docker compose up --build
```

Docker Compose поднимает два сервиса: `db` (PostgreSQL 16) и `web` (Django runserver).
Entrypoint автоматически дожидается готовности базы, выполняет `migrate`.
Приложение доступно на `http://localhost:8000`.

### Переменные из `.env.example`

| Переменная | Дефолт в dev | Описание |
|---|---|---|
| `SECRET_KEY` | `change-me` | Django secret key |
| `DEBUG` | `True` | Режим отладки |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost` | Разрешённые хосты |
| `USE_SQLITE` | `False` | `False` — PostgreSQL, `True` — SQLite (только локально без Docker) |
| `DATABASE_NAME` | `help_requests` | Имя базы |
| `DATABASE_USER` | `help_requests_app` | Пользователь БД |
| `DATABASE_PASSWORD` | `change-me` | Пароль БД |
| `DATABASE_HOST` | `localhost` | Хост БД (`db` внутри Docker) |
| `DATABASE_PORT` | `5432` | Порт БД |
| `PERSONAL_DATA_POLICY_VERSION` | _(дата)_ | Версия политики ПД (формат `YYYY-MM-DD`) |
| `USE_X_FORWARDED_PROTO` | `False` | Доверять заголовку `X-Forwarded-Proto` |
| `TRUST_X_FORWARDED_FOR` | `False` | Доверять `X-Forwarded-For` |
| `RATE_LIMIT_10_MINUTES` | `5` | Лимит заявок за 10 минут (с одного IP) |
| `RATE_LIMIT_24_HOURS` | `20` | Лимит заявок за 24 часа (с одного IP) |
| `CAPTCHA_ENABLED` | `False` | Включить капчу |
| `CAPTCHA_PROVIDER` | `hcaptcha` | Провайдер капчи |
| `CAPTCHA_SITE_KEY` | _(пусто)_ | Публичный ключ капчи |
| `CAPTCHA_SECRET_KEY` | _(пусто)_ | Секретный ключ капчи |

### DEV без Docker (venv)

Требует локально установленного PostgreSQL (или `USE_SQLITE=True`).

```bash
cp .env.example .env
# отредактировать DATABASE_HOST=localhost и DATABASE_PASSWORD

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

---

## PROD — Docker Compose (рекомендуемый способ)

Стек: `db` (PostgreSQL 16) + `web` (Gunicorn 3 workers) + `nginx` (nginx:1.27-alpine).
Nginx слушает порт 80 и проксирует запросы на Gunicorn; раздаёт `/static/` и `/media/` напрямую.
TLS-терминация — за пределами этого стека (внешний reverse proxy или Let's Encrypt + хостовой nginx).

### Шаги

```bash
cp .env.production.example .env
# заполнить все переменные (см. таблицу ниже)

docker compose -f docker-compose.prod.yml up -d --build
```

Entrypoint при старте `web` автоматически выполняет:
- ожидание готовности PostgreSQL (таймаут 60 с);
- `migrate --noinput`;
- `collectstatic --noinput`.

Флаги управляются переменными окружения в `docker-compose.prod.yml`:
`WAIT_FOR_DATABASE=True`, `RUN_MIGRATIONS=True`, `COLLECT_STATIC=True`.

### Создание суперпользователя

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### Заполнение начальных данных (районы, тестовые аккаунты)

```bash
docker compose -f docker-compose.prod.yml exec web \
  python manage.py seed_initial_data \
    --district "Название района" \
    --admin "admin@<project>.local" "Администратор" "<временный-пароль>" \
    --volunteer "volunteer@<project>.local" "Волонтёр" "<временный-пароль>"
```

Команда идемпотентна: существующие аккаунты не дублируются, пароли не перезаписываются.

### Переменные из `.env.production.example`

| Переменная | Пример значения | Описание |
|---|---|---|
| `SECRET_KEY` | `replace-with-a-long-random-secret` | Длинный случайный ключ (50+ символов) |
| `DEBUG` | `False` | Обязательно `False` в prod |
| `ALLOWED_HOSTS` | `help.example.ru` | Доменное имя сервера |
| `CSRF_TRUSTED_ORIGINS` | `https://help.example.ru` | Доверенные origins для CSRF |
| `USE_SQLITE` | `False` | Всегда `False` в prod |
| `DATABASE_NAME` | `help_requests` | Имя базы |
| `DATABASE_USER` | `help_requests_app` | Пользователь БД |
| `DATABASE_PASSWORD` | `replace-with-a-strong-password` | Сильный пароль БД |
| `DATABASE_HOST` | `127.0.0.1` | Хост БД (для Docker: имя сервиса задаётся в compose) |
| `DATABASE_PORT` | `5432` | Порт БД |
| `PERSONAL_DATA_POLICY_VERSION` | `replace-with-approved-version` | Версия утверждённой политики ПД |
| `SECURE_SSL_REDIRECT` | `True` | Редирект HTTP → HTTPS |
| `SESSION_COOKIE_SECURE` | `True` | Cookie только по HTTPS |
| `CSRF_COOKIE_SECURE` | `True` | CSRF-cookie только по HTTPS |
| `SECURE_HSTS_SECONDS` | `31536000` | Время HSTS (1 год) |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | `False` | Включить поддомены в HSTS |
| `SECURE_HSTS_PRELOAD` | `False` | Добавить в preload-список |
| `USE_X_FORWARDED_PROTO` | `True` | Доверять `X-Forwarded-Proto` от nginx |
| `TRUST_X_FORWARDED_FOR` | `True` | Доверять `X-Forwarded-For` от nginx |
| `RATE_LIMIT_10_MINUTES` | `5` | Лимит заявок за 10 минут |
| `RATE_LIMIT_24_HOURS` | `20` | Лимит заявок за 24 часа |
| `CAPTCHA_ENABLED` | `False` | Включить капчу |
| `CAPTCHA_PROVIDER` | `hcaptcha` | Провайдер капчи |
| `CAPTCHA_SITE_KEY` | _(пусто)_ | Публичный ключ капчи |
| `CAPTCHA_SECRET_KEY` | _(пусто)_ | Секретный ключ капчи |

> **HSTS.** Включать `SECURE_HSTS_SECONDS` только после того, как HTTPS проверен и работает стабильно: отозвать HSTS после включения крайне сложно.

---

## PROD — без Docker (systemd + Gunicorn + Nginx)

Подробный порядок — в `deploy/README.md`. Краткий:

1. Создать системного пользователя `help-requests`, каталог `/srv/help_requests_site`.
2. Установить Python, PostgreSQL, Nginx и системные зависимости WeasyPrint (`libcairo2`, `libpango-1.0-0`, `libpangoft2-1.0-0`, `libgdk-pixbuf-2.0-0`, `libffi8`, `shared-mime-info`, `fonts-dejavu-core`).
3. Создать PostgreSQL-роль и базу без прав суперпользователя.
4. Создать `.venv`, установить `requirements.txt`, заполнить `.env` по `.env.production.example`.
5. Проверить конфигурацию и выполнить первичные операции:
   ```bash
   python manage.py check --deploy
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py createsuperuser
   ```
6. Установить systemd-unit из `deploy/gunicorn.service.example`:
   - Сокет: `/run/help_requests/gunicorn.sock`
   - Пользователь: `help-requests`, группа: `www-data`
   - Рабочая директория: `/srv/help_requests_site`
   - Запуск: `gunicorn config.wsgi:application --workers 3 --bind unix:/run/help_requests/gunicorn.sock`
   ```bash
   sudo systemctl enable --now gunicorn-help-requests
   ```
7. Настроить Nginx по `deploy/nginx.conf.example` (заменить `help.example.ru` на реальный домен):
   - HTTP → 301 HTTPS
   - `/static/` → `/srv/help_requests_site/staticfiles/`
   - `/media/` → `/srv/help_requests_site/media/`
   - Остальное → unix-сокет Gunicorn
   ```bash
   sudo nginx -t && sudo systemctl reload nginx
   ```
8. Выпустить сертификат Let's Encrypt (certbot), затем включить HSTS.

---

## Бэкап и восстановление PostgreSQL

### Бэкап (`scripts/backup_postgres.sh`)

Скрипт делает `pg_dump --format=custom` и архивирует `media/`, затем удаляет файлы старше `RETENTION_DAYS`.

```bash
export DATABASE_URL="postgresql://<user>:<password>@<host>/<database>"
export BACKUP_DIR="/srv/backups"        # куда складывать дампы (по умолчанию ./backups)
export RETENTION_DAYS=14                # сколько дней хранить (по умолчанию 14)
export MEDIA_DIR="/srv/help_requests_site/media"  # путь к media (по умолчанию ./media)

bash scripts/backup_postgres.sh
```

Файлы:
- `$BACKUP_DIR/postgresql-<timestamp>.dump` — дамп базы
- `$BACKUP_DIR/media-<timestamp>.tar.gz` — архив media (если директория существует)

Дамп верифицируется через `pg_restore --list` перед переименованием из `.tmp`.

Для автоматизации добавить в cron:
```cron
0 3 * * * DATABASE_URL="postgresql://..." BACKUP_DIR=/srv/backups /srv/help_requests_site/scripts/backup_postgres.sh
```

### Восстановление (`scripts/restore_postgres.sh`)

**Внимание:** восстановление затирает текущие данные в базе (`--clean --if-exists`).

```bash
export DATABASE_URL="postgresql://<user>:<password>@<host>/<database>"
export CONFIRM_RESTORE=YES

bash scripts/restore_postgres.sh /srv/backups/postgresql-<timestamp>.dump
```

`CONFIRM_RESTORE=YES` — обязательный guard против случайного запуска. Без него скрипт завершится с ошибкой.

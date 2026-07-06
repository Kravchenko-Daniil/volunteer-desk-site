# volunteer-desk-site

Сайт приёма и координации заявок на волонтёрскую помощь. Лендинг и интерфейс заявителя брендированы «Рядом».

## Возможности

- Публичная форма заявки с согласием на обработку персональных данных
- Карточка заявки со статусами: новая → принята / отклонена → назначена → выполнена
- Роли: администратор и волонтёр с разграниченными правами доступа
- PDF-печать заявки (WeasyPrint)
- Excel-экспорт отфильтрованных заявок (openpyxl)
- Поиск и фильтры по заявкам
- Справочник районов
- Личный кабинет волонтёра
- История действий по каждой заявке
- Антиспам: honeypot и rate-limit по IP; опциональная hCaptcha
- django-axes: блокировка по неудачным попыткам входа
- Подготовка под требования ПДн (тексты политики и согласия, флаг согласия в форме)

## Стек

- **Backend:** Django 5.2, Python 3.12
- **База данных:** PostgreSQL 16 (production), SQLite (локальная демонстрация)
- **Деплой:** Docker Compose, Gunicorn, Nginx
- **Экспорт:** WeasyPrint (PDF), openpyxl (Excel)

## Quickstart (Docker)

```bash
git clone <repo-url> volunteer-desk-site
cd volunteer-desk-site
cp .env.example .env          # заполните SECRET_KEY и DB-параметры
docker compose up --build
```

Сайт доступен на `http://localhost:8000/`.

Первые шаги после запуска:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

### Локальный запуск без Docker (venv)

```bash
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # заполните переменные
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Для SQLite добавьте `USE_SQLITE=True` в `.env`. PostgreSQL обязателен для production.

## Документация

| Файл | Содержание |
|---|---|
| `docs/review.md` | Обзор архитектуры и ревью кода |
| `docs/changelog.md` | История изменений |
| `deploy/` | Инструкция по развёртыванию (Gunicorn + Nginx) |
| `requirements.txt` | Зависимости Python |

## Важно

Тексты политики конфиденциальности и согласия на обработку персональных данных — черновые. Перед боевым запуском необходима замена на юридически выверенные для вашей юрисдикции.

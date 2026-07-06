# Техническая архитектура

Документ описывает архитектуру системы по факту исходного кода (`apps/`, `config/`, `templates/`).
Volunteer Desk — сайт приёма и обработки заявок на волонтёрскую помощь: публичная форма для заявителей,
кабинет администратора для модерации и назначения волонтёров, кабинет волонтёра для работы с заявками.

## Стек

| Слой | Технология | Источник |
|------|-----------|----------|
| Веб-фреймворк | Django 5.x (`Django>=5.0,<6.0`) | `requirements.txt` |
| БД (прод) | PostgreSQL через `psycopg2-binary` | `config/settings.py`, `requirements.txt` |
| БД (dev/тесты) | SQLite (флаг `USE_SQLITE`) | `config/settings.py` |
| PDF | WeasyPrint (`HTML(...).write_pdf()`) | `apps/exports/views.py` |
| Excel | openpyxl (`Workbook`) | `apps/exports/views.py` |
| Защита логина | django-axes (brute-force lockout по IP) | `config/settings.py` |
| Конфигурация | python-dotenv (`load_dotenv`) | `config/settings.py` |
| WSGI-сервер | gunicorn | `Dockerfile`, `requirements.txt` |
| Контейнеризация | Docker (python:3.13-slim) + docker-compose | `Dockerfile`, `docker-compose*.yml` |
| Кастомная модель пользователя | `AUTH_USER_MODEL = 'users.User'` | `config/settings.py` |

Настройки полностью env-driven: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_*` — обязательные/через
`required_env`. Локаль `ru-ru`, таймзона `Europe/Moscow`, `USE_TZ=True`.
Секьюрити-флаги (`SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, HSTS,
`SECURE_PROXY_SSL_HEADER`) управляются переменными окружения и по умолчанию выключены (dev-friendly).

## Приложения и зоны ответственности

Проект разбит на 6 Django-приложений в пакете `apps.*` (`INSTALLED_APPS`).

| Приложение | Зона ответственности |
|-----------|----------------------|
| **applications** | Ядро домена. Модель заявки `Application`, FSM статусов (`transition_to`), журнал действий `ApplicationAction`, лог попыток отправки `SubmissionAttempt`. Публичная форма, кабинет администратора (список/деталь/принять/отклонить/назначить), кабинет волонтёра (свои заявки, отметить выполненной, создать заявку для себя/другого). Анти-спам (rate-limit по IP, honeypot) и hCaptcha. |
| **users** | Кастомная модель `User` (роли администратор/волонтёр), редирект после логина по роли, CRUD-управление волонтёрами администратором (создать, редактировать, сменить пароль, вкл/выкл активность). |
| **districts** | Справочник районов `District` (активность, порядок сортировки). Список и создание/редактирование районов администратором. |
| **exports** | Выгрузки для администратора: Excel (openpyxl) по отфильтрованному списку заявок и PDF отдельной заявки (WeasyPrint). Лог выгрузок `ExportLog`. |
| **notifications** | Модель `NotificationLog` — журнал уведомлений заявителю (принята/отклонена/выполнена, статус pending/sent/error). Только модель; отдельных view/url в коде нет. |
| **core** | Публичные статические страницы: главная, политика конфиденциальности, страница согласия на обработку ПДн. Обработчик 403 (`handler403 → permission_denied`). |

Дополнительные слои внутри `applications`: `forms.py` (формы + `get_client_ip`), `selectors.py`
(`filter_applications`), `services.py` (`log_action`), `anti_spam.py` (`register_submission_attempt`),
`captcha.py` (`verify_captcha` через hCaptcha siteverify).

## Роли и права

Модель `users.User` (`AbstractUser`, логин по email, `USERNAME_FIELD='email'`) имеет поле `role` со
значениями `admin` / `volunteer` (default `volunteer`) и два свойства:

- `is_project_admin` → `role == ADMIN` **или** `is_superuser`;
- `is_volunteer` → `role == VOLUNTEER`.

Доступ разграничивается не декораторами прав Django, а связкой `@login_required` +
ручных проверок-гардов в начале view:

```python
def require_admin(user):
    if not user.is_authenticated or not user.is_project_admin:
        raise PermissionDenied
def require_volunteer(user):
    if not user.is_authenticated or not user.is_volunteer:
        raise PermissionDenied
```

`require_admin` продублирован в `applications/views.py`, `users/views.py`, `exports/views.py`,
`districts/views.py`; `require_volunteer` — в `applications/views.py`. `PermissionDenied` перехватывается
`handler403` и рендерит `errors/403.html`.

| Роль | Что доступно (по коду) |
|------|------------------------|
| **Анонимный посетитель** | Главная, политика ПДн, страница согласия (`core`); публичная форма заявки `applications:public_create` и страница «спасибо». Форма защищена honeypot, rate-limit по IP (`RATE_LIMIT_10_MINUTES`, `RATE_LIMIT_24_HOURS`) и опциональной hCaptcha. Всё остальное — за `@login_required`. |
| **Волонтёр** (`role=volunteer`) | После логина редирект на `applications:volunteer_list`. Видит только заявки, где он `assigned_volunteer` или `created_by_user` (фильтр `Q(assigned_volunteer=user) | Q(created_by_user=user)`); деталь заявки доступна только если он назначенный или автор (иначе `PermissionDenied`). Может отметить свою назначенную заявку выполненной, создать заявку для себя (ФИО/email подставлены и `disabled`) и для другого человека. Не имеет доступа к списку всех заявок, управлению волонтёрами, районами, экспортам. |
| **Администратор** (`role=admin`) | После логина редирект на `applications:list`. Полный список заявок с фильтрами (`ApplicationFilterForm`), деталь заявки, переходы статусов: принять / отклонить / назначить волонтёра. Управление волонтёрами (`users`): список, создание, редактирование, смена пароля, вкл/выкл активности. Справочник районов (`districts`). Экспорты (`exports`): Excel списка и PDF заявки. |
| **Суперпользователь** (`is_superuser`) | Через `is_project_admin` получает все права администратора приложения. Дополнительно — доступ к стандартной Django-админке `django-admin/` (`admin.site.urls`). |

Ограничения записи в домене вшиты и в сами операции: назначить можно только пользователя с
`is_volunteer` и `is_active=True` (проверка в `transition_to` и в `get_object_or_404(... role=VOLUNTEER, is_active=True)`);
завершить заявку можно только при наличии `assigned_volunteer`.

## FSM статусов заявки

Статусы (`Application.Status`): `new` (Новая), `accepted` (Принята), `rejected` (Отклонена),
`assigned` (Назначена), `completed` (Выполнена). Default — `new`.

Разрешённые переходы заданы в `Application.can_transition_to()`:

```
             admin: принять                admin: назначить          volunteer: выполнить
                 (accept)                    (assign)                    (complete)
   ┌────────┐  ───────────►  ┌──────────┐  ───────────►  ┌──────────┐  ───────────►  ┌───────────┐
   │  NEW   │                │ ACCEPTED │                │ ASSIGNED │                │ COMPLETED │
   │ новая  │                │ принята  │                │назначена │                │ выполнена │
   └───┬────┘                └──────────┘                └──────────┘                └───────────┘
       │                                                                              (терминальный)
       │ admin: отклонить (reject)
       ▼
   ┌──────────┐
   │ REJECTED │  (терминальный)
   │отклонена │
   └──────────┘

Матрица переходов (can_transition_to):
  NEW       → {ACCEPTED, REJECTED}
  ACCEPTED  → {ASSIGNED}
  REJECTED  → {}          (тупик)
  ASSIGNED  → {COMPLETED}
  COMPLETED → {}          (тупик)
```

Правила перехода в `transition_to()`:
- `ACCEPTED` — проставляет `accepted_at`.
- `REJECTED` — проставляет `rejected_at`.
- `ASSIGNED` — требует `assigned_volunteer` c `is_volunteer=True`, иначе `ValidationError`.
- `COMPLETED` — требует непустой `assigned_volunteer_id`; проставляет `completed_at` и `completion_comment`.
- Любой запрещённый переход → `ValidationError` с человекочитаемым сообщением.

Переходы вызываются во view под `transaction.atomic()` + `select_for_update()` (защита от гонок),
каждый переход логируется в `ApplicationAction` через `log_action`. Дат `assigned` отдельного поля нет —
факт назначения фиксируется в истории.

## Модель данных

```
District ──1───────┐
                   │ (PROTECT)
                   ▼
User (роль) ──┬──► Application ──1──► ApplicationAction (история, CASCADE)
              │        │
              │        ├──1──► NotificationLog (уведомления, CASCADE)
              │        │
   created_by │        └── согласие ПДн (поля внутри Application)
   assigned   │
   changed_by │
   (все SET_NULL)

User ──► ExportLog (SET_NULL)     SubmissionAttempt (без FK, лог по IP)
```

**Application** (`apps/applications/models.py`) — центральная модель:
- Данные заявителя: `applicant_full_name`, `applicant_email`, `help_description`, `people_needed`, `comment`.
- `district` → `District` (`on_delete=PROTECT` — район нельзя удалить, пока есть заявки).
- `status` (FSM), `created_from` (public_form / admin_panel / volunteer_self / volunteer_for_other).
- `created_by_user`, `assigned_volunteer` → `User` (оба `SET_NULL`, разные `related_name`).
- Таймстемпы жизненного цикла: `created_at`, `updated_at`, `accepted_at`, `rejected_at`, `completed_at`, `completion_comment`.
- **Согласие ПДн**: `personal_data_agreed`, `personal_data_agreed_at`, `personal_data_policy_version`
  (версия из `PERSONAL_DATA_POLICY_VERSION`). Проставляются в `PublicApplicationForm.save()`.
- Аудит источника: `applicant_ip` (`get_client_ip`, учитывает `X-Forwarded-For` при `TRUST_X_FORWARDED_FOR`), `user_agent`.

**ApplicationAction** — журнал действий по заявке (`related_name='actions'`, `CASCADE`):
`old_status`, `new_status`, `action` (created / accepted / rejected / assigned / completed / pdf_generated / exported),
`changed_by_user`, `assigned_volunteer`, `comment`, `created_at`. Пишется как переходами статусов, так и экспортами
(EXPORTED — bulk при выгрузке в Excel, PDF_GENERATED — при генерации PDF).

**User** (`apps/users/models.py`) — `AbstractUser`, email уникальный и логин-поле, `full_name`, `phone`, `role`.

**District** (`apps/districts/models.py`) — `name` (unique), `is_active`, `sort_order`, таймстемпы.
Формы заявки показывают только `is_active=True`.

**NotificationLog** (`apps/notifications/models.py`) — заявка (`CASCADE`), `recipient_email`, `type`
(accepted/rejected/completed), `status` (pending/sent/error), `subject`, `body`, `sent_at`, `error_message`.

**ExportLog** (`apps/exports/models.py`) — кто (`SET_NULL`), `format` (xlsx/pdf), `filters_json`, `created_at`.

**SubmissionAttempt** (`apps/applications/models.py`) — анти-спам-лог без FK: `ip_address` (индекс),
`user_agent`, `was_blocked`, `was_honeypot`, `created_at`. Используется `register_submission_attempt`
для rate-limit по окнам 10 минут / 24 часа.

## Точки входа (URL)

Корневой роутер — `config/urls.py`; `handler403 = apps.core.views.permission_denied`.

**Публично / анонимно**
- `GET /` — главная (`core:home`).
- `GET /privacy/` — политика конфиденциальности (`core:privacy`).
- `GET /personal-data-consent/` — согласие на обработку ПДн (`core:personal_data_consent`).
- `GET|POST /applications/new/` — публичная форма заявки (`applications:public_create`); honeypot + rate-limit + hCaptcha.
- `GET /applications/thanks/` — страница «спасибо» (`applications:thanks`).
- `GET|POST /login/`, `/logout/` — Django `LoginView`/`LogoutView` (шаблон `users/login.html`), защищены django-axes.

**Кабинет волонтёра** (`@login_required` + `require_volunteer`)
- `GET /applications/volunteer/` — мои заявки (`volunteer_list`).
- `GET /applications/volunteer/<pk>/` — деталь (только своей) (`volunteer_detail`).
- `POST /applications/volunteer/<pk>/complete/` — отметить выполненной (`complete`).
- `GET|POST /applications/volunteer/new/self/` — заявка для себя (`volunteer_create_self`).
- `GET|POST /applications/volunteer/new/other/` — заявка для другого (`volunteer_create_for_other`).

**Кабинет администратора** (`@login_required` + `require_admin`)
- `GET /applications/admin/` — список заявок с фильтрами (`applications:list`).
- `GET /applications/admin/<pk>/` — деталь заявки (`applications:detail`).
- `POST /applications/admin/<pk>/accept/` | `/reject/` | `/assign/` — переходы статусов.
- `/users/volunteers/...` — список, создание, редактирование, смена пароля, toggle-active волонтёров.
- `/districts/`, `/districts/new/`, `/districts/<pk>/edit/` — справочник районов.
- `GET /exports/applications.xlsx` — Excel по текущим фильтрам (`exports:applications_xlsx`).
- `GET /exports/application/<pk>.pdf` — PDF заявки (`exports:application_pdf`).
- `/users/after-login/` (`post_login_redirect`, `LOGIN_REDIRECT_URL`) — редиректит по роли после логина: администратор → список заявок, волонтёр → свои заявки.

**Суперпользователь**
- `/django-admin/` — стандартная Django-админка.

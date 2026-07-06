# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased] — Ревью и исправления

### Added

- Защита логина от брутфорса через django-axes: лимит 5 попыток, кулдаун 15 минут (`config/settings.py`, `requirements.txt`, тесты).

### Fixed

- Excel-экспорт: при пустых фильтрах выгружались все заявки вместо отфильтрованных (`apps/exports/views.py`), покрыто тестами.

### Other

- `db.sqlite3` добавлен в `.gitignore`.

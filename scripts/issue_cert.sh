#!/usr/bin/env bash
# Первичный выпуск сертификата Let's Encrypt для домена сайта (по умолчанию youngnart.ru).
#
# Использование:
#   scripts/issue_cert.sh [--dry-run] [домен] [email]
#
# Примеры:
#   scripts/issue_cert.sh                          # youngnart.ru, email не указан — команда откажет
#   scripts/issue_cert.sh --dry-run youngnart.ru admin@youngnart.ru
#   scripts/issue_cert.sh youngnart.ru admin@youngnart.ru
#
# Что делает:
#   1. Проверяет, что домен резолвится и что сервер уже отвечает на порту 80.
#   2. Временно поднимает nginx в чистом HTTP-режиме (без ssl-блоков, которым ещё
#      не с чем работать — сертификата пока нет) с локацией /.well-known/acme-challenge/.
#   3. Запрашивает сертификат у Let's Encrypt через certbot (webroot-режим).
#   4. Переключает nginx на боевую HTTPS-конфигурацию (deploy/nginx.https.conf).
#
# Скрипт не хранит и не печатает секреты. Запускать из корня репозитория на сервере,
# где уже настроен .env (см. .env.production.example) и установлен Docker Compose.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

# --- разбор аргументов ---
DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  shift
fi

DOMAIN="${1:-youngnart.ru}"
EMAIL="${2:-}"
WWW_DOMAIN="www.${DOMAIN}"

if [[ -z "$EMAIL" ]]; then
  echo "Ошибка: не указан email для регистрации в Let's Encrypt (нужен для писем об истечении сертификата)." >&2
  echo "Использование: $0 [--dry-run] [домен] email" >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Ошибка: docker не найден в PATH. Установите Docker и Docker Compose перед выпуском сертификата." >&2
  exit 1
fi

COMPOSE=(docker compose -f docker-compose.prod.yml -f docker-compose.https.yml)

echo "== 1/4: проверяем, что домен ${DOMAIN} резолвится =="
if ! getent hosts "$DOMAIN" >/dev/null 2>&1; then
  echo "Ошибка: домен ${DOMAIN} не резолвится в IP-адрес." >&2
  echo "Проверьте, что A-запись (и AAAA, если используется IPv6) на регистраторе указывает" >&2
  echo "на IP этого сервера, и подождите обновления DNS (может занять до нескольких часов)." >&2
  exit 1
fi

echo "== 2/4: проверяем, что сервер отвечает на порту 80 =="
if ! curl -fsS --max-time 5 -o /dev/null "http://${DOMAIN}/health/"; then
  echo "Ошибка: http://${DOMAIN}/health/ не отвечает." >&2
  echo "Убедитесь, что:" >&2
  echo "  - контейнер nginx запущен (docker compose -f docker-compose.prod.yml up -d);" >&2
  echo "  - порт 80 открыт в файрволе сервера и у облачного провайдера;" >&2
  echo "  - A-запись домена уже указывает именно на этот сервер." >&2
  exit 1
fi

# --- временный HTTP-режим для ACME-challenge ---
# Полная HTTPS-конфигурация (deploy/nginx.https.conf) содержит ssl_certificate на файлы,
# которых до выпуска сертификата ещё не существует, и nginx с ней не запустится.
# Поэтому на время выпуска подставляем упрощённый конфиг: только порт 80 и webroot-challenge.
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

TMP_NGINX_CONF="$TMP_DIR/nginx-bootstrap.conf"
TMP_OVERRIDE="$TMP_DIR/docker-compose.bootstrap.yml"

cat > "$TMP_NGINX_CONF" <<EOF
server {
    listen 80;
    server_name ${DOMAIN} ${WWW_DOMAIN};

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 200 "temporary http mode: issuing certificate\n";
        add_header Content-Type text/plain;
    }
}
EOF

cat > "$TMP_OVERRIDE" <<EOF
services:
  nginx:
    volumes:
      - ${TMP_NGINX_CONF}:/etc/nginx/conf.d/default.conf:ro
      - certbot_www:/var/www/certbot:ro
EOF

echo "== 3/4: поднимаем nginx во временном HTTP-режиме =="
"${COMPOSE[@]}" -f "$TMP_OVERRIDE" up -d nginx

CERTBOT_ARGS=(
  certonly
  --webroot -w /var/www/certbot
  -d "$DOMAIN" -d "$WWW_DOMAIN"
  --email "$EMAIL"
  --agree-tos --no-eff-email
  --non-interactive
)

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Режим --dry-run: сертификат реально выпущен не будет, только проверка достижимости."
  CERTBOT_ARGS+=(--dry-run)
fi

echo "== 4/4: запрашиваем сертификат у Let's Encrypt =="
"${COMPOSE[@]}" run --rm --entrypoint certbot certbot "${CERTBOT_ARGS[@]}"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Сухой прогон завершён успешно. Реальный сертификат не создавался."
  echo "Возвращаем nginx к обычной конфигурации docker-compose.prod.yml."
  "${COMPOSE[@]}" up -d nginx
else
  echo "Сертификат выпущен. Переключаем nginx на боевую HTTPS-конфигурацию."
  "${COMPOSE[@]}" up -d --force-recreate nginx
  echo "Готово. Проверьте: curl -I https://${DOMAIN}/health/"
fi

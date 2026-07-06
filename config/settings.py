from pathlib import Path
import os
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {'1', 'true', 'yes', 'on'}


def required_env(name):
    value = os.getenv(name)
    if not value:
        raise ImproperlyConfigured(f'Environment variable {name} is required.')
    return value


SECRET_KEY = required_env('SECRET_KEY')
DEBUG = env_bool('DEBUG', False)
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',') if h.strip()]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.users',
    'apps.districts',
    'apps.applications',
    'apps.exports',
    'apps.notifications',
    'apps.core',
    'axes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

USE_SQLITE = env_bool('USE_SQLITE', False)
if USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': required_env('DATABASE_NAME'),
            'USER': required_env('DATABASE_USER'),
            'PASSWORD': required_env('DATABASE_PASSWORD'),
            'HOST': os.getenv('DATABASE_HOST', 'localhost'),
            'PORT': os.getenv('DATABASE_PORT', '5432'),
        }
    }

AUTH_USER_MODEL = 'users.User'

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'users:post_login_redirect'
LOGOUT_REDIRECT_URL = 'core:home'

PERSONAL_DATA_POLICY_VERSION = os.getenv('PERSONAL_DATA_POLICY_VERSION', 'draft')

SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', False)
SESSION_COOKIE_SECURE = env_bool('SESSION_COOKIE_SECURE', False)
CSRF_COOKIE_SECURE = env_bool('CSRF_COOKIE_SECURE', False)
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', False)
SECURE_HSTS_PRELOAD = env_bool('SECURE_HSTS_PRELOAD', False)

USE_X_FORWARDED_PROTO = env_bool('USE_X_FORWARDED_PROTO', False)
if USE_X_FORWARDED_PROTO:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

TRUST_X_FORWARDED_FOR = env_bool('TRUST_X_FORWARDED_FOR', False)
RATE_LIMIT_10_MINUTES = int(os.getenv('RATE_LIMIT_10_MINUTES', '5'))
RATE_LIMIT_24_HOURS = int(os.getenv('RATE_LIMIT_24_HOURS', '20'))

CAPTCHA_ENABLED = env_bool('CAPTCHA_ENABLED', False)
CAPTCHA_PROVIDER = os.getenv('CAPTCHA_PROVIDER', 'hcaptcha')
CAPTCHA_SITE_KEY = os.getenv('CAPTCHA_SITE_KEY', '')
CAPTCHA_SECRET_KEY = os.getenv('CAPTCHA_SECRET_KEY', '')
if CAPTCHA_ENABLED:
    if CAPTCHA_PROVIDER != 'hcaptcha':
        raise ImproperlyConfigured('Only CAPTCHA_PROVIDER=hcaptcha is supported.')
    if not CAPTCHA_SITE_KEY or not CAPTCHA_SECRET_KEY:
        raise ImproperlyConfigured('CAPTCHA_SITE_KEY and CAPTCHA_SECRET_KEY are required when CAPTCHA_ENABLED=True.')

# django-axes: brute-force protection
AXES_FAILURE_LIMIT = int(os.getenv('AXES_FAILURE_LIMIT', '5'))
AXES_COOLOFF_TIME = float(os.getenv('AXES_COOLOFF_TIME', '0.25'))  # hours (0.25 = 15 min)
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = ['ip_address']

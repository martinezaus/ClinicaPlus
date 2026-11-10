import os

from django.core.exceptions import ImproperlyConfigured

from .settings import *


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "").strip()
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY debe estar configurada en producción.")

DEBUG = False

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")
    if host.strip()
]
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS debe contener al menos un dominio.")

https_enabled = env_bool("DJANGO_HTTPS")
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = https_enabled
SESSION_COOKIE_SECURE = https_enabled
CSRF_COOKIE_SECURE = https_enabled
SECURE_HSTS_SECONDS = 3600 if https_enabled else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "clinica"),
        "USER": os.getenv("POSTGRES_USER", "clinica"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
        "HOST": os.getenv("POSTGRES_HOST", "db"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}
if not DATABASES["default"]["PASSWORD"]:
    raise ImproperlyConfigured("POSTGRES_PASSWORD debe estar configurada en producción.")

TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "America/Argentina/Buenos_Aires")
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media"

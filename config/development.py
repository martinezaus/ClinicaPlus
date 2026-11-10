import os

from .settings import *


DEBUG = True
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        "http://localhost:8084,http://127.0.0.1:8084",
    ).split(",")
    if origin.strip()
]
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "America/Argentina/Buenos_Aires")

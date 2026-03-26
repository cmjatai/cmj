import os

from .project import *

DEBUG = False
DJANGO_VITE_DEV_MODE = False


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(PROJECT_DIR, "db.sqlite3"),
    }
}

DJANGO_VITE_DEV_MODE = False
DJANGO_VITE = {
    "default": {
        "dev_mode": DJANGO_VITE_DEV_MODE,
        "manifest_path": DJANGO_VITE_ASSETS_PATH.child(Fv6, ".vite", "manifest.json"),
    }
}

STATICFILES_DIRS = [
    PROJECT_DIR.child("sapl", "static"),
    PROJECT_DIR_FRONTEND_2018.child("dist"),
    PROJECT_DIR_FRONTEND_2026.child("dist"),
]

# --- Cache: in-memory (sem dependência de Redis) ---
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}

# --- Channels: in-memory (sem dependência de Redis) ---
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# --- Haystack/Solr: backend simples (sem dependência de Solr) ---
USE_SOLR = False
HAYSTACK_SIGNAL_PROCESSOR = "haystack.signals.BaseSignalProcessor"
HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.simple_backend.SimpleEngine",
    },
}

# --- Celery: execução síncrona para testes ---
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"

# --- Email: captura em memória ---
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# --- Segurança/Performance ---
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# --- Desabilitar debug toolbar e silk em testes ---
DEBUG_TOOLBAR_ACTIVE = False

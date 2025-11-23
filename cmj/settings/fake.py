import os
from time import sleep

from .project import *

DEBUG = False
DJANGO_VITE_DEV_MODE = False


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_DIR, 'db.sqlite3'),
    }
}

DJANGO_VITE_DEV_MODE = False
DJANGO_VITE = {
    'default': {
        'dev_mode': DJANGO_VITE_DEV_MODE,
        'manifest_path': DJANGO_VITE_ASSETS_PATH.child(Fv2026, '.vite', 'manifest.json')
    }
}

STATICFILES_DIRS = [
    PROJECT_DIR.child('sapl', 'static'),
    PROJECT_DIR_FRONTEND_2018.child('dist'),
    PROJECT_DIR_FRONTEND_2026.child('dist')
]


print("Using fake settings")
print("DEBUG =", DEBUG)
print("DJANGO_VITE_DEV_MODE =", DJANGO_VITE_DEV_MODE)
print("STATICFILES_DIRS =", STATICFILES_DIRS)
sleep(5)

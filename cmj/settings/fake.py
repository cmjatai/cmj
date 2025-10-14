import os

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
        'manifest_path': DJANGO_VITE_ASSETS_PATH.child('.vite').child('manifest.json'),
    }
}

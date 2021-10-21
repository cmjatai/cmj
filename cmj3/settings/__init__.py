from pathlib import Path
import os

import environ

from .apps import *
from .auth import *
from .drf import *
from .email import *
from .frontend import *
from .languages import *
from .logs import *
from .medias import *
from .middleware import *


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR.joinpath('cmj3', '.env'))

SECRET_KEY = env.str('SECRET_KEY', default='Env')

DEBUG = env.bool('DEBUG', True)

SHELL_PLUS = "ipython"

ALLOWED_HOSTS = []

ROOT_URLCONF = 'cmj3.urls'

WSGI_APPLICATION = 'cmj3.wsgi.application'
ASGI_APPLICATION = 'cmj3.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

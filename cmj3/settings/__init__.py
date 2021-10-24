from . import ambiente

from .apps import *
from .auth import *
from .drf import *
from .email import *
from .frontend import *
from .languages import *
from .logs import *
from .medias import *
from .middleware import *


env = ambiente.env
BASE_DIR = ambiente.BASE_DIR
PROJECT_ROOT = ambiente.PROJECT_ROOT

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

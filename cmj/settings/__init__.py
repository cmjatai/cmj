import logging
import socket
import sys

from decouple import AutoConfig
from dj_database_url import parse as db_url
from unipath import Path

from .apps import *
from .auth import *
from .drf import *
from .email import *
from .frontend import *
from .languages import *
from .logs import *
from .medias import *
from .middleware import *


host = socket.gethostbyname_ex(socket.gethostname())[0]

config = AutoConfig()

BASE_DIR = Path(__file__).ancestor(2)
PROJECT_DIR = Path(__file__).ancestor(3)

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = ['*']

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/login/?next='

INITIAL_VALUE_FORMS_UF = config('INITIAL_VALUE_FORMS_UF')
INITIAL_VALUE_FORMS_MUNICIPIO = config('INITIAL_VALUE_FORMS_MUNICIPIO')
INITIAL_VALUE_FORMS_CEP = config('INITIAL_VALUE_FORMS_CEP')

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

ROOT_URLCONF = 'cmj.urls'

WSGI_APPLICATION = 'cmj.wsgi.application'
ASGI_APPLICATION = "cmj.routing.application"

DATABASES = {
    'default': config(
        'DATABASE_URL',
        cast=db_url,
    )
}

FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': PROJECT_DIR.child('whoosh'),
    },
}

SITE_URL = 'https://www.jatai.go.leg.br'
if DEBUG:
    SITE_URL = ''

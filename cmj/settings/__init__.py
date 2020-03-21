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
FONTS_DIR = Path(__file__).ancestor(3).child('fonts')

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

SAPL_VERSION = 'master'

SITE_URL = 'https://www.jatai.go.leg.br'
# if DEBUG:
#    SITE_URL = ''

HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.BaseSignalProcessor'  # Disable auto index
SEARCH_BACKEND = ''
SEARCH_URL = ['', '']


# SOLR
USE_SOLR = config('USE_SOLR', cast=bool, default=False)
SOLR_URL = config('SOLR_URL', cast=str, default='http://localhost:8983')
SOLR_COLLECTION = config('SOLR_COLLECTION', cast=str, default='cmj_portal')

if USE_SOLR:
    # enable auto-index

    #HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
    HAYSTACK_SIGNAL_PROCESSOR = 'cmj.signals.CelerySignalProcessor'
    SEARCH_BACKEND = 'haystack.backends.solr_backend.SolrEngine'
    SEARCH_URL = ('URL', '{}/solr/{}'.format(SOLR_URL, SOLR_COLLECTION))

#  BATCH_SIZE: default is 1000 if omitted, avoid Too Large Entity Body errors
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': SEARCH_BACKEND,
        SEARCH_URL[0]: SEARCH_URL[1],
        'BATCH_SIZE': 1000,
        'TIMEOUT': 600,
    },
}

CELERY_BROKER_URL = 'redis://localhost:6379'

CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'

#CELERY_ACCEPT_CONTENT = ['application/json']
#CELERY_RESULT_SERIALIZER = 'json'
#CELERY_TASK_SERIALIZER = 'json'

CACHES = {
    'default': {
        'BACKEND': 'speedinfo.backends.proxy_cache',
        'CACHE_BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache',
    }
}

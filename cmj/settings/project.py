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

INITIAL_VALUE_FORMS_UF = config('INITIAL_VALUE_FORMS_UF', default='')
INITIAL_VALUE_FORMS_MUNICIPIO = config(
    'INITIAL_VALUE_FORMS_MUNICIPIO', default='')
INITIAL_VALUE_FORMS_CEP = config('INITIAL_VALUE_FORMS_CEP', default='')

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

ROOT_URLCONF = 'cmj.urls'

WSGI_APPLICATION = 'cmj.wsgi.application'
ASGI_APPLICATION = "cmj.routing.application"

DATABASES = {
    'default': config(
        'DATABASE_URL_DEV' if DEBUG else 'DATABASE_URL_PRD',
        cast=db_url,
    )
}

PORTALCMJ_VERSION = 'master'

SITE_URL = 'https://www.jatai.go.leg.br'
# if DEBUG:
#    SITE_URL = ''

HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.BaseSignalProcessor'  # Disable auto index
SEARCH_BACKEND = ''
SEARCH_URL = ['', '']

USE_SOLR = True
SOLR_URL = 'http://localhost:8983' if DEBUG else 'http://cmjsolr:8983'
SOLR_COLLECTION = 'cmj_portal'


#HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
HAYSTACK_SIGNAL_PROCESSOR = 'cmj.signal_celery_haystack.CelerySignalProcessor'
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

CACHES = {
    'default': {
        'BACKEND': 'speedinfo.backends.proxy_cache',
        'CACHE_BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache',
    }
}

REDIS_HOST = config(
    'REDIS_HOST', cast=str, default='localhost' if DEBUG else 'cmjredis')
REDIS_PORT = config(
    'REDIS_PORT', cast=int, default=6379)

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
        },
    },
}

CELERY_BROKER_URL = 'redis://{}:{}'.format(REDIS_HOST, REDIS_PORT)
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'

#CELERY_ACCEPT_CONTENT = ['application/json']
#CELERY_RESULT_SERIALIZER = 'json'
#CELERY_TASK_SERIALIZER = 'json'


APPEND_SLASH = False

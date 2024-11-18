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
DEBUG_TOOLBAR_ACTIVE = config('DEBUG_TOOLBAR_ACTIVE', default=False, cast=bool)

FOLDER_DEBUG_CONTAINER = Path(
    config('FOLDER_DEBUG_CONTAINER', default=__file__, cast=str))

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
ASGI_APPLICATION = "cmj.asgi.application"

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

DATABASES = {
    'default': config(
        'DATABASE_URL_DEV' if DEBUG else 'DATABASE_URL_PRD',
        cast=db_url,
    )
}

PORTALCMJ_VERSION = 'master'

SITE_URL = 'https://www.jatai.go.leg.br'
# https, colocar no nginx-> proxy_set_header X-Forwarded-Proto $scheme;
# if DEBUG:
#    SITE_URL = ''

USE_SOLR = True
SOLR_URL = 'http://solr:solr@cmjsolr:8983'
SOLR_COLLECTION = 'portalcmj_cmj'
HAYSTACK_SIGNAL_PROCESSOR = 'cmj.haystack.CelerySignalProcessor'
CELERY_HAYSTACK_DEFAULT_TASK = 'celery_haystack.tasks.haystack_signal'

REDIS_HOST = config('REDIS_HOST', cast=str, default='cmjredis')
REDIS_PORT = config('REDIS_PORT', cast=int, default=6379)

if DEBUG:
    if FOLDER_DEBUG_CONTAINER != PROJECT_DIR:
        #HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
        SOLR_URL = 'http://solr:solr@localhost:8983'
        REDIS_HOST = 'localhost'

SEARCH_BACKEND = 'haystack.backends.solr_backend.SolrEngine'
SEARCH_URL = ('URL', '{}/solr/{}'.format(SOLR_URL, SOLR_COLLECTION))
HAYSTACK_ROUTERS = ['cmj.haystack.CmjDefaultRouter']
HAYSTACK_ITERATOR_LOAD_PER_QUERY = 100
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': SEARCH_BACKEND,
        SEARCH_URL[0]: SEARCH_URL[1],
        'BATCH_SIZE': 1000,
        'TIMEOUT': 600,
        'EXCLUDED_INDEXES': [
            'cmj.arq.search_indexes.ArqDocIndex',
        ]
    },
    'cmjarq': {
        'ENGINE': SEARCH_BACKEND,
        'URL': '{}/solr/{}'.format(SOLR_URL, 'portalcmj_arq'),
        'BATCH_SIZE': 1000,
        'TIMEOUT': 600,
        'EXCLUDED_INDEXES': [
            'cmj.search.search_indexes.DiarioOficialIndex',
            'cmj.search.search_indexes.NormaJuridicaIndex',
            'cmj.search.search_indexes.DocumentoAcessorioIndex',
            'cmj.search.search_indexes.MateriaLegislativaIndex',
            'cmj.search.search_indexes.SessaoPlenariaIndex',
            'cmj.search.search_indexes.DocumentoAdministrativoIndex',
            'cmj.search.search_indexes.DocumentoIndex',
        ]
    },
}

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
CELERY_CACHE_BACKEND = 'default'

#CELERY_ACCEPT_CONTENT = ['application/json']
#CELERY_RESULT_SERIALIZER = 'json'
#CELERY_TASK_SERIALIZER = 'json'


CACHES = {
    # 'default': {
    #    'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
    #    'LOCATION': '/var/tmp/django_cache',
    # }
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache' if not DEBUG else 'django.core.cache.backends.dummy.DummyCache',
        'LOCATION': 'unique-snowflake',
    }
    # "default": {
    #    "BACKEND": "django.core.cache.backends.redis.RedisCache",
    #    "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}",
    # }
}


APPEND_SLASH = False

if DEBUG_TOOLBAR_ACTIVE:
    INSTALLED_APPS += ('debug_toolbar',)
    MIDDLEWARE = MIDDLEWARE + \
        ('debug_toolbar.middleware.DebugToolbarMiddleware', )
    INTERNAL_IPS = ('127.0.0.1',)

if DEBUG:
    NOTEBOOK_ARGUMENTS = [
        '--notebook-dir', 'notebooks',
    ]

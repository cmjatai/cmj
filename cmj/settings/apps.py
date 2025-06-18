import sys
from decouple import AutoConfig
from unipath import Path

config = AutoConfig()
DEBUG = config('DEBUG', default=False, cast=bool)
FRONTEND_VERSION = config('FRONTEND_VERSION', default='v1', cast=str)

PYTHON_VERSION = sys.version_info[0:3]
PYTHON_VERSION_MIN_FOR_JWT = 3, 7, 0

INSTALLED_APPS = (
    'daphne',
    'channels',

    #'django_admin_bootstrapped',  # must come before django.contrib.admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'django_extensions',
    'django.forms',

    'django_vite',

    'social_django',

    'crispy_forms',
    'crispy_bootstrap4',
    'crispy_bootstrap5',

    'easy_thumbnails',
    'image_cropping',

    'drf_spectacular',
    'rest_framework',

    'rest_framework.authtoken',
    #'rest_framework_simplejwt' if PYTHON_VERSION >= PYTHON_VERSION_MIN_FOR_JWT else 'rest_framework.authtoken',

    'django_filters',

    'haystack',
    'django_celery_results',
    'celery_haystack',
    'django_celery_beat',


    # 'whoosh',
    # 'speedinfo',
    # 'taggit',

    'sapl',  # não retire, é necessário para os templates centralizados do sapl
)

INSTALLED_APPS = INSTALLED_APPS + ('webpack_loader', )

SAPL_APPS = (
    'sapl.audiencia',
    'sapl.base',
    'sapl.crud',
    'sapl.parlamentares',
    'sapl.comissoes',
    'sapl.materia',
    'sapl.norma',
    'sapl.sessao',
    'sapl.lexml',
    'sapl.painel',
    'sapl.protocoloadm',
    'sapl.redireciona_urls',
    'sapl.compilacao',
    'sapl.api',
)

# CMJ_APPS business apps in dependency order
CMJ_APPS = (
    'cmj.core',

    'cmj.diarios',
    'cmj.loa',
    'cmj.cerimonial',
    'cmj.ouvidoria',
    'cmj.arq',
    'cmj.agenda',
    'cmj.videos',
    'cmj.sigad',
    'cmj.search',
    'cmj.api',

    'cmj.dashboard',
)

RULES_APPS = (
    'sapl.rules',
    'cmj.globalrules',
)
BUSINESS_APPS = SAPL_APPS + CMJ_APPS + RULES_APPS
INSTALLED_APPS = INSTALLED_APPS + BUSINESS_APPS

# if DEBUG and 'debug_toolbar' not in INSTALLED_APPS:
#    INSTALLED_APPS += ('debug_toolbar',)

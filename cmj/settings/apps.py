import sys

PYTHON_VERSION = sys.version_info[0:3]
PYTHON_VERSION_MIN_FOR_JWT = 3, 7, 0


INSTALLED_APPS = (
    'django_admin_bootstrapped',  # must come before django.contrib.admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'social_django',

    'crispy_forms',
    'floppyforms',

    'easy_thumbnails',
    'image_cropping',

    'rest_framework',
    'rest_framework_simplejwt' if PYTHON_VERSION >= PYTHON_VERSION_MIN_FOR_JWT else 'rest_framework.authtoken',

    'django_filters',

    'django_celery_results',
    'haystack',
    'celery_haystack',

    'webpack_loader',

    'channels',

    # 'whoosh',
    # 'speedinfo',
    # 'taggit',

    'sapl',  # não retire, é necessário para os templates centralizados do sapl
)

SAPL_APPS = (
    'sapl.audiencia',
    'sapl.base',
    'sapl.crud',
    'sapl.parlamentares',
    'sapl.comissoes',
    'sapl.materia',
    'sapl.norma',
    'sapl.sessao',
    #'sapl.lexml',
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
    'cmj.cerimonial',
    'cmj.ouvidoria',
    'cmj.agenda',
    'cmj.videos',
    'cmj.sigad',
    'cmj.api',
)

RULES_APPS = (
    'sapl.rules',
    'cmj.globalrules',
)

INSTALLED_APPS = INSTALLED_APPS + SAPL_APPS + CMJ_APPS + RULES_APPS

# if DEBUG and 'debug_toolbar' not in INSTALLED_APPS:
#    INSTALLED_APPS += ('debug_toolbar',)

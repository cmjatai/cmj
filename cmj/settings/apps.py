from sapl import settings as sapl_settings
from sapl.settings import SAPL_VERSION


INSTALLED_APPS = (
    'django_admin_bootstrapped',  # must come before django.contrib.admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'social_django',

    # more
    'django_extensions',
    'crispy_forms',

    'easy_thumbnails',  # ?
    'image_cropping',  # ?
    'floppyforms',  # ?

    'rest_framework',
    'rest_framework_recursive',

    'haystack',
    'whoosh',
    'reversion',
    'reversion_compare',
    'speedinfo',

    'taggit',
    'webpack_loader',

    'channels',
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

    'cmj.cerimonial',
    'cmj.ouvidoria',
    'cmj.agenda',
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

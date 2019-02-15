from sapl import settings as sapl_settings

# CMJ_APPS business apps in dependency order
CMJ_APPS = (
    'cmj.core',
    'sapl',

    'cmj.cerimonial',
    'cmj.ouvidoria',
    'cmj.agenda',
    'cmj.sigad',
    'cmj.api',

    # manter sempre como o ultimo da lista de apps
    'cmj.globalrules',
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

    'sapl.rules'
)

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

)

INSTALLED_APPS = INSTALLED_APPS + tuple(
    list(
        set(sapl_settings.SAPL_APPS) - set(INSTALLED_APPS))) + CMJ_APPS

# if DEBUG and 'debug_toolbar' not in INSTALLED_APPS:
#    INSTALLED_APPS += ('debug_toolbar',)

from decouple import AutoConfig
from sapl.settings import WEBPACK_LOADER as SAPL_WEBPACK_LOADER
from unipath import Path


config = AutoConfig()
DEBUG = config('DEBUG', default=False, cast=bool)

BASE_DIR = Path(__file__).ancestor(2)
PROJECT_DIR = Path(__file__).ancestor(3)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['cmj/templates', 'sapl/templates'],
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                'django.contrib.auth.context_processors.auth',

                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                "django.template.context_processors.media",
                "django.template.context_processors.static",

                'django.contrib.messages.context_processors.messages',

                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',

                'cmj.context_processors.areatrabalho',
                'cmj.context_processors.debug',
            ],
            'loaders': [
                # Não troque a ordem, trocar a ordem faz, por exemplo,
                # base.html do sapl ser lido primeiro que o base.html
                # deste projeto
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader'
            ]
        },
    },
]

DAB_FIELD_RENDERER = \
    'django_admin_bootstrapped.renderers.BootstrapFieldRenderer'
CRISPY_TEMPLATE_PACK = 'bootstrap4'
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap4'
CRISPY_FAIL_SILENTLY = not DEBUG

STATIC_URL = '/static/'
STATIC_ROOT = PROJECT_DIR.child("collected_static")

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': 'dist/',
        'STATS_FILE': PROJECT_DIR.child('frontend').child('webpack-stats.json'),
    },
    'SAPL_DEFAULT':  SAPL_WEBPACK_LOADER['DEFAULT']
}


USE_CHANNEL_LAYERS = config(
    'USE_CHANNEL_LAYERS', cast=bool, default=False)
HOST_CHANNEL_LAYERS = config(
    'HOST_CHANNEL_LAYERS', cast=str, default='localhost')
PORT_CHANNEL_LAYERS = config(
    'PORT_CHANNEL_LAYERS', cast=int, default=6379)

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(HOST_CHANNEL_LAYERS, PORT_CHANNEL_LAYERS)],
        },
    },
}

STATICFILES_DIRS = (
    # BASE_DIR.child('static'),
    PROJECT_DIR.child('frontend').child('dist'),
)

# apenas para debug - na produção nginx deve entregar sw
PWA_SERVICE_WORKER_PATH = PROJECT_DIR.child(
    'frontend').child('dist').child('service-worker.js')
PWA_MANIFEST_PATH = PROJECT_DIR.child(
    'frontend').child('dist').child('manifest.json')

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

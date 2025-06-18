from decouple import AutoConfig
from unipath import Path


config = AutoConfig()
DEBUG = config('DEBUG', default=False, cast=bool)

BASE_DIR = Path(__file__).ancestor(2)
PROJECT_DIR = Path(__file__).ancestor(3)


def front_version():
    return ['_templates/v2025', '_templates/v1']

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': front_version(),
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
                'cmj.context_processors.site_url',

                'sapl.context_processors.parliament_info',
                'sapl.context_processors.mail_service_configured',

                'cmj.dashboard.context_processors.dashboard',

            ],
            'loaders': [
                'cmj.utils.CmjLoader',
                'django.template.loaders.app_directories.Loader'
            ]
        },
    },
]

DAB_FIELD_RENDERER = \
    'django_admin_bootstrapped.renderers.BootstrapFieldRenderer'

CRISPY_ALLOWED_TEMPLATE_PACKS = ['bootstrap4', 'bootstrap5']
CRISPY_TEMPLATE_PACK = 'bootstrap4'

CRISPY_FAIL_SILENTLY = not DEBUG

STATIC_URL = '/static/'
STATIC_ROOT = PROJECT_DIR.child("collected_static")

PROJECT_DIR_FRONTEND_V1 = PROJECT_DIR.child('_frontend').child('v1')

FRONTEND_BRASAO_PATH = {
    '32': PROJECT_DIR_FRONTEND_V1.child('public').child('brasao').child('brasao_32.png'),
    '64': PROJECT_DIR_FRONTEND_V1.child('public').child('brasao').child('brasao_64.png'),
    '128': PROJECT_DIR_FRONTEND_V1.child('public').child('brasao').child('brasao_128.png'),
    '256': PROJECT_DIR_FRONTEND_V1.child('public').child('brasao').child('brasao_256.png'),
    '512': PROJECT_DIR_FRONTEND_V1.child('public').child('brasao').child('brasao_512.png'),
    '1024': PROJECT_DIR_FRONTEND_V1.child('public').child('brasao').child('brasao_1024.png')
}

FRONTEND_ESCOLA_PATH = {
    '1024': PROJECT_DIR_FRONTEND_V1.child('public').child('brasao').child('escola_1024.png')
}

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': 'dist/',
        'STATS_FILE': PROJECT_DIR_FRONTEND_V1.child(f'{"dev-" if DEBUG else ""}webpack-stats.json'),
    }
}

if DEBUG and not WEBPACK_LOADER['DEFAULT']['STATS_FILE'].exists():
    WEBPACK_LOADER['DEFAULT']['STATS_FILE'] = PROJECT_DIR_FRONTEND_V1.child(
        f'webpack-stats.json')


# apenas para debug - na produção nginx deve entregar sw
PWA_SERVICE_WORKER_PATH = PROJECT_DIR.child(
    '_frontend').child('v1').child('dist').child('service-worker.js')
PWA_MANIFEST_PATH = PROJECT_DIR.child(
    '_frontend').child('v1').child('dist').child('manifest.json')

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

DJANGO_VITE_ASSETS_PATH = PROJECT_DIR.child('_frontend').child('dist')

STATICFILES_DIRS = (
    PROJECT_DIR.child('sapl').child('static'),
    PROJECT_DIR.child('_frontend').child('v1').child('dist'),
)

if DEBUG:
    STATICFILES_DIRS += (PROJECT_DIR.child('_frontend').child('v2025').child('src').child('assets'),)

DJANGO_VITE_DEV_MODE = config('DJANGO_VITE_DEV_MODE', default=True, cast=bool)
DJANGO_VITE_DEV_MODE = DJANGO_VITE_DEV_MODE and DEBUG
DJANGO_VITE = {
    'default': {
        'dev_mode': DJANGO_VITE_DEV_MODE,
        'manifest_path': (
            DJANGO_VITE_ASSETS_PATH if DJANGO_VITE_DEV_MODE else STATIC_ROOT
        ).child('.vite').child('manifest.json'),
    }
}

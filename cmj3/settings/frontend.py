from .ambiente import env, BASE_DIR, PROJECT_ROOT, DEBUG

FRONTEND_VERSION = env.str('FRONTEND_VERSION', default='v3')


CORS_ORIGIN_WHITELIST = ['http://localhost:3000', 'http://127.0.0.1:3000']


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['_templates/v3'],
        'APP_DIRS': False,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

STATIC_URL = '/static/'
STATIC_ROOT = PROJECT_ROOT.joinpath('collected_static')
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)


"""
PROJECT_DIR_FRONTEND = PROJECT_ROOT.joinpath(
    '_frontend').joinpath(FRONTEND_VERSION)

STATICFILES_DIRS = (
    PROJECT_ROOT.joinpath('_frontend').joinpath(
        FRONTEND_VERSION).joinpath('dist'),
)



# apenas para debug - na produção nginx deve entregar sw
PWA_SERVICE_WORKER_PATH = PROJECT_DIR_FRONTEND.joinpath(
    'dist').joinpath('service-worker.js')
PWA_MANIFEST_PATH = PROJECT_DIR_FRONTEND.joinpath(
    'dist').joinpath('manifest.json')


WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': 'dist/',
        'STATS_FILE': PROJECT_DIR_FRONTEND.joinpath(f'{"dev-" if DEBUG else ""}webpack-stats.json'),
    }
}

if DEBUG and not WEBPACK_LOADER['DEFAULT']['STATS_FILE'].exists():
    WEBPACK_LOADER['DEFAULT']['STATS_FILE'] = PROJECT_DIR_FRONTEND.joinpath(
        f'webpack-stats.json')
"""

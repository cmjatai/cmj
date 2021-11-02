from .ambiente import env, BASE_DIR, PROJECT_ROOT, DEBUG

CORS_ALLOWED_ORIGINS = ['http://localhost:8080', 'http://127.0.0.1:8080']

FRONTEND_VERSION = env.str('FRONTEND_VERSION', default='v3')

PROJECT_DIR_FRONTEND = PROJECT_ROOT.joinpath(
    '_frontend').joinpath(FRONTEND_VERSION)

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


STATICFILES_DIRS = (
    PROJECT_ROOT.joinpath('_frontend').joinpath(
        FRONTEND_VERSION).joinpath('dist'),
)
WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': 'dist/',
        'STATS_FILE': PROJECT_DIR_FRONTEND.joinpath(f'{"dev-" if DEBUG else ""}webpack-stats.json'),
    }
}

if DEBUG and not WEBPACK_LOADER['DEFAULT']['STATS_FILE'].exists():
    WEBPACK_LOADER['DEFAULT']['STATS_FILE'] = PROJECT_DIR_FRONTEND.joinpath(
        'webpack-stats.json')


PWA_SERVICE_WORKER_PATH = PROJECT_DIR_FRONTEND.joinpath(
    'dist').joinpath('service-worker.js')


"""
# apenas para debug - na produção nginx deve entregar sw
PWA_MANIFEST_PATH = PROJECT_DIR_FRONTEND.joinpath(
    'dist').joinpath('manifest.json')


"""

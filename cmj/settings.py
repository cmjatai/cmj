"""
Django settings for CMJ project.
"""
from decouple import AutoConfig
from dj_database_url import parse as db_url
from django.utils.translation import ugettext_lazy as _
from easy_thumbnails.conf import Settings as thumbnail_settings
from sapl import settings as sapl_settings
from unipath import Path


"""@property    gerar nomes para urls
def pretty_name(self):
    return "{0}.{1}".format(slugify(self.title),
            get_extension(self.file.name))"""

config = AutoConfig()

BASE_DIR = Path(__file__).ancestor(1)
PROJECT_DIR = Path(__file__).ancestor(2)
# print(BASE_DIR)
# print(PROJECT_DIR)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = ['*']

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/login/?next='

# CMJ_APPS business apps in dependency order
CMJ_APPS = (
    'cmj.core',
    'sapl',

    'cmj.cerimonial',
    'cmj.sigad',


    # manter sempre como o último da lista de apps
    'cmj.globalrules'

)

INITIAL_VALUE_FORMS_UF = config('INITIAL_VALUE_FORMS_UF')
INITIAL_VALUE_FORMS_MUNICIPIO = config('INITIAL_VALUE_FORMS_MUNICIPIO')
INITIAL_VALUE_FORMS_CEP = config('INITIAL_VALUE_FORMS_CEP')

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
    'djangobower',
    'bootstrap3',  # basically for django_admin_bootstrapped
    'crispy_forms',
    'easy_thumbnails',
    'image_cropping',
    'floppyforms',
    'sass_processor',
    'rest_framework',
    'reversion',

    # 'haystack',
    # "elasticstack",
    'taggit',
    'webpack_loader',
)

INSTALLED_APPS = INSTALLED_APPS + tuple(
    list(
        set(sapl_settings.INSTALLED_APPS) - set(INSTALLED_APPS))) + CMJ_APPS


# if DEBUG and 'debug_toolbar' not in INSTALLED_APPS:
#    INSTALLED_APPS += ('debug_toolbar',)


MIDDLEWARE_CLASSES = (
    'reversion.middleware.RevisionMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)


REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        # "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
        "sapl.api.permissions.DjangoModelPermissions",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "sapl.api.pagination.StandardPagination",
    "DEFAULT_FILTER_BACKENDS": (
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.DjangoFilterBackend",
    ),
}


SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

ROOT_URLCONF = 'cmj.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['cmj/templates'],
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                "django.core.context_processors.media",
                "django.core.context_processors.static",
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',


                'cmj.context_processors.areatrabalho',
            ],
            'debug': DEBUG,
            'loaders': ['django.template.loaders.filesystem.Loader',
                        'django.template.loaders.app_directories.Loader']
        },
    },
]

WSGI_APPLICATION = 'cmj.wsgi.application'

AUTH_USER_MODEL = 'core.User'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
DATABASES = {
    'default': config(
        'DATABASE_URL',
        cast=db_url,
    )
}


AUTHENTICATION_BACKENDS = (
    'social_core.backends.facebook.FacebookOAuth2',
    'django.contrib.auth.backends.ModelBackend',
    'social_core.backends.google.GoogleOAuth2',
)

""" 'social.backends.twitter.TwitterOAuth' """

SOCIAL_AUTH_FACEBOOK_KEY = config('SOCIAL_AUTH_FACEBOOK_KEY', cast=str)
SOCIAL_AUTH_FACEBOOK_SECRET = config('SOCIAL_AUTH_FACEBOOK_SECRET', cast=str)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config(
    'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', cast=str)
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config(
    'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', cast=str)

SOCIAL_AUTH_TWITTER_KEY = config('SOCIAL_AUTH_TWITTER_KEY', cast=str)
SOCIAL_AUTH_TWITTER_SECRET = config('SOCIAL_AUTH_TWITTER_SECRET', cast=str)

USER_FIELDS = ('email',)
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']

SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'id,name,first_name,last_name,email'
}

SOCIAL_BACKEND_INFO = {
    'facebook': {
        'title': 'Facebook',
        'icon': 'img/icon-facebook.png',
    },
    'google-oauth2': {
        'title': 'Google',
        'icon': 'img/icon-google-plus.png',
    },
}
# twitter não está funcinando com a customização do auth.User,
# ao menos localmente... testar em um domínio válido.

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/
LANGUAGE_CODE = 'pt-br'
LANGUAGES = (
    ('pt-br', u'Português'),
)

TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = False
USE_TZ = True
# DATE_FORMAT = 'N j, Y'
DATE_FORMAT = 'd/m/Y'
SHORT_DATE_FORMAT = 'd/m/Y'
DATE_INPUT_FORMATS = ('%d/%m/%Y', '%m-%d-%Y', '%Y-%m-%d')

LOCALE_PATHS = (
    BASE_DIR.child('locale'),
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = PROJECT_DIR.child("collected_static")
STATICFILES_DIRS = (
    BASE_DIR.child("static"),
    BASE_DIR.child("static").child('2017'),
    sapl_settings.STATICFILES_DIRS[0],
    PROJECT_DIR.child('assets'))

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'djangobower.finders.BowerFinder',
    'sass_processor.finders.CssFinder',
)

WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': 'bundles/',
        'STATS_FILE': PROJECT_DIR.child('webpack-stats.json'),
    }
}

MEDIA_ROOT = PROJECT_DIR.child("media")
MEDIA_URL = '/media/'

MEDIA_PROTECTED_ROOT = PROJECT_DIR.child("media_protected")

DAB_FIELD_RENDERER = \
    'django_admin_bootstrapped.renderers.BootstrapFieldRenderer'
CRISPY_TEMPLATE_PACK = 'bootstrap3'
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap3'
CRISPY_FAIL_SILENTLY = not DEBUG

BOWER_COMPONENTS_ROOT = PROJECT_DIR.child("bower")
BOWER_INSTALLED_APPS = (
    'jquery#3.1.1',
    'bootstrap-sass#3.3.7',
    'components-font-awesome#4.7.0',
    'tinymce#4.4.3',
    'jquery-ui#1.12.1',
    'jQuery-Mask-Plugin#1.14.0',
    'jsdiff#2.2.2',
    'https://github.com/cmjatai/drunken-parrot-flat-ui.git',
)

# Additional search paths for SASS files when using the @import statement
SASS_PROCESSOR_INCLUDE_DIRS = (
    BOWER_COMPONENTS_ROOT.child(
        'bower_components', 'bootstrap-sass', 'assets', 'stylesheets'),
)

# FIXME update cripy-forms and remove this
# hack to suppress many annoying warnings from crispy_forms
# see sapl.temp_suppress_crispy_form_warnings

# suprime texto de ajuda default do django-filter
FILTERS_HELP_TEXT_FILTER = False


THUMBNAIL_PROCESSORS = (
    'image_cropping.thumbnail_processors.crop_corners',
) + thumbnail_settings.THUMBNAIL_PROCESSORS

EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
EMAIL_HOST = config('EMAIL_HOST', cast=str)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', cast=str)
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', cast=str)
EMAIL_PORT = config('EMAIL_PORT', cast=int)

MAX_DOC_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB
MAX_IMAGE_UPLOAD_SIZE = 2 * 1024 * 1024  # 2MB

# django-haystack: http://django-haystack.readthedocs.org/
"""HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'haystack',
    },
}"""

"""HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': PROJECT_DIR.child('whoosh_index'),
    },
}
"""

"""HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'elasticstack.backends.ConfigurableElasticSearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'haystack',
    },
}
"""

#HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
#ELASTICSEARCH_DEFAULT_ANALYZER = "snowball"

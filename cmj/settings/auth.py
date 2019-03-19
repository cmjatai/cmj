from decouple import AutoConfig

config = AutoConfig()
DEBUG = config('DEBUG', default=False, cast=bool)

AUTH_USER_MODEL = 'core.User'
SOCIAL_AUTH_POSTGRES_JSONFIELD = True

str_pv = 'django.contrib.auth.password_validation'
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': str_pv + '.MinimumLengthValidator',
        'OPTIONS': {'min_length': 6, }
     },
    {'NAME': str_pv + '.UserAttributeSimilarityValidator', },
    {'NAME': str_pv + '.CommonPasswordValidator', },
    {'NAME': str_pv + '.NumericPasswordValidator', },
]


GOOGLE_URL_SHORTENER_KEY = config('GOOGLE_URL_SHORTENER_KEY', cast=str)
GOOGLE_URL_API_KEY = config('GOOGLE_URL_API_KEY', cast=str)

GOOGLE_RECAPTCHA_SITE_KEY = config('GOOGLE_RECAPTCHA_SITE_KEY', cast=str)
GOOGLE_RECAPTCHA_SECRET_KEY = config('GOOGLE_RECAPTCHA_SECRET_KEY', cast=str)

SOCIAL_AUTH_POSTGRES_JSONFIELD = True

AUTHENTICATION_BACKENDS = (
    #    'social_core.backends.facebook.FacebookOAuth2',
    'cmj.utils.FacebookOAuth2',
    'django.contrib.auth.backends.ModelBackend',
    'social_core.backends.google.GoogleOAuth2',
)

""" 'social.backends.twitter.TwitterOAuth' """

if DEBUG:
    SOCIAL_AUTH_FACEBOOK_KEY = config(
        'SOCIAL_AUTH_FACEBOOK_KEY_TEST', cast=str)
    SOCIAL_AUTH_FACEBOOK_SECRET = config(
        'SOCIAL_AUTH_FACEBOOK_SECRET_TEST', cast=str)
else:
    SOCIAL_AUTH_FACEBOOK_KEY = config(
        'SOCIAL_AUTH_FACEBOOK_KEY', cast=str)
    SOCIAL_AUTH_FACEBOOK_SECRET = config(
        'SOCIAL_AUTH_FACEBOOK_SECRET', cast=str)


SOCIAL_AUTH_FACEBOOK_API_VERSION = '3.2'

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config(
    'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', cast=str)
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config(
    'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', cast=str)

SOCIAL_AUTH_TWITTER_KEY = config('SOCIAL_AUTH_TWITTER_KEY', cast=str)
SOCIAL_AUTH_TWITTER_SECRET = config('SOCIAL_AUTH_TWITTER_SECRET', cast=str)

USER_FIELDS = ('email',)

SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']
REDIRECT_IS_HTTPS = True
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'locale': 'pt_BR',
    'fields': 'id, name, first_name, last_name, email'
}

SOCIAL_BACKEND_INFO = {
    'facebook': {
        'title': 'Facebook',
        'icon': 'fa-facebook',
    },
    'google-oauth2': {
        'title': 'Google',
        'icon': 'fa-google',
    },
}

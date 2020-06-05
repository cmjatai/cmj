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
    'cmj.mixins.FacebookOAuth2',
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


SOCIAL_AUTH_FACEBOOK_API_VERSION = '6.0'

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config(
    'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', cast=str)
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config(
    'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', cast=str)

SOCIAL_AUTH_TWITTER_KEY = config('SOCIAL_AUTH_TWITTER_KEY', cast=str)
SOCIAL_AUTH_TWITTER_SECRET = config('SOCIAL_AUTH_TWITTER_SECRET', cast=str)

USER_FIELDS = ('email',)

SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']

REDIRECT_IS_HTTPS = not DEBUG
SOCIAL_AUTH_REDIRECT_IS_HTTPS = not DEBUG


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

SOCIAL_AUTH_PIPELINE = (
    # Get the information we can about the user and return it in a simple
    # format to create the user instance later. On some cases the details are
    # already part of the auth response from the provider, but sometimes this
    # could hit a provider API.
    'social_core.pipeline.social_auth.social_details',

    # Get the social uid from whichever service we're authing thru. The uid is
    # the unique identifier of the given user in the provider.
    'social_core.pipeline.social_auth.social_uid',

    # Verifies that the current auth process is valid within the current
    # project, this is where emails and domains whitelists are applied (if
    # defined).
    'social_core.pipeline.social_auth.auth_allowed',

    # Checks if the current social-account is already associated in the site.
    'social_core.pipeline.social_auth.social_user',

    # Make up a username for this person, appends a random string at the end if
    # there's any collision.
    'social_core.pipeline.user.get_username',

    # Send a validation email to the user to verify its email address.
    # 'social_core.pipeline.mail.mail_validation',

    # Associates the current social details with another user account with
    # a similar email address.
    'social_core.pipeline.social_auth.associate_by_email',

    # Create a user account if we haven't found one yet.
    'social_core.pipeline.user.create_user',

    # Create the record that associated the social account with this user.
    'social_core.pipeline.social_auth.associate_user',

    # Populate the extra_data field in the social record with the values
    # specified by settings (and the default ones like access_token, etc).
    'social_core.pipeline.social_auth.load_extra_data',

    # Update the user record with any changed info from the auth service.
    'social_core.pipeline.user.user_details'
)


# LOCAWEB
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', cast=str, default='')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', cast=str, default='')
ABSOLUTE_PATH_BACKUP = config('ABSOLUTE_PATH_BACKUP', cast=str, default='')

# cert_public
CERT_PRIVATE_KEY_NAME = config('CERT_PRIVATE_KEY_NAME', cast=str, default='')
CERT_PRIVATE_KEY_ID = config('CERT_PRIVATE_KEY_ID', cast=str, default='')
CERT_PRIVATE_KEY_ACCESS = config(
    'CERT_PRIVATE_KEY_ACCESS', cast=str, default='')

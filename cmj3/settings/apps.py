
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',

    'webpack_loader',

    'rest_framework',

    'channels'

]

CMJ_APPS = [
    #'cmj.core'
]

INSTALLED_APPS += CMJ_APPS

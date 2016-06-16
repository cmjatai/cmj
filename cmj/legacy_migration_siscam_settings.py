# Settings for data migration from mysql legacy to new postgres database

from .settings import *  # flake8: noqa

INSTALLED_APPS += (
    'cmj.legacy_siscam',  # legacy reversed model definitions
)
DATABASES['legacy_siscam'] = {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': 'siscam',
    'USER': 'cmj',
    'PASSWORD': 'cmj',
    'HOST': 'localhost',   # Or an IP Address that your DB is hosted on
    'PORT': '5432',
}

DATABASE_ROUTERS = ['cmj.legacy_siscam.router.LegacyRouter', ]

MOMMY_CUSTOM_FIELDS_GEN = {
    'django.db.models.ForeignKey': 'cmj.legacy_siscam.migration.make_with_log'
}

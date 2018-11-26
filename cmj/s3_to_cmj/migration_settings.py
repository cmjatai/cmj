
from decouple import Config, RepositoryEnv
from dj_database_url import parse as db_url

from cmj.settings import *  # flake8: noqa


config = Config(RepositoryEnv(BASE_DIR.child('.env')))


INSTALLED_APPS += (
    'cmj.s3_to_cmj',
)

DATABASES['s3_to_cmj'] = config('DATABASE_URL_FONTE', cast=db_url,)

DATABASE_ROUTERS = ['cmj.s3_to_cmj.router.LegacyRouter', ]

DEBUG = True

import os

from decouple import Config, RepositoryEnv, AutoConfig
from dj_database_url import parse as db_url

from .settings import *  # flake8: noqa


config = AutoConfig()
config.config = Config(
    RepositoryEnv(os.path.abspath('cmj/legacy_siscam/.env')))

INSTALLED_APPS += (
    'cmj.legacy_siscam',  # legacy reversed model definitions
)

DATABASES['legacy_siscam'] = config('DATABASE_URL', cast=db_url,)

DATABASE_ROUTERS = ['cmj.legacy_siscam.router.LegacyRouter', ]

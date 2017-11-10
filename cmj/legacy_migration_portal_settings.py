import os

from decouple import Config, RepositoryEnv, AutoConfig
from dj_database_url import parse as db_url

from .settings import *  # flake8: noqa


config = AutoConfig()
config.config = Config(RepositoryEnv(
    os.path.abspath('cmj/legacy_portal/.env')))

INSTALLED_APPS += (
    'cmj.legacy_portal',  # legacy reversed model definitions
)

DATABASES['legacy_portal'] = config('DATABASE_URL', cast=db_url,)

DATABASE_ROUTERS = ['cmj.legacy_portal.router.LegacyRouter', ]

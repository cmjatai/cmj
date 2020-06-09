import os

from decouple import Config, RepositoryEnv, AutoConfig
from dj_database_url import parse as db_url

from .settings import *  # flake8: noqa


config = AutoConfig()
config.config = Config(RepositoryEnv(
    os.path.abspath('cmj/legacy_cep/.env')))

INSTALLED_APPS += (
    'cmj.legacy_cep',  # legacy reversed model definitions
)

DATABASES['legacy_cep'] = config('DATABASE_URL', cast=db_url,)

DATABASE_ROUTERS = ['cmj.legacy_cep.router.LegacyRouter', ]

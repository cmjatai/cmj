
from decouple import Config, RepositoryEnv
from dj_database_url import parse as db_url
from cmj.settings import *  # flake8: noqa


config = Config(RepositoryEnv(BASE_DIR.child('.env')))


INSTALLED_APPS += (
    'cmj.legacy_sislegis_publicacoes',
)

DATABASES['legacy_sislegis_publicacoes'] = config(
    'DATABASE_URL_SISLEGIS_PUBLICACOES', cast=db_url,)

DATABASE_ROUTERS = ['cmj.legacy_sislegis_publicacoes.router.LegacyRouter', ]

DEBUG = True

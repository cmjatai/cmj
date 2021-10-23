from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR.joinpath('cmj3', '.env'))

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = env.str('TZ', 'UTC')

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR.joinpath('static')

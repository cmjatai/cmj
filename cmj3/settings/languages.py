from .ambiente import env


LANGUAGE_CODE = 'pt-br'

TIME_ZONE = env.str('TZ', 'UTC')

USE_I18N = True

USE_L10N = True

USE_TZ = True

from unipath import Path
BASE_DIR = Path(__file__).ancestor(2)

LANGUAGE_CODE = 'pt-br'
LANGUAGES = (
    ('pt-br', u'Português'),
)

TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = True
USE_TZ = True
DATE_FORMAT = 'd/m/Y'
SHORT_DATE_FORMAT = 'd/m/Y'
DATETIME_FORMAT = 'd/m/Y - H:i:s'
DATE_INPUT_FORMATS = ('%d/%m/%Y', '%m-%d-%Y', '%Y-%m-%d')

LOCALE_PATHS = (
    BASE_DIR.child('locale'),
)

DECIMAL_SEPARATOR = ','
THOUSAND_SEPARATOR = '.'
USE_THOUSAND_SEPARATOR = True
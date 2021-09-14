
import logging
import sys

"""class MyFormatter(logging.Formatter):

        'verbose': {
            'class': 'cmj.settings.logs.MyFormatter',

    def __init__(self, fmt=None, datefmt=None, style='%'):
        logging.Formatter.__init__(self, fmt=fmt, datefmt=datefmt, style=style)

    def format(self, record):
        s = logging.Formatter.format(self, record)

        for i in inspect.stack():
                r = i.frame.f_locals.get('request', None)
                if r:
                    print(r)
        return s"""

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,

    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },

    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(pathname)s %(name)s:%(funcName)s:%(lineno)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(asctime)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'filters': ['require_debug_true'],

        },
        'cmj_logger_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/cmj_logger.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
            'filters': ['require_debug_false'],

        },
    },
    'loggers': {
        'sapl': {
            'handlers': ['console', 'cmj_logger_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'cmj': {
            'handlers': ['console', 'cmj_logger_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['console', 'cmj_logger_file'],
        'level': 'WARNING',
        }
}


def uncaught_exceptions(type, value, error_traceback):
    import traceback
    logger = logging.getLogger(__name__)
    error_msg = ''.join(traceback.format_tb(error_traceback))
    logger.error(error_msg)
    print(error_msg)


# captura exceções que não foram tratadas
sys.excepthook = uncaught_exceptions

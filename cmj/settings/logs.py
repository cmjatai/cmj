import logging
import socket
import sys

host = socket.gethostbyname_ex(socket.gethostname())[0]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s ' + host + ' %(pathname)s %(name)s:%(funcName)s:%(lineno)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(asctime)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'applogfile': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'sapl.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'sapl': {
            'handlers': ['applogfile'],
            'level': 'INFO',
            'propagate': True,
        },
        'cmj': {
            'handlers': ['applogfile'],
            'level': 'INFO',
            'propagate': True,
        },
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

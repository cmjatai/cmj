
from random import random

from decouple import AutoConfig, Csv


global idx_email
id_email = 0


config = AutoConfig()

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = config('EMAIL_HOST', cast=str, default='')
EMAIL_PORT = config('EMAIL_PORT', cast=int, default=587)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', cast=str,
                         default='noreply@jatai.go.leg.br')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', cast=str, default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool, default=True)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', cast=bool, default=False)
EMAIL_SEND_USER = config('EMAIL_SEND_USER', cast=str, default='')
EMAIL_RUNNING = None

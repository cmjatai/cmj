
import logging
import multiprocessing
from random import random

from decouple import AutoConfig, Csv


global idx_email
id_email = 0


config = AutoConfig()

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = config('EMAIL_HOST', cast=str)
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', cast=Csv(str))
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', cast=str)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', cast=bool)
EMAIL_SEND_USER = config('EMAIL_SEND_USER', cast=str)
EMAIL_RUNNING = None

len_emails = len(EMAIL_HOST_USER)
pos = int(random() * len_emails)
pos = pos % len_emails

print(pos, EMAIL_HOST_USER)
EMAIL_HOST_USER = EMAIL_HOST_USER[0]

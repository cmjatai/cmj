import certifi
import os

from decouple import AutoConfig

config = AutoConfig()

EMAIL_BACKEND = 'cmj.utils.CmjEmailBackend'

EMAIL_HOST = config('EMAIL_HOST', cast=str, default='smtp.jatai.go.leg.br')
EMAIL_PORT = config('EMAIL_PORT', cast=int, default=465)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', cast=str,
                         default='noreply@jatai.go.leg.br')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', cast=str, default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool, default=False)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', cast=bool, default=True)
EMAIL_SEND_USER = config('EMAIL_SEND_USER', cast=str,
                         default='Portal CMJ <noreply@jatai.go.leg.br>')
EMAIL_TIMEOUT = config('EMAIL_TIMEOUT', cast=int, default=60)
EMAIL_RUNNING = None

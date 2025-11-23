import logging

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from sapl.base.models import CasaLegislativa
from sapl.utils import mail_service_configured as mail_service_configured_utils


def parliament_info(request):
    casa = CasaLegislativa.casa_cache()
    if casa:
        casa = casa.__dict__
        del casa['_state']
        del casa['id']
        del casa['metadata']
        return casa
    else:
        return {}


def mail_service_configured(request):

    if not mail_service_configured_utils(request):
        if not settings.DEBUG:
            logger = logging.getLogger(__name__)
            logger.warning(_('Servidor de email não configurado.'))
        return {'mail_service_configured': False}
    return {'mail_service_configured': True}

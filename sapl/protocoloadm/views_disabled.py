import logging
from random import choice
from string import ascii_letters, digits

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import Http404, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls.base import reverse
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView

from sapl.base.email_utils import do_envia_email_confirmacao
from sapl.base.models import CasaLegislativa
from sapl.protocoloadm.forms import AcompanhamentoDocumentoForm
from sapl.protocoloadm.models import AcompanhamentoDocumento,\
    DocumentoAdministrativo
from sapl.utils import mail_service_configured, get_base_url

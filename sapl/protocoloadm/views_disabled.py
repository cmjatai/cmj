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


class AcompanhamentoConfirmarView(TemplateView):

    logger = logging.getLogger(__name__)

    def get_redirect_url(self, email):
        username = self.request.user.username
        self.logger.info(
            'user=' + username + '. Este documento está sendo acompanhado pelo e-mail: {}'.format(email))
        msg = _('Este documento está sendo acompanhado pelo e-mail: %s') % (
            email)
        messages.add_message(self.request, messages.SUCCESS, msg)
        return reverse('sapl.protocoloadm:documentoadministrativo_detail',
                       kwargs={'pk': self.kwargs['pk']})

    def get(self, request, *args, **kwargs):

        documento_id = kwargs['pk']
        hash_txt = request.GET.get('hash_txt', '')
        username = request.user.username

        try:
            self.logger.debug("user=" + username + ". Tentando obter objeto AcompanhamentoDocumento com documento_id={} e hash={}"
                              .format(documento_id, hash_txt))
            acompanhar = AcompanhamentoDocumento.objects.get(
                documento_id=documento_id,
                hash=hash_txt)
        except ObjectDoesNotExist as e:
            self.logger.error("user=" + username + ". " + str(e))
            raise Http404()
        # except MultipleObjectsReturned:
        # A melhor solução deve ser permitir que a exceção
        # (MultipleObjectsReturned) seja lançada e vá para o log,
        # pois só poderá ser causada por um erro de desenvolvimente

        acompanhar.confirmado = True
        acompanhar.save()

        return HttpResponseRedirect(self.get_redirect_url(acompanhar.email))


class AcompanhamentoExcluirView(TemplateView):

    logger = logging.getLogger(__name__)

    def get_success_url(self):
        username = self.request.user.username
        self.logger.info(
            "user=" + username + ". Você parou de acompanhar este Documento (pk={}).".format(self.kwargs['pk']))
        msg = _('Você parou de acompanhar este Documento.')
        messages.add_message(self.request, messages.INFO, msg)
        return reverse('sapl.protocoloadm:documentoadministrativo_detail',
                       kwargs={'pk': self.kwargs['pk']})

    def get(self, request, *args, **kwargs):
        documento_id = kwargs['pk']
        hash_txt = request.GET.get('hash_txt', '')
        username = request.user.username
        try:
            self.logger.debug("user=" + username + ". Tentando obter AcompanhamentoDocumento com documento_id={} e hash={}."
                              .format(documento_id, hash_txt))
            AcompanhamentoDocumento.objects.get(documento_id=documento_id,
                                                hash=hash_txt).delete()
        except ObjectDoesNotExist:
            self.logger.error("user=" + username + ". AcompanhamentoDocumento com documento_id={} e hash={} não encontrado."
                              .format(documento_id, hash_txt))

        return HttpResponseRedirect(self.get_success_url())


class AcompanhamentoDocumentoView(CreateView):
    template_name = "protocoloadm/acompanhamento_documento.html"

    logger = logging.getLogger(__name__)

    def get_random_chars(self):
        s = ascii_letters + digits
        return ''.join(choice(s) for i in range(choice([6, 7])))

    def get(self, request, *args, **kwargs):
        if not mail_service_configured():
            self.logger.warning(_('Servidor de email não configurado.'))
            messages.error(request, _('Serviço de Acompanhamento de '
                                      'Documentos não foi configurado'))
            return redirect('/')

        pk = self.kwargs['pk']
        documento = DocumentoAdministrativo.objects.get(id=pk)

        return self.render_to_response(
            {'form': AcompanhamentoDocumentoForm(),
             'documento': documento})

    def post(self, request, *args, **kwargs):
        if not mail_service_configured():
            self.logger.warning(_('Servidor de email não configurado.'))
            messages.error(request, _('Serviço de Acompanhamento de '
                                      'Documentos não foi configurado'))
            return redirect('/')

        form = AcompanhamentoDocumentoForm(request.POST)
        pk = self.kwargs['pk']
        documento = DocumentoAdministrativo.objects.get(id=pk)

        if form.is_valid():
            email = form.cleaned_data['email']
            usuario = request.user

            hash_txt = self.get_random_chars()

            acompanhar = AcompanhamentoDocumento.objects.get_or_create(
                documento=documento,
                email=form.data['email'])

            # Se o segundo elemento do retorno do get_or_create for True
            # quer dizer que o elemento não existia
            if acompanhar[1]:
                acompanhar = acompanhar[0]
                acompanhar.hash = hash_txt
                acompanhar.usuario = usuario.username
                acompanhar.confirmado = False
                acompanhar.save()

                base_url = get_base_url(request)

                destinatario = AcompanhamentoDocumento.objects.get(
                    documento=documento,
                    email=email,
                    confirmado=False)
                casa = CasaLegislativa.objects.first()

                do_envia_email_confirmacao(base_url,
                                           casa,
                                           "documento",
                                           documento,
                                           destinatario)
                self.logger.info('user={}. Foi enviado um e-mail de confirmação. Confira sua caixa '
                                 'de mensagens e clique no link que nós enviamos para '
                                 'confirmar o acompanhamento deste documento.'.format(usuario.username))
                msg = _('Foi enviado um e-mail de confirmação. Confira sua caixa \
                         de mensagens e clique no link que nós enviamos para \
                         confirmar o acompanhamento deste documento.')
                messages.add_message(request, messages.SUCCESS, msg)

            # Se o elemento existir e o email não foi confirmado:
            # gerar novo hash e reenviar mensagem de email
            elif not acompanhar[0].confirmado:
                acompanhar = acompanhar[0]
                acompanhar.hash = hash_txt
                acompanhar.save()

                base_url = get_base_url(request)

                destinatario = AcompanhamentoDocumento.objects.get(
                    documento=documento,
                    email=email,
                    confirmado=False
                )

                casa = CasaLegislativa.objects.first()

                do_envia_email_confirmacao(base_url,
                                           casa,
                                           "documento",
                                           documento,
                                           destinatario)

                self.logger.info('user={}. Foi enviado um e-mail de confirmação. Confira sua caixa \
                                  de mensagens e clique no link que nós enviamos para \
                                  confirmar o acompanhamento deste documento.'.format(usuario.username))

                msg = _('Foi enviado um e-mail de confirmação. Confira sua caixa \
                        de mensagens e clique no link que nós enviamos para \
                        confirmar o acompanhamento deste documento.')
                messages.add_message(request, messages.SUCCESS, msg)

            # Caso esse Acompanhamento já exista
            # avisa ao usuário que esse documento já está sendo acompanhado
            else:
                self.logger.info('user=' + request.user.username +
                                 '. Este e-mail já está acompanhando esse documento (pk={}).'.format(pk))
                msg = _('Este e-mail já está acompanhando esse documento.')
                messages.add_message(request, messages.ERROR, msg)

                return self.render_to_response(
                    {'form': form,
                     'documento': documento,
                     })
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(
                {'form': form,
                 'documento': documento})

    def get_success_url(self):
        return reverse('sapl.protocoloadm:documentoadministrativo_detail',
                       kwargs={'pk': self.kwargs['pk']})

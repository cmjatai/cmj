
from datetime import datetime, timedelta, date
from random import choice
from string import ascii_letters, digits
import csv
import io
import logging
import os
import shutil
import sys
import tempfile
import traceback
import zipfile

from crispy_forms.layout import HTML
from django import template
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, ValidationError, \
    PermissionDenied
from django.db.models import Max, Q
from django.http import HttpResponse, JsonResponse
from django.http.response import Http404, HttpResponseRedirect, \
    HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls.base import reverse
from django.utils import formats, timezone
from django.utils.encoding import force_str
from django.utils.text import slugify
from django.utils.timezone import get_default_timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, TemplateView, CreateView, UpdateView
from django.views.generic.base import RedirectView
from django.views.generic.edit import FormView
from django_filters.views import FilterView
import weasyprint

from cmj import celery
from cmj.core.models import AreaTrabalho
from cmj.genia import GoogleGenerativeIA
from cmj.globalrules import GROUP_MATERIA_WORKSPACE_VIEWER
from cmj.mixins import BtnCertMixin, CheckCheckMixin, MultiFormatOutputMixin, \
    AudigLogFilterMixin
from sapl.base.email_utils import do_envia_email_confirmacao
from sapl.base.models import Autor, CasaLegislativa, AppConfig as BaseAppConfig
from sapl.comissoes.models import Comissao, Participacao, Composicao
from sapl.compilacao.models import (STATUS_TA_IMMUTABLE_RESTRICT,
                                    STATUS_TA_PRIVATE)
from sapl.compilacao.views import IntegracaoTaView
from sapl.crispy_layout_mixin import SaplFormHelper
from sapl.crispy_layout_mixin import SaplFormLayout, form_actions
from sapl.crud.base import (RP_DETAIL, RP_LIST, Crud, CrudAux,
                            MasterDetailCrud,
                            PermissionRequiredForAppCrudMixin, make_pagination)
from sapl.materia.apps import AppConfig
from sapl.materia.forms import (AnexadaForm, AutoriaForm,
                                AutoriaMultiCreateForm,
                                ConfirmarProposicaoForm,
                                DevolverProposicaoForm, LegislacaoCitadaForm,
                                OrgaoForm, ProposicaoForm, TipoProposicaoForm,
                                TramitacaoForm, TramitacaoUpdateForm, MateriaPesquisaSimplesForm,
                                DespachoInicialCreateForm,
                                DocumentoAcessorioProtocoloForm,
                                AssuntoMateriaForm)
from sapl.norma.models import LegislacaoCitada
from sapl.parlamentares.models import Legislatura
from sapl.protocoloadm.models import Protocolo
from sapl.sessao.models import SessaoPlenaria
from sapl.settings import MEDIA_ROOT, MAX_DOC_UPLOAD_SIZE
from sapl.utils import (YES_NO_CHOICES, autor_label, autor_modal, SEPARADOR_HASH_PROPOSICAO,
                        gerar_hash_arquivo, get_base_url, get_client_ip,
                        get_mime_type_from_file_extension, montar_row_autor,
                        show_results_filter_set, mail_service_configured, lista_anexados,
                        gerar_pdf_impressos)
import requests as rq
import sapl

from .forms import (AcessorioEmLoteFilterSet, AcompanhamentoMateriaForm,
                    AnexadaEmLoteFilterSet,
                    AdicionarVariasAutoriasFilterSet, DespachoInicialForm,
                    DocumentoAcessorioForm, EtiquetaPesquisaForm,
                    FichaPesquisaForm, FichaSelecionaForm, MateriaAssuntoForm,
                    MateriaLegislativaFilterSet, MateriaLegislativaForm,
                    MateriaSimplificadaForm, PrimeiraTramitacaoEmLoteFilterSet,
                    ReceberProposicaoForm, RelatoriaForm,
                    TramitacaoEmLoteFilterSet, UnidadeTramitacaoForm,
                    filtra_tramitacao_destino,
                    filtra_tramitacao_destino_and_status,
                    filtra_tramitacao_status,
                    ExcluirTramitacaoEmLote, compara_tramitacoes_mat,
                    TramitacaoEmLoteForm)
from .models import (AcompanhamentoMateria, Anexada, AssuntoMateria, Autoria,
                     DespachoInicial, DocumentoAcessorio, MateriaAssunto,
                     MateriaLegislativa, Numeracao, Orgao, Origem, Proposicao,
                     RegimeTramitacao, Relatoria, StatusTramitacao,
                     TipoDocumento, TipoFimRelatoria, TipoMateriaLegislativa,
                     TipoProposicao, Tramitacao, UnidadeTramitacao)


logger = logging.getLogger(__name__)


def tipos_autores_materias(user=None, restricao_regimental=True):

    noww = timezone.localdate()

    data_ini = noww - timedelta(
        days=noww.day - (1 if noww.day <= 15 else 16))

    data_fim = noww + timedelta(
        days=-noww.day + (15 if noww.day <= 15 else 31))

    while data_fim.day <= data_ini.day:
        data_fim -= timedelta(days=1)

    sq = SessaoPlenaria.objects.filter(
        data_fim__range=(data_ini, data_fim)
    ).order_by('data_fim', 'id')

    q = Q(em_tramitacao=True)

    if sq.exists():
        if sq.count() < 3 or (noww - sq.last().data_fim).days == 0:
            q |= Q(
                tipo__turnos_aprovacao=1,
                registrovotacao__ordem__sessao_plenaria__finalizada=False,
                registrovotacao__data_hora__gte=data_ini,
                registrovotacao__data_hora__lte=data_fim,
            ) | Q(
                tipo__turnos_aprovacao=1,
                registrovotacao__expediente__sessao_plenaria__finalizada=False,
                registrovotacao__data_hora__gte=data_ini,
                registrovotacao__data_hora__lte=data_fim,
            )

    if user:
        q &= Q(autores__operadores=user)

    materias_em_tramitacao = MateriaLegislativa.objects.filter(q).order_by(
        '-tipo__limite_minimo_coletivo', 'id').distinct()

    proposicoes_enviadas_sem_recebimento = []
    if user:
        q = Q(
            data_envio__isnull=False,
            data_recebimento__isnull=True
        )

        q &= Q(autor__operadores=user)
        proposicoes_enviadas_sem_recebimento = Proposicao.objects.filter(
            q).distinct()

    r = {}
    for m in materias_em_tramitacao:

        if m.tipo not in r:
            r[m.tipo] = {}

        coletivo = m.tipo.limite_minimo_coletivo and m.autores.count(
        ) >= m.tipo.limite_minimo_coletivo

        for a in m.autores.all():
            if a not in r[m.tipo]:
                r[m.tipo][a] = {'individual': set(), 'coletivo': set()}

            key = 'coletivo' if coletivo else 'individual'

            r[m.tipo][a][key].add(m)

    if restricao_regimental:
        for p in proposicoes_enviadas_sem_recebimento:

            tipo_correspondente = p.tipo.tipo_conteudo_related

            coletivo = tipo_correspondente.limite_minimo_coletivo and m.autores.count(
            ) >= tipo_correspondente.limite_minimo_coletivo

            if tipo_correspondente not in r:
                r[tipo_correspondente] = {}

            if p.autor not in r[tipo_correspondente]:
                r[tipo_correspondente][p.autor] = {
                    'individual': set(), 'coletivo': set()
                }

            key = 'coletivo' if coletivo else 'individual'
            r[tipo_correspondente][p.autor][key].add(p)

    sorted_r = dict(
        map(
            lambda a: (
                    a[0],
                    dict( # 4 - Retorna para dicionário
                        sorted( # 3 - Ordena por nome do autor
                        a[1].items(),
                        key=lambda b: b[0].nome
                    )
                )
            ),
            sorted(# 2 - Ordena por sequencia_regimental
                filter( # 1 - Filtra tipos que não possuem campo sequencia_regimental
                    lambda c: hasattr(c[0], 'sequencia_regimental'),
                    r.items() # 0 - Converte em tupla de tipos e autores
                ),
                key=lambda d: d[0].sequencia_regimental
            )
        )
    )

    return sorted_r


OrigemCrud = CrudAux.build(Origem, '')

RegimeTramitacaoCrud = CrudAux.build(
    RegimeTramitacao, 'regime_tramitacao')

TipoDocumentoCrud = CrudAux.build(
    TipoDocumento, 'tipo_documento')

TipoFimRelatoriaCrud = CrudAux.build(
    TipoFimRelatoria, 'fim_relatoria')


def autores_ja_adicionados(materia_pk):
    autorias = Autoria.objects.filter(materia_id=materia_pk).values_list(
        'autor_id', flat=True)
    return autorias


def proposicao_texto__deprecated(request, pk):
    logger = logging.getLogger(__name__)
    username = request.user.username
    logger.debug('user=' + username +
                 '. Tentando obter objeto Proposicao com pk = {}.'.format(pk))
    proposicao = Proposicao.objects.get(pk=pk)

    if proposicao.texto_original:
        if (not proposicao.data_recebimento and
                proposicao.autor.user_id != request.user.id):
            logger.error("user=" + username + ". Usuário ({}) não tem permissão para acessar o texto original."
                         .format(request.user.id))
            messages.error(request, _(
                'Você não tem permissão para acessar o texto original.'))
            return redirect(reverse('sapl.materia:proposicao_detail',
                                    kwargs={'pk': pk}))

        arquivo = proposicao.texto_original

        mime = get_mime_type_from_file_extension(arquivo.name)

        with open(arquivo.path, 'rb') as f:
            data = f.read()

        response = HttpResponse(data, content_type='%s' % mime)
        response['Content-Disposition'] = (
            'inline; filename="%s"' % arquivo.name.split('/')[-1])
        return response
    logger.error('user=' + username +
                 '. Objeto Proposicao com pk={} não encontrado.'.format(pk))
    raise Http404


class AdicionarVariasAutorias(PermissionRequiredForAppCrudMixin, FilterView):
    app_label = sapl.materia.apps.AppConfig.label
    filterset_class = AdicionarVariasAutoriasFilterSet
    template_name = 'materia/adicionar_varias_autorias.html'
    model = Autor

    def get_filterset_kwargs(self, filterset_class):
        super(AdicionarVariasAutorias, self).get_filterset_kwargs(
            filterset_class)
        kwargs = {'data': self.request.GET or None}

        qs = self.get_queryset()
        qs = qs.exclude(
            id__in=autores_ja_adicionados(self.kwargs['pk'])).distinct()

        kwargs.update({'queryset': qs})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(AdicionarVariasAutorias, self).get_context_data(
            **kwargs)

        context['title'] = _('Pesquisar Autores')
        qr = self.request.GET.copy()
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)

        context['pk_materia'] = self.kwargs['pk']
        return context

    def post(self, request, *args, **kwargs):
        marcados = request.POST.getlist('autor_id')

        for m in marcados:
            Autoria.objects.create(
                materia_id=self.kwargs['pk'],
                autor_id=m
            )

        return HttpResponseRedirect(
            reverse('sapl.materia:autoria_list',
                    kwargs={'pk': self.kwargs['pk']}))


class CriarProtocoloMateriaView(CreateView):
    template_name = "crud/form.html"
    form_class = MateriaSimplificadaForm
    form_valid_message = _('Matéria cadastrada com sucesso!')
    logger = logging.getLogger(__name__)

    def get_success_url(self, materia):
        return reverse('sapl.materia:materialegislativa_detail', kwargs={
            'pk': materia.pk})

    def get_context_data(self, **kwargs):
        context = super(
            CriarProtocoloMateriaView, self).get_context_data(**kwargs)
        username = self.request.user.username

        try:
            self.logger.debug("user=" + username +
                              ". Tentando obter objeto Protocolo.")
            protocolo = Protocolo.objects.get(pk=self.kwargs['pk'])
        except ObjectDoesNotExist as e:
            self.logger.error(
                "user=" + username + ". Objeto Protocolo com pk={} não encontrado. ".format(self.kwargs['pk']) + str(e))
            raise Http404()

        numero = 1
        try:
            self.logger.debug("user=" + username +
                              ". Tentando obter materias do último ano.")
            materias_ano = MateriaLegislativa.objects.filter(
                ano=protocolo.ano,
                tipo=protocolo.tipo_conteudo_protocolado).latest('numero')
            numero = materias_ano.numero + 1
        except ObjectDoesNotExist:
            self.logger.error("user=" + username + ". Não foram encontradas matérias no último ano ({}). "
                              "Definido 1 como padrão.".format(protocolo.ano))
            pass  # numero ficou com o valor padrão 1 acima

        context['form'].fields[
            'tipo'].initial = protocolo.tipo_conteudo_protocolado
        context['form'].fields['numero'].initial = numero
        context['form'].fields['ano'].initial = protocolo.ano
        if protocolo:
            if protocolo.timestamp:
                context['form'].fields['data_apresentacao'].initial = protocolo.timestamp.date(
                )
            elif protocolo.timestamp_data_hora_manual:
                context['form'].fields[
                    'data_apresentacao'].initial = protocolo.timestamp_data_hora_manual.date()
            elif protocolo.data:
                context['form'].fields[
                    'data_apresentacao'].initial = protocolo.data
        context['form'].fields['numero_protocolo'].initial = protocolo.numero
        context['form'].fields['ementa'].initial = protocolo.assunto_ementa

        return context

    def form_valid(self, form):
        materia = form.save()
        username = self.request.user.username

        try:
            self.logger.info(
                "user=" + username + ". Tentando obter objeto Procolo com pk={}.".format(self.kwargs['pk']))
            protocolo = Protocolo.objects.get(pk=self.kwargs['pk'])
            protocolo.conteudo_protocolado = materia
            protocolo.save()
        except ObjectDoesNotExist:
            self.logger.error(
                'user=' + username + '. Objeto Protocolo com pk={} não encontrado.'.format(self.kwargs['pk']))
            raise Http404()

        if protocolo.autor:
            Autoria.objects.create(
                materia=materia,
                autor=protocolo.autor,
                primeiro_autor=True)

        return redirect(self.get_success_url(materia))


class MateriaTaView(IntegracaoTaView):
    model = MateriaLegislativa
    model_type_foreignkey = TipoMateriaLegislativa
    map_fields = {
        'data': 'data_apresentacao',
        'ementa': 'ementa',
        'observacao': None,
        'numero': 'numero',
        'ano': 'ano',
        'tipo': 'tipo',
    }
    map_funcs = {
        'publicacao_func': False,
    }
    ta_values = {
        'editable_only_by_owners': False,
        'editing_locked': False,
    }

    def get(self, request, *args, **kwargs):
        """
        Para manter a app compilacao isolada das outras aplicações,
        este get foi implementado para tratar uma prerrogativa externa
        de usuário.
        """
        if sapl.base.models.AppConfig.attr('texto_articulado_materia'):
            return IntegracaoTaView.get(self, request, *args, **kwargs)
        else:
            return self.get_redirect_deactivated()


class ProposicaoTaView(IntegracaoTaView):
    model = Proposicao
    model_type_foreignkey = TipoProposicao
    map_fields = {
        'data': 'data_envio',
        'ementa': 'descricao',
        'observacao': None,
        'numero': 'numero_proposicao',
        'ano': 'ano',
        'tipo': 'tipo',
    }
    map_funcs = {
        'publicacao_func': False
    }
    ta_values = {
        'editable_only_by_owners': True,
        'editing_locked': False,
        'privacidade': STATUS_TA_PRIVATE
    }

    def get(self, request, *args, **kwargs):
        """
        Para manter a app compilacao isolada das outras aplicações,
        este get foi implementado para tratar uma prerrogativa externa
        de usuário.
        """
        if sapl.base.models.AppConfig.attr('texto_articulado_proposicao'):

            proposicao = get_object_or_404(self.model, pk=kwargs['pk'])

            if not proposicao.data_envio and\
                    request.user not in proposicao.autor.operadores.all():
                raise Http404()

            return IntegracaoTaView.get(self, request, *args, **kwargs)
        else:
            return self.get_redirect_deactivated()


@permission_required('materia.detail_materialegislativa')
def recuperar_materia(request):
    logger = logging.getLogger(__name__)
    username = request.user.username
    tipo = TipoMateriaLegislativa.objects.get(pk=request.GET['tipo'])
    ano = request.GET.get('ano', '')

    numeracao = None
    try:
        logger.debug("user=" + username +
                     ". Tentando obter numeração da matéria.")
        numeracao = sapl.base.models.AppConfig.objects.last(
        ).sequencia_numeracao_protocolo
    except AttributeError as e:
        logger.error("user=" + username + ". " + str(e) +
                     " Numeracao da matéria definida como None.")
        pass

    if tipo.sequencia_numeracao:
        numeracao = tipo.sequencia_numeracao

    if numeracao == 'A':
        numero = MateriaLegislativa.objects.filter(
            ano=ano, tipo=tipo).aggregate(Max('numero'))
    elif numeracao == 'L':
        legislatura = Legislatura.objects.filter(
            data_inicio__year__lte=ano,
            data_fim__year__gte=ano).first()
        data_inicio = legislatura.data_inicio
        data_fim = legislatura.data_fim
        numero = MateriaLegislativa.objects.filter(
            data_apresentacao__gte=data_inicio,
            data_apresentacao__lte=data_fim,
            tipo=tipo).aggregate(
            Max('numero'))
    elif numeracao == 'U':
        numero = MateriaLegislativa.objects.filter(
            tipo=tipo).aggregate(Max('numero'))

    if numeracao is None:
        numero['numero__max'] = 0

    max_numero = numero['numero__max'] + 1 if numero['numero__max'] else 1

    response = JsonResponse({'numero': max_numero, 'ano': ano})

    return response


StatusTramitacaoCrud = CrudAux.build(StatusTramitacao, 'status_tramitacao')


class AssuntoMateriaCrud(CrudAux):
    model = AssuntoMateria

    class CreateView(CrudAux.CreateView):
        layout_key = None
        form_class = AssuntoMateriaForm

    class UpdateView(CrudAux.UpdateView):
        layout_key = None
        form_class = AssuntoMateriaForm


class OrgaoCrud(CrudAux):
    model = Orgao

    class CreateView(CrudAux.CreateView):
        form_class = OrgaoForm


class TipoProposicaoCrud(CrudAux):
    model = TipoProposicao
    help_text = 'tipo_proposicao'

    class BaseMixin(CrudAux.BaseMixin):
        list_field_names = [
            "descricao", "content_type", 'tipo_conteudo_related']

    class CreateView(CrudAux.CreateView):
        form_class = TipoProposicaoForm
        layout_key = None

    class UpdateView(CrudAux.UpdateView):
        form_class = TipoProposicaoForm
        layout_key = None

        def get_initial(self):
            initial = CrudAux.UpdateView.get_initial(self)
            ct = self.object.content_type
            initial['content_type'] = f'{ct.app_label}/{ct.model}'
            initial['tipo_conteudo_related'] = self.object.object_id
            return initial


def criar_materia_proposicao(proposicao):
    tipo_materia = TipoMateriaLegislativa.objects.get(
        descricao=proposicao.tipo.descricao)
    numero = MateriaLegislativa.objects.filter(
        ano=timezone.now().year).order_by('numero').last().numero + 1
    regime = RegimeTramitacao.objects.get(descricao='Normal')

    return MateriaLegislativa.objects.create(
        tipo=tipo_materia,
        ano=timezone.now().year,
        numero=numero,
        data_apresentacao=timezone.now(),
        regime_tramitacao=regime,
        em_tramitacao=True,
        ementa=proposicao.descricao,
        texto_original=proposicao.texto_original
    )


def criar_doc_proposicao(proposicao):
    tipo_doc = TipoDocumento.objects.get(
        descricao=proposicao.tipo.descricao)
    if proposicao.autor is None:
        autor = 'Desconhecido'
    else:
        autor = proposicao.autor

    return DocumentoAcessorio.objects.create(
        materia=proposicao.materia,
        tipo=tipo_doc,
        arquivo=proposicao.texto_original,
        nome=proposicao.descricao,
        data=proposicao.data_envio,
        autor=autor
    )


class ProposicaoDevolvida(PermissionRequiredMixin, ListView):
    template_name = 'materia/prop_devolvidas_list.html'
    model = Proposicao
    ordering = ['data_envio']
    paginate_by = 10
    permission_required = ('materia.detail_proposicao_devolvida',)

    def get_queryset(self):
        return Proposicao.objects.filter(
            data_envio__isnull=True,
            data_recebimento__isnull=True,
            data_devolucao__isnull=False)

    def get_context_data(self, **kwargs):
        context = super(ProposicaoDevolvida, self).get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        context['NO_ENTRIES_MSG'] = 'Nenhuma proposição devolvida.'
        context['subnav_template_name'] = 'materia/subnav_prop.yaml'
        return context


class ProposicaoPendente(PermissionRequiredMixin, ListView):
    template_name = 'materia/prop_pendentes_list.html'
    model = Proposicao
    ordering = ['data_envio', 'autor', 'tipo', 'descricao']
    paginate_by = 50
    permission_required = ('materia.detail_proposicao_enviada',)

    def get_queryset(self):
        return Proposicao.objects.filter(
            data_envio__isnull=False,
            data_recebimento__isnull=True,
            data_devolucao__isnull=True)

    def get_context_data(self, **kwargs):
        context = super(ProposicaoPendente, self).get_context_data(**kwargs)

        context['object_list'] = Proposicao.objects.filter(
            data_envio__isnull=False,
            data_recebimento__isnull=True,
            data_devolucao__isnull=True)

        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        context['AppConfig'] = sapl.base.models.AppConfig.objects.all().last()

        context['NO_ENTRIES_MSG'] = 'Nenhuma proposição pendente.'

        context['subnav_template_name'] = 'materia/subnav_prop.yaml'

        qr = self.request.GET.copy()
        context['filter_url'] = ('&o=' + qr['o']) if 'o' in qr.keys() else ''

        context['tipos_autores_materias'] = tipos_autores_materias(
            None).items()

        return context


class ProposicaoRecebida(PermissionRequiredMixin, ListView):
    template_name = 'materia/prop_recebidas_list.html'
    model = Proposicao

    paginate_by = 10
    permission_required = 'materia.detail_proposicao_incorporada'

    def get_queryset(self):
        return Proposicao.objects.filter(
            data_envio__isnull=False,
            data_recebimento__isnull=False,
            data_devolucao__isnull=True)

    def get_context_data(self, **kwargs):
        context = super(ProposicaoRecebida, self).get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        context['NO_ENTRIES_MSG'] = 'Nenhuma proposição recebida.'
        context['subnav_template_name'] = 'materia/subnav_prop.yaml'
        return context


class ReceberProposicao(PermissionRequiredForAppCrudMixin, FormView):
    app_label = sapl.protocoloadm.apps.AppConfig.label
    template_name = "crud/form.html"
    form_class = ReceberProposicaoForm

    def post(self, request, *args, **kwargs):

        form = ReceberProposicaoForm(request.POST)

        if form.is_valid():
            try:
                # A ultima parte do código deve ser a pk da Proposicao
                cod_hash = form.cleaned_data["cod_hash"]. \
                    replace('/', SEPARADOR_HASH_PROPOSICAO)
                id = cod_hash.split(SEPARADOR_HASH_PROPOSICAO)[1]
                proposicao = Proposicao.objects.get(id=id,
                                                    data_envio__isnull=False,
                                                    data_recebimento__isnull=True)

                if proposicao.texto_articulado.exists():
                    ta = proposicao.texto_articulado.first()
                    # FIXME hash para textos articulados
                    hasher = 'P' + ta.hash() + SEPARADOR_HASH_PROPOSICAO + str(proposicao.id)
                else:
                    hasher = gerar_hash_arquivo(
                        proposicao.texto_original.path,
                        str(proposicao.id)) \
                        if proposicao.texto_original else None
                if hasher == cod_hash:
                    return HttpResponseRedirect(
                        reverse('sapl.materia:proposicao-confirmar',
                                kwargs={
                                    'hash': hasher.split(SEPARADOR_HASH_PROPOSICAO)[0][1:],
                                    'pk': proposicao.pk}))
            except ObjectDoesNotExist:
                messages.error(request, _('Proposição não encontrada!'))
            except IndexError:
                messages.error(request, _('Código de recibo mal formado!'))
            except IOError:
                messages.error(request, _(
                    'Erro abrindo texto original de proposição'))
        return self.form_invalid(form)

    def get_success_url(self):
        return reverse('sapl.materia:receber-proposicao')

    def get_context_data(self, **kwargs):
        context = super(ReceberProposicao, self).get_context_data(**kwargs)
        context['subnav_template_name'] = 'materia/subnav_prop.yaml'
        return context


class RetornarProposicao(UpdateView):
    app_label = sapl.protocoloadm.apps.AppConfig.label
    template_name = "materia/proposicao_confirm_return.html"
    model = Proposicao
    fields = ['data_envio', 'descricao']
    permission_required = ('materia.detail_proposicao_enviada',)
    logger = logging.getLogger(__name__)

    def dispatch(self, request, *args, **kwargs):
        username = request.user.username
        try:
            self.logger.info(
                "user=" + username + ". Tentando obter objeto Proposicao com id={}.".format(kwargs['pk']))
            p = Proposicao.objects.get(id=kwargs['pk'])
        except BaseException:
            self.logger.error(
                "user=" + username + ". Objeto Proposicao com id={} não encontrado.".format(kwargs['pk']))
            raise Http404()

        if not p.autor.operadores.filter(pk=request.user.id).exists():
            self.logger.error(
                "user=" + username + ". Usuário ({}) sem acesso a esta opção.".format(request.user))
            messages.error(
                request,
                'Usuário sem acesso a esta opção.' %
                request.user)
            return redirect('/')

        return super(RetornarProposicao, self).dispatch(
            request, *args, **kwargs)


class ConfirmarProposicao(PermissionRequiredForAppCrudMixin, UpdateView):
    app_label = sapl.protocoloadm.apps.AppConfig.label
    template_name = "materia/confirmar_proposicao.html"
    model = Proposicao
    form_class = ConfirmarProposicaoForm, DevolverProposicaoForm
    logger = logging.getLogger(__name__)

    def get_success_url(self):
        msgs = self.object.results['messages']

        for key, value in msgs.items():
            for item in value:
                getattr(messages, key)(self.request, item)

        return self.object.results['url']

    def post(self, request, *args, **kwargs):

        try:
            return UpdateView.post(self, request, *args, **kwargs)
        except Exception as e:
            tb = ''.join(traceback.format_tb(e.__traceback__))
            #x_type, ex, tb = sys.exc_info()
            # raceback.print_tb(tb)
            self.logger.error(str(tb))

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object and self.object.proposicao_vinculada:
            messages.error(request, ('Esta proposição está vinculada a: {}. Acesse-a e faça a incorporação primeiro dela.').format(
                self.object.proposicao_vinculada))
            return redirect(reverse('sapl.materia:proposicao-pendente'))

        return UpdateView.get(self, request, *args, **kwargs)

    def get_initial(self):
        initial = UpdateView.get_initial(self)
        obj = self.get_object()
        initial['numero_de_paginas'] = obj.paginas

        return initial

    def get_object(self, queryset=None):

        if hasattr(self, 'object') and self.object:
            return self.object

        username = self.request.user.username

        try:
            """
            Não deve haver acesso na rotina de confirmação a proposições:
            já recebidas -> data_recebimento != None
            não enviadas -> data_envio == None
            """
            self.logger.debug("user=" + username +
                              ". Tentando obter objeto Proposicao.")
            proposicao = Proposicao.objects.get(pk=self.kwargs['pk'],
                                                data_envio__isnull=False,
                                                data_recebimento__isnull=True)
            self.object = None

            if proposicao.texto_articulado.exists():
                ta = proposicao.texto_articulado.first()
                hasher = 'P' + ta.hash() + SEPARADOR_HASH_PROPOSICAO + str(proposicao.id)
            else:
                hasher = gerar_hash_arquivo(
                    proposicao.texto_original.path,
                    str(proposicao.pk)) if proposicao.texto_original else None

            if hasher == 'P%s%s%s' % (
                    self.kwargs['hash'], SEPARADOR_HASH_PROPOSICAO, proposicao.pk):
                self.object = proposicao
        except Exception as e:
            self.logger.error("user=" + username + ". Objeto Proposicao com atributos (pk={}, data_envio=Not Null, "
                              "data_recebimento=Null) não encontrado. ".format(self.kwargs['pk']) + str(e))
            raise Http404()

        if not self.object:
            self.logger.error("user=" + username + ". Objeto vazio.")
            raise Http404()

        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subnav_template_name'] = ''
        return context

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()

        if self.request.POST:
            if 'justificativa_devolucao' in self.request.POST:
                return form_class[1](**self.get_form_kwargs())
            else:
                return form_class[0](**self.get_form_kwargs())
        else:
            forms = []
            for form in form_class:
                forms.append(form(**self.get_form_kwargs()))
            return forms

    def form_invalid(self, form):
        # Só um form é enviado por vez mas podem existir invalidade em ambos.
        # em caso de um form ser inválido e retornar para a tela dos
        # formulários, o outro precisa ser renderizado, mas neste ponto por ser
        # um POST só chega um form dada lógica no método acima get_form,
        # assim o form_invalid cria o form alternativo e o insere para
        # renderização do template_name definido nesta classe

        kwargs = {
            'initial': self.get_initial(),
            'prefix': self.get_prefix(),
            'instance': form.instance
        }

        if isinstance(form, self.form_class[0]):
            forms = [form, DevolverProposicaoForm(**kwargs)]
        else:
            forms = [ConfirmarProposicaoForm(**kwargs), form]

        return self.render_to_response(self.get_context_data(form=forms))


class UnidadeTramitacaoCrud(CrudAux):
    model = UnidadeTramitacao
    help_topic = 'unidade_tramitacao'

    class BaseMixin(CrudAux.BaseMixin):
        list_field_names = ['comissao', 'orgao', 'parlamentar']

    class ListView(CrudAux.ListView):

        def get_headers(self):
            return [_('Unidade de Tramitação')]

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            for row in context['rows']:
                if row[0][0]:  # Comissão
                    pass
                elif row[1][0]:  # Órgão
                    row[0] = (row[1][0], row[0][1])
                elif row[2][0]:  # Parlamentar
                    row[0] = (row[2][0], row[0][1])
                row[1], row[2] = ('', ''), ('', '')
            return context

    class UpdateView(Crud.UpdateView):
        form_class = UnidadeTramitacaoForm

    class CreateView(Crud.CreateView):
        form_class = UnidadeTramitacaoForm


class ProposicaoCrud(Crud):
    model = Proposicao
    help_topic = 'proposicao'
    container_field = 'autor__operadores'

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['detalhe', 'tipo', 'data_envio', 'data_recebimento',
                            'conteudo_gerado_related', ]  # 'cancelado', ]
        ordered_list = False

    class BaseLocalMixin:
        form_class = ProposicaoForm
        layout_key = None

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = ''
            return context

        def get(self, request, *args, **kwargs):

            p = Proposicao.objects.get(id=kwargs['pk'])

            u = request.user
            oa = u.operadorautor_set.all().first()

            if oa and oa.visibilidade_restrita and u != p.user and p.data_recebimento is None:
                raise PermissionDenied(
                    "Proposição de criação e edição por: {}".format(p.user))

            if not self._action_is_valid(request, *args, **kwargs):
                return redirect(reverse('sapl.materia:proposicao_detail',
                                        kwargs={'pk': kwargs['pk']}))
            return super().get(self, request, *args, **kwargs)

        def post(self, request, *args, **kwargs):

            if not self._action_is_valid(request, *args, **kwargs):
                return redirect(reverse('sapl.materia:proposicao_detail',
                                        kwargs={'pk': kwargs['pk']}))
            return super().post(self, request, *args, **kwargs)

    class DetailView(Crud.DetailView):
        layout_key = 'Proposicao'
        permission_required = (RP_DETAIL, 'materia.detail_proposicao_enviada',
                               'materia.detail_proposicao_devolvida',
                               'materia.detail_proposicao_incorporada')

        logger = logging.getLogger(__name__)

        def impedimentos_de_envio(self):
            imp = []

            if not self.object.metadata or not self.object.tipo.tipo_conteudo_related.limite_minimo_coletivo:
                return imp

            signs = self.object.metadata.get(
                'signs', {}
            ).get(
                'texto_original', {}
            ).get('signs', [])

            signs = set(map(lambda x: x[0], signs))

            if not signs:
                return imp

            if len(signs) >= self.object.tipo.tipo_conteudo_related.limite_minimo_coletivo:
                return imp

            tam = tipos_autores_materias()

            autores_com_materias_em_tramitacao = tam.get(
                self.object.tipo.tipo_conteudo_related, {})

            autores_key_nome_completo = dict(
                map(
                    lambda el: (
                        (el[0], el[0].autor_related.nome_completo), el[1]),
                    autores_com_materias_em_tramitacao.items())
            )

            assinantes_com_mat_em_tramitacao = signs.intersection(
                set(dict(autores_key_nome_completo.keys()).values())
            )

            autores_key_nome_completo = filter(
                lambda el: el[0][1] in assinantes_com_mat_em_tramitacao,
                autores_key_nome_completo.items()
            )

            for registro in autores_key_nome_completo:
                autor, formatos = registro
                fmt_individual = formatos['individual']

                if len(fmt_individual) >= self.object.tipo.tipo_conteudo_related.limite_por_autor_tramitando:
                    imp.append((autor[0], autor[1], len(fmt_individual)))

            return imp

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = ''
            context['AppConfig'] = sapl.base.models.AppConfig.objects.all().last()

            context['title'] = '%s <small>(%s)</small>' % (
                self.object, self.object.autor)

            context['user'] = self.request.user
            context['proposicao'] = self.object
            context['impedimentos_de_envio'] = self.impedimentos_de_envio()
            return context

        def get(self, request, *args, **kwargs):

            action = request.GET.get('action', '')
            username = request.user.username

            p = self.object

            if not action:
                u = request.user
                oa = u.operadorautor_set.all().first()

                if oa and oa.visibilidade_restrita and u != p.user and p.data_recebimento is None:
                    raise PermissionDenied(
                        "Proposição de criação e edição por: {}".format(p.user))

                return Crud.DetailView.get(self, request, *args, **kwargs)

            msg_error = ''
            if p:
                if action == 'send':

                    if p.data_envio and p.data_recebimento:
                        msg_error = _('Proposição já foi enviada e recebida.')
                    elif p.data_envio:
                        msg_error = _('Proposição já foi enviada.')
                    elif not p.texto_original and\
                            not p.texto_articulado.exists():
                        msg_error = _('Proposição não possui nenhum tipo de '
                                      'Texto associado.')
                    elif p.tipo.exige_assinatura_digital and \
                            p.metadata.get(
                                'signs', {}
                            ).get(
                                'texto_original', {}
                            ).get(
                                'running_extraction', False
                            ):
                        msg_error = _(
                            'Assinaturas Eletrônicas em processo de extração. Aguarde a conclusão para posterior envio...')
                    elif p.tipo.exige_assinatura_digital and \
                            (
                                not p.metadata.get('signs', {}) or
                                not p.metadata.get(
                                    'signs', {}).get(
                                    'texto_original', {}).get(
                                        'signs', {})
                            ):
                        msg_error = _(
                            'Documento não possui assinatura digital.')
                    else:

                        tcr = p.tipo.tipo_conteudo_related
                        msg_pre_error = _(
                            f'''Limite Regimental atingido.
                            O envio só será possível quando a quantidade
                            de Requerimentos em tramitação for inferior
                            a {tcr.limite_por_autor_tramitando}
                            Requerimentos.''')

                        impedimentos = self.impedimentos_de_envio()

                        if not impedimentos:
                            tam = tipos_autores_materias(self.request.user)

                            if tcr.limite_por_autor_tramitando and tcr in tam:
                                fmt_individual = tam.get(
                                    tcr, {}
                                ).get(
                                    p.autor, {}
                                ).get(
                                    'individual', set()
                                )
                                if len(fmt_individual) >= tcr.limite_por_autor_tramitando:
                                    msg_error = msg_pre_error
                        else:
                            msg_error = msg_pre_error

                        if not msg_error:

                            if p.texto_articulado.exists():
                                ta = p.texto_articulado.first()
                                ta.privacidade = STATUS_TA_IMMUTABLE_RESTRICT
                                ta.editing_locked = True
                                ta.save()

                                receber_recibo = BaseAppConfig.attr(
                                    'receber_recibo_proposicao')

                                if not receber_recibo:
                                    ta = p.texto_articulado.first()
                                    p.hash_code = 'P' + ta.hash() + SEPARADOR_HASH_PROPOSICAO + str(p.pk)

                            p.data_devolucao = None
                            p.data_envio = timezone.now()
                            p.save()

                            messages.success(request, _(
                                'Proposição enviada com sucesso.'))
                            try:
                                self.logger.debug("user=" + username + ". Tentando obter número do objeto MateriaLegislativa com "
                                                  "atributos tipo={} e ano={}."
                                                  .format(p.tipo.tipo_conteudo_related, p.ano))

                                # if p.numero_materia_futuro:
                                #    numero = p.numero_materia_futuro
                                # else:
                                #    numero = MateriaLegislativa.objects.filter(tipo=p.tipo.tipo_conteudo_related,
                                #                                               ano=p.ano).last().numero + 1
                                # messages.success(request, _(
                                #    '%s : nº %s de %s <br>Atenção! Este número é apenas um provável '
                                #    'número que pode não corresponder com a realidade'
                                #    % (p.tipo, numero, p.ano)))
                            except ValueError as e:
                                self.logger.error(
                                    "user=" + username + "." + str(e))
                                pass
                            except AttributeError as e:
                                self.logger.error(
                                    "user=" + username + "." + str(e))
                                pass
                            except TypeError as e:
                                self.logger.error(
                                    "user=" + username + "." + str(e))
                                pass

                elif action == 'return':
                    if not p.data_envio:
                        self.logger.error(
                            "user=" + username + ". Proposição (numero={}) ainda não foi enviada.".format(p.numero_proposicao))
                        msg_error = _('Proposição ainda não foi enviada.')
                    elif p.data_recebimento:
                        self.logger.error("user=" + username + ". Proposição (numero={}) já foi recebida, não é "
                                          "possível retorná-la.".format(p.numero_proposicao))
                        msg_error = _('Proposição já foi recebida, não é '
                                      'possível retorná-la.')
                    else:
                        p.data_envio = None
                        p.save()
                        if p.texto_articulado.exists():
                            ta = p.texto_articulado.first()
                            ta.privacidade = STATUS_TA_PRIVATE
                            ta.editing_locked = False
                            ta.save()
                        self.logger.info(
                            "user=" + username + ". Proposição (numero={}) Retornada com sucesso.".format(p.numero_proposicao))
                        messages.success(request, _(
                            'Proposição Retornada com sucesso.'))

                if msg_error:
                    messages.error(request, msg_error)

            # retornar redirecionando para limpar a variavel action
            return redirect(reverse('sapl.materia:proposicao_detail',
                                    kwargs={'pk': kwargs['pk']}))

        def dispatch(self, request, *args, **kwargs):
            username = request.user.username
            try:
                self.logger.debug(
                    "user=" + username + ". Tentando obter objeto Proposicao com pk={}".format(kwargs['pk']))
                self.object = p = Proposicao.objects.get(id=kwargs['pk'])
            except Exception as e:
                self.logger.error(
                    "user=" + username + ". Erro ao obter proposicao com pk={}. Retornando 404. ".format(kwargs['pk']) + str(e))
                raise Http404()

            if not self.has_permission():
                return self.handle_no_permission()

            if not p.autor.operadores.filter(pk=request.user.id).exists():
                if not p.data_envio and not p.data_devolucao:
                    raise Http404()

                if p.data_devolucao and not request.user.has_perm(
                        'materia.detail_proposicao_devolvida'):
                    raise Http404()

                if p.data_envio and not p.data_recebimento\
                    and not request.user.has_perm(
                        'materia.detail_proposicao_enviada'):
                    raise Http404()

                if p.data_envio and p.data_recebimento\
                    and not request.user.has_perm(
                        'materia.detail_proposicao_incorporada'):
                    raise Http404()

            return super(PermissionRequiredMixin, self).dispatch(
                request, *args, **kwargs)

    class DeleteView(BaseLocalMixin, Crud.DeleteView):

        logger = logging.getLogger(__name__)

        def _action_is_valid(self, request, *args, **kwargs):
            proposicao = Proposicao.objects.filter(
                id=kwargs['pk']).values_list(
                    'data_envio', 'data_recebimento')

            username = request.user.username

            if proposicao:
                if proposicao[0][0] and proposicao[0][1]:
                    self.logger.error("user=" + username + ". Proposição (id={}) já foi enviada e recebida."
                                      "Não pode mais ser excluida.".format(kwargs['pk']))
                    msg = _('Proposição já foi enviada e recebida.'
                            'Não pode mais ser excluida.')
                elif proposicao[0][0] and not proposicao[0][1]:
                    self.logger.error("user=" + username + ". Proposição (id={}) já foi enviada mas ainda não recebida "
                                      "pelo protocolo. Use a opção Recuperar Proposição "
                                      "para depois excluí-la.".format(kwargs['pk']))
                    msg = _('Proposição já foi enviada mas ainda não recebida '
                            'pelo protocolo. Use a opção Recuperar Proposição '
                            'para depois excluí-la.')

                if proposicao[0][0] or proposicao[0][1]:
                    messages.error(request, msg)
                    return False
            return True

        def post(self, request, *args, **kwargs):

            if not self._action_is_valid(request, *args, **kwargs):
                return redirect(reverse('sapl.materia:proposicao_detail',
                                        kwargs={'pk': kwargs['pk']}))
            return super().delete(self, request, *args, **kwargs)

    class UpdateView(BaseLocalMixin, Crud.UpdateView):

        logger = logging.getLogger(__name__)
        form_class = ProposicaoForm

        def get_initial(self):
            initial = super().get_initial()

            initial['user'] = self.request.user
            initial['ip'] = get_client_ip(self.request)

            initial['ultima_edicao'] = timezone.localtime()

            return initial

        def form_valid(self, form):

            objeto_antigo = Proposicao.objects.get(
                pk=self.kwargs['pk']
            )
            dict_objeto_antigo = objeto_antigo.__dict__

            tipo_texto = self.request.POST.get('tipo_texto', '')
            if tipo_texto == 'D' and objeto_antigo.texto_articulado.exists(
            ) or tipo_texto == 'T' and not objeto_antigo.texto_articulado.exists():
                self.object.user = self.request.user
                self.object.ip = get_client_ip(self.request)
                self.object.ultima_edicao = timezone.localtime()
                self.object.save()

            self.object = form.save()
            dict_objeto_novo = self.object.__dict__

            atributos = [
                'tipo_id', 'descricao', 'observacao', 'texto_original',
                'materia_de_vinculo_id', 'proposicao_vinculada_id'
            ]

            for atributo in atributos:
                if dict_objeto_antigo[atributo] != dict_objeto_novo[atributo]:
                    self.object.user = self.request.user
                    self.object.ip = get_client_ip(self.request)
                    self.object.ultima_edicao = timezone.localtime()
                    self.object.save()
                    break

            return super().form_valid(form)

        def _action_is_valid(self, request, *args, **kwargs):

            proposicao = Proposicao.objects.filter(
                id=kwargs['pk']).values_list(
                    'data_envio', 'data_recebimento')

            username = request.user.username

            if proposicao:
                msg = ''
                if proposicao[0][0] and proposicao[0][1]:
                    self.logger.error('user=' + username + '. Proposição (id={}) já foi enviada e recebida.'
                                      'Não pode mais ser editada'.format(kwargs['pk']))
                    msg = _('Proposição já foi enviada e recebida.'
                            'Não pode mais ser editada')
                elif proposicao[0][0] and not proposicao[0][1]:
                    self.logger.error('user=' + username + '. Proposição (id={}) já foi enviada mas ainda não recebida '
                                      'pelo protocolo. Use a opção Recuperar Proposição '
                                      'para voltar para edição.'.format(kwargs['pk']))
                    msg = _('Proposição já foi enviada mas ainda não recebida '
                            'pelo protocolo. Use a opção Recuperar Proposição '
                            'para voltar para edição.')

                if proposicao[0][0] or proposicao[0][1]:
                    messages.error(request, msg)
                    return False
            return True

        def get_success_url(self):

            tipo_texto = self.request.POST.get('tipo_texto', '')
            username = self.request.user.username

            if tipo_texto == 'T':
                messages.info(self.request,
                              _('Sempre que uma Proposição é inclusa ou '
                                'alterada e a opção "Texto Articulado " for '
                                'marcada, você será redirecionado para a '
                                'edição do Texto Eletrônico.'))
                self.logger.debug('user=' + username + '. Sempre que uma Proposição é inclusa ou '
                                  'alterada e a opção "Texto Articulado " for '
                                  'marcada, você será redirecionado para a '
                                  'edição do Texto Eletrônico.')
                return reverse('sapl.materia:proposicao_ta',
                               kwargs={'pk': self.object.pk})
            else:
                return Crud.UpdateView.get_success_url(self)

    class CreateView(Crud.CreateView):
        logger = logging.getLogger(__name__)
        form_class = ProposicaoForm
        layout_key = None

        def get_initial(self):
            initial = super().get_initial()

            initial['user'] = self.request.user
            initial['ip'] = get_client_ip(self.request)

            initial['ultima_edicao'] = timezone.localtime()

            return initial

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = ''
            return context

        def get_success_url(self):

            tipo_texto = self.request.POST.get('tipo_texto', '')
            username = self.request.user.username

            if tipo_texto == 'T':
                messages.info(self.request,
                              _('Sempre que uma Proposição é inclusa ou '
                                'alterada e a opção "Texto Articulado " for '
                                'marcada, você será redirecionado para o '
                                'Texto Eletrônico. Use a opção "Editar Texto" '
                                'para construir seu texto.'))
                self.logger.debug('user=' + username + '. Sempre que uma Proposição é inclusa ou '
                                  'alterada e a opção "Texto Articulado " for '
                                  'marcada, você será redirecionado para o '
                                  'Texto Eletrônico. Use a opção "Editar Texto" '
                                  'para construir seu texto.')
                return reverse('sapl.materia:proposicao_ta',
                               kwargs={'pk': self.object.pk})
            else:
                return Crud.CreateView.get_success_url(self)

    class ListView(Crud.ListView):
        ordering = ['-data_recebimento', '-data_envio', '-id']

        def hook_header_detalhe(self, *args, **kwargs):
            return 'Proposição'

        def hook_detalhe(self, *args, **kwargs):
            return '''
                <strong>{}</strong><br>{}<br><small><i>Registrado por: {}</i></small>
            '''.format(args[0], args[0].descricao, args[0].user), args[2]

        def get_queryset(self):
            qs = super().get_queryset()

            u = self.request.user
            oa = u.operadorautor_set.all().first()

            if oa and oa.visibilidade_restrita:
                qs = Proposicao.objects.all()

                q = Q(
                    data_recebimento__isnull=True,
                    autor__operadores=u,
                    user=u,
                ) | Q(
                    data_recebimento__isnull=False,
                    autor__operadores=u
                )

                qs = qs.filter(q).order_by(
                    '-data_recebimento', '-data_envio', '-id')

            return qs

        def get_rows(self, object_list):

            tam = tipos_autores_materias(self.request.user)
            for obj in object_list:

                if obj.data_envio is None:
                    tcr = obj.tipo.tipo_conteudo_related
                    if tcr.limite_por_autor_tramitando and tcr in tam:
                        fmt_individual = tam.get(
                            tcr, {}
                        ).get(
                            obj.autor, {}
                        ).get('individual', set())

                        if len(fmt_individual) >= tcr.limite_por_autor_tramitando:
                            obj.data_envio = """
                            <strong class="text-red">Limite Regimental atingido.</strong>
                            """
                            continue

                    obj.data_envio = 'Em elaboração...'
                    if obj.justificativa_devolucao:
                        obj.data_envio = f"""
                        <div class="text-red">
                        <strong>Proposição devolvida</strong><br>
                        {obj.justificativa_devolucao}
                        </div>
                        """

                else:
                    obj.data_envio = timezone.localtime(obj.data_envio)
                    obj.data_envio = formats.date_format(
                        obj.data_envio, "DATETIME_FORMAT")

                if obj.data_recebimento is None:
                    obj.data_recebimento = 'Não recebida'\
                        if obj.data_envio else 'Não enviada'

                else:
                    obj.data_recebimento = timezone.localtime(
                        obj.data_recebimento)
                    obj.data_recebimento = formats.date_format(
                        obj.data_recebimento, "DATETIME_FORMAT")

            return [self._as_row(obj) for obj in object_list]

        def tipos_autores_materias(self):
            # chamado do template
            return tipos_autores_materias(self.request.user).items()


class ReciboProposicaoView(TemplateView):
    logger = logging.getLogger(__name__)
    template_name = "materia/recibo_proposicao.html"
    permission_required = ('materia.detail_proposicao',)

    def has_permission(self):
        perms = self.get_permission_required()
        if not self.request.user.has_perms(perms):
            return False

        return (Proposicao.objects.filter(
            id=self.kwargs['pk'],
            autor__operadores=self.request.user).exists())

    def get_context_data(self, **kwargs):
        from sapl.utils import create_barcode

        context = super(ReciboProposicaoView, self).get_context_data(
            **kwargs)
        proposicao = Proposicao.objects.get(pk=self.kwargs['pk'])

        if proposicao.conteudo_gerado_related:
            self.template_name = "protocoloadm/comprovante.html"

            protocolo = proposicao.conteudo_gerado_related.protocolo_gr.first()
            # numero is string, padd with zeros left via .zfill()
            base64_data = create_barcode(str(protocolo.numero).zfill(6))
            barcode = 'data:image/png;base64,{0}'.format(base64_data)

            autenticacao = _("** NULO **")

            if not protocolo.anulado:
                if protocolo.timestamp:
                    data = protocolo.timestamp.strftime("%Y/%m/%d")
                else:
                    data = protocolo.data.strftime("%Y/%m/%d")

                # data is not i18n sensitive 'Y-m-d' is the right format.
                autenticacao = str(protocolo.tipo_processo) + \
                    data + str(protocolo.numero).zfill(6)

            context.update({"protocolo": protocolo,
                            "barcode": barcode,
                            "autenticacao": autenticacao})

            return context

        if proposicao.texto_original:
            _hash = gerar_hash_arquivo(
                proposicao.texto_original.path,
                self.kwargs['pk'])
        elif proposicao.texto_articulado.exists():
            ta = proposicao.texto_articulado.first()
            # FIXME hash para textos articulados
            _hash = 'P' + ta.hash() + '/' + str(proposicao.id)

        base64_data = create_barcode(_hash, 100, 500)
        barcode = 'data:image/png;base64,{0}'.format(base64_data)

        context.update({'proposicao': proposicao,
                        'hash': _hash,
                        'barcode': barcode})
        return context

    def get(self, request, *args, **kwargs):
        proposicao = Proposicao.objects.get(pk=self.kwargs['pk'])
        username = request.user.username

        if proposicao.data_envio:
            return TemplateView.get(self, request, *args, **kwargs)

        if not proposicao.data_envio and not proposicao.data_devolucao:
            self.logger.error('user=' + username + '. Não é possível gerar recibo para uma '
                              'Proposição (pk={}) ainda não enviada.'.format(self.kwargs['pk']))
            messages.error(request, _('Não é possível gerar recibo para uma '
                                      'Proposição ainda não enviada.'))
        elif proposicao.data_devolucao:
            self.logger.error(
                "user=" + username + ". Não é possível gerar recibo para proposicao de pk={}.".format(self.kwargs['pk']))
            messages.error(request, _('Não é possível gerar recibo.'))

        return redirect(reverse('sapl.materia:proposicao_detail',
                                kwargs={'pk': proposicao.pk}))


class RelatoriaCrud(MasterDetailCrud):
    model = Relatoria
    parent_field = 'materia'
    help_topic = 'tramitacao_relatoria'
    public = [RP_LIST, RP_DETAIL]

    class CreateView(MasterDetailCrud.CreateView):
        form_class = RelatoriaForm
        layout_key = None
        logger = logging.getLogger(__name__)

        def get_initial(self):
            materia = MateriaLegislativa.objects.get(id=self.kwargs['pk'])

            loc_atual = Tramitacao.objects.filter(materia=materia).last()

            if loc_atual is None:
                localizacao = 0
            else:
                comissao = loc_atual.unidade_tramitacao_destino.comissao
                if comissao:
                    localizacao = comissao.pk
                else:
                    localizacao = 0

            return {'comissao': localizacao}

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = RelatoriaForm
        layout_key = None
        logger = logging.getLogger(__name__)

        def get_initial(self):
            relatoria = Relatoria.objects.get(id=self.kwargs['pk'])
            parlamentar = relatoria.parlamentar
            comissao = relatoria.comissao
            composicoes = [p.composicao for p in
                           Participacao.objects.filter(
                               parlamentar=parlamentar,
                               composicao__comissao=comissao)]
            data_designacao = relatoria.data_designacao_relator
            composicao = ''
            for c in composicoes:
                data_inicial = c.periodo.data_inicio
                data_fim = c.periodo.data_fim if c.periodo.data_fim else timezone.now().date()
                if data_inicial <= data_designacao <= data_fim:
                    composicao = c.id
                    break
            return {'comissao': relatoria.comissao.id,
                    'parlamentar': relatoria.parlamentar.id,
                    'composicao': composicao}


class TramitacaoCrud(MasterDetailCrud):
    model = Tramitacao
    parent_field = 'materia'
    help_topic = 'tramitacao_relatoria'
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['data_tramitacao', 'unidade_tramitacao_local',
                            'unidade_tramitacao_destino', 'status']
        ordered_list = False
        ordering = '-data_tramitacao',

    class CreateView(MasterDetailCrud.CreateView):
        form_class = TramitacaoForm
        logger = logging.getLogger(__name__)

        def get_success_url(self):
            return reverse('sapl.materia:tramitacao_list', kwargs={
                'pk': self.kwargs['pk']})

        def get_initial(self):
            initial = super(CreateView, self).get_initial()
            local = MateriaLegislativa.objects.get(
                pk=self.kwargs['pk']).tramitacao_set.order_by(
                '-data_tramitacao',
                '-id').first()

            if local:
                initial['unidade_tramitacao_local'
                        ] = local.unidade_tramitacao_destino.pk

                if local.materia.tipo.turnos_aprovacao == 1:
                    initial['turno'] = 'U'
                else:
                    initial[
                        'turno'
                    ] = 'S' if local.materia.registrovotacao_set.exists() else 'P'

            else:
                initial['unidade_tramitacao_local'] = ''
            initial['data_tramitacao'] = timezone.now().date()
            initial['ip'] = get_client_ip(self.request)
            initial['user'] = self.request.user
            return initial

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            username = self.request.user.username

            ultima_tramitacao = Tramitacao.objects.filter(
                materia_id=self.kwargs['pk']).order_by(
                '-data_tramitacao',
                '-timestamp',
                '-id').first()

            # TODO: Esta checagem foi inserida na issue #2027, mas é mesmo
            # necessária?
            if ultima_tramitacao:
                if ultima_tramitacao.unidade_tramitacao_destino:
                    context['form'].fields[
                        'unidade_tramitacao_local'].choices = [
                        (ultima_tramitacao.unidade_tramitacao_destino.pk,
                         ultima_tramitacao.unidade_tramitacao_destino)]
                else:
                    self.logger.error('user=' + username + '. Unidade de tramitação destino '
                                      'da última tramitação não pode ser vazia!')
                    msg = _('Unidade de tramitação destino '
                            ' da última tramitação não pode ser vazia!')
                    messages.add_message(self.request, messages.ERROR, msg)

            primeira_tramitacao = not(Tramitacao.objects.filter(
                materia_id=int(kwargs['root_pk'])).exists())

            # Se não for a primeira tramitação daquela matéria, o campo
            # não pode ser modificado
            if not primeira_tramitacao:
                context['form'].fields[
                    'unidade_tramitacao_local'].widget.attrs['readonly'] = True

            return context

        def form_valid(self, form):

            self.object = form.save()
            username = self.request.user.username

            try:
                self.logger.debug("user=" + username + ". Tentando enviar Tramitacao (sender={}, post={}, request={})."
                                  .format(Tramitacao, self.object, self.request))
            except Exception as e:
                msg = _('Tramitação criada, mas e-mail de acompanhamento '
                        'de matéria não enviado. Há problemas na configuração '
                        'do e-mail.')
                self.logger.warning('user=' + username + '. Tramitação criada, mas e-mail de acompanhamento '
                                    'de matéria não enviado. Há problemas na configuração '
                                    'do e-mail. ' + str(e))
                messages.add_message(self.request, messages.WARNING, msg)
                return HttpResponseRedirect(self.get_success_url())
            return super().form_valid(form)

    class UpdateView(CheckCheckMixin, MasterDetailCrud.UpdateView):
        form_class = TramitacaoUpdateForm
        logger = logging.getLogger(__name__)

        layout_key = 'TramitacaoUpdate'

        def form_valid(self, form):
            dict_objeto_antigo = Tramitacao.objects.get(
                pk=self.kwargs['pk']).__dict__

            self.object = form.save()
            dict_objeto_novo = self.object.__dict__

            user = self.request.user

            atributos = [
                'data_tramitacao', 'unidade_tramitacao_destino_id', 'status_id', 'texto',
                'data_encaminhamento', 'data_fim_prazo', 'urgente', 'turno'
            ]

            # Se não houve qualquer alteração em um dos dados, mantém o usuário
            # e ip
            for atributo in atributos:
                if dict_objeto_antigo[atributo] != dict_objeto_novo[atributo]:
                    self.object.user = user
                    self.object.ip = get_client_ip(self.request)
                    self.object.save()
                    break

            try:
                self.logger.debug("user=" + user.username + ". Tentando enviar Tramitacao (sender={}, post={}, request={}"
                                  .format(Tramitacao, self.object, self.request))
                pass
            except Exception:
                msg = _('Tramitação atualizada, mas e-mail de acompanhamento '
                        'de matéria não enviado. Há problemas na configuração '
                        'do e-mail.')
                self.logger.warning('user=' + user.username + '. Tramitação atualizada, mas e-mail de acompanhamento '
                                    'de matéria não enviado. Há problemas na configuração '
                                    'do e-mail.')
                messages.add_message(self.request, messages.WARNING, msg)
            return HttpResponseRedirect(self.get_success_url())

    class ListView(MasterDetailCrud.ListView):
        paginate_by = None

        def get_queryset(self):
            qs = super(MasterDetailCrud.ListView, self).get_queryset()
            kwargs = {self.crud.parent_field: self.kwargs['pk']}
            return qs.filter(**kwargs).order_by('-data_tramitacao',
                                                '-timestamp',
                                                '-id')

    class DeleteView(CheckCheckMixin, MasterDetailCrud.DeleteView):

        logger = logging.getLogger(__name__)

        def delete(self, request, *args, **kwargs):
            tramitacao = Tramitacao.objects.get(id=self.kwargs['pk'])
            materia = tramitacao.materia
            url = reverse('sapl.materia:tramitacao_list',
                          kwargs={'pk': materia.id})

            ultima_tramitacao = materia.tramitacao_set.order_by(
                '-data_tramitacao',
                '-timestamp',
                '-id').first()

            if tramitacao.pk != ultima_tramitacao.pk:
                username = request.user.username
                self.logger.error("user=" + username + ". Não é possível deletar a tramitação de pk={}. "
                                  "Somente a última tramitação (pk={}) pode ser deletada!."
                                  .format(tramitacao.pk, ultima_tramitacao.pk))
                msg = _('Somente a última tramitação pode ser deletada!')
                messages.add_message(request, messages.ERROR, msg)
                return HttpResponseRedirect(url)
            else:
                tramitacoes_deletar = [tramitacao.id]
                if materia.tramitacao_set.count() == 0:
                    materia.em_tramitacao = False
                    materia.save()
                tramitar_anexadas = sapl.base.models.AppConfig.attr(
                    'tramitacao_materia')
                if tramitar_anexadas:
                    mat_anexadas = lista_anexados(materia)
                    for ma in mat_anexadas:
                        tram_anexada = ma.tramitacao_set.first()
                        if compara_tramitacoes_mat(tram_anexada, tramitacao):
                            tramitacoes_deletar.append(tram_anexada.id)
                            if ma.tramitacao_set.count() == 0:
                                ma.em_tramitacao = False
                                ma.save()
                Tramitacao.objects.filter(id__in=tramitacoes_deletar).delete()

                return HttpResponseRedirect(url)

    class DetailView(MasterDetailCrud.DetailView):

        template_name = "materia/tramitacao_detail.html"

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['user'] = self.request.user
            return context


def montar_helper_documento_acessorio(self):
    autor_row = montar_row_autor('autor')
    self.helper = SaplFormHelper()
    self.helper.layout = SaplFormLayout(*self.get_layout())

    # Adiciona o novo campo 'autor' e mecanismo de busca
    self.helper.layout[0][0].append(HTML(autor_label))
    self.helper.layout[0][0].append(HTML(autor_modal))
    self.helper.layout[0][1] = autor_row

    # Remove botões que estão fora do form
    self.helper.layout[1].pop()

    # Adiciona novos botões dentro do form
    self.helper.layout[0][3][0].insert(1, form_actions(more=[
        HTML('<a href="{{ view.cancel_url }}"'
             ' class="btn btn-dark">Cancelar</a>')]))


class DocumentoAcessorioCrud(MasterDetailCrud):
    model = DocumentoAcessorio
    parent_field = 'materia'
    help_topic = 'despacho_autoria'
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['itemlist']
        ordered_list = False

    class CreateView(MasterDetailCrud.CreateView):
        form_class = DocumentoAcessorioForm

        def get_initial(self):
            initial = super(CreateView, self).get_initial()
            initial['data'] = timezone.now().date()
            initial['user'] = self.request.user
            return initial

    class DeleteView(CheckCheckMixin, MasterDetailCrud.DeleteView):
        pass

    class DetailView(MasterDetailCrud.DetailView):
        layout_key = 'DocumentoAcessorioDetail'

        def hook_protocolo_gr(self, obj):
            if obj.protocolo_gr.exists():
                return 'Protocolo', obj.protocolo_gr.first().epigrafe
            else:
                return 'Protocolo', ''

        def hook_arquivo(self, obj):

            doc_template = template.loader.get_template(
                'materia/documentoacessorio_widget_file.html')
            context = {}
            context['doc'] = obj
            rendered = doc_template.render(context, self.request)

            return 'Arquivo do Documento Acessório', rendered

    class UpdateView(CheckCheckMixin, MasterDetailCrud.UpdateView):
        form_class = DocumentoAcessorioForm

        def get_initial(self):
            initial = super(UpdateView, self).get_initial()
            initial['user'] = self.request.user
            return initial

    class ListView(MasterDetailCrud.ListView):
        paginate_by = None

        def hook_header_itemlist(self):
            return 'Documentos Acessórios'

        def hook_itemlist(self, obj, default, url):

            doc_template = template.loader.get_template(
                'materia/documentoacessorio_widget_itemlist.html')
            context = {}
            context['object'] = obj
            rendered = doc_template.render(context, self.request)

            return '{}'.format(rendered), ''


class AutoriaCrud(MasterDetailCrud):
    model = Autoria
    parent_field = 'materia'
    help_topic = 'despacho_autoria'
    public = [RP_LIST, RP_DETAIL]
    list_field_names = ['autor', 'autor__tipo__descricao', 'primeiro_autor']

    class LocalBaseMixin():
        form_class = AutoriaForm

        @property
        def layout_key(self):
            return None

    class CreateView(LocalBaseMixin, MasterDetailCrud.CreateView):

        def get_initial(self):
            initial = super().get_initial()
            materia = MateriaLegislativa.objects.get(id=self.kwargs['pk'])
            initial['data_relativa'] = materia.data_apresentacao
            initial['autor'] = []
            initial['materia'] = materia
            return initial

    class UpdateView(CheckCheckMixin, LocalBaseMixin,
                     MasterDetailCrud.UpdateView):

        def get_initial(self):
            initial = super().get_initial()
            initial.update({
                'data_relativa': self.object.materia.data_apresentacao,
                'tipo_autor': self.object.autor.tipo.id,
                'materia': self.object.materia
            })
            return initial

    class DeleteView(CheckCheckMixin, MasterDetailCrud.DeleteView):
        pass


class AutoriaMultiCreateView(PermissionRequiredForAppCrudMixin, FormView):
    app_label = sapl.materia.apps.AppConfig.label
    form_class = AutoriaMultiCreateForm
    template_name = 'materia/autoria_multicreate_form.html'

    @classmethod
    def get_url_regex(cls):
        return r'^/(?P<pk>\d+)/%s/multicreate' % cls.model._meta.model_name

    @property
    def layout_key(self):
        return None

    def get_initial(self):
        initial = super().get_initial()
        self.materia = MateriaLegislativa.objects.get(id=self.kwargs['pk'])
        initial['data_relativa'] = self.materia.data_apresentacao
        initial['autores'] = self.materia.autores.all()
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '%s <small>(%s)</small>' % (
            _('Adicionar Várias Autorias'), self.materia)
        return context

    def get_success_url(self):
        messages.add_message(
            self.request, messages.SUCCESS,
            _('Autorias adicionadas com sucesso.'))
        return reverse(
            'sapl.materia:autoria_list', kwargs={'pk': self.materia.pk})

    def form_valid(self, form):
        autores_selecionados = form.cleaned_data['autor']
        primeiro_autor = form.cleaned_data['primeiro_autor']
        for autor in autores_selecionados:
            Autoria.objects.create(materia=self.materia,
                                   autor=autor, primeiro_autor=primeiro_autor)

        return FormView.form_valid(self, form)


class DespachoInicialMultiCreateView(
        PermissionRequiredForAppCrudMixin, FormView):
    app_label = sapl.materia.apps.AppConfig.label
    form_class = DespachoInicialCreateForm
    template_name = 'materia/despachoinicial_multicreate_form.html'

    def get_initial(self):
        initial = super().get_initial()
        self.materia = MateriaLegislativa.objects.get(id=self.kwargs['pk'])
        initial['materia'] = self.materia
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '%s <small>(%s)</small>' % (
            _('Adicionar Vários Despachos'), self.materia)
        context['root_pk'] = self.kwargs['pk']
        context['subnav_template_name'] = 'materia/subnav.yaml'
        return context

    def get_success_url(self):
        messages.add_message(
            self.request, messages.SUCCESS,
            _('Despachos adicionados com sucesso.'))
        return reverse(
            'sapl.materia:despachoinicial_list', kwargs={'pk': self.materia.pk})

    def form_valid(self, form):
        comissoes_selecionadas = form.cleaned_data['comissao']
        for comissao in comissoes_selecionadas:
            DespachoInicial.objects.create(
                materia=self.materia, comissao=comissao)

        return FormView.form_valid(self, form)

    @property
    def cancel_url(self):
        return reverse(
            'sapl.materia:despachoinicial_list', kwargs={'pk': self.materia.pk})


class DespachoInicialCrud(MasterDetailCrud):
    model = DespachoInicial
    parent_field = 'materia'
    help_topic = 'despacho_autoria'
    public = [RP_LIST, RP_DETAIL]

    class UpdateView(CheckCheckMixin, MasterDetailCrud.UpdateView):
        form_class = DespachoInicialForm


class LegislacaoCitadaCrud(MasterDetailCrud):
    model = LegislacaoCitada
    parent_field = 'materia'
    help_topic = 'legislacao_cita_matanexada'
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['norma', 'disposicoes']

        def resolve_url(self, suffix, args=None):
            namespace = 'sapl.materia'
            return reverse('%s:%s' % (namespace, self.url_name(suffix)),
                           args=args)

    class CreateView(MasterDetailCrud.CreateView):
        form_class = LegislacaoCitadaForm

    class UpdateView(CheckCheckMixin, MasterDetailCrud.UpdateView):
        form_class = LegislacaoCitadaForm

        def get_initial(self):
            initial = super(UpdateView, self).get_initial()
            initial['tipo'] = self.object.norma.tipo.id
            initial['numero'] = self.object.norma.numero
            initial['ano'] = self.object.norma.ano
            return initial

    class DetailView(MasterDetailCrud.DetailView):

        layout_key = 'LegislacaoCitadaDetail'

    class DeleteView(CheckCheckMixin, MasterDetailCrud.DeleteView):
        pass


class NumeracaoCrud(MasterDetailCrud):
    model = Numeracao
    parent_field = 'materia'
    help_topic = 'numeracao_docsacess'
    public = [RP_LIST, RP_DETAIL]


class AnexadaCrud(MasterDetailCrud):
    model = Anexada
    parent_field = 'materia_principal'
    help_topic = 'materia_anexada'
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['materia_anexada',
                            'data_anexacao', 'data_desanexacao']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = AnexadaForm

    class UpdateView(CheckCheckMixin, MasterDetailCrud.UpdateView):
        form_class = AnexadaForm

        def get_initial(self):
            initial = super(UpdateView, self).get_initial()
            initial['tipo'] = self.object.materia_anexada.tipo.id
            initial['numero'] = self.object.materia_anexada.numero
            initial['ano'] = self.object.materia_anexada.ano
            return initial

    class DetailView(MasterDetailCrud.DetailView):

        @property
        def layout_key(self):
            return 'AnexadaDetail'

    class DeleteView(CheckCheckMixin, MasterDetailCrud.DeleteView):
        pass


class MateriaAssuntoCrud(MasterDetailCrud):
    model = MateriaAssunto
    parent_field = 'materia'
    help_topic = ''
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['assunto', 'materia']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = MateriaAssuntoForm

        def get_initial(self):
            initial = super(CreateView, self).get_initial()
            initial['materia'] = self.kwargs['pk']
            return initial

    class UpdateView(CheckCheckMixin, MasterDetailCrud.UpdateView):
        form_class = MateriaAssuntoForm

        def get_initial(self):
            initial = super(UpdateView, self).get_initial()
            initial['materia'] = self.get_object().materia
            initial['assunto'] = self.get_object().assunto
            return initial

    class DeleteView(CheckCheckMixin, MasterDetailCrud.DeleteView):
        pass


class MateriaLegislativaCrud(Crud):
    model = MateriaLegislativa
    help_topic = 'materia_legislativa'
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['tipo', 'numero', 'ano', 'data_apresentacao']

        list_url = ''

        @property
        def search_url(self):
            return reverse('cmj.search:materia_haystack_search')

        @property
        def sub_title(self):
            try:
                return self.object.ementa
            except BaseException:
                return ''

    class CreateView(Crud.CreateView):

        form_class = MateriaLegislativaForm

        def get_initial(self):
            initial = super().get_initial()

            initial['user'] = self.request.user
            initial['ip'] = get_client_ip(self.request)

            return initial

        @property
        def cancel_url(self):
            return self.search_url

    class UpdateView(CheckCheckMixin, Crud.UpdateView):

        form_class = MateriaLegislativaForm

        def get_initial(self):
            initial = super().get_initial()

            initial['user'] = self.request.user
            initial['ip'] = get_client_ip(self.request)

            return initial

        def form_valid(self, form):
            dict_objeto_antigo = MateriaLegislativa.objects.get(
                pk=self.kwargs['pk']
            ).__dict__

            self.object = form.save()
            dict_objeto_novo = self.object.__dict__

            atributos = [
                'tipo_id', 'ano', 'numero', 'data_apresentacao', 'numero_protocolo',
                'tipo_apresentacao', 'texto_original', 'apelido', 'dias_prazo', 'polemica',
                'objeto', 'regime_tramitacao_id', 'em_tramitacao', 'data_fim_prazo',
                'data_publicacao', 'complementar', 'tipo_origem_externa_id',
                'numero_origem_externa', 'ano_origem_externa', 'local_origem_externa_id',
                'data_origem_externa', 'ementa', 'indexacao', 'observacao'
            ]

            for atributo in atributos:
                if dict_objeto_antigo[atributo] != dict_objeto_novo[atributo]:
                    self.object.user = self.request.user
                    self.object.ip = get_client_ip(self.request)
                    self.object.save()
                    break

            if Anexada.objects.filter(
                    materia_principal=self.kwargs['pk']).exists():
                materia = MateriaLegislativa.objects.get(pk=self.kwargs['pk'])
                anexadas = lista_anexados(materia)

                for anexada in anexadas:
                    anexada.em_tramitacao = True if form.instance.em_tramitacao else False
                    anexada.save()

            return super().form_valid(form)

    class DeleteView(CheckCheckMixin, Crud.DeleteView):

        def get_success_url(self):
            return self.search_url

    class DetailView(GoogleGenerativeIA, BtnCertMixin, Crud.DetailView):

        layout_key = 'MateriaLegislativaDetail'
        template_name = "materia/materialegislativa_detail.html"

        @property
        def extras_url(self):
            btns = self.btn_certidao('texto_original')

            if self.request.user.has_perm('compilacao.add_textoarticulado'):
                if not self.object.texto_articulado.exists():
                    btns.extend(
                        [
                            (
                                reverse('sapl.materia:materia_ta',
                                        kwargs={'pk': self.kwargs['pk']}),
                                'btn-primary',
                                _('Criar Texto Articulado')
                            )
                        ]
                    )
                elif self.request.user.is_superuser:
                    btns.extend(
                        [
                            (
                                reverse('sapl.compilacao:ta_delete',
                                        kwargs={'pk': self.object.texto_articulado.first().pk}),
                                'btn-danger',
                                _('Excluir Texto Articulado')
                            )
                        ]
                    )

            if self.request.user.has_perm('core.generate_analise_genia'):
                btns.extend(
                    self.get_btn_generate(
                        'sapl.materia:materialegislativa_detail')
                )

            btns = list(filter(None, btns))
            return btns

        def download(self, download):

            ff = 'original_path' if download == 'original' else 'path'

            m_paths = []

            principal = self.get_object()

            def get_anexadas_from(m, prefixo=''):
                p = getattr(m.texto_original, ff)
                m_paths.append((m, prefixo, p))
                for a in m.materia_principal_set.filter(
                    data_desanexacao__isnull=True
                ).order_by('materia_anexada__tipo', 'data_anexacao'):
                    manex = a.materia_anexada
                    p2 = 'MatAnexadas-{}-{}-{:03d}-{}'.format(
                        slugify(manex.tipo.descricao),
                        manex.ano,
                        manex.numero,
                        slugify(manex.tipo.sigla)
                    )

                    get_anexadas_from(
                        a.materia_anexada,
                        prefixo=p2)

                for d in m.documentoacessorio_set.all():

                    if d.data > timezone.localtime().date() - timedelta(days=30):
                        continue

                    m_paths.append((d, prefixo, getattr(d.arquivo, ff)))

            def get_docadm_anexados_from(d):
                if d.texto_integral:
                    p = getattr(d.texto_integral, ff)
                    m_paths.append((d, 'DocAdms', p))

                for danex in d.anexados.all():
                    get_docadm_anexados_from(danex)

            get_anexadas_from(principal)

            docs = principal.documentoadministrativo_set.all()
            for d in docs:
                get_docadm_anexados_from(d)

            m_paths = list(set(m_paths))

            with tempfile.SpooledTemporaryFile(max_size=512000000) as tmp:

                with zipfile.ZipFile(tmp, 'w') as file:

                    for i, prefixo, path in m_paths:

                        if isinstance(i, DocumentoAcessorio):
                            arcname = '{}-DA-{}-{}-{}-{}.{}'.format(
                                prefixo,
                                i.ano,
                                slugify(i.tipo.descricao),
                                slugify(i.nome),
                                i.id,
                                path.split('.')[-1]
                            )
                        else:
                            arcname = '{}-{}-{}-{}-{}-{}-{:02d}.{}'.format(
                                prefixo,
                                'ML' if isinstance(
                                    i, MateriaLegislativa) else 'DA',
                                i.ano,
                                i.numero,
                                slugify(i.tipo.sigla),
                                slugify(i.tipo.descricao),
                                i.id,
                                path.split('.')[-1])

                        file.write(
                            path,
                            arcname
                        )

                tmp.seek(0)

                response = HttpResponse(tmp.read(),
                                        content_type='application/zip')

            response['Cache-Control'] = 'no-cache'
            response['Pragma'] = 'no-cache'
            response['Expires'] = 0
            response['Content-Disposition'] = \
                'inline; filename=%s-%s-%s.zip' % (
                    slugify(principal.tipo.sigla),
                    principal.numero,
                    principal.ano)

            return response

        def cabec_autografo(self, cabec_autografo):
            self.template_name = "materia/materialegislativa_cabec_autografo.html"

            self.object = self.get_object()
            context = self.get_context_data(object=self.object)
            return self.render_to_response(context)

        def is_run(self):
            md = super().ia_run()

            if md and md.metadata:
                temas = md.metadata.get('genia', {}).get('temas', [])

                obj = md.content_object

                for tema in temas:
                    assunto, created = AssuntoMateria.objects.get_or_create(
                        assunto=tema
                    )

                    mass, created = MateriaAssunto.objects.get_or_create(
                        assunto=assunto,
                        materia=obj
                    )

            return HttpResponseRedirect(reverse(
                'sapl.materia:materialegislativa_detail',
                kwargs={'pk': self.kwargs['pk']}
            ))

        def get(self, request, *args, **kwargs):
            # celery.debug_task.apply_async(
            #    (kwargs['pk'], ),
            #    countdown=10
            # )
            if 'download' in request.GET:
                return self.download(request.GET.get('download'))

            if 'ia_run' in request.GET and request.user.has_perm('core.generate_analise_genia'):
                return self.is_run()
            elif 'cabec_autografo' in request.GET:
                return self.cabec_autografo(request.GET.get('cabec_autografo'))

            if 'homologar' in request.GET and request.user.is_superuser:
                self.object = self.get_object()
                x = int(self.request.GET.get('x', 193))
                y = int(self.request.GET.get('y', 50))
                compression = self.request.GET.get('compression', False)
                original2copia = self.request.GET.get('original2copia', True)
                self.object.homologar(x=x, y=y, compression=compression, original2copia=original2copia)

            return Crud.DetailView.get(self, request, *args, **kwargs)

        def hook_documentoadministrativo_set__deprecated(self, obj):

            docs = obj.documentoadministrativo_set.all()
            if not docs.exists():
                return '', ''

            doc_template = template.loader.get_template(
                'protocoloadm/documentoadministrativo_widget_materia.html')
            context = {}
            context['doc_list'] = docs
            rendered = doc_template.render(context, self.request)

            return 'Documentos Administrativos Vinculados a Matéria', rendered

        def hook_protocolo_gr(self, obj):
            if obj.protocolo_gr.exists():
                p = obj.protocolo_gr.first()
                value = p.epigrafe
                if self.request.user.has_perm('protocoloadm.list_protocolo'):
                    value = '<a href="{}">{}</a>'.format(
                        reverse('sapl.protocoloadm:protocolo_mostrar',
                                kwargs={'pk': p.id}),
                        value)

                return 'Protocolo', value
            else:
                return 'Protocolo', ''

        def hook_diariooficial_set(self, obj):
            if obj.diariosoficiais.exists():
                d = obj.diariosoficiais.first().diario
                value = '<a href="{}">{}</a> <small><i>({})</i></small>'.format(
                    reverse('cmj.diarios:diariooficial_detail',
                            kwargs={'pk': d.id}),
                    d,
                    formats.date_format(
                        d.data, "DATE_FORMAT")
                )
                return 'Diário Oficial', value
            else:
                return 'Diário Oficial', ''

        def hook_documentoadministrativo_set__deprecated(self, obj):

            docs = obj.documentoadministrativo_set.all()
            if not docs.exists():
                return '', ''

            result = ['', []]

            for d in docs:
                if not d.texto_integral:
                    continue

                if d.workspace.tipo != AreaTrabalho.TIPO_PUBLICO:
                    if not self.request.user.groups.filter(
                            name=GROUP_MATERIA_WORKSPACE_VIEWER).exists():

                        rede = self.request.META.get(
                            'HTTP_X_FORWARDED_FOR', '')
                        if not rede.startswith('168.228.184') and \
                                self.request.META.get(
                                'REMOTE_ADDR', '') != '127.0.0.1':
                            continue

                if not result[0]:
                    result[0] = _('Documentos Administrativos Vinculados')

                result[1].append(d)

            if not result[0]:
                return '', ''

            result[1] = '<br>'.join(
                map(
                    lambda d:
                    '<a class="w-100" href="{}">{}</a><br><small>{}</small>'.format(
                        d.texto_integral.url, d,
                        d.observacao if d.workspace.tipo == AreaTrabalho.TIPO_PROCURADORIA else d.assunto
                    ),
                    result[1]
                )
            )

            return result

        def hook_normajuridica_set(self, obj):

            normas = obj.normajuridica_set.exclude(tipo_id=27)
            if not normas.exists():
                return '', ''

            return _('Norma Jurídica Vinculada'), '<br>'.join(['<a href="{}">{}</a>'.format(
                reverse('sapl.norma:normajuridica_detail',
                        kwargs={'pk': n.id}), n
            ) for n in normas]
            )

        def hook_autografo_set(self, obj):

            autografos = obj.normajuridica_set.filter(tipo_id=27)
            if not autografos.exists():
                return '', ''

            return _('Autógrafo'), '<br>'.join(['<a href="{}">{}</a>'.format(
                reverse('sapl.norma:normajuridica_detail',
                        kwargs={'pk': a.id}), a
            ) for a in autografos]
            )

        """def get_queryset(self):
            qs = Crud.DetailView.get_queryset(self)

            if not self.request.user.groups.filter(
                    name=GROUP_MATERIA_WORKSPACE_VIEWER).exists():
                qs = qs.exclude(despachoinicial_set__isnull=True)

            return qs"""

        def hook_anexadas__materias_anexadas(self, *args, **kwargs):
            if kwargs.get('field_display', ''):
                return 'Matérias Anexadas', kwargs['field_display']
            else:
                return '', ''

        def hook_anexadas__materias_desanexadas(self, *args, **kwargs):
            if kwargs['field_display']:
                return 'Matérias Desanexadas', kwargs['field_display']
            else:
                return '', ''

    class ListView(Crud.ListView, RedirectView):

        def get_redirect_url(self, *args, **kwargs):
            return reverse('cmj.search:materia_haystack_search')

        def get(self, request, *args, **kwargs):
            return RedirectView.get(self, request, *args, **kwargs)


# FIXME - qual a finalidade dessa classe??
class DocumentoAcessorioView(PermissionRequiredMixin, CreateView):
    template_name = "materia/documento_acessorio.html"
    form_class = DocumentoAcessorioForm
    permission_required = ('materia.add_documentoacessorio',)

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        docs = DocumentoAcessorio.objects.filter(
            materia_id=kwargs['pk']).order_by('data')
        form = DocumentoAcessorioForm()

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'docs': docs})

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        docs_list = DocumentoAcessorio.objects.filter(
            materia_id=kwargs['pk'])

        if form.is_valid():
            documento_acessorio = form.save(commit=False)
            documento_acessorio.materia = materia
            documento_acessorio.save()
            return self.form_valid(form)
        else:
            return self.render_to_response({'form': form,
                                            'object': materia,
                                            'docs': docs_list})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.materia:documento_acessorio', kwargs={'pk': pk})


class AcompanhamentoConfirmarView(TemplateView):

    logger = logging.getLogger(__name__)

    def get_redirect_url(self, email):
        username = self.request.user.username
        self.logger.debug(
            'user=' + username + '. Esta matéria está sendo acompanhada pelo e-mail: %s' % (email))
        msg = _('Esta matéria está sendo acompanhada pelo e-mail: %s') % (
            email)
        messages.add_message(self.request, messages.SUCCESS, msg)
        return reverse('sapl.materia:materialegislativa_detail',
                       kwargs={'pk': self.kwargs['pk']})

    def get(self, request, *args, **kwargs):
        materia_id = kwargs['pk']
        hash_txt = request.GET.get('hash_txt', '')
        username = self.request.user.username

        try:
            self.logger.info("user=" + username + ". Tentando obter objeto AcompanhamentoMateria (materia_id={}, hash={})."
                             .format(materia_id, hash_txt))
            acompanhar = AcompanhamentoMateria.objects.get(
                materia_id=materia_id,
                hash=hash_txt)
        except ObjectDoesNotExist:
            self.logger.error("user=" + username + ". Objeto AcompanhamentoMateria(materia_id={}, hash={}) não encontrado."
                              .format(materia_id, hash_txt))
            raise Http404()
        except MultipleObjectsReturned as e:
            # A melhor solução deve ser permitir que a exceção
            # (MultipleObjectsReturned) seja lançada e vá para o log,
            # pois só poderá ser causada por um erro de desenvolvimente
            self.logger.error('user=' + username + '.' + str(e))
            pass
        acompanhar.confirmado = True
        acompanhar.save()

        return HttpResponseRedirect(self.get_redirect_url(acompanhar.email))


class AcompanhamentoExcluirView(TemplateView):

    logger = logging.getLogger(__name__)

    def get_success_url(self):
        username = self.request.user.username
        self.logger.debug("user=" + username +
                          ". Você parou de acompanhar esta matéria.")
        msg = _('Você parou de acompanhar esta matéria.')
        messages.add_message(self.request, messages.INFO, msg)
        return reverse('sapl.materia:materialegislativa_detail',
                       kwargs={'pk': self.kwargs['pk']})

    def get(self, request, *args, **kwargs):
        materia_id = kwargs['pk']
        hash_txt = request.GET.get('hash_txt', '')
        username = self.request.user.username

        try:
            self.logger.info("user=" + username + ". Tentando deletar objeto AcompanhamentoMateria (materia_id={}, hash={})."
                             .format(materia_id, hash_txt))
            AcompanhamentoMateria.objects.get(materia_id=materia_id,
                                              hash=hash_txt).delete()
        except ObjectDoesNotExist:
            self.logger.error("user=" + username + ". Objeto AcompanhamentoMateria (materia_id={}, hash={}) não encontrado."
                              .format(materia_id, hash_txt))
            pass

        return HttpResponseRedirect(self.get_success_url())


class MateriaLegislativaPesquisaView(
        AudigLogFilterMixin, MultiFormatOutputMixin, FilterView):
    model = MateriaLegislativa
    filterset_class = MateriaLegislativaFilterSet
    paginate_by = 50
    app_label = AppConfig.label

    fields_base_report = [
        'id', 'ano', 'numero', 'tipo__sigla', 'tipo__descricao', 'autoria__autor__nome', 'texto_original', 'ementa'
    ]
    fields_report = {
        'csv': fields_base_report,
        'xlsx': fields_base_report,
        'json': fields_base_report,
    }

    def hook_header_texto_original(self):
        return force_str(_('Link para Matéria Legislativa'))

    def hook_texto_original(self, obj):
        id = obj["id"] if isinstance(obj, dict) else obj.id
        return f'{settings.SITE_URL}/materia/{id}'

    def render_to_response(self, context, **response_kwargs):

        if not context['show_results'] and \
                not self.request.user.is_superuser and \
                self.app_label in __name__:
            return HttpResponsePermanentRedirect(
                reverse('cmj.search:materia_haystack_search'))

        return MultiFormatOutputMixin.render_to_response(
            self, context, **response_kwargs)

    def get_filterset_kwargs(self, filterset_class):
        super().get_filterset_kwargs(filterset_class)

        kwargs = {'data': self.request.GET or None}

        tipo_listagem = self.request.GET.get('tipo_listagem', '1')
        tipo_listagem = '1' if not tipo_listagem else tipo_listagem

        qs = self.get_queryset().distinct()
        if tipo_listagem == '1':

            status_tramitacao = self.request.GET.get('tramitacao__status')
            unidade_destino = self.request.GET.get(
                'tramitacao__unidade_tramitacao_destino')

            if status_tramitacao and unidade_destino:
                lista = filtra_tramitacao_destino_and_status(status_tramitacao,
                                                             unidade_destino)
                qs = qs.filter(id__in=lista).distinct()

            elif status_tramitacao:
                lista = filtra_tramitacao_status(status_tramitacao)
                qs = qs.filter(id__in=lista).distinct()

            elif unidade_destino:
                lista = filtra_tramitacao_destino(unidade_destino)
                qs = qs.filter(id__in=lista).distinct()

            qs = qs.prefetch_related("autoria_set",
                                     "autoria_set__autor",
                                     "numeracao_set",
                                     "anexadas",
                                     "tipo",
                                     "texto_articulado",
                                     "tramitacao_set",
                                     "tramitacao_set__status",
                                     "tramitacao_set__unidade_tramitacao_local",
                                     "tramitacao_set__unidade_tramitacao_destino",
                                     "normajuridica_set",
                                     "registrovotacao_set",
                                     "documentoacessorio_set")
        else:

            qs = qs.prefetch_related("autoria_set",
                                     "numeracao_set",
                                     "autoria_set__autor",
                                     "tipo",)

        # if 'o' in self.request.GET and not self.request.GET['o']:
        #    qs = qs.order_by('-ano', '-id')

        kwargs.update({
            'queryset': qs,
        })
        return kwargs

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context['title'] = _('Matérias Legislativas')

        context['bg_title'] = 'bg-red text-white'

        tipo_listagem = self.request.GET.get('tipo_listagem', '1')
        tipo_listagem = '1' if not tipo_listagem else tipo_listagem

        context['tipo_listagem'] = tipo_listagem

        qr = self.request.GET.copy()
        if 'page' in qr:
            del qr['page']

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)

        context['USE_SOLR'] = settings.USE_SOLR if hasattr(
            settings, 'USE_SOLR') else False

        acesso_rapido_list = list(tipos_autores_materias(
            None, restricao_regimental=False).items()
        )

        acesso_rapido_list.sort(key=lambda tup: tup[0].sequencia_regimental)

        context['tipos_autores_materias'] = acesso_rapido_list

        return context


class AcompanhamentoMateriaView(CreateView):
    logger = logging.getLogger(__name__)
    template_name = "materia/acompanhamento_materia.html"

    def get_random_chars(self):
        s = ascii_letters + digits
        return ''.join(choice(s) for i in range(choice([6, 7])))

    def get(self, request, *args, **kwargs):
        if not mail_service_configured():
            self.logger.warning(_('Servidor de email não configurado.'))
            messages.error(request, _('Serviço de Acompanhamento de '
                                      'Matérias não foi configurado'))
            return redirect('/')

        pk = self.kwargs['pk']
        materia = MateriaLegislativa.objects.get(id=pk)

        return self.render_to_response(
            {'form': AcompanhamentoMateriaForm(),
             'materia': materia})

    def post(self, request, *args, **kwargs):

        if not settings.EMAIL_HOST:
            self.logger.warning(_('Servidor de email não configurado.'))
            messages.error(request, _('Serviço de Acompanhamento de '
                                      'Matérias não foi configurado'))
            return redirect('/')

        form = AcompanhamentoMateriaForm(request.POST)
        pk = self.kwargs['pk']
        materia = MateriaLegislativa.objects.get(id=pk)

        if form.is_valid():
            email = form.cleaned_data['email']
            usuario = request.user

            hash_txt = self.get_random_chars()

            acompanhar = AcompanhamentoMateria.objects.get_or_create(
                materia=materia,
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

                destinatario = AcompanhamentoMateria.objects.get(
                    materia=materia,
                    email=email,
                    confirmado=False)
                casa = CasaLegislativa.objects.first()

                do_envia_email_confirmacao(base_url,
                                           casa,
                                           "materia",
                                           materia,
                                           destinatario)
                self.logger.debug('user=' + usuario.username + '. Foi enviado um e-mail de confirmação. Confira sua caixa \
                                de mensagens e clique no link que nós enviamos para \
                                confirmar o acompanhamento desta matéria.')
                msg = _('Foi enviado um e-mail de confirmação. Confira sua caixa \
                         de mensagens e clique no link que nós enviamos para \
                         confirmar o acompanhamento desta matéria.')
                messages.add_message(request, messages.SUCCESS, msg)

            # Se o elemento existir e o email não foi confirmado:
            # gerar novo hash e reenviar mensagem de email
            elif not acompanhar[0].confirmado:
                acompanhar = acompanhar[0]
                acompanhar.hash = hash_txt
                acompanhar.save()

                base_url = get_base_url(request)

                destinatario = AcompanhamentoMateria.objects.get(
                    materia=materia,
                    email=email,
                    confirmado=False
                )

                casa = CasaLegislativa.objects.first()

                do_envia_email_confirmacao(base_url,
                                           casa,
                                           "materia",
                                           materia,
                                           destinatario)

                self.logger.debug('user=' + usuario.username + '. Foi enviado um e-mail de confirmação. Confira sua caixa \
                                  de mensagens e clique no link que nós enviamos para \
                                  confirmar o acompanhamento desta matéria.')

                msg = _('Foi enviado um e-mail de confirmação. Confira sua caixa \
                        de mensagens e clique no link que nós enviamos para \
                        confirmar o acompanhamento desta matéria.')
                messages.add_message(request, messages.SUCCESS, msg)

            # Caso esse Acompanhamento já exista
            # avisa ao usuário que essa matéria já está sendo acompanhada
            else:
                self.logger.debug("user=" + usuario.username +
                                  ". Este e-mail já está acompanhando essa matéria.")
                msg = _('Este e-mail já está acompanhando essa matéria.')
                messages.add_message(request, messages.ERROR, msg)

                return self.render_to_response(
                    {'form': form,
                     'materia': materia
                     })
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(
                {'form': form,
                 'materia': materia})

    def get_success_url(self):
        return reverse('sapl.materia:materialegislativa_detail',
                       kwargs={'pk': self.kwargs['pk']})


class DocumentoAcessorioEmLoteView(PermissionRequiredMixin, FilterView):
    filterset_class = AcessorioEmLoteFilterSet
    template_name = 'materia/em_lote/acessorio.html'
    permission_required = ('materia.add_documentoacessorio',)
    logger = logging.getLogger(__name__)

    def get_context_data(self, **kwargs):
        context = super(DocumentoAcessorioEmLoteView,
                        self).get_context_data(**kwargs)

        context['title'] = _('Documentos Acessórios em Lote')
        # Verifica se os campos foram preenchidos
        if not self.filterset.form.is_valid():
            return context

        qr = self.request.GET.copy()
        context['tipos_docs'] = TipoDocumento.objects.all()
        context['object_list'] = context['object_list'].order_by(
            'ano', 'numero')
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)

        return context

    def post(self, request, *args, **kwargs):
        username = request.user.username
        marcadas = request.POST.getlist('materia_id')

        if len(marcadas) == 0:
            msg = _('Nenhuma máteria foi selecionada.')
            messages.add_message(request, messages.ERROR, msg)
            return self.get(request, self.kwargs)

        tipo = TipoDocumento.objects.get(descricao=request.POST['tipo'])

        if len(request.POST['autor']) > 50:
            msg = _('Autor tem que ter menos do que 50 caracteres.')
            messages.add_message(request, messages.ERROR, msg)
            return self.get(request, self.kwargs)

        if request.FILES['arquivo'].size > MAX_DOC_UPLOAD_SIZE:
            msg = _("O arquivo Anexo de Texto Integral deve ser menor que {0:.1f} MB, \
                o tamanho atual desse arquivo é {1:.1f} MB"
                    .format((MAX_DOC_UPLOAD_SIZE / 1024) / 1024, (request.FILES['arquivo'].size / 1024) / 1024))
            messages.add_message(request, messages.ERROR, msg)
            return self.get(request, self.kwargs)

        tmp_name = os.path.join(MEDIA_ROOT, request.FILES['arquivo'].name)
        with open(tmp_name, 'wb') as destination:
            for chunk in request.FILES['arquivo'].chunks():
                destination.write(chunk)
        try:
            doc_data = tz.localize(datetime.strptime(
                request.POST['data'], "%d/%m/%Y"))
        except Exception as e:
            msg = _(
                'Formato da data incorreto. O formato deve ser da forma dd/mm/aaaa.')
            messages.add_message(request, messages.ERROR, msg)
            self.logger.error("User={}. {}. Data inserida: {}".format(
                username, str(msg), request.POST['data']))
            os.remove(tmp_name)
            return self.get(request, self.kwargs)

        for materia_id in marcadas:
            doc = DocumentoAcessorio()
            doc.materia_id = materia_id
            doc.tipo = tipo
            doc.nome = request.POST['nome']
            doc.data = doc_data
            doc.autor = request.POST['autor']
            doc.ementa = request.POST['ementa']
            doc.arquivo.name = tmp_name
            try:
                doc.clean_fields()
            except ValidationError as e:
                for m in ['%s: %s' % (DocumentoAcessorio()._meta.get_field(k).verbose_name, '</br>'.join(v))
                          for k, v in e.message_dict.items()]:
                    # Insere as mensagens de erro no formato:
                    # 'verbose_name do nome do campo': 'mensagem de erro'
                    messages.add_message(request, messages.ERROR, m)
                    self.logger.error("User={}. {}. Nome do arquivo: {}.".format(
                        username, str(msg), request.FILES['arquivo'].name))
                os.remove(tmp_name)
                return self.get(request, self.kwargs)
            doc.save()
            diretorio = os.path.join(MEDIA_ROOT,
                                     'sapl/public/documentoacessorio',
                                     str(doc_data.year),
                                     str(doc.id))
            if not os.path.exists(diretorio):
                os.makedirs(diretorio)
            file_path = os.path.join(diretorio,
                                     request.FILES['arquivo'].name)
            shutil.copy2(tmp_name, file_path)
            doc.arquivo.name = file_path.split(
                MEDIA_ROOT + "/")[1]  # Retira MEDIA_ROOT do nome
            doc.save()
        os.remove(tmp_name)

        msg = _('Documento(s) criado(s).')
        messages.add_message(request, messages.SUCCESS, msg)
        return self.get(request, self.kwargs)


class MateriaAnexadaEmLoteView(PermissionRequiredMixin, FilterView):
    filterset_class = AnexadaEmLoteFilterSet
    template_name = 'materia/em_lote/anexada.html'
    permission_required = ('materia.add_documentoacessorio',)

    def get_context_data(self, **kwargs):
        context = super(MateriaAnexadaEmLoteView,
                        self).get_context_data(**kwargs)

        context['root_pk'] = self.kwargs['pk']

        context['subnav_template_name'] = 'materia/subnav.yaml'

        context['title'] = _('Matérias Anexadas em Lote')

        # Verifica se os campos foram preenchidos
        if not self.request.GET.get('tipo', " "):
            msg = _('Por favor, selecione um tipo de matéria.')
            messages.add_message(self.request, messages.ERROR, msg)

            if not self.request.GET.get('data_apresentacao_0', " ") or not self.request.GET.get(
                    'data_apresentacao_1', " "):
                msg = _('Por favor, preencha as datas.')
                messages.add_message(self.request, messages.ERROR, msg)

            return context

        if not self.request.GET.get('data_apresentacao_0', " ") or not self.request.GET.get(
                'data_apresentacao_1', " "):
            msg = _('Por favor, preencha as datas.')
            messages.add_message(self.request, messages.ERROR, msg)
            return context

        qr = self.request.GET.copy()
        context['object_list'] = context['object_list'].order_by(
            'numero', '-ano')
        principal = MateriaLegislativa.objects.get(pk=self.kwargs['pk'])
        not_list = [self.kwargs['pk']] + \
            [m for m in principal.materia_principal_set.all(
            ).values_list('materia_anexada_id', flat=True)]
        context['object_list'] = context['object_list'].exclude(
            pk__in=not_list)

        context['temp_object_list'] = context['object_list']
        context['object_list'] = []
        for obj in context['temp_object_list']:
            materia_anexada = obj
            ciclico = False
            anexadas_anexada = Anexada.objects.filter(
                materia_principal=materia_anexada
            )

            while anexadas_anexada and not ciclico:
                anexadas = []

                for anexa in anexadas_anexada:

                    if principal == anexa.materia_anexada:
                        ciclico = True
                    else:
                        for a in Anexada.objects.filter(
                                materia_principal=anexa.materia_anexada):
                            anexadas.append(a)

                anexadas_anexada = anexadas

            if not ciclico:
                context['object_list'].append(obj)

        context['numero_res'] = len(context['object_list'])

        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)

        return context

    def post(self, request, *args, **kwargs):
        marcadas = request.POST.getlist('materia_id')

        data_anexacao = datetime.strptime(
            request.POST['data_anexacao'], "%d/%m/%Y").date()

        if request.POST['data_desanexacao'] == '':
            data_desanexacao = None
            v_data_desanexacao = data_anexacao
        else:
            data_desanexacao = datetime.strptime(
                request.POST['data_desanexacao'], "%d/%m/%Y").date()
            v_data_desanexacao = data_desanexacao

        if len(marcadas) == 0:
            msg = _('Nenhuma máteria foi selecionada.')
            messages.add_message(request, messages.ERROR, msg)

            if data_anexacao > v_data_desanexacao:
                msg = _('Data de anexação posterior à data de desanexação.')
                messages.add_message(request, messages.ERROR, msg)

            return self.get(request, self.kwargs)

        if data_anexacao > v_data_desanexacao:
            msg = _('Data de anexação posterior à data de desanexação.')
            messages.add_message(request, messages.ERROR, msg)
            return self.get(request, self.kwargs)

        principal = MateriaLegislativa.objects.get(pk=kwargs['pk'])
        for materia in MateriaLegislativa.objects.filter(id__in=marcadas):

            anexada = Anexada()
            anexada.materia_principal = principal
            anexada.materia_anexada = materia
            anexada.data_anexacao = data_anexacao
            anexada.data_desanexacao = data_desanexacao
            anexada.save()

        msg = _('Matéria(s) anexada(s).')
        messages.add_message(request, messages.SUCCESS, msg)

        success_url = reverse('sapl.materia:anexada_list',
                              kwargs={'pk': kwargs['pk']})
        return HttpResponseRedirect(success_url)


class PrimeiraTramitacaoEmLoteView(PermissionRequiredMixin, FilterView):
    filterset_class = PrimeiraTramitacaoEmLoteFilterSet
    template_name = 'materia/em_lote/tramitacao.html'
    permission_required = ('materia.add_tramitacao',)

    primeira_tramitacao = True

    logger = logging.getLogger(__name__)

    def get_context_data(self, **kwargs):
        context = super(PrimeiraTramitacaoEmLoteView,
                        self).get_context_data(**kwargs)

        context['subnav_template_name'] = 'materia/em_lote/subnav_em_lote.yaml'
        context['primeira_tramitacao'] = self.primeira_tramitacao

        # Verifica se os campos foram preenchidos
        if not self.filterset.form.is_valid():
            return context

        context['object_list'] = context['object_list'].order_by(
            'ano', 'numero')
        qr = self.request.GET.copy()

        form = TramitacaoEmLoteForm()
        context['form'] = form

        if self.primeira_tramitacao:
            context['title'] = _('Primeira Tramitação em Lote')
            # Pega somente documentos que não possuem tramitação
            context['object_list'] = [obj for obj in context['object_list']
                                      if obj.tramitacao_set.all().count() == 0]
        else:
            context['title'] = _('Tramitação em Lote')
            context['form'].fields['unidade_tramitacao_local'].initial = UnidadeTramitacao.objects.get(
                id=qr['tramitacao__unidade_tramitacao_destino'])

        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)

        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        ip = get_client_ip(request)

        materias_ids = request.POST.getlist('materias')
        if not materias_ids:
            msg = _("Escolha alguma matéria para ser tramitada.")
            messages.add_message(request, messages.ERROR, msg)
            return self.get(request, self.kwargs)

        form = TramitacaoEmLoteForm(request.POST,
                                    initial={'materias': materias_ids,
                                             'user': user, 'ip': ip})

        if form.is_valid():
            form.save()

            msg = _('Tramitação completa.')
            self.logger.info('user=' + user.username +
                             '. Tramitação completa.')
            messages.add_message(request, messages.SUCCESS, msg)
            return self.get_success_url()

        return self.form_invalid(form)

    def get_success_url(self):
        return HttpResponseRedirect(
            reverse('sapl.materia:primeira_tramitacao_em_lote'))

    def form_invalid(self, form, *args, **kwargs):
        for key, erros in form.errors.items():
            if not key == '__all__':
                [messages.add_message(
                    self.request, messages.ERROR, form.fields[key].label + ": " + e) for e in erros]
            else:
                [messages.add_message(self.request, messages.ERROR, e)
                 for e in erros]
        return self.get(self.request, kwargs, {'form': form})


class TramitacaoEmLoteView(PrimeiraTramitacaoEmLoteView):
    filterset_class = TramitacaoEmLoteFilterSet

    primeira_tramitacao = False

    def get_context_data(self, **kwargs):
        context = super(TramitacaoEmLoteView,
                        self).get_context_data(**kwargs)

        qr = self.request.GET.copy()

        context['primeira_tramitacao'] = self.primeira_tramitacao

        if ('tramitacao__status' in qr and
                'tramitacao__unidade_tramitacao_destino' in qr and
                qr['tramitacao__status'] and
                qr['tramitacao__unidade_tramitacao_destino']):
            lista = filtra_tramitacao_destino_and_status(
                qr['tramitacao__status'],
                qr['tramitacao__unidade_tramitacao_destino'])
            context['object_list'] = context['object_list'].filter(
                id__in=lista).distinct()

        return context


class ImpressosView(PermissionRequiredMixin, TemplateView):
    template_name = 'materia/impressos/impressos.html'
    permission_required = ('materia.can_access_impressos',)


class EtiquetaPesquisaView(PermissionRequiredMixin, FormView):
    form_class = EtiquetaPesquisaForm
    template_name = 'materia/impressos/impressos_form.html'
    permission_required = ('materia.can_access_impressos',)

    def form_valid(self, form):
        context = {}

        materias = MateriaLegislativa.objects.all().order_by(
            '-data_apresentacao')

        if form.cleaned_data['tipo_materia']:
            materias = materias.filter(tipo=form.cleaned_data['tipo_materia'])

        if form.cleaned_data['data_inicial']:
            materias = materias.filter(
                data_apresentacao__gte=form.cleaned_data['data_inicial'],
                data_apresentacao__lte=form.cleaned_data['data_final'])

        if form.cleaned_data['processo_inicial']:
            materias = materias.filter(
                numeracao__numero_materia__gte=form.cleaned_data[
                    'processo_inicial'],
                numeracao__numero_materia__lte=form.cleaned_data[
                    'processo_final'])

        context['quantidade'] = len(materias)

        if context['quantidade'] > 20:
            materias = materias[:20]

        for m in materias:
            if len(m.ementa) > 100:
                m.ementa = m.ementa[0:99] + "[...]"

        context['materias'] = materias

        return gerar_pdf_impressos(self.request, context,
                                   'materia/impressos/etiqueta_pdf.html')


class FichaPesquisaView(PermissionRequiredMixin, FormView):
    form_class = FichaPesquisaForm
    template_name = 'materia/impressos/impressos_form.html'
    permission_required = ('materia.can_access_impressos',)

    def form_valid(self, form):
        tipo_materia = form.data['tipo_materia']
        data_inicial = form.data['data_inicial']
        data_final = form.data['data_final']

        url = reverse('sapl.materia:impressos_ficha_seleciona')
        url = url + '?tipo=%s&data_inicial=%s&data_final=%s' % (
            tipo_materia, data_inicial, data_final)

        return HttpResponseRedirect(url)


class FichaSelecionaView(PermissionRequiredMixin, FormView):
    logger = logging.getLogger(__name__)
    form_class = FichaSelecionaForm
    template_name = 'materia/impressos/impressos_form.html'
    permission_required = ('materia.can_access_impressos',)

    def get_context_data(self, **kwargs):
        if ('tipo' not in self.request.GET or
            'data_inicial' not in self.request.GET or
                'data_final' not in self.request.GET):
            return HttpResponseRedirect(reverse(
                'sapl.materia:impressos_ficha_pesquisa'))

        context = super(FichaSelecionaView, self).get_context_data(
            **kwargs)

        tipo = self.request.GET['tipo']
        data_inicial = datetime.strptime(
            self.request.GET['data_inicial'], "%d/%m/%Y").date()
        data_final = datetime.strptime(
            self.request.GET['data_final'], "%d/%m/%Y").date()

        materia_list = MateriaLegislativa.objects.filter(
            tipo=tipo,
            data_apresentacao__range=(data_inicial, data_final))
        context['quantidade'] = len(materia_list)
        materia_list = materia_list[:100]

        context['form'].fields['materia'].choices = [
            (m.id, str(m)) for m in materia_list]

        username = self.request.user.username

        if context['quantidade'] > 100:
            self.logger.info('user=' + username + '. Sua pesquisa (tipo={}, data_inicial={}, data_final={}) retornou mais do que '
                             '100 impressos. Por questões de '
                             'performance, foram retornados '
                             'apenas os 100 primeiros. Caso '
                             'queira outros, tente fazer uma '
                             'pesquisa mais específica'.format(tipo, data_inicial, data_final))
            messages.info(self.request, _('Sua pesquisa retornou mais do que '
                                          '100 impressos. Por questões de '
                                          'performance, foram retornados '
                                          'apenas os 100 primeiros. Caso '
                                          'queira outros, tente fazer uma '
                                          'pesquisa mais específica'))

        return context

    def form_valid(self, form):
        context = {}
        username = self.request.user.username

        try:
            self.logger.debug(
                "user=" + username + ". Tentando obter objeto MateriaLegislativa com id={}".format(form.data['materia']))
            materia = MateriaLegislativa.objects.get(
                id=form.data['materia'])
        except ObjectDoesNotExist:
            self.logger.error(
                "user=" + username + ". Esta MáteriaLegislativa não existe (id={}).".format(form.data['materia']))
            mensagem = _('Esta Máteria não existe!')
            self.messages.add_message(self.request, messages.INFO, mensagem)

            return self.render_to_response(context)
        if len(materia.ementa) > 301:
            materia.ementa = materia.ementa[0:300] + '[...]'
        context['materia'] = materia
        context['despachos'] = materia.despachoinicial_set.all().values_list(
            'comissao__nome', flat=True)

        return gerar_pdf_impressos(self.request, context,
                                   'materia/impressos/ficha_pdf.html')


class ExcluirTramitacaoEmLoteView(PermissionRequiredMixin, FormView):

    template_name = 'materia/em_lote/excluir_tramitacao.html'
    permission_required = ('materia.add_tramitacao',)
    form_class = ExcluirTramitacaoEmLote
    form_valid_message = _('Tramitações excluídas com sucesso!')

    def get_success_url(self):
        return reverse('sapl.materia:excluir_tramitacao_em_lote')

    def form_valid(self, form):

        tramitacao_set = Tramitacao.objects.filter(
            data_tramitacao=form.cleaned_data['data_tramitacao'],
            unidade_tramitacao_local=form.cleaned_data[
                'unidade_tramitacao_local'],
            unidade_tramitacao_destino=form.cleaned_data[
                'unidade_tramitacao_destino'],
            status=form.cleaned_data['status'])
        for tramitacao in tramitacao_set:
            materia = tramitacao.materia
            if tramitacao == materia.tramitacao_set.first():
                tramitacao.delete()

        return redirect(self.get_success_url())


class MateriaPesquisaSimplesView(PermissionRequiredMixin, FormView):
    form_class = MateriaPesquisaSimplesForm
    template_name = 'materia/impressos/impressos_form.html'
    permission_required = ('materia.can_access_impressos',)

    def form_valid(self, form):
        template_materia = 'materia/impressos/materias_pdf.html'

        kwargs = {}
        if form.cleaned_data.get('tipo_materia'):
            kwargs.update({'tipo': form.cleaned_data['tipo_materia']})

        if form.cleaned_data.get('data_inicial'):
            kwargs.update({'data__gte': form.cleaned_data['data_inicial'],
                           'data__lte': form.cleaned_data['data_final']})

        materias = MateriaLegislativa.objects.filter(
            **kwargs).order_by('-numero', 'ano')

        quantidade_materias = materias.count()
        materias = materias[:2000] if quantidade_materias > 2000 else materias

        context = {'quantidade': quantidade_materias,
                   'titulo': form.cleaned_data['titulo'],
                   'materias': materias}

        return gerar_pdf_impressos(self.request, context, template_materia)


class TipoMateriaCrud(CrudAux):
    model = TipoMateriaLegislativa

    class DetailView(CrudAux.DetailView):
        layout_key = 'TipoMateriaLegislativaDetail'

    class DeleteView(CrudAux.DeleteView):

        def delete(self, request, *args, **kwargs):
            d = CrudAux.DeleteView.delete(self, request, *args, **kwargs)
            TipoMateriaLegislativa.objects.reordene()
            return d

    class ListView(CrudAux.ListView):
        paginate_by = None
        layout_key = 'TipoMateriaLegislativaDetail'
        template_name = "materia/tipomaterialegislativa_list.html"

        def hook_sigla(self, obj, default, url):
            return '<a href="{}" pk="{}">{}</a>'.format(
                url, obj.id, obj.sigla), ''

        def get(self, request, *args, **kwargs):
            if TipoMateriaLegislativa.objects.filter(
                    sequencia_regimental=0).exists():
                TipoMateriaLegislativa.objects.reordene()
            return CrudAux.ListView.get(self, request, *args, **kwargs)

    class CreateView(CrudAux.CreateView):

        def form_valid(self, form):
            fv = super().form_valid(form)

            if not TipoMateriaLegislativa.objects.exclude(
                    sequencia_regimental=0).exists():
                TipoMateriaLegislativa.objects.reordene()
            else:
                sr__max = TipoMateriaLegislativa.objects.all().aggregate(
                    Max('sequencia_regimental'))
                self.object.sequencia_regimental = sr__max[
                    'sequencia_regimental__max'] + 1
                self.object.save()

            return fv


class MateriaLegislativaCheckView(ListView):
    model = MateriaLegislativa
    template_name = "materia/materialegislativa_check.html"

    @property
    def title(self):
        return 'Checagem de Registro do Processo Legislativo'

    def get(self, request, *args, **kwargs):

        check = request.GET.get('check', '')
        uncheck = request.GET.get('uncheck', '')
        if request.user.has_perm(
                'materia.can_check_complete') and (check or uncheck):
            try:
                m = MateriaLegislativa.objects.get(pk=check or uncheck)
            except BaseException:
                raise Http404
            else:
                m.checkcheck = True if check else False
                m.em_tramitacao = False
                m.save(update_fields=('checkcheck', 'em_tramitacao' ))
                return redirect('/materia/check')

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()

        qs = qs.filter(checkcheck=False)

        qs = qs.order_by('tipo__sequencia_regimental',
                         '-data_apresentacao', '-numero')

        return qs


class CriarDocumentoAcessorioProtocolo(PermissionRequiredMixin, CreateView):
    template_name = "materia/criar_documentoacessorio_protocolo.html"
    form_class = DocumentoAcessorioProtocoloForm
    permission_required = ('materia.add_documentoacessorio',)

    def get_initial(self):
        protocolo = Protocolo.objects.get(pk=self.kwargs['pk'])
        return self.criar_documento(protocolo)

    def get_success_url(self):
        return reverse('sapl.protocoloadm:protocolo_mostrar',
                       kwargs={'pk': self.kwargs['pk']})

    def criar_documento(self, protocolo):
        #curr_year = timezone.now().year

        # numero_max = DocumentoAcessorio.objects.filter(
        #    tipo=protocolo.tipo_conteudo_protocolado, ano=curr_year
        # ).aggregate(Max('numero'))['numero__max']

        doc = {}
        doc['tipo'] = protocolo.tipo_conteudo_protocolado
        doc['data'] = timezone.now()
        doc['ementa'] = protocolo.assunto_ementa
        doc['autor'] = protocolo.interessado
        doc['protocolo'] = protocolo

        return doc

from re import sub
import ast
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Max, Q, F
from django.http import JsonResponse
from django.http.response import Http404, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls.base import reverse
from django.utils import timezone, formats
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, ListView, TemplateView
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormMixin
from django_filters.views import FilterView

from cmj.mixins import BtnCertMixin, PluginSignMixin, MultiFormatOutputMixin, \
    AudigLogFilterMixin
from sapl.base.models import AppConfig as AppsAppConfig
from sapl.crud.base import (RP_DETAIL, RP_LIST, Crud, CrudAux,
                            MasterDetailCrud,
                            PermissionRequiredForAppCrudMixin, make_pagination)
from sapl.materia.forms import filtra_tramitacao_status
from sapl.materia.models import (Autoria, TipoMateriaLegislativa,
                                 Tramitacao)
from sapl.materia.views import MateriaLegislativaPesquisaView
from sapl.parlamentares.models import (Filiacao, Legislatura, Mandato,
                                       Parlamentar, SessaoLegislativa)
from sapl.sessao.apps import AppConfig
from sapl.sessao.forms import OrdemExpedienteLeituraForm, ExpedienteMateriaForm, OrdemDiaForm
from sapl.sessao.models import RegistroLeitura
from sapl.utils import (show_results_filter_set, remover_acentos, get_client_ip,
                        verifica_afastamento_parlamentar)

from .forms import (AdicionarVariasMateriasFilterSet, ExpedienteForm,
                    JustificativaAusenciaForm, OcorrenciaSessaoForm, ListMateriaForm,
                    MesaForm, OradorExpedienteForm, OradorForm,
                    PautaSessaoFilterSet, PautaComissaoFilterSet,
                    PresencaForm, SessaoPlenariaFilterSet,
                    SessaoPlenariaForm, VotacaoEditForm, VotacaoForm,
                    VotacaoNominalForm, RetiradaPautaForm, OradorOrdemDiaForm)
from .models import (CargoMesa, ExpedienteMateria, ExpedienteSessao, OcorrenciaSessao, IntegranteMesa,
                     MateriaLegislativa, Orador, OradorExpediente, OrdemDia,
                     PresencaOrdemDia, RegistroVotacao, ResumoOrdenacao,
                     SessaoPlenaria, SessaoPlenariaPresenca, TipoExpediente,
                     TipoResultadoVotacao, TipoSessaoPlenaria, VotoParlamentar, TipoRetiradaPauta,
                     RetiradaPauta, TipoJustificativa, JustificativaAusencia, OradorOrdemDia, ORDENACAO_RESUMO)


TipoSessaoCrud = CrudAux.build(TipoSessaoPlenaria, 'tipo_sessao_plenaria')
TipoJustificativaCrud = CrudAux.build(TipoJustificativa, 'tipo_justificativa')
TipoResultadoVotacaoCrud = CrudAux.build(
    TipoResultadoVotacao, 'tipo_resultado_votacao')
TipoRetiradaPautaCrud = CrudAux.build(TipoRetiradaPauta, 'tipo_retirada_pauta')

# constantes
SIMBOLICA = 1
NOMINAL = 2
SECRETA = 3
LEITURA = 4


def reordernar_materias_expediente(request, pk):
    expedientes = ExpedienteMateria.objects.filter(
        sessao_plenaria_id=pk
    ).order_by(
        '-materia__regime_tramitacao__sequencia_regimental',
        'materia__tipo__sequencia_regimental',
        'materia__ano',
        'materia__numero'
    )

    for exp_num, e in enumerate(expedientes, 1):
        e.numero_ordem = exp_num
        e.save()

    return HttpResponseRedirect(
        reverse('sapl.sessao:expedientemateria_list', kwargs={'pk': pk}))


def reordernar_materias_ordem(request, pk):
    ordens = OrdemDia.objects.filter(
        sessao_plenaria_id=pk,
        parent__isnull=True
    ).order_by(
        '-materia__regime_tramitacao__sequencia_regimental',
        'materia__tipo__sequencia_regimental',
        'materia__ano',
        'materia__numero'
    )
    for ordem_num, o in enumerate(ordens, 1):
        o.numero_ordem = ordem_num
        o.save()

    return HttpResponseRedirect(
        reverse('sapl.sessao:ordemdia_list', kwargs={'pk': pk}))


def renumerar_materias_ordem(request, pk):
    ordens = OrdemDia.objects.filter(
        sessao_plenaria_id=pk,
        parent__isnull=True
    )

    for ordem_num, o in enumerate(ordens, 1):
        o.numero_ordem = ordem_num
        o.save()

    return HttpResponseRedirect(
        reverse('sapl.sessao:ordemdia_list', kwargs={'pk': pk}))


def renumerar_materias_expediente(request, pk):
    expedientes = ExpedienteMateria.objects.filter(sessao_plenaria_id=pk)

    for exp_num, e in enumerate(expedientes, 1):
        e.numero_ordem = exp_num
        e.save()

    return HttpResponseRedirect(
        reverse('sapl.sessao:expedientemateria_list', kwargs={'pk': pk}))


def verifica_presenca(request, model, spk, is_leitura=False):
    logger = logging.getLogger(__name__)
    if not model.objects.filter(sessao_plenaria_id=spk).exists():
        username = request.user.username
        if is_leitura:
            text = 'Leitura não pode ser feita sem presenças'
        else:
            text = 'Votação não pode ser aberta sem presenças'

        logger.error("user={}. {} (sessao_plenaria_id={}).".format(
            username, text, spk))
        msg = _(text)
        messages.add_message(request, messages.ERROR, msg)
        return False
    return True


def verifica_votacoes_abertas(request):
    votacoes_abertas = SessaoPlenaria.objects.filter(
        Q(ordemdia__votacao_aberta=True) |
        Q(expedientemateria__votacao_aberta=True)).distinct()

    logger = logging.getLogger(__name__)

    if votacoes_abertas:
        msg_abertas = []
        for v in votacoes_abertas:
            msg_abertas.append('''<li><a href="%s">%s</a></li>''' % (
                reverse('sapl.sessao:sessaoplenaria_detail',
                        kwargs={'pk': v.id}),
                v.__str__()))
        username = request.user.username
        logger.info('user=' + username + '. Já existem votações ou leituras abertas nas seguintes Sessões: ' +
                    ', '.join(msg_abertas) + '. Para abrir '
                    'outra, termine ou feche as votações abertas.')
        msg = _('Já existem votações ou leituras abertas nas seguintes Sessões: ' +
                ', '.join(msg_abertas) + '. Para abrir '
                'outra, termine ou feche as votações ou leituras abertas.')
        messages.add_message(request, messages.INFO, msg)

        return False

    return True


def verifica_sessao_iniciada(request, spk, is_leitura=False):
    logger = logging.getLogger(__name__)
    sessao = SessaoPlenaria.objects.get(id=spk)

    if not sessao.iniciada or sessao.finalizada:
        username = request.user.username
        aux_text = 'leitura' if is_leitura else 'votação'
        logger.info('user=' + username + '. Não é possível abrir matérias para {}. '
                    'Esta SessaoPlenaria (id={}) não foi iniciada ou está finalizada.'.format(aux_text, spk))
        msg = _('Não é possível abrir matérias para {}. '
                'Esta Sessão Plenária não foi iniciada ou está finalizada.'
                ' Vá em "Abertura"->"Dados Básicos" e altere os valores dos campos necessários.'.format(aux_text))
        messages.add_message(request, messages.INFO, msg)
        return False

    return True


@permission_required('sessao.change_expedientemateria',
                     'sessao.change_ordemdia')
def abrir_votacao(request, pk, spk):
    model = None

    if 'tipo_materia' in request.GET:
        if request.GET['tipo_materia'] == 'ordem':
            model = OrdemDia
            presenca_model = PresencaOrdemDia
            redirect_url = 'ordemdia_list'
        elif request.GET['tipo_materia'] == 'expediente':
            model = ExpedienteMateria
            presenca_model = SessaoPlenariaPresenca
            redirect_url = 'expedientemateria_list'

    if not model:
        raise Http404()

    materia_votacao = model.objects.get(id=pk)
    is_leitura = materia_votacao.tipo_votacao == 4
    if (verifica_presenca(request, presenca_model, spk, is_leitura) and
        verifica_votacoes_abertas(request) and
            verifica_sessao_iniciada(request, spk, is_leitura)):
        materia_votacao.votacao_aberta = True

        if 'pedido_prazo' in request.GET:
            materia_votacao.votacao_aberta_pedido_prazo = True

        sessao = SessaoPlenaria.objects.get(id=spk)
        sessao.painel_aberto = True
        sessao.save()
        materia_votacao.save()

    query_params = "#id{}".format(materia_votacao.materia.id)
    success_url = reverse('sapl.sessao:' + redirect_url, kwargs={'pk': spk})
    success_url += query_params

    return HttpResponseRedirect(success_url)


def item_sessao_url(obj, sufixo=''):
    url = ''
    exp = 'exp' if obj._meta.model == ExpedienteMateria else ''
    kwargs = {
        'pk': obj.sessao_plenaria_id,
        'oid': obj.pk,
        'mid': obj.materia_id
    }
    if obj.tipo_votacao == SIMBOLICA:
        url = reverse(
            f'sapl.sessao:votacaosimbolica{exp}{sufixo}', kwargs=kwargs)
    elif obj.tipo_votacao == NOMINAL:
        url = reverse(
            f'sapl.sessao:votacaonominal{exp}{sufixo}', kwargs=kwargs)
    elif obj.tipo_votacao == SECRETA:
        url = reverse(
            f'sapl.sessao:votacaosecreta{exp}{sufixo}', kwargs=kwargs)
    elif obj.tipo_votacao == LEITURA:
        url = reverse(
            f'sapl.sessao:leitura{exp if exp else "od"}', kwargs=kwargs)
    return url


def customize_link_materia(context, pk, has_permission, user=None):
    rows = context['rows']

    rows_dict = {}

    for i, row in enumerate(context['rows']):
        obj = context['object_list'][i]
        row.append(obj)
        if obj.parent:
            continue

        rows_dict[obj.id] = {
            'item': row,
            'childs': []
        }

    for i, row in enumerate(context['rows']):
        obj = context['object_list'][i]
        if not obj.parent:
            continue
        rows_dict[obj.parent.id]['childs'].append(row)

    rows_new = []

    for i, row in enumerate(context['rows']):
        obj = context['object_list'][i]
        if obj.id not in rows_dict:
            continue
        rows_new.append(row)
        for c in rows_dict[obj.id]['childs']:
            items_row = list(c[0])
            items_row[0] = rows_dict[obj.id]['item'][0][0] + '.' + items_row[0]
            c[0] = items_row
            rows_new.append(c)

        #rows_new += rows_dict[obj.id]['childs']
    context['rows'] = rows_new

    for i, row in enumerate(context['rows']):
        obj = row[-1]
        del row[-1]
        materia = obj.materia

        url_materia = reverse('sapl.materia:materialegislativa_detail',
                              kwargs={'pk': materia.id})
        numeracao = materia.numeracao_set.first()
        autoria = materia.autoria_set.all()
        autores = ', '.join(map(lambda x: x.autor.nome, autoria))
        num_protocolo = materia.numero_protocolo

        data_inicio_sessao = SessaoPlenaria.objects.get(id=pk).data_inicio

        tramitacao = Tramitacao.objects.filter(
            materia=materia,
            turno__isnull=False,
            data_tramitacao__lte=data_inicio_sessao
        ).exclude(
            turno__exact=''
        ).select_related(
            'materia',
            'status',
            'materia__tipo'
        ).order_by(
            '-data_tramitacao'
        ).first()

        if user and user.is_anonymous:
            row[2] = (materia.ementa, None)

        turno = '  '
        if tramitacao:
            for t in Tramitacao.TURNO_CHOICES:
                if t[0] == tramitacao.turno:
                    turno = t[1]
                    break

        #                   <b>Processo:</b> %s </br>

        action_signs = ''
        if user.is_superuser:
            url_prot_mostrar = reverse('sapl.protocoloadm:protocolo_homologar',
                    kwargs={'pk': obj.materia.protocolo_gr.first().pk})

            url_sessao_detail = reverse('sapl.sessao:sessaoplenaria_detail',
                    kwargs={'pk': pk}) + f'?add_selo_votacao&materia_unica={obj.materia.id}'
            action_signs = f'''
                <div class="d-none actions-signs">
                    <div class="preview"></div>
                    <div class="d-flex actions flex-column justify-content-center">
                        <a class="btn btn-link" target="blank" href="{url_prot_mostrar}?recreate&compression=True">SPcc</a>
                        <a class="btn btn-link" target="blank" href="{url_prot_mostrar}?recreate&compression=False">SPsc</a>

                        <a class="btn btn-link" target="blank" href="{url_sessao_detail}&compression=True">SVcc</a>
                        <a class="btn btn-link" target="blank" href="{url_sessao_detail}&compression=False">SVsc</a>
                    </div>
                </div>'''

        title_materia = f'''
        <div class="d-flex ordemdia_materia justify-content-between align-items-center" id="mat_od_%s">
            <div>
                <a name="id{obj.materia.id}"
                    data-pk="{obj.materia.id}"
                    class="link_materia_ordemdia"
                    href={url_materia}>
                    {row[1][0]}
                </a> </br>
                <b>Autoria:</b> {autores if autores else ''} </br>
                <b>Protocolo:</b> {num_protocolo if num_protocolo else ''} </br>
                <b>Turno:</b> {turno} </br>
            </div>
            {action_signs}
        </div>'''


        if isinstance(obj, OrdemDia) and materia.anexadas.exists() and user and user.has_perm('sessao.add_ordemdia'):
            title_materia += '''
                <a href="%s?add_anexadas"><small>Adicionar emendas nesta sessão</small></a>
            ''' % (
                row[0][1],

            )

        # Na linha abaixo, o segundo argumento é None para não colocar
        # url em toda a string de title_materia
        context['rows'][i][1] = (title_materia, None)

        is_expediente = obj._meta.model == ExpedienteMateria

        prazo_registrado = obj.registrovotacao_set.filter(
            materia=obj.materia,
            tipo_resultado_votacao__natureza='P'
        )

        exist_resultado = obj.registrovotacao_set.filter(
            materia=obj.materia,
        ).exclude(
            tipo_resultado_votacao__natureza='P'
        ).exists()

        exist_retirada = obj.retiradapauta_set.filter(
            materia=obj.materia).exists()

        exist_leitura = obj.registroleitura_set.filter(
            materia=obj.materia).exists()

        if (obj.tipo_votacao != 4 and not exist_resultado and not exist_retirada) or\
                (obj.tipo_votacao == 4 and not exist_leitura):
            if obj.votacao_aberta:
                url = item_sessao_url(obj, '')
                if has_permission:
                    if obj.tipo_votacao != LEITURA:
                        btn_registrar = '''
                                        <form action="%s">
                                        <input type="submit" class="btn btn-primary"
                                        value="Registrar Votação" />

                                    </form>''' % (
                            url)
                    else:
                        btn_registrar = '''
                                        <form action="%s">
                                        <input type="submit" class="btn btn-primary"
                                        value="Registrar Leitura" />

                                    </form>''' % (
                            url)

                    resultado = btn_registrar
                else:
                    resultado = '''Não há resultado'''
            else:
                url = reverse('sapl.sessao:abrir_votacao', kwargs={
                    'pk': obj.pk,
                    'spk': obj.sessao_plenaria_id
                }) + f'?tipo_materia={"expediente" if is_expediente else "ordem"}'

                if has_permission:
                    if obj.tipo_votacao == LEITURA:
                        btns_abrir = f'''
                                Matéria não lida<br />
                                <a href="{url}"
                                class="btn btn-primary"
                                role="button">Abrir para Leitura</a>'''
                    else:
                        pre_votacao = 'Matéria não votada'

                        if prazo_registrado.exists():
                            url_pre_votacao = item_sessao_url(
                                obj, sufixo='edit')
                            pre_votacao = '<a href="%s">%s</a>' % (
                                url_pre_votacao,
                                prazo_registrado.last().tipo_resultado_votacao)
                        else:
                            pre_votacao = 'Matéria não votada'
                            pre_votacao = f'''
                                            <a href="{url}&pedido_prazo"
                                            class="btn btn-sm btn-warning w-100"
                                            role="button">Abrir Votação de<br>Pedido de Adiamento</a>
                                            <br />
                                            {pre_votacao}
                                            '''

                        btns_abrir = f'''{pre_votacao}
                                           <br />
                                            <a href="{url}"
                                            class="btn btn-primary w-100"
                                            role="button">Abrir Votação</a>'''
                    resultado = btns_abrir
                else:

                    if prazo_registrado.exists():
                        resultado = f'{prazo_registrado.last().tipo_resultado_votacao}'
                    else:
                        resultado = '''Não há resultado'''

        elif exist_retirada:
            retirada = obj.retiradapauta_set.filter(
                materia_id=obj.materia_id).last()
            retirada_descricao = retirada.tipo_de_retirada.descricao
            retirada_observacao = retirada.observacao
            url = reverse('sapl.sessao:retiradapauta_detail',
                          kwargs={'pk': retirada.id})
            resultado = ('<a href="%s">%s<br/>%s</a>' %
                         (url,
                          retirada_descricao,
                          retirada_observacao))

        else:
            if obj.tipo_votacao == LEITURA:
                resultado = obj.registroleitura_set.filter(
                    materia_id=obj.materia_id).last()
                resultado_descricao = "Matéria lida"
                resultado_observacao = resultado.observacao
            else:
                resultado = obj.registrovotacao_set.filter(
                    materia_id=obj.materia_id).last()
                resultado_descricao = resultado.tipo_resultado_votacao.nome

                resultado_observacao = '{}{}{}'.format(
                    resultado.observacao,
                    '<br>Subscrições:' if resultado.subscricoes.exists() else '',
                    '<br><ul>{}</ul>'.format(
                        ''.join(
                            [
                                '<li>{}</li>'.format(p)
                                for p in resultado.subscricoes.all()
                            ]
                        )

                    )

                )

            if has_permission:
                url = item_sessao_url(obj, sufixo='edit')
                resultado = ('<a href="%s">%s<br/>%s</a>' %
                             (url,
                              resultado_descricao,
                              resultado_observacao))
            else:
                if obj.tipo_votacao == NOMINAL:
                    if is_expediente:
                        url = reverse(
                            'sapl.sessao:votacao_nominal_transparencia',
                            kwargs={
                                'pk': obj.sessao_plenaria_id,
                                'oid': obj.pk,
                                'mid': obj.materia_id}) + \
                            '?&materia=expediente'
                    else:
                        url = reverse(
                            'sapl.sessao:votacao_nominal_transparencia',
                            kwargs={
                                'pk': obj.sessao_plenaria_id,
                                'oid': obj.pk,
                                'mid': obj.materia_id}) + \
                            '?&materia=ordem'

                    resultado = ('<a href="%s">%s<br/>%s</a>' %
                                 (url,
                                  resultado_descricao,
                                  resultado_observacao))

                elif obj.tipo_votacao == SIMBOLICA:
                    if is_expediente:
                        url = reverse(
                            'sapl.sessao:votacao_simbolica_transparencia',
                            kwargs={
                                'pk': obj.sessao_plenaria_id,
                                'oid': obj.pk,
                                'mid': obj.materia_id}) + \
                            '?&materia=expediente'
                    else:
                        url = reverse(
                            'sapl.sessao:votacao_simbolica_transparencia',
                            kwargs={
                                'pk': obj.sessao_plenaria_id,
                                'oid': obj.pk,
                                'mid': obj.materia_id}) + \
                            '?&materia=ordem'

                    resultado = ('<a href="%s">%s<br/>%s</a>' %
                                 (url,
                                  resultado_descricao,
                                  resultado_observacao))
                else:
                    resultado = ('%s<br/>%s' %
                                 (resultado_descricao,
                                  resultado_observacao))
        context['rows'][i][3] = (resultado, None)

    return context


def get_presencas_generic(model, sessao, legislatura):
    presentes = [p.parlamentar for p in model.objects.filter(
        sessao_plenaria=sessao)]

    parlamentares_mandato = Mandato.objects.filter(
        legislatura=legislatura,
        data_inicio_mandato__lte=sessao.data_inicio,
        data_fim_mandato__gte=sessao.data_inicio
    ).distinct().order_by(
        'parlamentar__nome_parlamentar')

    for m in parlamentares_mandato:
        if m.parlamentar in presentes:
            yield (m.parlamentar, True)
        else:
            yield (m.parlamentar, False)


def get_presencas_generic__old(model, sessao, legislatura):
    presencas = model.objects.filter(
        sessao_plenaria=sessao)

    presentes = [p.parlamentar for p in presencas]

    presentes = sorted(
        presentes, key=lambda x: remover_acentos(x.nome_parlamentar))

    mandato = Mandato.objects.filter(
        legislatura=legislatura).order_by('parlamentar__nome_parlamentar')

    for m in mandato:
        parlamentar = m.parlamentar
        p_afastado = verifica_afastamento_parlamentar(
            parlamentar, sessao.data_inicio, sessao.data_fim)
        if parlamentar in presentes:
            yield (parlamentar, True, p_afastado)
        else:
            yield (parlamentar, False, p_afastado)


class TipoExpedienteCrud(CrudAux):
    model = TipoExpediente

    class DeleteView(CrudAux.DeleteView):

        def delete(self, *args, **kwargs):
            self.object = self.get_object()

            # Se todas as referências a este tipo forem de conteúdo vazio,
            # significa que pode ser apagado
            if self.object.expedientesessao_set.filter(conteudo='').count() == \
                    self.object.expedientesessao_set.all().count():
                self.object.expedientesessao_set.all().delete()

            return CrudAux.DeleteView.delete(self, *args, **kwargs)


class MateriaOrdemDiaCrud(MasterDetailCrud):
    model = OrdemDia
    parent_field = 'sessao_plenaria'
    help_topic = 'sessao_plenaria_materias_ordem_dia'
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['numero_ordem', 'materia',
                            ('materia__ementa', '', 'observacao', 'url_video'),
                            'resultado']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = OrdemDiaForm

        def get_initial(self):
            self.initial['data_ordem'] = SessaoPlenaria.objects.get(
                pk=self.kwargs['pk']).data_inicio.strftime('%d/%m/%Y')
            max_numero_ordem = OrdemDia.objects.filter(
                sessao_plenaria=self.kwargs['pk']).aggregate(
                    Max('numero_ordem'))['numero_ordem__max']
            self.initial['numero_ordem'] = (
                max_numero_ordem if max_numero_ordem else 0) + 1
            return self.initial

        def get_success_url(self):
            return reverse('sapl.sessao:ordemdia_list',
                           kwargs={'pk': self.kwargs['pk']})

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = OrdemDiaForm

        def get_context_data(self, **kwargs):
            context = MasterDetailCrud.UpdateView.get_context_data(
                self, **kwargs)
            context["tramitacao_salvo"] = self.object.tramitacao.id if self.object.tramitacao is not None else ''
            return context

        def get_initial(self):
            initial = super().get_initial()
            initial['tipo_materia'] = self.object.materia.tipo.id
            initial['numero_materia'] = self.object.materia.numero
            initial['ano_materia'] = self.object.materia.ano
            initial['tramitacao'] = self.object.tramitacao.id if self.object.tramitacao is not None else ''

            return initial

    class DetailView(MasterDetailCrud.DetailView):
        layout_key = 'OrdemDiaDetail'

        def hook_observacao(self, *args, **kwargs):
            if self.request.user.is_anonymous:
                return '', ''
            else:
                return _('Observação'), args[0].observacao.replace('\n', '<br>')

        def get(self, request, *args, **kwargs):

            add_anexadas = request.GET.get('add_anexadas', None)
            if add_anexadas is None or not request.user.has_perm('sessao.add_ordemdia'):
                return MasterDetailCrud.DetailView.get(self, request, *args, **kwargs)

            obj = self.get_object()

            materias_ja_adicionadas = set(
                obj.childs.values_list('materia', flat=True))

            # OrdemDia.objects.filter(
            #    sessao_plenaria=obj.sessao_plenaria,
            #    id__gt=13288
            # ).delete()
            # OrdemDia.objects.filter(
            #    materia__in=list(materias_ja_adicionadas)).delete()

            materias = set()
            for m in obj.materia.anexadas.materias_anexadas_ordem_crescente():
                if not m.registrovotacao_set.filter(
                        ordem__sessao_plenaria__tipo__gera_selo_votacao=True,
                        tipo_resultado_votacao__natureza='A').exists():
                    materias.add(m.id)

            materias_a_adicionar = materias - materias_ja_adicionadas

            # OrdemDia.objects.filter(
            #    sessao_plenaria=obj.sessao_plenaria,
            #    numero_ordem__gt=obj.numero_ordem
            # ).update(numero_ordem=F('numero_ordem') + len(materias_a_adicionar))

            for m in materias_a_adicionar:
                oc = OrdemDia()
                oc.parent = obj
                oc.sessao_plenaria = obj.sessao_plenaria
                oc.materia_id = m
                oc.numero_ordem = 1
                oc.data_ordem = obj.data_ordem
                oc.observacao = ''
                oc.resultado = ''
                oc.tipo_votacao = obj.tipo_votacao
                oc.votacao_aberta = False
                oc.votacao_aberta_pedido_prazo = False
                oc.registro_aberto = False
                oc.save()

            if materias_ja_adicionadas or materias_a_adicionar:
                sub_ordens = obj.childs.order_by(
                    'materia__tipo__sequencia_regimental',
                    'materia__ano',
                    'materia__numero'
                )
                numero_ordem = 1
                for o in sub_ordens:
                    o.numero_ordem = numero_ordem
                    o.save()
                    numero_ordem += 1

            return HttpResponseRedirect(
                '{}#id{}'.format(
                    reverse('sapl.sessao:ordemdia_list', kwargs={
                            'pk': obj.sessao_plenaria.id}),
                    obj.materia.id
                )
            )

    class ListView(MasterDetailCrud.ListView):
        paginate_by = None
        ordering = ['numero_ordem', 'materia', 'resultado']

        def get_queryset(self):
            qs = MasterDetailCrud.ListView.get_queryset(self)

            if not self.request.user.has_perm('sessao.add_ordemdia'):
                qs = qs.filter(parent__isnull=True)
            return qs

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            has_permition = self.request.user.has_module_perms(AppConfig.label)
            return customize_link_materia(context, self.kwargs['pk'], has_permition, self.request.user)

        def hook_header_materiaementa(self, *args, **kwargs):
            return _('Ementa')

        def hook_header_url_video(self, *args, **kwargs):
            return ''

        def hook_header_observacao(self, *args, **kwargs):
            if self.request.user.is_anonymous:
                return ''
            else:
                return _('Observação')


def recuperar_materia(request):
    tipo = TipoMateriaLegislativa.objects.get(pk=request.GET['tipo_materia'])
    numero = request.GET['numero_materia']
    ano = request.GET['ano_materia']

    try:
        materia = MateriaLegislativa.objects.filter(tipo=tipo,
                                                 ano=ano,
                                                 numero=numero).first()
        if not materia:
            raise ObjectDoesNotExist
        response = JsonResponse({'ementa': materia.ementa,
                                 'id': materia.id,
                                 'indexacao': materia.indexacao})
    except ObjectDoesNotExist:
        response = JsonResponse({'ementa': '', 'id': 0, 'indexacao': ''})

    return response


def recuperar_tramitacao(request):
    tipo = request.GET['tipo_materia']
    numero = request.GET['numero_materia']
    ano = request.GET['ano_materia']

    try:
        materia = MateriaLegislativa.objects.filter(tipo=tipo,
                                                 ano=ano,
                                                 numero=numero).first()
        if not materia:
            raise ObjectDoesNotExist
        
        tramitacao = {}
        for obj in materia.tramitacao_set.all():
            tramitacao[obj.id] = {
                'status': obj.status.descricao,
                'texto': obj.texto,
                'data_tramitacao': obj.data_tramitacao.strftime('%d/%m/%Y'),
                'unidade_tramitacao_local': str(obj.unidade_tramitacao_local),
                'unidade_tramitacao_destino': str(obj.unidade_tramitacao_destino)

            }

        response = JsonResponse(tramitacao)
    except ObjectDoesNotExist:
        response = JsonResponse({'id': 0})

    return response


class ExpedienteMateriaCrud(MasterDetailCrud):
    model = ExpedienteMateria
    parent_field = 'sessao_plenaria'
    help_topic = 'sessao_plenaria_materia_expediente'
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['numero_ordem', 'materia',
                            ('materia__ementa', '', 'observacao', 'url_video'),
                            'resultado']

    class ListView(MasterDetailCrud.ListView):
        paginate_by = None
        ordering = ['numero_ordem', 'materia', 'resultado']

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            has_permition = self.request.user.has_module_perms(AppConfig.label)
            return customize_link_materia(context, self.kwargs['pk'], has_permition, user=self.request.user)

        def hook_header_materiaementa(self, *args, **kwargs):
            return _('Ementa')

        def hook_header_url_video(self, *args, **kwargs):
            return ''

        def hook_header_observacao(self, *args, **kwargs):
            if self.request.user.is_anonymous:
                return ''
            else:
                return _('Observação')

    class CreateView(MasterDetailCrud.CreateView):
        form_class = ExpedienteMateriaForm

        def get_initial(self):
            initial = super().get_initial()
            initial['data_ordem'] = SessaoPlenaria.objects.get(
                pk=self.kwargs['pk']).data_inicio.strftime('%d/%m/%Y')
            max_numero_ordem = ExpedienteMateria.objects.filter(
                sessao_plenaria=self.kwargs['pk']).aggregate(
                    Max('numero_ordem'))['numero_ordem__max']
            initial['numero_ordem'] = (
                max_numero_ordem if max_numero_ordem else 0) + 1
            return initial

        def get_success_url(self):
            return reverse('sapl.sessao:expedientemateria_list',
                           kwargs={'pk': self.kwargs['pk']})

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = ExpedienteMateriaForm

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context["tramitacao_salvo"] = self.object.tramitacao.id if self.object.tramitacao is not None else ''
            return context

        def get_initial(self):
            initial = super().get_initial()
            initial['tipo_materia'] = self.object.materia.tipo.id
            initial['numero_materia'] = self.object.materia.numero
            initial['ano_materia'] = self.object.materia.ano
            initial['tramitacao_select'] = None if not self.object.tramitacao else self.object.tramitacao.id

            return initial

    class DetailView(MasterDetailCrud.DetailView):

        layout_key = 'ExpedienteMateriaDetail'

        def hook_observacao(self, *args, **kwargs):
            if self.request.user.is_anonymous:
                return '', ''
            else:
                return _('Observação'), args[0].observacao.replace('\n', '<br>')


# Orador das Explicações Pessoais
class OradorCrud(MasterDetailCrud):
    model = Orador
    parent_field = 'sessao_plenaria'
    help_topic = 'sessao_plenaria_oradores'
    public = [RP_LIST, RP_DETAIL]

    class ListView(MasterDetailCrud.ListView):
        ordering = ['numero_ordem', 'parlamentar']

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            sessao_pk = context['root_pk']
            sessao = SessaoPlenaria.objects.get(id=sessao_pk)
            tipo_sessao = sessao.tipo
            if tipo_sessao.nome == "Solene":
                context.update(
                    {'subnav_template_name': 'sessao/subnav-solene.yaml'})
            return context

    class CreateView(MasterDetailCrud.CreateView):

        form_class = OradorForm

        def get_initial(self):
            return {'id_sessao': self.kwargs['pk']}

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            sessao_pk = context['root_pk']
            sessao = SessaoPlenaria.objects.get(id=sessao_pk)
            tipo_sessao = sessao.tipo
            if tipo_sessao.nome == "Solene":
                context.update(
                    {'subnav_template_name': 'sessao/subnav-solene.yaml'})
            return context

        def get_success_url(self):
            return reverse('sapl.sessao:orador_list',
                           kwargs={'pk': self.kwargs['pk']})

    class DetailView(MasterDetailCrud.DetailView):

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            sessao_pk = context['root_pk']
            sessao = SessaoPlenaria.objects.get(id=sessao_pk)
            tipo_sessao = sessao.tipo
            if tipo_sessao.nome == "Solene":
                context.update(
                    {'subnav_template_name': 'sessao/subnav-solene.yaml'})
            return context

    class UpdateView(MasterDetailCrud.UpdateView):

        form_class = OradorForm

        def get_initial(self):
            initial = super().get_initial()
            initial.update({'id_sessao': self.object.sessao_plenaria.id})
            initial.update({'numero': self.object.numero_ordem})
            return initial

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            sessao_pk = context['root_pk']
            sessao = SessaoPlenaria.objects.get(id=sessao_pk)
            tipo_sessao = sessao.tipo
            if tipo_sessao.nome == "Solene":
                context.update(
                    {'subnav_template_name': 'sessao/subnav-solene.yaml'})
            return context

    class DeleteView(MasterDetailCrud.DeleteView):

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            sessao_pk = context['root_pk']
            sessao = SessaoPlenaria.objects.get(id=sessao_pk)
            tipo_sessao = sessao.tipo
            if tipo_sessao.nome == "Solene":
                context.update(
                    {'subnav_template_name': 'sessao/subnav-solene.yaml'})
            return context


class OradorExpedienteCrud(OradorCrud):
    model = OradorExpediente

    class CreateView(MasterDetailCrud.CreateView):

        form_class = OradorExpedienteForm

        def get_initial(self):
            return {'id_sessao': self.kwargs['pk']}

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            pk = context['root_pk']
            sessao = SessaoPlenaria.objects.get(id=pk)
            tipo_sessao = sessao.tipo
            if tipo_sessao.nome == "Solene":
                context.update(
                    {'subnav_template_name': 'sessao/subnav-solene.yaml'})
            return context

        def get_success_url(self):
            return reverse('sapl.sessao:oradorexpediente_list',
                           kwargs={'pk': self.kwargs['pk']})

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = OradorExpedienteForm

        def get_initial(self):
            return {'id_sessao': self.object.sessao_plenaria.id,
                    'numero': self.object.numero_ordem}

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            pk = context['root_pk']
            sessao = SessaoPlenaria.objects.get(id=pk)
            tipo_sessao = sessao.tipo
            if tipo_sessao.nome == "Solene":
                context.update(
                    {'subnav_template_name': 'sessao/subnav-solene.yaml'})
            return context

    class ListView(MasterDetailCrud.ListView):

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            pk = context['root_pk']
            sessao = SessaoPlenaria.objects.get(id=pk)
            tipo_sessao = sessao.tipo
            if tipo_sessao.nome == "Solene":
                context.update(
                    {'subnav_template_name': 'sessao/subnav-solene.yaml'})
            return context

    class DetailView(MasterDetailCrud.DetailView):

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            pk = context['root_pk']
            sessao = SessaoPlenaria.objects.get(id=pk)
            tipo_sessao = sessao.tipo
            if tipo_sessao.nome == "Solene":
                context.update(
                    {'subnav_template_name': 'sessao/subnav-solene.yaml'})
            return context

    class DeleteView(MasterDetailCrud.DeleteView):

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            sessao_pk = context['root_pk']
            sessao = SessaoPlenaria.objects.get(id=sessao_pk)
            tipo_sessao = sessao.tipo
            if tipo_sessao.nome == "Solene":
                context.update(
                    {'subnav_template_name': 'sessao/subnav-solene.yaml'})
            return context


class OradorOrdemDiaCrud(OradorCrud):
    model = OradorOrdemDia

    class CreateView(MasterDetailCrud.CreateView):
        form_class = OradorOrdemDiaForm

        def get_initial(self):
            return {'id_sessao': self.kwargs['pk']}

        def get_success_url(self):
            return reverse('sapl.sessao:oradorordemdia_list',
                           kwargs={'pk': self.kwargs['pk']})

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = OradorOrdemDiaForm

        def get_initial(self):
            initial = super().get_initial()

            initial.update({'id_sessao': self.object.sessao_plenaria.id})
            initial.update({'numero': self.object.numero_ordem})

            return initial


def recuperar_numero_sessao_view(request):
    try:
        tipo = TipoSessaoPlenaria.objects.get(pk=request.GET.get('tipo', '0'))
        sl = request.GET.get('sessao_legislativa', '0')
        l = request.GET.get('legislatura', '0')
        data = request.GET.get('data_inicio', timezone.now())

        if isinstance(data, str):
            if data:
                data = timezone.datetime.strptime(data, '%d/%m/%Y').date()
            else:
                data = timezone.now().date()

        sessao = SessaoPlenaria.objects.filter(
            tipo.queryset_tipo_numeracao(
                l, sl, data
            )).last()

    except ObjectDoesNotExist:
        numero = 1
    else:
        if sessao:
            numero = sessao.numero + 1
        else:
            numero = 1

    return JsonResponse({'numero': numero})


def sessao_legislativa_legislatura_ajax(request):
    try:
        sessao = SessaoLegislativa.objects.filter(
            legislatura=request.GET['legislatura']).order_by('-data_inicio')
    except ObjectDoesNotExist:
        sessao = SessaoLegislativa.objects.all().order_by('-data_inicio')

    lista_sessoes = [(s.id, s.__str__()) for s in sessao]

    return JsonResponse({'sessao_legislativa': lista_sessoes})


def recuperar_nome_tipo_sessao(request):
    try:
        tipo = TipoSessaoPlenaria.objects.get(pk=request.GET['tipo'])
        tipo_nome = tipo.nome
    except ObjectDoesNotExist:
        tipo_nome = ''

    return JsonResponse({'nome_tipo': tipo_nome})


class SessaoCrud(Crud):
    model = SessaoPlenaria
    help_topic = 'sessao_legislativa'
    public = [RP_DETAIL]

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['data_inicio', 'legislatura', 'sessao_legislativa',
                            'tipo']

        list_url = ''

        @property
        def search_url(self):
            namespace = self.model._meta.app_config.name
            return reverse('%s:%s' % (namespace, 'pesquisar_sessao'))

    class ListView(Crud.ListView, RedirectView):

        def get_redirect_url(self, *args, **kwargs):
            namespace = self.model._meta.app_config.name
            return reverse('%s:%s' % (namespace, 'pesquisar_sessao'))

        def get(self, request, *args, **kwargs):
            return RedirectView.get(self, request, *args, **kwargs)

    class UpdateView(Crud.UpdateView):

        form_class = SessaoPlenariaForm

        @property
        def layout_key(self):
            tipogeral = self.object.tipo.TIPOGERAL_CHOICES.triple(
                self.object.tipo.tipogeral).capitalize()

            return f'SessaoPlenaria{tipogeral}Edit'

        def get_initial(self):
            return {'sessao_legislativa': self.object.sessao_legislativa}

    class CreateView(Crud.CreateView):
        layout_key = 'SessaoPlenariaCreate'
        form_class = SessaoPlenariaForm
        logger = logging.getLogger(__name__)

        @property
        def cancel_url(self):
            return self.search_url

        def get_initial(self):
            legislatura = Legislatura.objects.filter(
                data_inicio__lte=timezone.localdate()
            ).order_by('-data_inicio').first()

            if legislatura:
                return {
                    'legislatura': legislatura,
                    'sessao_legislativa': legislatura.sessaolegislativa_set.filter(
                        legislatura_id=legislatura.id,
                        data_inicio__year=timezone.now().year
                    ).first()
                }
            else:
                msg = _('Cadastre alguma legislatura antes de adicionar ' +
                        'uma sessão plenária!')

                username = self.request.user.username
                self.logger.error('user=' + username + '. Cadastre alguma legislatura antes de adicionar '
                                  'uma sessão plenária!')

                messages.add_message(self.request, messages.ERROR, msg)
                return {}

    class DeleteView(Crud.DeleteView, RedirectView):

        def get_success_url(self):
            namespace = self.model._meta.app_config.name
            return reverse('%s:%s' % (namespace, 'sessaoplenaria_list'))

    class SeloVotacaoMixin(PluginSignMixin):

        def btn_selo_votacao(self):

            btn = []
            if not self.object.selo_votacao_adicionado and \
                    self.object.iniciada and self.object.finalizada and \
                    self.request.user.has_perm('core.add_certidaopublicacao'):

                btn = [
                    reverse('sapl.sessao:sessaoplenaria_detail',
                            kwargs={'pk': self.object.pk}) + '?add_selo_votacao',
                    'btn-success',
                    _('Adicionar Selo de Votação')
                ]
            return btn

        def add_selo_votacao(self):

            item = self.object

            materia_unica = self.request.GET.get('materia_unica', None)

            q = Q(registrovotacao__ordem__sessao_plenaria=item) | Q(
                registrovotacao__expediente__sessao_plenaria=item)

            materias_votadas = MateriaLegislativa.objects.filter(
                q,
                registrovotacao__tipo_resultado_votacao__natureza__in=(
                    'A', 'R'
                ),
                registrovotacao__selo_votacao=False
            ).order_by('id')

            if materia_unica:
                materias_votadas = materias_votadas.filter(id=materia_unica)

            for m in materias_votadas:

                votacoes_da_materia = RegistroVotacao.objects.filter(
                    materia=m, tipo_resultado_votacao__natureza__in=(
                        'A', 'R'
                    ),
                    ordem__sessao_plenaria__tipo__gera_selo_votacao=True
                ).order_by('data_hora')

                titulopre = ''
                titulo = ''
                titulopos = ''

                v_unica = False

                titulopos_mask = 'Sim: {} - Não: {} - Abstenção: {} - {}'

                # titulopos_mask = f'S: {v.numero_votos_sim} N
                # {v.numero_votos_nao}: A:{v.numero_abstencoes} - {'

                if votacoes_da_materia.count() == 1 and \
                        m.tipo.turnos_aprovacao == 1:
                    v = votacoes_da_materia.first()
                    v_unica = True

                count = 1
                for v in votacoes_da_materia:
                    oe = v.ordem or v.expediente
                    sp = oe.sessao_plenaria

                    if sp != item:
                        count += 1
                        continue

                    titulopre = '{}\n{}'.format(
                        sp.str_title(), sp.str_subtitle())
                    titulo = str(v.tipo_resultado_votacao).upper()
                    titulopos = titulopos_mask.format(
                        v.numero_votos_sim,
                        v.numero_votos_nao,
                        v.numero_abstencoes,
                        '{}{}'.format(
                            'Votação Única' if v_unica else count,
                            '' if v_unica else 'ª Votação'
                        )
                    )

                    paths = m.texto_original.path

                    compression = self.request.GET.get('compression', 'False')

                    try:
                        x = m.metadata['selos']['cert_protocolo']['x']
                        y = m.metadata['selos']['cert_protocolo']['y'] + \
                            m.metadata['selos']['cert_protocolo']['h'] + 10
                    except:
                        x = 190
                        y = 120

                    cmd = self.cmd_mask

                    params = {
                        'plugin': self.plugin_path,
                        'comando': 'deliberacao_plenario',
                        'in_file': paths,
                        'certificado': settings.CERT_PRIVATE_KEY_ID,
                        'password': settings.CERT_PRIVATE_KEY_ACCESS,
                        'data_ocorrencia': formats.date_format(
                            timezone.localtime(v.data_hora), 'd/m/Y'
                        ),
                        'hora_ocorrencia': formats.date_format(
                            timezone.localtime(v.data_hora), 'H:i'
                        ),
                        'data_comando': formats.date_format(timezone.localtime(), 'd/m/Y'),
                        'hora_comando': formats.date_format(timezone.localtime(), 'H:i'),
                        'titulopre': titulopre,
                        'titulo': titulo,
                        'titulopos': titulopos,
                        'x': x,
                        'y': (count - 1) * 53 + y,
                        'w': 12,
                        'h': 50,
                        'cor': "0, 76, {}, 255".format(170 - count * 20) if v.tipo_resultado_votacao.natureza == 'A' else "150, 20, 0, 255",
                        'compression': compression,
                        'debug': False #settings.DEBUG
                    }

                    cmd = cmd.format(**params)

                    # if not settings.DEBUG:
                    self.run(cmd)
                    # print(cmd)

                    del params['plugin']
                    del params['in_file']
                    del params['certificado']
                    del params['password']
                    del params['debug']
                    del params['comando']

                    if 'selos' not in m.metadata:
                        m.metadata['selos'] = {}

                    m.metadata['selos'][f'deliberacao_plenario_{count}'] = params
                    m.save()

                    v.selo_votacao = True
                    v.save()

                # print(cmd)
                # return

            # item.save()

    class DetailView(SeloVotacaoMixin, BtnCertMixin, Crud.DetailView):

        @property
        def extras_url(self):
            btns = []
            btns.extend(
                self.btn_certidao(
                    'upload_pauta',
                    btn_title_public=_('Certidão de Publicação da Pauta'),
                    btn_title_admin=_('Gerar Certidão de Publicação da Pauta'),
                ) if self.object.upload_pauta else [])

            btns.extend(
                self.btn_certidao(
                    'upload_ata',
                    btn_title_public=_(
                        'Certidão de Publicação da Ata'),
                    btn_title_admin=_('Gerar Certidão de Publicação da Ata'),
                ) if self.object.upload_ata else [])

            btns.extend([self.btn_selo_votacao()]
                        if self.object.tipo.gera_selo_votacao else [])
            btns = list(filter(lambda x: x, btns))
            return btns

        def get_context_data(self, **kwargs):

            context = super().get_context_data(**kwargs)

            if self.request.user.is_anonymous and self.object.tipo.tipogeral == TipoSessaoPlenaria.TIPOGERAL_AUDIENCIA:
                context.update(
                    {'subnav_template_name': 'sessao/subnav-audiencia.yaml'})

            return context

        def get(self, request, *args, **kwargs):

            response = Crud.DetailView.get(self, request, *args, **kwargs)

            if 'add_selo_votacao' in request.GET and request.user.has_perm('sessao.add_sessaoplenaria'):
                if self.object.tipo.gera_selo_votacao:
                    self.add_selo_votacao()
                    messages.add_message(
                        request, messages.SUCCESS, 'Selos de Votação Adicionados.')
                else:
                    messages.add_message(
                        request, messages.ERROR, 'Este tipo de sessão não gera selo de votação.')

            return response

        def hook_url_video(self, obj, verbose_name, field_display):
            if 'youtu' in obj.url_video:
                return _(f'Vídeo da {obj.tipo.nome}'), field_display
            return verbose_name, field_display

        def hook_url_audio(self, obj, verbose_name, field_display):
            if not obj.url_audio:
                return '', ''
            return verbose_name, field_display

        def hook_upload_pauta(self, obj, verbose_name, field_display):
            if not obj.upload_pauta:
                return '', ''
            return verbose_name, field_display

        def hook_upload_ata(self, obj, verbose_name, field_display):
            if not obj.upload_ata:
                return '', ''
            return verbose_name, sub(r'>.+</a>', '>ata_aprovada.pdf</a>', field_display)

        def hook_upload_anexo(self, obj, verbose_name, field_display):
            if not obj.upload_anexo:
                return '', ''
            return verbose_name, field_display

        def hook_diariooficial(self, obj, verbose_name, field_display):
            d = obj.diariooficial
            if not d:
                return '', ''
            return _('Diário Oficial'), '<a href="{}">{}</a>'.format(
                reverse(
                    '%s:%s_detail' % (
                        d._meta.app_config.name, d._meta.model_name),
                    args=(d.id,)
                ),
                field_display
            )


class SessaoPermissionMixin(PermissionRequiredForAppCrudMixin,
                            FormMixin,
                            DetailView):
    model = SessaoPlenaria
    app_label = AppConfig.label,


class PresencaMixin:

    def get_presencas(self):
        return get_presencas_generic(
            SessaoPlenariaPresenca,
            self.object,
            self.object.legislatura)

    def get_presencas_ordem(self):
        return get_presencas_generic(
            PresencaOrdemDia,
            self.object,
            self.object.legislatura)


class PresencaView(FormMixin, PresencaMixin, DetailView):
    template_name = 'sessao/presenca.html'
    form_class = PresencaForm
    model = SessaoPlenaria
    logger = logging.getLogger(__name__)

    def get_context_data(self, **kwargs):
        context = FormMixin.get_context_data(self, **kwargs)
        context['title'] = '%s <small>(%s)</small>' % (
            _('Presença'), self.object)
        sessao = context['object']
        tipo_sessao = sessao.tipo
        if tipo_sessao.nome == "Solene":
            context.update(
                {'subnav_template_name': 'sessao/subnav-solene.yaml'})
        return context

    @method_decorator(permission_required(
        'sessao.add_sessaoplenariapresenca'))
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        if form.is_valid():
            # Pegar os presentes salvos no banco
            presentes_banco = SessaoPlenariaPresenca.objects.filter(
                sessao_plenaria_id=self.object.id).values_list(
                'parlamentar_id', flat=True).distinct()

            # Id dos parlamentares presentes
            marcados = request.POST.getlist('presenca_ativos') \
                + request.POST.getlist('presenca_inativos')

            # Deletar os que foram desmarcados
            deletar = set(presentes_banco) - set(marcados)
            SessaoPlenariaPresenca.objects.filter(
                parlamentar_id__in=deletar,
                sessao_plenaria_id=self.object.id).delete()

            for p in marcados:
                sessao = SessaoPlenariaPresenca()
                sessao.sessao_plenaria = self.object
                sessao.parlamentar = Parlamentar.objects.get(id=p)
                sessao.save()
                username = request.user.username
                self.logger.info(
                    "user=" + username + ". SessaoPlenariaPresenca salva com sucesso (parlamentar_id={})!".format(p))
            msg = _('Presença em Sessão salva com sucesso!')
            messages.add_message(request, messages.SUCCESS, msg)

            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:presenca', kwargs={'pk': pk})


class PainelView(PermissionRequiredForAppCrudMixin, TemplateView):
    template_name = 'sessao/painel.html'
    app_label = 'painel'
    logger = logging.getLogger(__name__)

    def get(self, request, *args, **kwargs):
        if request.user.is_anonymous:
            self.template_name = 'painel/index.html'

        request.session['discurso'] = 'stop'
        request.session['aparte'] = 'stop'
        request.session['ordem'] = 'stop'
        request.session['consideracoes'] = 'stop'

        return TemplateView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        cronometro_discurso = AppsAppConfig.attr('cronometro_discurso')
        cronometro_aparte = AppsAppConfig.attr('cronometro_aparte')
        cronometro_ordem = AppsAppConfig.attr('cronometro_ordem')
        cronometro_consideracoes = AppsAppConfig.attr(
            'cronometro_consideracoes')

        if (not cronometro_discurso or not cronometro_aparte
                or not cronometro_ordem or not cronometro_consideracoes):

            username = self.request.user.username
            self.logger.error('user=' + username + '. Você precisa primeiro configurar os cronômetros'
                                                   ' nas Configurações da Aplicação')
            msg = _(
                'Você precisa primeiro configurar os cronômetros \
                nas Configurações da Aplicação')
            messages.add_message(self.request, messages.ERROR, msg)

        else:
            cronometro_discurso = cronometro_discurso.seconds
            cronometro_aparte = cronometro_aparte.seconds
            cronometro_ordem = cronometro_ordem.seconds
            cronometro_consideracoes = cronometro_consideracoes.seconds

        sessao_pk = kwargs['pk']
        sessao = SessaoPlenaria.objects.get(pk=sessao_pk)
        context = TemplateView.get_context_data(self, **kwargs)
        context.update({
            'head_title': str(_('Painel Plenário')),
            'sessao_id': sessao_pk,
            'root_pk': sessao_pk,
            'sessaoplenaria': sessao,
            'cronometro_discurso': cronometro_discurso,
            'cronometro_aparte': cronometro_aparte,
            'cronometro_ordem': cronometro_ordem,
            'cronometro_consideracoes': cronometro_consideracoes})

        tipo_sessao = sessao.tipo
        if tipo_sessao.nome == "Solene":
            context.update(
                {'subnav_template_name': 'sessao/subnav-solene.yaml'})

        return context


class PresencaOrdemDiaView(FormMixin, PresencaMixin, DetailView):
    template_name = 'sessao/presenca_ordemdia.html'
    form_class = PresencaForm
    model = SessaoPlenaria
    logger = logging.getLogger(__name__)

    def get_context_data(self, **kwargs):
        context = FormMixin.get_context_data(self, **kwargs)
        context['title'] = '%s <small>(%s)</small>' % (
            _('Presença Ordem do Dia'), self.object)
        return context

    @method_decorator(permission_required('sessao.add_presencaordemdia'))
    def post(self, request, *args, **kwargs):

        self.object = self.get_object()
        form = self.get_form()

        if form.is_valid():
            # Pegar os presentes salvos no banco
            presentes_banco = PresencaOrdemDia.objects.filter(
                sessao_plenaria_id=self.object.id).values_list(
                'parlamentar_id', flat=True).distinct()

            # Id dos parlamentares presentes
            marcados = request.POST.getlist('presenca_ativos') \
                + request.POST.getlist('presenca_inativos')

            # Deletar os que foram desmarcados
            deletar = set(presentes_banco) - set(marcados)
            PresencaOrdemDia.objects.filter(
                parlamentar_id__in=deletar,
                sessao_plenaria_id=self.object.id).delete()

            for p in marcados:
                ordem = PresencaOrdemDia()
                ordem.sessao_plenaria = self.object
                ordem.parlamentar = Parlamentar.objects.get(id=p)
                ordem.save()
                username = request.user.username
                self.logger.info(
                    'user=' + username + '. PresencaOrdemDia (parlamentar com id={}) salva com sucesso!'.format(p))

            msg = _('Presença em Ordem do Dia salva com sucesso!')
            messages.add_message(request, messages.SUCCESS, msg)

            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:presencaordemdia', kwargs={'pk': pk})


class ListMateriaOrdemDiaView(FormMixin, DetailView):
    template_name = 'sessao/materia_ordemdia_list.html'
    form_class = ListMateriaForm
    model = SessaoPlenaria

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        pk = self.kwargs['pk']
        ordem = OrdemDia.objects.filter(sessao_plenaria_id=pk)

        materias_ordem = []
        for o in ordem:
            ementa = o.materia.ementa
            titulo = o.materia
            numero = o.numero_ordem

            autoria = Autoria.objects.filter(materia_id=o.materia_id)
            autor = [str(a.autor) for a in autoria]

            mat = {'pk': pk,
                   'oid': o.id,
                   'ordem_id': o.materia_id,
                   'ementa': ementa,
                   'titulo': titulo,
                   'numero': numero,
                   'resultado': o.resultado,
                   'autor': autor,
                   'votacao_aberta': o.votacao_aberta,
                   'tipo_votacao': o.tipo_votacao,
                   'materia': o.materia
                   }
            materias_ordem.append(mat)

        sorted(materias_ordem, key=lambda x: x['numero'])

        context.update({'materias_ordem': materias_ordem})

        return self.render_to_response(context)

    @method_decorator(permission_required('sessao.change_ordemdia'))
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        pk = self.kwargs['pk']
        form = ListMateriaForm(request.POST)

        # TODO: Existe uma forma de atualizar em lote de acordo
        # com a forma abaixo, mas como setar o primeiro para "1"?
        # OrdemDia.objects.filter(sessao_plenaria_id=pk)
        # .order_by('numero_ordem').update(numero_ordem=3)

        if 'materia_reorder' in request.POST:
            ordens = OrdemDia.objects.filter(sessao_plenaria_id=pk)
            ordem_num = 1
            for o in ordens:
                o.numero_ordem = ordem_num
                o.save()
                ordem_num += 1
        elif 'abrir-votacao' in request.POST:
            existe_votacao_aberta = OrdemDia.objects.filter(
                sessao_plenaria_id=pk, votacao_aberta=True).exists()
            if existe_votacao_aberta:
                context = self.get_context_data(object=self.object)

                form._errors = {'error_message': 'error_message'}
                context.update({'form': form})

                pk = self.kwargs['pk']
                ordem = OrdemDia.objects.filter(sessao_plenaria_id=pk)

                materias_ordem = []
                for o in ordem:
                    ementa = o.materia.ementa
                    titulo = o.materia
                    numero = o.numero_ordem

                    autoria = Autoria.objects.filter(materia_id=o.materia_id)
                    autor = [str(a.autor) for a in autoria]

                    mat = {'pk': pk,
                           'oid': o.id,
                           'ordem_id': o.materia_id,
                           'ementa': ementa,
                           'titulo': titulo,
                           'numero': numero,
                           'resultado': o.resultado,
                           'autor': autor,
                           'votacao_aberta': o.votacao_aberta,
                           'tipo_votacao': o.tipo_votacao,
                           'materia': o.materia
                           }
                    materias_ordem.append(mat)

                sorted(materias_ordem, key=lambda x: x['numero'])
                context.update({'materias_ordem': materias_ordem})
                return self.render_to_response(context)
            else:
                ordem_id = request.POST['ordem_id']
                ordem = OrdemDia.objects.get(id=ordem_id)
                ordem.votacao_aberta = True
                ordem.registro_aberto = False
                ordem.save()
        return self.get(self, request, args, kwargs)


class MesaView(FormMixin, DetailView):
    template_name = 'sessao/mesa.html'
    form_class = MesaForm
    model = SessaoPlenaria
    logger = logging.getLogger(__name__)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        username = request.user.username

        try:
            self.logger.debug(
                "user=" + username + ". Tentando obter SessaoPlenaria com id={}".format(kwargs['pk']))
            sessao = SessaoPlenaria.objects.get(
                id=kwargs['pk'])
        except ObjectDoesNotExist:
            self.logger.error(
                "user=" + username + ". SessaoPlenaria com id={} não existe.".format(kwargs['pk']))
            mensagem = _('Esta Sessão Plenária não existe!')
            messages.add_message(request, messages.INFO, mensagem)

            return self.render_to_response(context)

        mesa = sessao.integrantemesa.all().order_by('cargo_id') if sessao else []
        cargos_ocupados = [m.cargo for m in mesa]
        cargos = CargoMesa.objects.all()
        cargos_vagos = list(set(cargos) - set(cargos_ocupados))

        # FIX-ME: tem formas melhores de fazer isso, poupando linhas.
        parlamentares = Legislatura.objects.get(
            id=sessao.legislatura_id).mandato_set.all()
        parlamentares_ocupados = [m.parlamentar for m in mesa]
        parlamentares_vagos = list(
            set(
                [p.parlamentar for p in parlamentares]) - set(
                parlamentares_ocupados))
        org_parlamentares_vagos = parlamentares_vagos
        org_parlamentares_vagos.sort(
            key=lambda x: remover_acentos(x.nome_parlamentar))
        org_parlamentares_vagos = [
            p for p in org_parlamentares_vagos if (p.ativo and
                                                   not verifica_afastamento_parlamentar(
                                                       p, sessao.data_inicio, sessao.data_fim)
                                                   )]
        # Se todos os cargos estiverem ocupados, a listagem de parlamentares
        # deve ser renderizada vazia
        if not cargos_vagos:
            org_parlamentares_vagos = []

        context.update(
            {'composicao_mesa': mesa,
             'parlamentares': org_parlamentares_vagos,
             'cargos_vagos': cargos_vagos})

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = FormMixin.get_context_data(self, **kwargs)
        context['title'] = '%s <small>(%s)</small>' % (
            _('Mesa Diretora'), self.object)
        sessao = context['object']
        tipo_sessao = sessao.tipo
        if tipo_sessao.nome == "Solene":
            context.update(
                {'subnav_template_name': 'sessao/subnav-solene.yaml'})
        return context

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:mesa', kwargs={'pk': pk})


def atualizar_mesa(request):
    """
        Esta função lida com qualquer alteração nos campos
        da Mesa Diretora, atualizando os campos após cada alteração
    """
    logger = logging.getLogger(__name__)
    username = request.user.username
    try:
        logger.debug("user=" + username +
                     ". Tentando obter SessaoPlenaria com id={}.".format(request.GET['sessao']))
        sessao = SessaoPlenaria.objects.get(
            id=int(request.GET['sessao']))
    except ObjectDoesNotExist:
        logger.error("user=" + username +
                     ". SessaoPlenaria com id={} inexistente.".format(request.GET['sessao']))
        return JsonResponse({'msg': ('Sessão Inexistente!', 0)})

    # Atualiza os componentes da view após a mudança
    composicao_mesa = IntegranteMesa.objects.filter(
        sessao_plenaria=sessao.id).order_by('cargo_id')

    cargos_ocupados = [m.cargo for m in composicao_mesa]
    cargos = CargoMesa.objects.all()
    cargos_vagos = list(set(cargos) - set(cargos_ocupados))

    parlamentares = Legislatura.objects.get(
        id=sessao.legislatura.id).mandato_set.all()
    parlamentares_ocupados = [m.parlamentar for m in composicao_mesa]
    parlamentares_vagos = list(
        set(
            [p.parlamentar for p in parlamentares]) - set(
            parlamentares_ocupados))

    lista_composicao = [(c.id, c.parlamentar.__str__(),
                         c.cargo.__str__()) for c in composicao_mesa]
    lista_parlamentares = [(
        p.id, p.nome_parlamentar)
        for p in parlamentares_vagos if p.ativo]
    lista_cargos = [(c.id, c.__str__()) for c in cargos_vagos]
    lista_parlamentares.sort(key=lambda x: remover_acentos(x[1]))

    return JsonResponse(
        {'lista_composicao': lista_composicao,
         'lista_parlamentares': lista_parlamentares,
         'lista_cargos': lista_cargos,
         'msg': ('', 1)})


def insere_parlamentar_composicao(request):
    """
        Esta função lida com qualquer operação de inserção
        na composição da Mesa Diretora
    """
    logger = logging.getLogger(__name__)
    username = request.user.username
    if request.user.has_perm(
            '%s.add_%s' % (
                AppConfig.label, IntegranteMesa._meta.model_name)):

        composicao = IntegranteMesa()

        try:
            logger.debug(
                "user=" + username + ". Tentando obter SessaoPlenaria com id={}.".format(request.POST['sessao']))
            composicao.sessao_plenaria = SessaoPlenaria.objects.get(
                id=int(request.POST['sessao']))
        except MultiValueDictKeyError:
            logger.error(
                "user=" + username + ". SessaoPlenaria com id={} não existe.".format(request.POST['sessao']))
            return JsonResponse({'msg': ('A Sessão informada não existe!', 0)})

        try:
            logger.debug(
                "user=" + username + ". Tentando obter Parlamentar com id={}.".format(request.POST['parlamentar']))
            composicao.parlamentar = Parlamentar.objects.get(
                id=int(request.POST['parlamentar']))
        except MultiValueDictKeyError:
            logger.error(
                "user=" + username + ". Parlamentar com id={} não existe.".format(request.POST['parlamentar']))
            return JsonResponse({
                'msg': ('Nenhum parlamentar foi inserido!', 0)})

        try:
            composicao.cargo = CargoMesa.objects.get(
                id=int(request.POST['cargo']))
            parlamentar_ja_inserido = IntegranteMesa.objects.filter(
                sessao_plenaria_id=composicao.sessao_plenaria.id,
                cargo_id=composicao.cargo.id).exists()

            if parlamentar_ja_inserido:
                logger.debug("user=" + username + ". Parlamentar (id={}) já inserido na sessao_plenaria(id={}) e cargo(ìd={})."
                             .format(request.POST['parlamentar'], composicao.sessao_plenaria.id, composicao.cargo.id))
                return JsonResponse({'msg': ('Parlamentar já inserido!', 0)})

            composicao.save()

        except MultiValueDictKeyError as e:
            logger.error("user=" + username +
                         ". Nenhum cargo foi inserido! " + str(e))
            return JsonResponse({'msg': ('Nenhum cargo foi inserido!', 0)})

        logger.info("user=" + username +
                    ". Parlamentar (id={}) inserido com sucesso na sessao_plenaria(id={}) e cargo(ìd={}).")
        return JsonResponse({'msg': ('Parlamentar inserido com sucesso!', 1)})

    else:
        return JsonResponse(
            {'msg': ('Você não tem permissão para esta operação!', 0)})


def remove_parlamentar_composicao(request):
    """
        Essa função lida com qualquer operação de remoção
        na composição da Mesa Diretora
    """
    logger = logging.getLogger(__name__)
    username = request.user.username
    if request.POST and request.user.has_perm(
        '%s.delete_%s' % (
            AppConfig.label, IntegranteMesa._meta.model_name)):

        if 'composicao_mesa' in request.POST:
            try:
                logger.debug("user=" + username + ". Tentando remover IntegranteMesa com id={}".format(
                    request.POST['composicao_mesa']))
                IntegranteMesa.objects.get(
                    id=int(request.POST['composicao_mesa'])).delete()
            except ObjectDoesNotExist:
                logger.error("user=" + username + ". IntegranteMesa com id={} não existe e não pôde ser removido."
                             .format(request.POST['composicao_mesa']))
                return JsonResponse(
                    {'msg': (
                        'Composição da Mesa não pôde ser removida!', 0)})

            logger.info("user=" + username +
                        ". IntegranteMesa com id={} removido com sucesso.")
            return JsonResponse(
                {'msg': (
                    'Parlamentar excluido com sucesso!', 1)})
        else:
            logger.debug("user=" + username +
                         ". Nenhum parlamentar selecionado para ser excluido!")
            return JsonResponse(
                {'msg': (
                    'Selecione algum parlamentar para ser excluido!', 0)})


def get_tupla(tupla_key):
    for tupla in ORDENACAO_RESUMO:
        if tupla[0] == tupla_key:
            return tupla


def resumo_ordenacao(request):
    ordenacao = ResumoOrdenacao.objects.get_or_create()[0]

    initial = [
        get_tupla(ordenacao.primeiro),
        get_tupla(ordenacao.segundo),
        get_tupla(ordenacao.terceiro),
        get_tupla(ordenacao.quarto),
        get_tupla(ordenacao.quinto),
        get_tupla(ordenacao.sexto),
        get_tupla(ordenacao.setimo),
        get_tupla(ordenacao.oitavo),
        get_tupla(ordenacao.nono),
        get_tupla(ordenacao.decimo),
        get_tupla(ordenacao.decimo_primeiro),
        get_tupla(ordenacao.decimo_segundo),
        get_tupla(ordenacao.decimo_terceiro),
        get_tupla(ordenacao.decimo_quarto)
    ]

    context = {
        'ordenacao': initial
    }
    if request.method == 'GET':
        return render(request, 'sessao/resumo_ordenacao.html', context)
    elif request.method == 'POST':
        ordenacao.primeiro = ast.literal_eval(request.POST['0'])[0]
        ordenacao.segundo = ast.literal_eval(request.POST['1'])[0]
        ordenacao.terceiro = ast.literal_eval(request.POST['2'])[0]
        ordenacao.quarto = ast.literal_eval(request.POST['3'])[0]
        ordenacao.quinto = ast.literal_eval(request.POST['4'])[0]
        ordenacao.sexto = ast.literal_eval(request.POST['5'])[0]
        ordenacao.setimo = ast.literal_eval(request.POST['6'])[0]
        ordenacao.oitavo = ast.literal_eval(request.POST['7'])[0]
        ordenacao.nono = ast.literal_eval(request.POST['8'])[0]
        ordenacao.decimo = ast.literal_eval(request.POST['9'])[0]
        ordenacao.decimo_primeiro = ast.literal_eval(request.POST['10'])[0]
        ordenacao.decimo_segundo = ast.literal_eval(request.POST['11'])[0]
        ordenacao.decimo_terceiro = ast.literal_eval(request.POST['12'])[0]
        ordenacao.decimo_quarto = ast.literal_eval(request.POST['13'])[0]
        ordenacao.save()

        msg = _('Ordem salva com sucesso.')
        messages.add_message(request, messages.SUCCESS, msg)

        return HttpResponseRedirect(reverse(
            'sapl.sessao:resumo_ordenacao'))


def get_turno(turno):
    for i in Tramitacao.TURNO_CHOICES:
        if i[0] == turno:
            return str(i[1])
    else:
        return ''


def get_identificacao_basica(sessao_plenaria):
    # =====================================================================
    # Identificação Básica
    data_inicio = sessao_plenaria.data_inicio
    abertura = data_inicio.strftime('%d/%m/%Y') if data_inicio else ''
    data_fim = sessao_plenaria.data_fim
    encerramento = data_fim.strftime('%d/%m/%Y') + ' -' if data_fim else ''
    tema_solene = sessao_plenaria.tema_solene
    context = {'basica': [
        _('Tipo de Sessão: %(tipo)s') % {'tipo': sessao_plenaria.tipo},
        _('Abertura: %(abertura)s - %(hora_inicio)s') % {
            'abertura': abertura, 'hora_inicio': sessao_plenaria.hora_inicio},
        _('Encerramento: %(encerramento)s %(hora_fim)s') % {
            'encerramento': encerramento, 'hora_fim': sessao_plenaria.hora_fim},
    ],
        'sessaoplenaria': sessao_plenaria}
    if sessao_plenaria.tipo.nome == "Solene" and tema_solene:
        context.update(
            {'tema_solene': 'Tema da Sessão Solene: %s' % tema_solene})
    return context


def get_conteudo_multimidia(sessao_plenaria):
    context = {}
    if sessao_plenaria.url_audio:
        context['multimidia_audio'] = _(
            'Audio: ') + str(sessao_plenaria.url_audio)
    else:
        context['multimidia_audio'] = _('Audio: Indisponível')
    if sessao_plenaria.url_video:
        context['multimidia_video'] = _(
            'Video: ') + str(sessao_plenaria.url_video)
    else:
        context['multimidia_video'] = _('Video: Indisponível')
    return context


def get_mesa_diretora(sessao_plenaria):
    mesa = IntegranteMesa.objects.filter(
        sessao_plenaria=sessao_plenaria).order_by('cargo_id')
    integrantes = [{'parlamentar': m.parlamentar,
                    'cargo': m.cargo} for m in mesa]
    return {'mesa': integrantes}


def get_presenca_sessao(sessao_plenaria):

    parlamentares_sessao = [p.parlamentar for p in SessaoPlenariaPresenca.objects.filter(
        sessao_plenaria_id=sessao_plenaria.id
    ).order_by('parlamentar__nome_parlamentar').distinct()]

    ausentes_sessao = JustificativaAusencia.objects.filter(
        sessao_plenaria_id=sessao_plenaria.id
    ).distinct().order_by('parlamentar__nome_parlamentar')

    return ({'presenca_sessao': parlamentares_sessao,
             'justificativa_ausencia': ausentes_sessao})


def get_expedientes(sessao_plenaria):
    expediente = ExpedienteSessao.objects.filter(
        sessao_plenaria_id=sessao_plenaria.id).order_by('tipo__nome')
    expedientes = []
    for e in expediente:
        tipo = TipoExpediente.objects.get(id=e.tipo_id)
        conteudo = e.conteudo
        ex = {'tipo': tipo, 'conteudo': conteudo}
        expedientes.append(ex)
    return ({'expedientes': expedientes})


def get_materias_expediente(sessao_plenaria):
    materias = ExpedienteMateria.objects.filter(
        sessao_plenaria_id=sessao_plenaria.id).order_by('numero_ordem')

    materias_expediente = []
    for m in materias:

        ementa = m.materia.ementa
        titulo = m.materia
        numero = m.numero_ordem

        tramitacao = ''
        tramitacoes = Tramitacao.objects.filter(
            materia=m.materia).order_by('-pk')
        for aux_tramitacao in tramitacoes:
            if aux_tramitacao.turno:
                tramitacao = aux_tramitacao
                break

        turno = None
        if tramitacao:
            turno = get_turno(tramitacao.turno)

        if m.tipo_votacao == LEITURA:
            rv = m.registroleitura_set.first()
            rp = m.retiradapauta_set.filter(materia=m.materia).first()
            if rv:
                resultado = 'Matéria Lida.'
                resultado_observacao = rv.observacao
            elif rp:
                resultado = rp.tipo_de_retirada.descricao
                resultado_observacao = rp.observacao
            else:
                resultado = _('Matéria não lida.')
                resultado_observacao = _(' ')
        else:
            rv = m.registrovotacao_set.first()
            rp = m.retiradapauta_set.filter(materia=m.materia).first()
            if rv:
                resultado = rv.tipo_resultado_votacao.nome
                resultado_observacao = rv.observacao
            elif rp:
                resultado = rp.tipo_de_retirada.descricao
                resultado_observacao = rp.observacao
            else:
                resultado = _('Matéria não votada.')
                resultado_observacao = _(' ')

        autoria = Autoria.objects.filter(materia_id=m.materia_id)
        autor = [str(x.autor) for x in autoria]

        mat = {'ementa': ementa,
               'titulo': titulo,
               'numero': numero,
               'turno': turno,
               'resultado': resultado,
               'resultado_observacao': resultado_observacao,
               'autor': autor,
               'numero_protocolo': m.materia.numero_protocolo,
               'numero_processo': m.materia.numeracao_set.last(),
               'observacao': m.observacao
               }
        materias_expediente.append(mat)

    context = {'materia_expediente': materias_expediente}
    return context


def get_oradores_expediente(sessao_plenaria):
    oradores = []
    for orador in OradorExpediente.objects.filter(
            sessao_plenaria_id=sessao_plenaria.id).order_by('numero_ordem'):
        numero_ordem = orador.numero_ordem
        url_discurso = orador.url_discurso
        observacao = orador.observacao
        parlamentar = Parlamentar.objects.get(
            id=orador.parlamentar_id)
        ora = {'numero_ordem': numero_ordem,
               'url_discurso': url_discurso,
               'parlamentar': parlamentar,
               'observacao': observacao
               }
        oradores.append(ora)
    return {'oradores': oradores}


def get_presenca_ordem_do_dia(sessao_plenaria):
    parlamentares_ordem = [p.parlamentar for p in PresencaOrdemDia.objects.filter(
        sessao_plenaria_id=sessao_plenaria.id
    ).distinct().order_by('parlamentar__nome_parlamentar')]

    return {'presenca_ordem': parlamentares_ordem}


def get_assinaturas(sessao_plenaria):
    mesa_dia = get_mesa_diretora(sessao_plenaria)['mesa']

    presidente_dia = [next(iter(
        [m['parlamentar'] for m in mesa_dia if m['cargo'].descricao == 'Presidente']),
        '')]

    parlamentares_ordem = [p.parlamentar for p in PresencaOrdemDia.objects.filter(
        sessao_plenaria_id=sessao_plenaria.id
    ).order_by('parlamentar__nome_parlamentar')]

    parlamentares_mesa = [m['parlamentar'] for m in mesa_dia]

    # filtra parlamentares retirando os que sao da mesa
    parlamentares_ordem = [
        p for p in parlamentares_ordem if p not in parlamentares_mesa]

    context = {}
    config_assinatura_ata = AppsAppConfig.attr('assinatura_ata')
    if config_assinatura_ata == 'T' and parlamentares_ordem:
        context.update(
            {'texto_assinatura': 'Assinatura de Todos os Parlamentares Presentes na Sessão'})
        context.update({'assinatura_mesa': mesa_dia,
                        'assinatura_presentes': parlamentares_ordem})
    elif config_assinatura_ata == 'M' and mesa_dia:
        context.update(
            {'texto_assinatura': 'Assinatura da Mesa Diretora da Sessão'})
        context.update({'assinatura_mesa': mesa_dia})
    elif config_assinatura_ata == 'P' and presidente_dia and presidente_dia[0]:
        context.update(
            {'texto_assinatura': 'Assinatura do Presidente da Sessão'})
        assinatura_presidente = [
            {'parlamentar': presidente_dia[0], 'cargo': "Presidente"}]
        context.update({'assinatura_mesa': assinatura_presidente})

    return context


def get_materias_ordem_do_dia(sessao_plenaria):
    ordem = OrdemDia.objects.filter(
        sessao_plenaria_id=sessao_plenaria.id,
        parent__isnull=True).order_by('numero_ordem')
    materias_ordem = []
    for o in ordem:
        ementa = o.materia.ementa
        ementa_observacao = o.observacao
        titulo = o.materia
        numero = o.numero_ordem

        tramitacao = ''
        tramitacoes = Tramitacao.objects.filter(
            materia=o.materia).order_by('-pk')
        for aux_tramitacao in tramitacoes:
            if aux_tramitacao.turno:
                tramitacao = aux_tramitacao
                break

        turno = None
        if tramitacao:
            turno = get_turno(tramitacao.turno)

        # Verificar resultado
        rv = o.registrovotacao_set.filter(materia=o.materia).first()
        rp = o.retiradapauta_set.filter(materia=o.materia).first()
        if rv:
            resultado = rv.tipo_resultado_votacao.nome
            resultado_observacao = rv.observacao

        elif rp:
            resultado = rp.tipo_de_retirada.descricao
            resultado_observacao = rp.observacao

        else:
            resultado = _('Matéria não votada')
            resultado_observacao = _(' ')

        voto_sim = ""
        voto_nao = ""
        voto_abstencoes = ""
        voto_nominal = []

        if o.tipo_votacao == 2:
            votos = VotoParlamentar.objects.filter(ordem=o.id)
            for voto in votos:
                aux_voto = (voto.parlamentar.nome_completo, voto.voto)
                voto_nominal.append(aux_voto)
        try:
            voto = RegistroVotacao.objects.filter(ordem=o.id).last()
            voto_sim = voto.numero_votos_sim
            voto_nao = voto.numero_votos_nao
            voto_abstencoes = voto.numero_abstencoes
        except AttributeError:
            voto_sim = " Não Informado"
            voto_nao = " Não Informado"
            voto_abstencoes = " Não Informado"

        autoria = Autoria.objects.filter(
            materia_id=o.materia_id)
        autor = [str(x.autor) for x in autoria]
        mat = {'ementa': ementa,
               'ementa_observacao': ementa_observacao,
               'titulo': titulo,
               'numero': numero,
               'turno': turno,
               'resultado': resultado,
               'resultado_observacao': resultado_observacao,
               'autor': autor,
               'numero_protocolo': o.materia.numero_protocolo,
               'numero_processo': o.materia.numeracao_set.last(),
               'tipo_votacao': o.TIPO_VOTACAO_CHOICES[o.tipo_votacao],
               'voto_sim': voto_sim,
               'voto_nao': voto_nao,
               'voto_abstencoes': voto_abstencoes,
               'voto_nominal': voto_nominal,
               'materia': o.materia
               }
        materias_ordem.append(mat)

    context = {'materias_ordem': materias_ordem}
    return context


def get_oradores_ordemdia(sessao_plenaria):
    oradores = []

    oradores_ordem_dia = OradorOrdemDia.objects.filter(
        sessao_plenaria_id=sessao_plenaria.id
    ).order_by('numero_ordem')

    for orador in oradores_ordem_dia:
        numero_ordem = orador.numero_ordem
        url_discurso = orador.url_discurso
        observacao = orador.observacao
        parlamentar = Parlamentar.objects.get(
            id=orador.parlamentar_id
        )
        o = {
            'numero_ordem': numero_ordem,
            'url_discurso': url_discurso,
            'parlamentar': parlamentar,
            'observacao': observacao
        }
        oradores.append(o)

    context = {'oradores_ordemdia': oradores}
    return context


def get_oradores_explicacoes_pessoais(sessao_plenaria):
    oradores_explicacoes = []
    for orador in Orador.objects.filter(
            sessao_plenaria_id=sessao_plenaria.id).order_by('numero_ordem'):
        for parlamentar in Parlamentar.objects.filter(
                id=orador.parlamentar.id):
            partido_sigla = Filiacao.objects.filter(
                parlamentar=parlamentar).last()
            if not partido_sigla:
                sigla = ''
            else:
                sigla = partido_sigla.partido.sigla
            oradores = {
                'numero_ordem': orador.numero_ordem,
                'parlamentar': parlamentar,
                'sgl_partido': sigla
            }
            oradores_explicacoes.append(oradores)
    context = {'oradores_explicacoes': oradores_explicacoes}
    return context


def get_ocorrencias_da_sessao(sessao_plenaria):
    ocorrencias_sessao = OcorrenciaSessao.objects.filter(
        sessao_plenaria_id=sessao_plenaria.id)
    context = {'ocorrencias_da_sessao': ocorrencias_sessao}
    return context


class ResumoView(DetailView):
    template_name = 'sessao/resumo.html'
    model = SessaoPlenaria
    logger = logging.getLogger(__name__)

    def get_context(self, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        # Votos de Votação Nominal de Matérias Expediente
        materias_expediente_votacao_nominal = ExpedienteMateria.objects.filter(
            sessao_plenaria_id=self.object.id,
            tipo_votacao=2).order_by('-materia')

        votacoes = []
        for mevn in materias_expediente_votacao_nominal:

            votos_materia = []
            titulo_materia = mevn.materia
            registro = RegistroVotacao.objects.filter(expediente=mevn)
            if registro:
                for vp in VotoParlamentar.objects.filter(votacao=registro).order_by('parlamentar'):
                    votos_materia.append(vp)

            dados_votacao = {
                'titulo': titulo_materia,
                'votos': votos_materia
            }
            votacoes.append(dados_votacao)

        context.update({'votos_nominais_materia_expediente': votacoes})

        # =====================================================================
        # Identificação Básica
        context.update(get_identificacao_basica(self.object))
        # =====================================================================
        # Conteúdo Multimídia
        context.update(get_conteudo_multimidia(self.object))
        # =====================================================================
        # Mesa Diretora
        context.update(get_mesa_diretora(self.object))
        # =====================================================================
        # Presença Sessão
        context.update(get_presenca_sessao(self.object))
        # =====================================================================
        # Expedientes
        context.update(get_expedientes(self.object))
        # =====================================================================
        # Matérias Expediente
        context.update(get_materias_expediente(self.object))
        # =====================================================================
        # Oradores Expediente
        context.update(get_oradores_expediente(self.object))
        # =====================================================================
        # Presença Ordem do Dia
        context.update(get_presenca_ordem_do_dia(self.object))
        # =====================================================================
        # Assinaturas
        context.update(get_assinaturas(self.object))
        # =====================================================================
        # Matérias Ordem do Dia
        # Votos de Votação Nominal de Matérias Ordem do Dia
        materias_ordem_dia_votacao_nominal = OrdemDia.objects.filter(
            sessao_plenaria_id=self.object.id,
            tipo_votacao=2).order_by('-materia')

        votacoes_od = []
        for modvn in materias_ordem_dia_votacao_nominal:
            votos_materia_od = []
            t_materia = modvn.materia
            registro_od = RegistroVotacao.objects.filter(ordem=modvn)
            if registro_od:
                for vp_od in VotoParlamentar.objects.filter(votacao__in=registro_od).order_by('parlamentar'):
                    votos_materia_od.append(vp_od)

            dados_votacao_od = {
                'titulo': t_materia,

                'votos': votos_materia_od
            }
            votacoes_od.append(dados_votacao_od)

        context.update({'votos_nominais_materia_ordem_dia': votacoes_od})

        context.update(get_materias_ordem_do_dia(self.object))
        # =====================================================================
        # Oradores Ordem do Dia
        context.update(get_oradores_ordemdia(self.object))
        # =====================================================================
        # Oradores nas Explicações Pessoais
        context.update(get_oradores_explicacoes_pessoais(self.object))
        # =====================================================================
        # Ocorrẽncias da Sessão
        context.update(get_ocorrencias_da_sessao(self.object))
        # =====================================================================
        # Indica a ordem com a qual o template será renderizado
        dict_ord_template = {
            'cont_mult': 'conteudo_multimidia.html',
            'exp': 'expedientes.html',
            'id_basica': 'identificacao_basica.html',
            'lista_p': 'lista_presenca_sessao.html',
            'lista_p_o_d': 'lista_presenca_ordem_dia.html',
            'mat_exp': 'materias_expediente.html',
            'v_n_mat_exp': 'votos_nominais_materias_expediente.html',
            'mat_o_d': 'materias_ordem_dia.html',
            'v_n_mat_o_d': 'votos_nominais_materias_ordem_dia.html',
            'mesa_d': 'mesa_diretora.html',
            'oradores_exped': 'oradores_expediente.html',
            'oradores_o_d': 'oradores_ordemdia.html',
            'oradores_expli': 'oradores_explicacoes.html',
            'ocorr_sessao': 'ocorrencias_da_sessao.html'
        }

        ordenacao = ResumoOrdenacao.objects.get_or_create()[0]
        try:
            context.update({
                'primeiro_ordenacao': dict_ord_template[ordenacao.primeiro],
                'segundo_ordenacao': dict_ord_template[ordenacao.segundo],
                'terceiro_ordenacao': dict_ord_template[ordenacao.terceiro],
                'quarto_ordenacao': dict_ord_template[ordenacao.quarto],
                'quinto_ordenacao': dict_ord_template[ordenacao.quinto],
                'sexto_ordenacao': dict_ord_template[ordenacao.sexto],
                'setimo_ordenacao': dict_ord_template[ordenacao.setimo],
                'oitavo_ordenacao': dict_ord_template[ordenacao.oitavo],
                'nono_ordenacao': dict_ord_template[ordenacao.nono],
                'decimo_ordenacao': dict_ord_template[ordenacao.decimo],
                'decimo_primeiro_ordenacao': dict_ord_template[ordenacao.decimo_primeiro],
                'decimo_segundo_ordenacao': dict_ord_template[ordenacao.decimo_segundo],
                'decimo_terceiro_ordenacao': dict_ord_template[ordenacao.decimo_terceiro],
                'decimo_quarto_ordenacao': dict_ord_template[ordenacao.decimo_quarto]
            })
        except KeyError as e:
            self.logger.error("KeyError: " + str(e) + ". Erro ao tentar utilizar "
                              "configuração de ordenação. Utilizando ordenação padrão.")
            context.update({
                'primeiro_ordenacao': 'identificacao_basica.html',
                'segundo_ordenacao': 'conteudo_multimidia.html',
                'terceiro_ordenacao': 'mesa_diretora.html',
                'quarto_ordenacao': 'lista_presenca_sessao.html',
                'quinto_ordenacao': 'expedientes.html',
                'sexto_ordenacao': 'materias_expediente.html',
                'setimo_ordenacao': 'votos_nominais_materias_expediente.html',
                'oitavo_ordenacao': 'oradores_expediente.html',
                'nono_ordenacao': 'lista_presenca_ordem_dia.html',
                'decimo_ordenacao': 'materias_ordem_dia.html',
                'decimo_primeiro_ordenacao': 'votos_nominais_materias_ordem_dia.html',
                'decimo_segundo_ordenacao': 'oradores_ordemdia.html',
                'decimo_terceiro_ordenacao': 'oradores_explicacoes.html',
                'decimo_quarto_ordenacao': 'ocorrencias_da_sessao.html'
            })

        sessao = context['object']
        tipo_sessao = sessao.tipo
        if tipo_sessao.nome == "Solene":
            context.update(
                {'subnav_template_name': 'sessao/subnav-solene.yaml'})
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context()
        return self.render_to_response(context)


class ResumoAtaView(ResumoView):
    template_name = 'sessao/resumo_ata.html'
    logger = logging.getLogger(__name__)


class ExpedienteView(FormMixin, DetailView):
    template_name = 'sessao/expediente.html'
    form_class = ExpedienteForm
    model = SessaoPlenaria

    logger = logging.getLogger(__name__)

    def get_context_data(self, **kwargs):
        context = FormMixin.get_context_data(self, **kwargs)
        context['title'] = '%s <small>(%s)</small>' % (
            _('Expediente Diversos'), self.object)
        sessao = context['object']
        tipo_sessao = sessao.tipo
        if tipo_sessao.nome == "Solene":
            context.update(
                {'subnav_template_name': 'sessao/subnav-solene.yaml'})
        return context

    @method_decorator(permission_required('sessao.add_expedientesessao'))
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ExpedienteForm(request.POST)
        username = request.user.username

        if 'apagar-expediente' in request.POST:
            ExpedienteSessao.objects.filter(
                sessao_plenaria_id=self.object.id).delete()
            self.logger.info(
                'user=' + username + '. ExpedienteSessao de sessao_plenaria_id={} deletado.'.format(self.object.id))
            return self.form_valid(form)

        if form.is_valid():
            list_tipo = request.POST.getlist('tipo')
            list_conteudo = request.POST.getlist('conteudo')

            for tipo, conteudo in zip(list_tipo, list_conteudo):

                ExpedienteSessao.objects.filter(
                    sessao_plenaria_id=self.object.id,
                    tipo_id=tipo).delete()

                expediente = ExpedienteSessao()
                expediente.sessao_plenaria_id = self.object.id
                expediente.tipo_id = tipo
                expediente.conteudo = conteudo
                expediente.save()

                msg = _('Registro salvo com sucesso')
                messages.add_message(self.request, messages.SUCCESS, msg)
                self.logger.info('user=' + username + '. ExpedienteSessao(sessao_plenaria_id={} e tipo_id={}) salvo com sucesso.'
                                 .format(self.object.id, tipo))

            return self.form_valid(form)
        else:
            self.logger.error(
                "user=" + username + ". Erro ao salvar registro (sessao_plenaria_id={}).".format(self.object.id))
            msg = _('Erro ao salvar ExpedienteSessao')
            messages.add_message(self.request, messages.SUCCESS, msg)
            return self.form_invalid(form)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        tipos = TipoExpediente.objects.all().order_by('ordenacao', 'nome')
        expedientes_sessao = ExpedienteSessao.objects.filter(
            sessao_plenaria_id=self.object.id).order_by('tipo__ordenacao', 'tipo__nome')

        expedientes_salvos = [e.tipo.id for e in expedientes_sessao]

        tipos_null = TipoExpediente.objects.all().exclude(
            id__in=expedientes_salvos).order_by('ordenacao', 'nome')

        expedientes = []
        for e, t in zip(expedientes_sessao, tipos):
            expedientes.append({'tipo': e.tipo,
                                'conteudo': e.conteudo
                                })
        context.update({'expedientes': expedientes})

        for e in tipos_null:
            expedientes.append({'tipo': e,
                                'conteudo': ''
                                })

        context.update({'expedientes': expedientes})
        return self.render_to_response(context)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:expediente', kwargs={'pk': pk})


class OcorrenciaSessaoView(FormMixin, DetailView):
    template_name = 'sessao/ocorrencia_sessao.html'
    form_class = OcorrenciaSessaoForm
    model = SessaoPlenaria

    logger = logging.getLogger(__name__)

    def get_context_data(self, **kwargs):
        context = FormMixin.get_context_data(self, **kwargs)
        context['title'] = 'Ocorrências da Sessão <small>(%s)</small>' % (
            self.object)
        sessao = context['object']
        tipo_sessao = sessao.tipo
        if tipo_sessao.nome == "Solene":
            context.update(
                {'subnav_template_name': 'sessao/subnav-solene.yaml'})
        return context

    def delete(self):
        OcorrenciaSessao.objects.filter(sessao_plenaria=self.object).delete()

        username = self.request.user.username
        self.logger.info('user=' + username + '. OcorrenciaSessao com SessaoPlenaria de id={} deletada.'
                         .format(self.object.id))

        msg = _('Registro deletado com sucesso')
        messages.add_message(self.request, messages.SUCCESS, msg)

    def save(self, form):
        conteudo = form.cleaned_data['conteudo']

        OcorrenciaSessao.objects.filter(sessao_plenaria=self.object).delete()

        ocorrencia = OcorrenciaSessao()
        ocorrencia.sessao_plenaria_id = self.object.id
        ocorrencia.conteudo = conteudo
        ocorrencia.save()

        msg = _('Registro salvo com sucesso')
        messages.add_message(self.request, messages.SUCCESS, msg)

        username = self.request.user.username
        self.logger.info(
            'user=' + username + '. OcorrenciaSessao de sessao_plenaria_id={} atualizada com sucesso.'.format(self.object.id))

    @method_decorator(permission_required('sessao.add_ocorrenciasessao'))
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = OcorrenciaSessaoForm(request.POST)

        if not form.is_valid():
            return self.form_invalid(form)

        if request.POST.get('delete'):
            self.delete()

        elif request.POST.get('save'):
            self.save(form)

        return self.form_valid(form)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:ocorrencia_sessao', kwargs={'pk': pk})


class VotacaoEditView(SessaoPermissionMixin):

    '''
        Votação Simbólica e Secreta
    '''

    template_name = 'sessao/votacao/votacao_edit.html'

    def post(self, request, *args, **kwargs):
        # TODO: refatorar código... forma incorreta de lidar com forms no
        # django
        self.object = self.get_object()
        form = VotacaoEditForm(request.POST)

        materia_id = kwargs['mid']
        ordem_id = kwargs['oid']

        if(int(request.POST['anular_votacao']) == 1):
            ordem = OrdemDia.objects.get(
                sessao_plenaria_id=self.object.id,
                materia_id=materia_id)
            fechar_votacao_materia(ordem)
        else:
            rv = RegistroVotacao.objects.filter(ordem_id=ordem_id).last()
            rv.observacao = request.POST['observacao']
            rv.save()

        return self.form_valid(form)

    def get(self, request, *args, **kwargs):
        context = {}

        url = request.get_full_path()

        if "votsimb" in url:
            titulo = _("Votação Simbólica")
        elif "votsec" in url:
            titulo = _("Votação Secreta")
        else:
            titulo = _("Não definida")

        materia_id = kwargs['mid']
        ordem_id = kwargs['oid']

        ordem = OrdemDia.objects.get(id=ordem_id)

        materia = {'materia': ordem.materia, 'ementa': ordem.materia.ementa}
        context.update({'materia': materia})

        votacao = RegistroVotacao.objects.filter(
            materia_id=materia_id, ordem_id=ordem_id).last()
        votacao_existente = {
            'observacao': votacao.observacao,
            'resultado': votacao.tipo_resultado_votacao.nome,
            'tipo_resultado':
            votacao.tipo_resultado_votacao_id
        }
        context.update({'votacao_titulo': titulo,
                        'votacao': votacao_existente,
                        'tipos': self.get_tipos_votacao()})

        return self.render_to_response(context)

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:ordemdia_list',
                       kwargs={'pk': pk})


class VotacaoView(SessaoPermissionMixin):

    """
        Votação Simbólica e Secreta
    """

    template_name = 'sessao/votacao/votacao.html'
    form_class = VotacaoForm

    logger = logging.getLogger(__name__)

    def get_initial(self):
        initial = SessaoPermissionMixin.get_initial(self)

        ordem_id = self.kwargs['oid']
        ordem = OrdemDia.objects.get(id=ordem_id)

        presentes_id = [
            presente.parlamentar.id for presente in PresencaOrdemDia.objects.filter(
                sessao_plenaria_id=self.kwargs['pk']
            )
        ]

        presenca_ativos = Parlamentar.objects.filter(
            id__in=presentes_id, ativo=True
        )

        initial['subscricoes_choice'] = presenca_ativos
        return initial

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        url = request.get_full_path()

        # TODO: HACK, VERIFICAR MELHOR FORMA DE FAZER ISSO
        if "votsimb" in url:
            titulo = _("Votação Simbólica")
        elif "votsec" in url:
            titulo = _("Votação Secreta")
        else:
            titulo = _("Não definida")

        ordem_id = kwargs['oid']
        self.item_sessao = ordem = OrdemDia.objects.get(id=ordem_id)

        presentes_id = [
            presente.parlamentar.id for presente in PresencaOrdemDia.objects.filter(
                sessao_plenaria_id=self.kwargs['pk']
            )
        ]
        qtde_presentes = len(presentes_id)

        presenca_ativos = Parlamentar.objects.filter(
            id__in=presentes_id, ativo=True
        )
        qtde_ativos = len(presenca_ativos)

        materia = {'materia': ordem.materia, 'ementa': ordem.materia.ementa}
        context.update({'votacao_titulo': titulo,
                        'materia': materia,
                        'total_presentes': qtde_presentes,
                        'total_votantes': qtde_ativos,
                        'subscricoes': presenca_ativos
                        })

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        form = context['form']
        url = request.get_full_path()

        # ====================================================
        if "votsimb" in url:
            titulo = _("Votação Simbólica")
        elif "votsec" in url:
            titulo = _("Votação Secreta")
        else:
            titulo = _("Não definida")

        ordem_id = kwargs['oid']
        self.item_sessao = ordem = OrdemDia.objects.get(id=ordem_id)

        presentes_id = [
            presente.parlamentar.id for presente in PresencaOrdemDia.objects.filter(
                sessao_plenaria_id=self.kwargs['pk']
            )
        ]
        qtde_presentes = len(presentes_id)

        presenca_ativos = Parlamentar.objects.filter(
            id__in=presentes_id, ativo=True
        )
        qtde_ativos = len(presenca_ativos)

        materia = {'materia': ordem.materia, 'ementa': ordem.materia.ementa}
        context.update({'votacao_titulo': titulo,
                        'materia': materia,
                        'total_presentes': qtde_presentes,
                        'total_votantes': qtde_ativos})
        context.update({'form': form})
        # ====================================================

        if 'cancelar-votacao' in request.POST:
            ordem.votacao_aberta = False
            ordem.votacao_aberta_pedido_prazo = False
            ordem.save()
            return self.form_valid(form)

        if form.is_valid():
            materia_id = kwargs['mid']
            ordem_id = kwargs['oid']

            qtde_votos = (int(request.POST['votos_sim']) +
                          int(request.POST['votos_nao']) +
                          int(request.POST['abstencoes']))

            if (int(request.POST['voto_presidente']) == 0):
                qtde_ativos -= 1

            if qtde_votos != qtde_ativos:
                msg = _(
                    'O total de votos não corresponde com a quantidade de votantes!')
                messages.add_message(request, messages.ERROR, msg)
                return self.render_to_response(context)
            else:

                try:

                    subs = form.cleaned_data['subscricoes']

                    resultado = TipoResultadoVotacao.objects.get(
                        id=request.POST['resultado_votacao'])

                    votacao = RegistroVotacao()
                    votacao.numero_votos_sim = int(request.POST['votos_sim'])
                    votacao.numero_votos_nao = int(request.POST['votos_nao'])
                    votacao.numero_abstencoes = int(request.POST['abstencoes'])
                    votacao.observacao = request.POST['observacao']
                    votacao.materia_id = materia_id
                    votacao.ordem_id = ordem_id
                    votacao.tipo_resultado_votacao = resultado
                    votacao.user = request.user
                    votacao.ip = get_client_ip(request)
                    votacao.save()

                    votacao.subscricoes.add(*list(subs))
                except Exception as e:
                    username = request.user.username
                    self.logger.error('user=' + username + '. Problemas ao salvar RegistroVotacao da materia de id={} '
                                      'e da ordem de id={}. '.format(materia_id, ordem_id) + str(e))
                    return self.form_invalid(form)
                else:
                    ordem = OrdemDia.objects.get(
                        sessao_plenaria_id=self.object.id,
                        materia_id=materia_id)
                    ordem.resultado = resultado.nome
                    ordem.votacao_aberta = False
                    ordem.votacao_aberta_pedido_prazo = False

                    ordem.save()

                return self.form_valid(form)
        else:
            return self.render_to_response(context)

    def get_tipos_votacao(self):
        params = {}
        if self.item_sessao.votacao_aberta_pedido_prazo:
            params = dict(natureza='P')
        for tipo in TipoResultadoVotacao.objects.filter(**params):
            yield tipo

    def get_success_url(self):
        pk = self.kwargs['pk']
        url = reverse('sapl.sessao:ordemdia_list',
                      kwargs={'pk': pk})

        return '{}#id{}'.format(url, self.kwargs['mid'])


def fechar_votacao_materia(materia):
    if type(materia) == OrdemDia:
        rv_list = RegistroVotacao.objects.filter(ordem=materia)
        rv_last = rv_list.last()

        VotoParlamentar.objects.filter(ordem=materia).delete()
        rv_last.delete()

    elif type(materia) == ExpedienteMateria:
        rv_list = RegistroVotacao.objects.filter(expediente=materia)
        rv_last = rv_list.last()

        VotoParlamentar.objects.filter(expediente=materia).delete()
        rv_last.delete()

    rv_first = rv_list.first()

    if materia.resultado:
        materia.resultado = '' if not rv_first else rv_first.tipo_resultado_votacao.nome
    materia.votacao_aberta = False
    materia.votacao_aberta_pedido_prazo = False
    materia.registro_aberto = False
    materia.save()


class VotacaoNominalAbstract(SessaoPermissionMixin):
    template_name = 'sessao/votacao/nominal.html'
    ordem = None
    expediente = None
    form_class = VotacaoNominalForm

    logger = logging.getLogger(__name__)

    def get(self, request, *args, **kwargs):
        username = request.user.username
        if self.ordem:
            ordem_id = kwargs['oid']
            if RegistroVotacao.objects.filter(ordem_id=ordem_id).exists():
                msg = _('Esta matéria já foi votada!')
                messages.add_message(request, messages.ERROR, msg)
                self.logger.info(
                    'user=' + username + '. Matéria (ordem_id={}) já votada!'.format(ordem_id))
                return HttpResponseRedirect(reverse(
                    'sapl.sessao:ordemdia_list', kwargs={'pk': kwargs['pk']}))

            try:
                ordem = OrdemDia.objects.get(id=ordem_id)
            except ObjectDoesNotExist:
                self.logger.error(
                    'user=' + username + '. Objeto OrdemDia (pk={}) não existe.'.format(ordem_id))
                raise Http404()

            presentes = PresencaOrdemDia.objects.filter(
                sessao_plenaria_id=ordem.sessao_plenaria_id)
            total = presentes.count()

            materia_votacao = ordem

            if not ordem.votacao_aberta:
                self.logger.error(
                    'user=' + username + '. A votação para esta OrdemDia (id={}) encontra-se fechada!'.format(ordem_id))
                msg = _('A votação para esta matéria encontra-se fechada!')
                messages.add_message(request, messages.ERROR, msg)
                return HttpResponseRedirect(reverse(
                    'sapl.sessao:ordemdia_list', kwargs={'pk': kwargs['pk']}))

            ordem.registro_aberto = True
            ordem.save()

        elif self.expediente:
            expediente_id = kwargs['oid']
            if (RegistroVotacao.objects.filter(
                    expediente_id=expediente_id).exists()):
                self.logger.error(
                    "user=" + username + ". RegistroVotacao (expediente_id={}) já existe.".format(expediente_id))
                msg = _('Esta matéria já foi votada!')
                messages.add_message(request, messages.ERROR, msg)
                return HttpResponseRedirect(reverse(
                    'sapl.sessao:expedientemateria_list',
                    kwargs={'pk': kwargs['pk']}))

            try:
                self.logger.debug(
                    "user=" + username + ". Tentando obter Objeto ExpedienteMateria com id={}.".format(expediente_id))
                expediente = ExpedienteMateria.objects.get(id=expediente_id)
            except ObjectDoesNotExist:
                self.logger.error(
                    'user=' + username + '. Objeto ExpedienteMateria com id={} não existe.'.format(expediente_id))
                raise Http404()

            presentes = SessaoPlenariaPresenca.objects.filter(
                sessao_plenaria_id=expediente.sessao_plenaria_id)
            total = presentes.count()

            materia_votacao = expediente

            if not expediente.votacao_aberta:
                msg = _(
                    'A votação para este ExpedienteMateria (id={}) encontra-se fechada!'.format(expediente_id))
                messages.add_message(request, messages.ERROR, msg)
                return HttpResponseRedirect(reverse(
                    'sapl.sessao:expedientemateria_list',
                    kwargs={'pk': kwargs['pk']}))

            expediente.registro_aberto = True
            expediente.save()

        materia = {'materia': materia_votacao.materia,
                   'ementa': sub(
                       '&nbsp;', ' ', strip_tags(
                           materia_votacao.materia.ementa))}
        context = {'materia': materia, 'object': self.get_object(),
                   'parlamentares': self.get_parlamentares(presentes),
                   'form': self.get_form(),
                   'total': total}

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        username = request.user.username

        if self.ordem:
            ordem_id = kwargs['oid']
            try:
                self.logger.debug(
                    "user=" + username + ". Tentando obter objeto OrdemDia com id={}.".format(ordem_id))
                materia_votacao = OrdemDia.objects.get(id=ordem_id)
            except ObjectDoesNotExist:
                self.logger.error(
                    'user=' + username + '. Objeto OrdemDia com id={} não existe.'.format(ordem_id))
                raise Http404()
        elif self.expediente:
            expediente_id = kwargs['oid']
            try:
                self.logger.debug(
                    "user=" + username + ". Tentando obter ExpedienteMateria com id={}.".format(expediente_id))
                materia_votacao = ExpedienteMateria.objects.get(
                    id=expediente_id)
            except ObjectDoesNotExist:
                self.logger.error(
                    'user=' + username + '. Objeto ExpedienteMateria com id={} não existe.'.format(expediente_id))
                raise Http404()

        if form.is_valid():
            votos_sim = 0
            votos_nao = 0
            abstencoes = 0
            nao_votou = 0

            if 'cancelar-votacao' in request.POST:
                fechar_votacao_materia(materia_votacao)
                if self.ordem:
                    return HttpResponseRedirect(reverse(
                        'sapl.sessao:ordemdia_list', kwargs={'pk': kwargs['pk']}))
                else:
                    return HttpResponseRedirect(reverse(
                        'sapl.sessao:expedientemateria_list',
                        kwargs={'pk': kwargs['pk']}))
            else:
                if form.cleaned_data['resultado_votacao'] == None:
                    form.add_error(None, 'Não é possível finalizar a votação sem '
                                         'nenhum resultado da votação')
                    return self.form_invalid(form)

            for votos in request.POST.getlist('voto_parlamentar'):
                v = votos.split(':')
                voto = v[0]
                parlamentar_id = v[1]

                if voto == 'Sim':
                    votos_sim += 1
                elif voto == 'Não':
                    votos_nao += 1
                elif voto == 'Abstenção':
                    abstencoes += 1
                elif voto == 'Não Votou':
                    nao_votou += 1

            # Caso todas as opções sejam 'Não votou', fecha a votação
            if nao_votou == len(request.POST.getlist('voto_parlamentar')):
                self.logger.error('user=' + username + '. Não é possível finalizar a votação sem '
                                  'nenhum voto')
                form.add_error(None, 'Não é possível finalizar a votação sem '
                                     'nenhum voto')
                return self.form_invalid(form)
            # Remove todas as votação desta matéria, caso existam
            if self.ordem:
                RegistroVotacao.objects.filter(ordem_id=ordem_id).delete()
            elif self.expediente:
                RegistroVotacao.objects.filter(
                    expediente_id=expediente_id).delete()

            votacao = RegistroVotacao()
            votacao.numero_votos_sim = votos_sim
            votacao.numero_votos_nao = votos_nao
            votacao.numero_abstencoes = abstencoes
            votacao.observacao = request.POST.get('observacao', None)
            votacao.user = request.user
            votacao.ip = get_client_ip(request)

            votacao.materia_id = materia_votacao.materia.id
            if self.ordem:
                votacao.ordem_id = ordem_id
            elif self.expediente:
                votacao.expediente_id = expediente_id

            votacao.tipo_resultado_votacao = form.cleaned_data['resultado_votacao']
            votacao.save()

            for votos in request.POST.getlist('voto_parlamentar'):
                v = votos.split(':')
                voto = v[0]
                parlamentar_id = v[1]

                if self.ordem:
                    voto_parlamentar = VotoParlamentar.objects.get_or_create(
                        parlamentar_id=parlamentar_id,
                        ordem_id=ordem_id)[0]
                elif self.expediente:
                    voto_parlamentar = VotoParlamentar.objects.get_or_create(
                        parlamentar_id=parlamentar_id,
                        expediente_id=expediente_id)[0]

                voto_parlamentar.voto = voto
                voto_parlamentar.parlamentar_id = parlamentar_id
                voto_parlamentar.votacao_id = votacao.id
                voto_parlamentar.user = request.user
                voto_parlamentar.ip = get_client_ip(request)
                voto_parlamentar.save()

                resultado = form.cleaned_data['resultado_votacao']

                materia_votacao.resultado = resultado.nome
                materia_votacao.votacao_aberta = False
                materia_votacao.votacao_aberta_pedido_prazo = False
                materia_votacao.save()

            # Verifica se existe algum VotoParlamentar sem RegistroVotacao
            # Por exemplo, se algum parlamentar votar e sua presença for
            # removida da ordem do dia/expediente antes da conclusão da
            # votação
            if self.ordem:
                VotoParlamentar.objects.filter(
                    ordem_id=ordem_id,
                    votacao__isnull=True).delete()
            elif self.expediente:
                VotoParlamentar.objects.filter(
                    expediente_id=expediente_id,
                    votacao__isnull=True).delete()
            return self.form_valid(form)

        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        errors_tuple = [(form[e].label, form.errors[e])
                        for e in form.errors if e in form.fields]
        error_message = '''<ul>'''
        for e in errors_tuple:
            error_message += '''<li><b>%s</b>: %s</li>''' % (e[0], e[1][0])
        for e in form.non_field_errors():
            error_message += '''<li>%s</li>''' % e
        error_message += '''</ul>'''

        messages.add_message(self.request, messages.ERROR, error_message)

        if self.ordem:
            view = 'sapl.sessao:votacaonominal'
        elif self.expediente:
            view = 'sapl.sessao:votacaonominalexp'
        else:
            view = None

        return HttpResponseRedirect(reverse(
            view,
            kwargs={'pk': self.kwargs['pk'],
                    'oid': self.kwargs['oid'],
                    'mid': self.kwargs['mid']}))

    def get_parlamentares(self, presencas):
        self.object = self.get_object()

        presentes = [p.parlamentar for p in presencas]

        if self.ordem:
            voto_parlamentar = VotoParlamentar.objects.filter(
                ordem=self.kwargs['oid'])
        elif self.expediente:
            voto_parlamentar = VotoParlamentar.objects.filter(
                expediente=self.kwargs['oid'])

        for parlamentar in Parlamentar.objects.filter(ativo=True):
            if parlamentar in presentes:
                try:
                    voto = voto_parlamentar.get(
                        parlamentar=parlamentar)
                except ObjectDoesNotExist:
                    username = self.request.user.username
                    self.logger.error('user=' + username + '. Objeto voto_parlamentar do ' +
                                      'parlamentar de id={} não existe.'.format(parlamentar.pk))
                    yield [parlamentar, None]
                else:
                    yield [parlamentar, voto.voto]

    def get_success_url(self):
        pk = self.kwargs['pk']

        if self.ordem:
            return reverse('sapl.sessao:ordemdia_list',
                           kwargs={'pk': pk})
        elif self.expediente:
            return reverse('sapl.sessao:expedientemateria_list',
                           kwargs={'pk': pk})


class VotacaoNominalEditAbstract(SessaoPermissionMixin):
    template_name = 'sessao/votacao/nominal_edit.html'

    logger = logging.getLogger(__name__)

    def get(self, request, *args, **kwargs):
        context = {}
        username = request.user.username

        if self.ordem:
            ordem_id = kwargs['oid']

            ordem = OrdemDia.objects.filter(id=ordem_id).last()
            votacao = RegistroVotacao.objects.filter(ordem_id=ordem_id).last()

            if not ordem or not votacao:
                self.logger.error(
                    'user=' + username + '. Objeto OrdemDia com id={} ou RegistroVotacao de OrdemDia não existe.'.format(ordem_id))
                raise Http404()

            materia = ordem.materia
            ementa = ordem.materia.ementa

        elif self.expediente:
            expediente_id = kwargs['oid']

            expediente = ExpedienteMateria.objects.filter(
                id=expediente_id).last()
            votacao = RegistroVotacao.objects.filter(
                expediente_id=expediente_id).last()

            if not expediente or not votacao:
                self.logger.error('user=' + username + '. Objeto ExpedienteMateria com id={} ou RegistroVotacao de ' +
                                  'ExpedienteMateria não existe.'.format(expediente_id))
                raise Http404()

            materia = expediente.materia
            ementa = expediente.materia.ementa

        votos = VotoParlamentar.objects.filter(votacao_id=votacao.id)

        list_votos = []
        for v in votos:
            parlamentar = Parlamentar.objects.get(id=v.parlamentar_id)
            list_votos.append({'parlamentar': parlamentar, 'voto': v.voto})

        context.update({'votos': list_votos})

        materia = {'materia': materia,
                   'ementa': sub(
                       '&nbsp;', ' ', strip_tags(ementa))}
        context.update({'materia': materia})

        votosSim = votosNao = abstencoes = naoRegistrados = 0
        for v in votos:
            if v.voto == 'Sim':
                votosSim += 1
            elif v.voto == 'Não':
                votosNao += 1
            elif v.voto == 'Abstenção':
                abstencoes += 1
            elif v.voto == 'Não Votou':
                naoRegistrados += 1

        list_contagem = {'votosSim': votosSim, 'votosNao': votosNao, 'abstencoes': abstencoes,
                         'naoRegistrados': naoRegistrados}

        context.update({'contagem': list_contagem})

        votacao_existente = {'observacao': sub(
            '&nbsp;', ' ', strip_tags(votacao.observacao)),
            'resultado': votacao.tipo_resultado_votacao.nome,
            'tipo_resultado':
                votacao.tipo_resultado_votacao_id}
        context.update({'votacao': votacao_existente,
                        'tipos': self.get_tipos_votacao()})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = VotacaoEditForm(request.POST)
        username = request.user.username

        if self.ordem:
            ordem_id = kwargs['oid']

            try:
                materia_votacao = OrdemDia.objects.get(id=ordem_id)
            except ObjectDoesNotExist:
                self.logger.error(
                    'user=' + username + '. Objeto OrdemDia com id={} não existe.'.format(ordem_id))
                raise Http404()

        elif self.expediente:
            expediente_id = kwargs['oid']

            try:
                materia_votacao = ExpedienteMateria.objects.get(
                    id=expediente_id)
            except ObjectDoesNotExist:
                self.logger.error(
                    'user=' + username + '. Objeto ExpedienteMateria com id={} não existe.'.format(expediente_id))
                raise Http404()

        if(int(request.POST['anular_votacao']) == 1):
            fechar_votacao_materia(materia_votacao)

        return self.form_valid(form)

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get_success_url(self):
        pk = self.kwargs['pk']

        if self.ordem:
            return reverse('sapl.sessao:ordemdia_list',
                           kwargs={'pk': pk})
        elif self.expediente:
            return reverse('sapl.sessao:expedientemateria_list',
                           kwargs={'pk': pk})


class VotacaoNominalView(VotacaoNominalAbstract):
    ordem = True
    expediente = False


class VotacaoNominalExpedienteView(VotacaoNominalAbstract):
    expediente = True
    ordem = False


class VotacaoNominalEditView(VotacaoNominalEditAbstract):
    ordem = True
    expediente = False


class VotacaoNominalExpedienteEditView(VotacaoNominalEditAbstract):
    expediente = True
    ordem = False


class VotacaoNominalTransparenciaDetailView(TemplateView):
    template_name = 'sessao/votacao/nominal_transparencia.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        materia_votacao = self.request.GET.get('materia', None)

        if materia_votacao == 'ordem':
            votacao = RegistroVotacao.objects.filter(
                ordem=self.kwargs['oid']).last()
        elif materia_votacao == 'expediente':
            votacao = RegistroVotacao.objects.filter(
                expediente=self.kwargs['oid']).last()
        else:
            raise Http404()

        context['votacao'] = votacao

        voto_parlamentar = VotoParlamentar.objects.filter(
            votacao=votacao).order_by('parlamentar__nome_parlamentar')

        context['voto_parlamentar'] = voto_parlamentar

        votacao_existente = {'observacao': sub(
            '&nbsp;', ' ', strip_tags(votacao.observacao)),
            'resultado': votacao.tipo_resultado_votacao.nome,
            'tipo_resultado':
            votacao.tipo_resultado_votacao_id}
        context.update({'resultado_votacao': votacao_existente,
                        'tipos': self.get_tipos_votacao()})

        return context

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo


class VotacaoNominalExpedienteDetailView(DetailView):
    template_name = 'sessao/votacao/nominal_detail.html'

    def get(self, request, *args, **kwargs):
        context = {}
        materia_id = kwargs['mid']
        expediente_id = kwargs['oid']

        votacao = RegistroVotacao.objects.filter(materia_id=materia_id,
                                                 expediente_id=expediente_id).last()
        expediente = ExpedienteMateria.objects.filter(id=expediente_id).last()
        votos = VotoParlamentar.objects.filter(votacao_id=votacao.id)

        list_votos = []
        for v in votos:
            parlamentar = Parlamentar.objects.get(id=v.parlamentar_id)
            list_votos.append({'parlamentar': parlamentar, 'voto': v.voto})

        context.update({'votos': list_votos})

        materia = {'materia': expediente.materia,
                   'ementa': sub(
                       '&nbsp;', ' ', strip_tags(expediente.materia.ementa))}
        context.update({'materia': materia})

        votacao_existente = {'observacao': sub(
            '&nbsp;', ' ', strip_tags(votacao.observacao)),
            'resultado': votacao.tipo_resultado_votacao.nome,
            'tipo_resultado':
            votacao.tipo_resultado_votacao_id}
        context.update({'votacao': votacao_existente,
                        'tipos': self.get_tipos_votacao()})

        return self.render_to_response(context)

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:expedientemateria_list',
                       kwargs={'pk': pk})


class VotacaoSimbolicaTransparenciaDetailView(TemplateView):
    template_name = 'sessao/votacao/simbolica_transparencia.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        materia_votacao = self.request.GET.get('materia', None)

        if materia_votacao == 'ordem':
            votacao = RegistroVotacao.objects.filter(
                ordem=self.kwargs['oid']).last()
        elif materia_votacao == 'expediente':
            votacao = RegistroVotacao.objects.filter(
                expediente=self.kwargs['oid']).last()
        else:
            raise Http404()

        context['votacao'] = votacao

        registro_votacao = {'numero_votos_sim': votacao.numero_votos_sim,
                            'numero_votos_nao': votacao.numero_votos_nao,
                            'numero_abstencoes': votacao.numero_abstencoes}
        context.update({'registro_votacao': registro_votacao})

        votacao_existente = {'observacao': sub(
            '&nbsp;', ' ', strip_tags(votacao.observacao)),
            'resultado': votacao.tipo_resultado_votacao.nome,
            'tipo_resultado':
            votacao.tipo_resultado_votacao_id}
        context.update({'resultado_votacao': votacao_existente,
                        'tipos': self.get_tipos_votacao()})

        return context

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo


class VotacaoExpedienteView(SessaoPermissionMixin):

    """
        Votação Simbólica e Secreta
    """

    template_name = 'sessao/votacao/votacao.html'
    form_class = VotacaoForm
    logger = logging.getLogger(__name__)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        url = request.get_full_path()

        # TODO: HACK, VERIFICAR MELHOR FORMA DE FAZER ISSO
        if "votsimb" in url:
            titulo = _("Votação Simbólica")
        elif "votsec" in url:
            titulo = _("Votação Secreta")
        else:
            titulo = _("Não definida")

        expediente_id = kwargs['oid']
        self.item_sessao = expediente = ExpedienteMateria.objects.get(
            id=expediente_id)

        presentes_id = [
            presente.parlamentar.id for presente in SessaoPlenariaPresenca.objects.filter(
                sessao_plenaria_id=self.kwargs['pk']
            )
        ]
        qtde_presentes = len(presentes_id)

        presentes_ativos = Parlamentar.objects.filter(
            id__in=presentes_id, ativo=True
        )
        qtde_ativos = len(presentes_ativos)

        materia = {'materia': expediente.materia,
                   'ementa': expediente.materia.ementa}
        context.update({'votacao_titulo': titulo,
                        'materia': materia,
                        'total_presentes': qtde_presentes,
                        'total_votantes': qtde_ativos})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = VotacaoForm(request.POST)
        context = self.get_context_data(object=self.object)
        url = request.get_full_path()

        # ====================================================
        if "votsimb" in url:
            titulo = _("Votação Simbólica")
        elif "votsec" in url:
            titulo = _("Votação Secreta")
        else:
            titulo = _("Não definida")

        expediente_id = kwargs['oid']
        self.item_sessao = expediente = ExpedienteMateria.objects.get(
            id=expediente_id)

        presentes_id = [
            presente.parlamentar.id for presente in SessaoPlenariaPresenca.objects.filter(
                sessao_plenaria_id=self.kwargs['pk']
            )
        ]
        qtde_presentes = len(presentes_id)

        presentes_ativos = Parlamentar.objects.filter(
            id__in=presentes_id, ativo=True
        )
        qtde_ativos = len(presentes_ativos)

        materia = {'materia': expediente.materia,
                   'ementa': expediente.materia.ementa}
        context.update({'votacao_titulo': titulo,
                        'materia': materia,
                        'total_presentes': qtde_presentes,
                        'total_votantes': qtde_ativos})
        context.update({'form': form})
        # ====================================================

        if 'cancelar-votacao' in request.POST:
            expediente.votacao_aberta = False
            expediente.votacao_aberta_pedido_prazo = False
            expediente.save()
            return self.form_valid(form)

        if form.is_valid():
            materia_id = kwargs['mid']
            expediente_id = kwargs['oid']

            qtde_votos = (int(request.POST['votos_sim']) +
                          int(request.POST['votos_nao']) +
                          int(request.POST['abstencoes']))

            if (int(request.POST['voto_presidente']) == 0):
                qtde_ativos -= 1

            if qtde_votos != qtde_ativos:
                msg = _(
                    'O total de votos não corresponde com a quantidade de votantes!')
                messages.add_message(request, messages.ERROR, msg)
                return self.render_to_response(context)
            else:
                try:
                    votacao = RegistroVotacao()
                    votacao.numero_votos_sim = int(request.POST['votos_sim'])
                    votacao.numero_votos_nao = int(request.POST['votos_nao'])
                    votacao.numero_abstencoes = int(request.POST['abstencoes'])
                    votacao.observacao = request.POST['observacao']
                    votacao.materia_id = materia_id
                    votacao.expediente_id = expediente_id
                    votacao.tipo_resultado_votacao_id = int(
                        request.POST['resultado_votacao'])
                    votacao.user = request.user
                    votacao.ip = get_client_ip(request)
                    votacao.save()
                except Exception as e:
                    username = request.user.username
                    self.logger.error("user=" + username + ". " + str(e))
                    return self.form_invalid(form)
                else:
                    expediente = ExpedienteMateria.objects.get(
                        sessao_plenaria_id=self.object.id,
                        materia_id=materia_id)
                    resultado = TipoResultadoVotacao.objects.get(
                        id=request.POST['resultado_votacao'])
                    expediente.resultado = resultado.nome
                    expediente.votacao_aberta = False
                    expediente.votacao_aberta_pedido_prazo = False
                    expediente.save()

                return self.form_valid(form)
        else:
            return self.render_to_response(context)

    def get_tipos_votacao(self):
        params = {}
        if self.item_sessao.votacao_aberta_pedido_prazo:
            params = dict(natureza='P')
        for tipo in TipoResultadoVotacao.objects.filter(**params):
            yield tipo

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:expedientemateria_list',
                       kwargs={'pk': pk})


class VotacaoExpedienteEditView(SessaoPermissionMixin):

    """
        Votação Simbólica e Secreta
    """

    template_name = 'sessao/votacao/votacao_edit.html'
    form_class = VotacaoEditForm

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:expedientemateria_list',
                       kwargs={'pk': pk})

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        url = request.get_full_path()

        if "votsimb" in url:
            titulo = _("Votação Simbólica")
        elif "votsec" in url:
            titulo = _("Votação Secreta")
        else:
            titulo = _("Não definida")

        materia_id = kwargs['mid']
        expediente_id = kwargs['oid']

        expediente = ExpedienteMateria.objects.get(id=expediente_id)

        materia = {'materia': expediente.materia,
                   'ementa': expediente.materia.ementa}
        context.update({'materia': materia})

        votacao = RegistroVotacao.objects.filter(materia_id=materia_id,
                                                 expediente_id=expediente_id
                                                 ).last()
        votacao_existente = {'observacao': sub(
            '&nbsp;', ' ', strip_tags(votacao.observacao)),
            'resultado': votacao.tipo_resultado_votacao.nome,
            'tipo_resultado':
            votacao.tipo_resultado_votacao_id}
        context.update({'votacao_titulo': titulo,
                        'votacao': votacao_existente})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):

        self.object = self.get_object()
        form = VotacaoEditForm(request.POST)

        materia_id = kwargs['mid']
        expediente_id = kwargs['oid']

        if int(request.POST['anular_votacao']) == 1:

            expediente = ExpedienteMateria.objects.get(
                sessao_plenaria_id=self.object.id,
                materia_id=materia_id)
            fechar_votacao_materia(expediente)

        return self.form_valid(form)


class SessaoListView(ListView):
    template_name = "sessao/sessao_list.html"
    paginate_by = 10
    model = SessaoPlenaria

    def get_queryset(self):
        return SessaoPlenaria.objects.all().order_by('-data_inicio')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        return context

def retira_materias_ja_adicionadas(id_sessao, model):
    lista = model.objects.filter(
        sessao_plenaria_id=id_sessao)
    lista_id_materias = [l.materia_id for l in lista]
    return lista_id_materias


class AdicionarVariasMateriasExpediente(PermissionRequiredForAppCrudMixin,
                                        MateriaLegislativaPesquisaView):
    filterset_class = AdicionarVariasMateriasFilterSet
    template_name = 'sessao/adicionar_varias_materias_expediente.html'
    app_label = AppConfig.label

    logger = logging.getLogger(__name__)

    paginate_by = 1000

    def get_filterset_kwargs(self, filterset_class):
        super().get_filterset_kwargs(filterset_class)

        kwargs = {'data': self.request.GET or None}

        qs = self.get_queryset()

        if 'tramitacao__status' in self.request.GET:
            if self.request.GET['tramitacao__status']:
                lista_status = filtra_tramitacao_status(
                    self.request.GET['tramitacao__status'])

                lista_materias_adicionadas = retira_materias_ja_adicionadas(
                    self.kwargs['pk'], ExpedienteMateria)

                qs = qs.filter(id__in=lista_status).exclude(
                    id__in=lista_materias_adicionadas).distinct()

                kwargs.update({
                    'queryset': qs,
                })

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('Pesquisar Matéria Legislativa')
        context['root_pk'] = self.kwargs['pk']

        self.filterset.form.fields['o'].label = _('Ordenação')

        qr = self.request.GET.copy()

        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''
        context['pk_sessao'] = self.kwargs['pk']

        return context

    def post(self, request, *args, **kwargs):
        marcadas = request.POST.getlist('materia_id')
        username = request.user.username

        for m in marcadas:
            try:
                tipo_votacao = request.POST['tipo_votacao_%s' % m]
                msg = _('%s adicionado(a) com sucesso!'
                        % MateriaLegislativa.objects.get(id=m))
                messages.add_message(request, messages.SUCCESS, msg)
                self.logger.info(
                    "user=" + username + ". MateriaLegislativa de id={} adicionado(a) com sucesso!".format(m))
            except MultiValueDictKeyError:
                msg = _('Formulário Inválido. Você esqueceu de selecionar ' +
                        '%s' %
                        MateriaLegislativa.objects.get(id=m))
                messages.add_message(request, messages.ERROR, msg)
                self.logger.error("user=" + username + '. Formulário Inválido. Você esqueceu de ' +
                                  'selecionar o tipo de votação de MateriaLegislativa de id={}.'.format(m))
                return self.get(request, self.kwargs)

            if tipo_votacao:
                lista_materias_expediente = ExpedienteMateria.objects.filter(
                    sessao_plenaria_id=self.kwargs[
                        'pk'])

                materia = MateriaLegislativa.objects.get(id=m)

                expediente = ExpedienteMateria()
                expediente.sessao_plenaria_id = self.kwargs['pk']
                expediente.materia_id = materia.id
                if lista_materias_expediente:
                    posicao = lista_materias_expediente.last().numero_ordem + 1
                    expediente.numero_ordem = posicao
                else:
                    expediente.numero_ordem = 1
                expediente.data_ordem = timezone.now()
                expediente.tipo_votacao = request.POST['tipo_votacao_%s' % m]

                ultima_tramitacao = materia.tramitacao_set.first()
                expediente.tramitacao = ultima_tramitacao

                expediente.save()

        pk = self.kwargs['pk']

        return HttpResponseRedirect(
            reverse('sapl.sessao:expedientemateria_list', kwargs={'pk': pk}))


class AdicionarVariasMateriasOrdemDia(AdicionarVariasMateriasExpediente):
    filterset_class = AdicionarVariasMateriasFilterSet
    template_name = 'sessao/adicionar_varias_materias_ordem.html'

    logger = logging.getLogger(__name__)

    def get_filterset_kwargs(self, filterset_class):
        super().get_filterset_kwargs(filterset_class)

        kwargs = {'data': self.request.GET or None}

        qs = self.get_queryset()

        if 'tramitacao__status' in self.request.GET:
            if self.request.GET['tramitacao__status']:
                lista_status = filtra_tramitacao_status(
                    self.request.GET['tramitacao__status'])

                lista_materias_adicionadas = retira_materias_ja_adicionadas(
                    self.kwargs['pk'], OrdemDia)

                qs = qs.filter(id__in=lista_status).exclude(
                    id__in=lista_materias_adicionadas).distinct()

                kwargs.update({
                    'queryset': qs,
                })
        return kwargs

    def post(self, request, *args, **kwargs):
        marcadas = request.POST.getlist('materia_id')
        username = request.user.username

        for m in marcadas:
            try:
                tipo_votacao = request.POST['tipo_votacao_%s' % m]
                msg = _('%s adicionado(a) com sucesso!'
                        % MateriaLegislativa.objects.get(id=m))
                messages.add_message(request, messages.SUCCESS, msg)
                self.logger.debug(
                    'user=' + username + '. MateriaLegislativa de id={} adicionado(a) com sucesso!'.format(m))
            except MultiValueDictKeyError:
                msg = _('Formulário Inválido. Você esqueceu de selecionar ' +
                        'o tipo de votação de %s' %
                        MateriaLegislativa.objects.get(id=m))
                messages.add_message(request, messages.ERROR, msg)
                self.logger.error('user=' + username + '. Formulário Inválido. Você esqueceu de selecionar '
                                  'o tipo de votação de MateriaLegislativa com id={}'.format(m))

                return self.get(request, self.kwargs)

            if tipo_votacao:
                lista_materias_ordem_dia = OrdemDia.objects.filter(
                    sessao_plenaria_id=self.kwargs[
                        'pk'])

                materia = MateriaLegislativa.objects.get(id=m)

                ordem_dia = OrdemDia()
                ordem_dia.sessao_plenaria_id = self.kwargs['pk']
                ordem_dia.materia_id = materia.id
                if lista_materias_ordem_dia:
                    posicao = lista_materias_ordem_dia.last().numero_ordem + 1
                    ordem_dia.numero_ordem = posicao
                else:
                    ordem_dia.numero_ordem = 1
                ordem_dia.data_ordem = timezone.now()
                ordem_dia.tipo_votacao = tipo_votacao

                ultima_tramitacao = materia.tramitacao_set.first()
                ordem_dia.tramitacao = ultima_tramitacao

                ordem_dia.save()

        return HttpResponseRedirect(
            reverse('sapl.sessao:ordemdia_list', kwargs=self.kwargs))


@csrf_exempt
@permission_required('sessao.change_expedientemateria',
                     'sessao.change_ordemdia')
def mudar_ordem_materia_sessao(request):
    # Pega os dados vindos da requisição
    posicao_inicial = int(request.POST['pos_ini']) + 1
    posicao_final = int(request.POST['pos_fim']) + 1
    pk_sessao = int(request.POST['pk_sessao'])
    logger = logging.getLogger(__name__)

    materia = request.POST['materia']

    # Verifica se está nas Matérias do Expediente ou da Ordem do Dia
    if materia == 'expediente':
        materia = ExpedienteMateria
    elif materia == 'ordem':
        materia = OrdemDia
    else:
        return JsonResponse({}, safe=False)

    # Testa se existe alguma matéria na posição recebida
    try:
        materia_1 = materia.objects.get(
            sessao_plenaria=pk_sessao,
            numero_ordem=posicao_inicial)
    except ObjectDoesNotExist:
        username = request.user.username
        logger.error("user=" + username +
                     ". Materia com sessao_plenaria={} e numero_ordem={}.".format(pk_sessao, posicao_inicial))
        raise  # TODO tratar essa exceção

    # Se a posição inicial for menor que a final, todos que
    # estiverem acima da nova posição devem ter sua ordem decrementada
    # em uma posição
    if posicao_inicial < posicao_final:
        materias_expediente = materia.objects.filter(
            sessao_plenaria=pk_sessao,
            numero_ordem__lte=posicao_final,
            numero_ordem__gte=posicao_inicial)
        for m in materias_expediente:
            m.numero_ordem = m.numero_ordem - 1
            m.save()

    # Se a posição inicial for maior que a final, todos que
    # estiverem abaixo da nova posição devem ter sua ordem incrementada
    # em uma posição
    elif posicao_inicial > posicao_final:
        materias_expediente = materia.objects.filter(
            sessao_plenaria=pk_sessao,
            numero_ordem__gte=posicao_final,
            numero_ordem__lte=posicao_inicial)
        for m in materias_expediente:
            m.numero_ordem = m.numero_ordem + 1
            m.save()

    materia_1.numero_ordem = posicao_final
    materia_1.save()

    return JsonResponse({}, safe=False)


class JustificativaAusenciaCrud(MasterDetailCrud):
    model = JustificativaAusencia
    public = [RP_LIST, RP_DETAIL, ]
    parent_field = 'sessao_plenaria'

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['parlamentar', 'sessao_plenaria', 'ausencia', 'tipo_ausencia',
                            'data']

        @property
        def layout_display(self):

            layout = super().layout_display

            if self.object.ausencia == 2:
                # rm materias_da_ordem_do_dia do detail
                layout[0]['rows'].pop(6)
                # rm materias_do_expediente do detail
                layout[0]['rows'].pop(5)

            return layout

    class ListView(MasterDetailCrud.ListView):
        paginate_by = 10

    class CreateView(MasterDetailCrud.CreateView):
        form_class = JustificativaAusenciaForm
        layout_key = None

        def get_context_data_old(self, **kwargs):

            context = super().get_context_data(**kwargs)

            presencas = SessaoPlenariaPresenca.objects.filter(
                sessao_plenaria_id=kwargs['root_pk']
            ).order_by('parlamentar__nome_parlamentar')

            parlamentares_sessao = [p.parlamentar for p in presencas]

            context.update({'presenca_sessao': parlamentares_sessao})

            expedientes = ExpedienteMateria.objects.filter(
                sessao_plenaria_id=kwargs['root_pk'])

            expedientes_materia = [e.materia for e in expedientes]

            context.update({'expedientes': expedientes})

            ordens = OrdemDia.objects.filter(
                sessao_plenaria_id=kwargs['root_pk'])

            ordem_materia = [o.materia for o in ordens]

            context.update({'ordens': ordens})

            return context

        def get_initial(self):
            sessao_plenaria = SessaoPlenaria.objects.get(id=self.kwargs['pk'])
            return {'sessao_plenaria': sessao_plenaria}

        def get_success_url(self):
            return reverse('sapl.sessao:justificativaausencia_list',
                           kwargs={'pk': self.kwargs['pk']})

    class UpdateView(MasterDetailCrud.UpdateView):

        form_class = JustificativaAusenciaForm
        layout_key = None

        def get_initial(self):
            sessao_plenaria = JustificativaAusencia.objects.get(
                id=self.kwargs['pk']).sessao_plenaria
            return {'sessao_plenaria': sessao_plenaria}

    class DeleteView(MasterDetailCrud.DeleteView):
        pass


class VotacaoEmBlocoExpediente(PermissionRequiredForAppCrudMixin, ListView):
    template_name = 'sessao/votacao/votacao_bloco.html'
    app_label = AppConfig.label
    expediente = True

    def get_queryset(self):
        return ExpedienteMateria.objects.filter(sessao_plenaria_id=self.kwargs['pk'],
                                                resultado='',
                                                retiradapauta=None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pk'] = self.kwargs['pk']
        context['root_pk'] = self.kwargs['pk']
        if not verifica_sessao_iniciada(self.request, self.kwargs['pk']):
            context['sessao_iniciada'] = False
            return context
        context['sessao_iniciada'] = True
        context['turno_choices'] = Tramitacao.TURNO_CHOICES
        context['title'] = SessaoPlenaria.objects.get(id=self.kwargs['pk'])
        if self.expediente:
            context['expediente'] = True
        else:
            context['expediente'] = False
        return context


class VotacaoEmBlocoOrdemDia(VotacaoEmBlocoExpediente):
    expediente = False

    def get_queryset(self):
        return OrdemDia.objects.filter(sessao_plenaria_id=self.kwargs['pk'],
                                       resultado='',
                                       retiradapauta=None).order_by('numero_ordem')


class VotacaoEmBlocoSimbolicaView(PermissionRequiredForAppCrudMixin, TemplateView):

    """
        Votação Simbólica
    """
    app_label = AppConfig.label
    template_name = 'sessao/votacao/votacao_simbolica_bloco.html'
    logger = logging.getLogger(__name__)

    def post(self, request, *args, **kwargs):

        if not 'context' in locals():
            context = {'pk': self.kwargs['pk'],
                       'root_pk': self.kwargs['pk'],
                       'title': SessaoPlenaria.objects.get(id=self.kwargs['pk']),
                       'origem': request.POST['origem'],
                       'subnav_template_name': 'sessao/subnav.yaml'
                       }

        if 'marcadas_1' in request.POST:

            context.update({'resultado_votacao': TipoResultadoVotacao.objects.all(),
                            'origem': request.POST['origem']})

            # marcadas_1 se refere a votação simbólica e marcadas_2 a votação
            # nominal
            if request.POST['origem'] == 'ordem':
                ordens = OrdemDia.objects.filter(
                    id__in=request.POST.getlist('marcadas_1'))

                presentes_id = [
                    presente.parlamentar.id for presente in PresencaOrdemDia.objects.filter(
                        sessao_plenaria_id=self.kwargs['pk']
                    )
                ]
                qtde_presentes = len(presentes_id)

                presenca_ativos = Parlamentar.objects.filter(
                    id__in=presentes_id, ativo=True
                )
                qtde_ativos = len(presenca_ativos)

                context.update({'ordens': ordens,
                                'total_presentes': qtde_presentes,
                                'total_votantes': qtde_ativos})
            else:
                expedientes = ExpedienteMateria.objects.filter(
                    id__in=request.POST.getlist('marcadas_1'))

                presentes_id = [
                    presente.parlamentar.id for presente in SessaoPlenariaPresenca.objects.filter(
                        sessao_plenaria_id=self.kwargs['pk']
                    )
                ]
                qtde_presentes = len(presentes_id)

                presenca_ativos = Parlamentar.objects.filter(
                    id__in=presentes_id, ativo=True
                )
                qtde_ativos = len(presenca_ativos)

                context.update({'expedientes': expedientes,
                                'total_presentes': qtde_presentes,
                                'total_votantes': qtde_ativos})

        if 'salvar-votacao' in request.POST:
            form = VotacaoForm(request.POST)

            if form.is_valid():

                origem = request.POST['origem']

                if origem == 'ordem':
                    ordens = OrdemDia.objects.filter(
                        id__in=request.POST.getlist('ordens'))

                    for ordem in ordens:
                        try:
                            votacao = RegistroVotacao()
                            votacao.numero_votos_sim = int(
                                request.POST['votos_sim'])
                            votacao.numero_votos_nao = int(
                                request.POST['votos_nao'])
                            votacao.numero_abstencoes = int(
                                request.POST['abstencoes'])
                            votacao.observacao = request.POST['observacao']
                            votacao.materia = ordem.materia
                            votacao.ordem = ordem
                            resultado = TipoResultadoVotacao.objects.get(
                                id=request.POST['resultado_votacao'])
                            votacao.tipo_resultado_votacao = resultado
                            votacao.user = request.user
                            votacao.ip = get_client_ip(request)
                            votacao.save()
                        except Exception as e:
                            username = request.user.username
                            self.logger.error('user=' + username + '. Problemas ao salvar '
                                              'RegistroVotacao da materia de id={} '
                                              'e da ordem de id={}. '
                                              .format(ordem.materia.id, ordem.id) + str(e))
                            return self.form_invalid(form, context)
                        else:
                            ordem.resultado = resultado.nome
                            ordem.votacao_aberta = False
                            ordem.votacao_aberta_pedido_prazo = False
                            ordem.save()

                else:
                    expedientes = ExpedienteMateria.objects.filter(
                        id__in=request.POST.getlist('expedientes'))
                    for expediente in expedientes:
                        try:
                            votacao = RegistroVotacao()
                            votacao.numero_votos_sim = int(
                                request.POST['votos_sim'])
                            votacao.numero_votos_nao = int(
                                request.POST['votos_nao'])
                            votacao.numero_abstencoes = int(
                                request.POST['abstencoes'])
                            votacao.observacao = request.POST['observacao']
                            votacao.materia = expediente.materia
                            votacao.expediente = expediente
                            resultado = TipoResultadoVotacao.objects.get(
                                id=request.POST['resultado_votacao'])
                            votacao.tipo_resultado_votacao = resultado
                            votacao.user = request.user
                            votacao.ip = get_client_ip(request)
                            votacao.save()
                        except Exception as e:
                            username = request.user.username
                            self.logger.error('user=' + username + '. Problemas ao salvar RegistroVotacao da materia de id={} '
                                              'e da ordem de id={}. '.format(expediente.materia.id, expediente.id) + str(e))
                            return self.form_invalid(form, context)
                        else:
                            expediente.resultado = resultado.nome
                            expediente.votacao_aberta = False
                            expediente.votacao_aberta_pedido_prazo = False
                            expediente.save()

                return HttpResponseRedirect(self.get_success_url())

            else:
                return self.form_invalid(form, context)

        if 'cancelar-votacao' in request.POST:
            if request.POST['origem'] == 'ordem':
                ordens = OrdemDia.objects.filter(
                    id__in=request.POST.getlist('ordens'))
                for ordem in ordens:
                    ordem.votacao_aberta = False
                    ordem.votacao_aberta_pedido_prazo = False
                    ordem.save()
            else:
                expedientes = ExpedienteMateria.objects.filter(
                    id__in=request.POST.getlist('expedientes'))
                for expediente in expedientes:
                    expediente.votacao_aberta = False
                    expediente.votacao_aberta_pedido_prazo = False
                    expediente.save()

            return HttpResponseRedirect(self.get_success_url())

        return self.render_to_response(context)

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get_success_url(self):
        if self.request.POST['origem'] == 'ordem':
            return reverse('sapl.sessao:ordemdia_list',
                           kwargs={'pk': self.kwargs['pk']})
        else:
            return reverse('sapl.sessao:expedientemateria_list',
                           kwargs={'pk': self.kwargs['pk']})

    def form_invalid(self, form, context):

        errors_tuple = [(form[e].label, form.errors[e])
                        for e in form.errors if e in form.fields]
        error_message = '<ul>'
        for e in errors_tuple:
            error_message += '<li><b>%s</b>: %s</li>' % (e[0], e[1][0])
        for e in form.non_field_errors():
            error_message += '<li>%s</li>' % e
        error_message += '</ul>'

        messages.add_message(self.request, messages.ERROR, error_message)

        if self.request.POST['origem'] == 'ordem':
            ordens = OrdemDia.objects.filter(
                id__in=self.request.POST.getlist('ordens'))

            presentes_id = [
                presente.parlamentar.id for presente in PresencaOrdemDia.objects.filter(
                    sessao_plenaria_id=self.kwargs['pk']
                )
            ]
            qtde_presentes = len(presentes_id)

            presenca_ativos = Parlamentar.objects.filter(
                id__in=presentes_id, ativo=True
            )
            qtde_ativos = len(presenca_ativos)

            context.update({'ordens': ordens,
                            'total_presentes': qtde_presentes,
                            'total_votantes': qtde_ativos})
        elif self.request.POST['origem'] == 'expediente':
            expedientes = ExpedienteMateria.objects.filter(
                id__in=self.request.POST.getlist('expedientes'))

            presentes_id = [
                presente.parlamentar.id for presente in SessaoPlenariaPresenca.objects.filter(
                    sessao_plenaria_id=self.kwargs['pk']
                )
            ]
            qtde_presentes = len(presentes_id)

            presenca_ativos = Parlamentar.objects.filter(
                id__in=presentes_id, ativo=True
            )
            qtde_ativos = len(presenca_ativos)

            context.update({'expedientes': expedientes,
                            'total_presentes': qtde_presentes,
                            'total_votantes': qtde_ativos})

        context.update({'resultado_votacao': TipoResultadoVotacao.objects.all(),
                        'form': form,
                        'origem': self.request.POST['origem']})

        return self.render_to_response(context)


class VotacaoEmBlocoNominalView(PermissionRequiredForAppCrudMixin, TemplateView):
    """
        Votação Nominal
    """
    app_label = AppConfig.label
    template_name = 'sessao/votacao/votacao_nominal_bloco.html'
    logger = logging.getLogger(__name__)

    def post(self, request, *args, **kwargs):
        username = request.user.username
        form = VotacaoNominalForm(request.POST)

        if not 'context' in locals():
            context = {'pk': self.kwargs['pk'],
                       'root_pk': self.kwargs['pk'],
                       'title': SessaoPlenaria.objects.get(id=self.kwargs['pk']),
                       'origem': request.POST['origem'],
                       'subnav_template_name': 'sessao/subnav.yaml'}

        if 'marcadas_2' in request.POST:

            context.update({'resultado_votacao': TipoResultadoVotacao.objects.all(),
                            'origem': request.POST['origem']})

            # marcadas_1 se refere a votação simbólica e marcadas_2 a votação
            # nominal
            if request.POST['origem'] == 'ordem':
                ordens = OrdemDia.objects.filter(
                    id__in=request.POST.getlist('marcadas_2'))
                presentes = PresencaOrdemDia.objects.filter(
                    sessao_plenaria_id=kwargs['pk'])
                context.update({'ordens': ordens})
            else:
                expedientes = ExpedienteMateria.objects.filter(
                    id__in=request.POST.getlist('marcadas_2'))
                presentes = SessaoPlenariaPresenca.objects.filter(
                    sessao_plenaria_id=kwargs['pk'])
                context.update({'expedientes': expedientes})
            total_presentes = presentes.count()
            context.update({'parlamentares': self.get_parlamentares(),
                            'total_presentes': total_presentes})

        if 'cancelar-votacao' in request.POST:
            if request.POST['origem'] == 'ordem':
                for ordem_id in request.POST.getlist('ordens'):
                    ordem = OrdemDia.objects.get(id=ordem_id)
                    fechar_votacao_materia(ordem)
                return HttpResponseRedirect(reverse(
                    'sapl.sessao:ordemdia_list', kwargs={'pk': self.kwargs['pk']}))
            else:
                for expediente_id in request.POST.getlist('expedientes'):
                    expediente = ExpedienteMateria.objects.get(
                        id=expediente_id)
                    fechar_votacao_materia(expediente)
                return HttpResponseRedirect(reverse(
                    'sapl.sessao:expedientemateria_list',
                    kwargs={'pk': self.kwargs['pk']}))

        if 'salvar-votacao' in request.POST:

            if form.is_valid():
                if form.cleaned_data['resultado_votacao'] == None:
                    form.add_error(None, 'Não é possível finalizar a votação sem '
                                   'nenhum resultado da votação.')
                    return self.form_invalid(form, context)

                qtde_votos = (int(request.POST['votos_sim']) +
                              int(request.POST['votos_nao']) +
                              int(request.POST['abstencoes']) +
                              int(request.POST['nao_votou']))

                # Caso todas as opções sejam 'Não votou', fecha a votação
                if int(request.POST['nao_votou']) == qtde_votos:
                    self.logger.error('user=' + username + '. Não é possível finalizar a votação sem '
                                      'nenhum voto.')
                    form.add_error(None, 'Não é possível finalizar a votação sem '
                                   'nenhum voto.')
                    return self.form_invalid(form, context)

                if request.POST['origem'] == 'ordem':
                    for ordem_id in request.POST.getlist('ordens'):
                        ordem = OrdemDia.objects.get(id=ordem_id)
                        # Remove todas as votação desta matéria, caso existam
                        RegistroVotacao.objects.filter(
                            ordem_id=ordem_id).delete()
                        votacao = RegistroVotacao()
                        votacao.numero_votos_sim = int(
                            request.POST['votos_sim'])
                        votacao.numero_votos_nao = int(
                            request.POST['votos_nao'])
                        votacao.numero_abstencoes = int(
                            request.POST['abstencoes'])
                        votacao.observacao = request.POST['observacao']
                        votacao.materia = ordem.materia
                        votacao.ordem = ordem
                        votacao.tipo_resultado_votacao = form.cleaned_data['resultado_votacao']
                        votacao.user = request.user
                        votacao.ip = get_client_ip(request)
                        votacao.save()

                        for votos in request.POST.getlist('voto_parlamentar'):
                            v = votos.split(':')
                            voto = v[0]
                            parlamentar_id = v[1]

                            voto_parlamentar = VotoParlamentar.objects.get_or_create(
                                parlamentar_id=parlamentar_id,
                                ordem_id=ordem_id)[0]

                            voto_parlamentar.voto = voto
                            voto_parlamentar.parlamentar_id = parlamentar_id
                            voto_parlamentar.votacao_id = votacao.id
                            voto_parlamentar.user = request.user
                            voto_parlamentar.ip = get_client_ip(request)
                            voto_parlamentar.save()

                            ordem.resultado = form.cleaned_data['resultado_votacao'].nome
                            ordem.votacao_aberta = False
                            ordem.votacao_aberta_pedido_prazo = False
                            ordem.save()

                    VotoParlamentar.objects.filter(
                        ordem_id=ordem_id,
                        votacao__isnull=True).delete()

                else:
                    for expediente_id in request.POST.getlist('expedientes'):
                        expediente = ExpedienteMateria.objects.get(
                            id=expediente_id)
                        RegistroVotacao.objects.filter(
                            expediente_id=expediente_id).delete()
                        votacao = RegistroVotacao()
                        votacao.numero_votos_sim = int(
                            request.POST['votos_sim'])
                        votacao.numero_votos_nao = int(
                            request.POST['votos_nao'])
                        votacao.numero_abstencoes = int(
                            request.POST['abstencoes'])
                        votacao.observacao = request.POST['observacao']
                        votacao.materia = expediente.materia
                        votacao.expediente = expediente
                        votacao.tipo_resultado_votacao = form.cleaned_data['resultado_votacao']
                        votacao.user = request.user
                        votacao.ip = get_client_ip(request)
                        votacao.save()

                        # Salva os votos de cada parlamentar
                        for votos in request.POST.getlist('voto_parlamentar'):
                            v = votos.split(':')
                            voto = v[0]
                            parlamentar_id = v[1]

                            voto_parlamentar = VotoParlamentar.objects.get_or_create(
                                parlamentar_id=parlamentar_id,
                                expediente_id=expediente_id)[0]

                            voto_parlamentar.voto = voto
                            voto_parlamentar.parlamentar_id = parlamentar_id
                            voto_parlamentar.votacao_id = votacao.id
                            voto_parlamentar.user = request.user
                            voto_parlamentar.ip = get_client_ip(request)
                            voto_parlamentar.save()

                            expediente.resultado = form.cleaned_data['resultado_votacao'].nome
                            expediente.votacao_aberta = False
                            expediente.votacao_aberta_pedido_prazo = False
                            expediente.save()

                    VotoParlamentar.objects.filter(
                        expediente_id=expediente_id,
                        votacao__isnull=True).delete()

                return HttpResponseRedirect(self.get_success_url())

            else:
                return self.form_invalid(form, context)

        return self.render_to_response(context)

    def get_parlamentares(self):

        # campos hidden ainda não preenchidos
        if 'marcadas_2' in self.request.POST:
            if self.request.POST['origem'] == 'ordem':
                presencas = PresencaOrdemDia.objects.filter(
                    sessao_plenaria_id=self.kwargs['pk'])
                ordens_id = self.request.POST.getlist('marcadas_2')
                voto_parlamentar = VotoParlamentar.objects.filter(
                    ordem=ordens_id[0])
            else:
                presencas = SessaoPlenariaPresenca.objects.filter(
                    sessao_plenaria_id=self.kwargs['pk'])
                expedientes_id = self.request.POST.getlist('marcadas_2')
                voto_parlamentar = VotoParlamentar.objects.filter(
                    expediente=expedientes_id[0])

        # campos hidden já preenchidos
        else:
            if self.request.POST['origem'] == 'ordem':
                presencas = PresencaOrdemDia.objects.filter(
                    sessao_plenaria_id=self.kwargs['pk'])
                ordens_id = self.request.POST.getlist('ordens')
                voto_parlamentar = VotoParlamentar.objects.filter(
                    ordem=ordens_id[0])
            else:
                presencas = SessaoPlenariaPresenca.objects.filter(
                    sessao_plenaria_id=self.kwargs['pk'])
                expedientes_id = self.request.POST.getlist('expedientes')
                voto_parlamentar = VotoParlamentar.objects.filter(
                    expediente=expedientes_id[0])

        presentes = [p.parlamentar for p in presencas]

        for parlamentar in Parlamentar.objects.filter(ativo=True):
            if parlamentar in presentes:
                try:
                    voto = voto_parlamentar.get(
                        parlamentar=parlamentar)
                except ObjectDoesNotExist:
                    username = self.request.user.username
                    self.logger.error('user=' + username + '. Objeto voto_parlamentar do ' +
                                      'parlamentar de id={} não existe.'.format(parlamentar.pk))
                    yield [parlamentar, None]
                else:
                    yield [parlamentar, voto.voto]

    def get_success_url(self):
        if self.request.POST['origem'] == 'ordem':
            return reverse('sapl.sessao:ordemdia_list',
                           kwargs={'pk': self.kwargs['pk']})
        else:
            return reverse('sapl.sessao:expedientemateria_list',
                           kwargs={'pk': self.kwargs['pk']})

    def form_invalid(self, form, context):

        errors_tuple = [(form[e].label, form.errors[e])
                        for e in form.errors if e in form.fields]
        error_message = '<ul>'
        for e in errors_tuple:
            error_message += '<li><b>%s</b>: %s</li>' % (e[0], e[1][0])
        for e in form.non_field_errors():
            error_message += '<li>%s</li>' % e
        error_message += '</ul>'

        messages.add_message(self.request, messages.ERROR, error_message)

        if self.request.POST['origem'] == 'ordem':
            ordens = OrdemDia.objects.filter(
                id__in=self.request.POST.getlist('ordens'))
            presentes = PresencaOrdemDia.objects.filter(
                sessao_plenaria_id=self.kwargs['pk'])
            context.update({'ordens': ordens})
        elif self.request.POST['origem'] == 'expediente':
            expedientes = ExpedienteMateria.objects.filter(
                id__in=self.request.POST.getlist('expedientes'))
            presentes = SessaoPlenariaPresenca.objects.filter(
                sessao_plenaria_id=self.kwargs['pk'])
            context.update({'expedientes': expedientes})

        total_presentes = presentes.count()
        context.update({'parlamentares': self.get_parlamentares(),
                        'total_presentes': total_presentes,
                        'resultado_votacao': TipoResultadoVotacao.objects.all(),
                        'form': form,
                        'origem': self.request.POST['origem']})

        return self.render_to_response(context)


class RetiradaPautaCrud(MasterDetailCrud):
    model = RetiradaPauta
    public = [RP_LIST, RP_DETAIL, ]
    parent_field = 'sessao_plenaria'

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['tipo_de_retirada',
                            'materia', 'observacao', 'parlamentar']

    class ListView(MasterDetailCrud.ListView):
        paginate_by = 10

    class CreateView(MasterDetailCrud.CreateView):
        form_class = RetiradaPautaForm
        layout_key = None

        def get_initial(self):
            sessao_plenaria = SessaoPlenaria.objects.get(id=self.kwargs['pk'])
            return {'sessao_plenaria': sessao_plenaria}

        def get_success_url(self):
            return reverse('sapl.sessao:retiradapauta_list',
                           kwargs={'pk': self.kwargs['pk']})

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = RetiradaPautaForm
        layout_key = None

        def get_initial(self):
            sessao_plenaria = RetiradaPauta.objects.get(
                id=self.kwargs['pk']).sessao_plenaria
            return {'sessao_plenaria': sessao_plenaria}

    class DeleteView(MasterDetailCrud.DeleteView):
        pass


def voto_nominal_parlamentar(request):
    parlamentar_id = request.GET.get('parlamentar_id')
    parlamentar_voto = request.GET.get('parlamentar_voto')
    id_ordem_expediente = request.GET.get('id_ordem_expediente')
    is_ordemdia = request.GET.get('is_ordemdia') == 'true'

    if is_ordemdia:
        # Apaga o voto (opção selecionada: Não Votou)
        if parlamentar_voto == "Não ":
            VotoParlamentar.objects.filter(
                ordem_id=id_ordem_expediente, parlamentar_id=parlamentar_id).delete()
        else:
            # Salva o voto
            parlamentar_voto = "Abstenção" if parlamentar_voto == 'Abst' else parlamentar_voto[
                :3]
            try:
                voto = VotoParlamentar.objects.get(
                    parlamentar_id=parlamentar_id,
                    ordem_id=id_ordem_expediente)
            except ObjectDoesNotExist:
                voto = VotoParlamentar.objects.create(
                    parlamentar_id=parlamentar_id,
                    voto=parlamentar_voto,
                    user=request.user,
                    ip=get_client_ip(request),
                    ordem_id=id_ordem_expediente)
            else:
                voto.voto = parlamentar_voto
                voto.ip = get_client_ip(request)
                voto.user = request.user
                voto.save()

    # expediente
    else:
        # Apaga o voto (opção selecionada: Não Votou)
        if parlamentar_voto == "Não ":
            VotoParlamentar.objects.filter(
                expediente_id=id_ordem_expediente, parlamentar_id=parlamentar_id).delete()
        # Salva o voto
        else:
            parlamentar_voto = parlamentar_voto[:3]
            try:
                voto = VotoParlamentar.objects.get(
                    parlamentar_id=parlamentar_id,
                    expediente_id=id_ordem_expediente)
            except ObjectDoesNotExist:
                voto = VotoParlamentar.objects.create(
                    parlamentar_id=parlamentar_id,
                    voto=parlamentar_voto,
                    user=request.user,
                    ip=get_client_ip(request),
                    expediente_id=id_ordem_expediente)
            else:
                voto.voto = parlamentar_voto
                voto.ip = get_client_ip(request)
                voto.user = request.user
                voto.save()

    return JsonResponse({})


class AbstractLeituraView(FormView):
    template_name = 'sessao/votacao/leitura_form.html'
    success_url = '/'
    form_class = OrdemExpedienteLeituraForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['materia'] = MateriaLegislativa.objects.get(
            id=self.kwargs['mid'])
        return context

    def get_initial(self):
        initial = super().get_initial()
        materia = MateriaLegislativa.objects.get(id=self.kwargs['mid'])
        initial['materia'] = materia
        initial['materia__ementa'] = materia.ementa
        if self.expediente:
            expediente = ExpedienteMateria.objects.get(id=self.kwargs['oid'])
            instance = RegistroLeitura.objects.filter(
                materia=materia, expediente=expediente)
            initial['expediente'] = expediente
        else:
            ordem = OrdemDia.objects.get(id=self.kwargs['oid'])
            instance = RegistroLeitura.objects.filter(
                materia=materia, ordem=ordem)
            initial['ordem'] = ordem
        initial['instance'] = instance
        initial['user'] = self.request.user
        initial['ip'] = get_client_ip(self.request)
        return initial

    def form_valid(self, form):
        if self.expediente:
            model = ExpedienteMateria
        else:
            model = OrdemDia
        ordem_expediente = model.objects.get(id=self.kwargs['oid'])
        ordem_expediente.resultado = "Matéria lida"
        ordem_expediente.votacao_aberta = False
        ordem_expediente.votacao_aberta_pedido_prazo = False
        ordem_expediente.save()
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        page = ''
        if 'page' in self.request.GET:
            page = '?page={}'.format(self.request.GET['page'])

        pk = self.kwargs['pk']
        if self.expediente:
            url = reverse('sapl.sessao:expedientemateria_list',
                          kwargs={'pk': pk}) + page
        else:
            url = reverse('sapl.sessao:ordemdia_list',
                          kwargs={'pk': pk}) + page
        return url

    def cancel_url(self):
        page = ''
        if 'page' in self.request.GET:
            page = '?page={}'.format(self.request.GET['page'])
        url = reverse('sapl.sessao:retirar_leitura',
                      kwargs={
                          'pk': self.kwargs['pk'],
                          'iso': 1 if not self.expediente else 0,
                          'oid': self.kwargs['oid'],
                      },
                      ) + page
        return url


class ExpedienteLeituraView(AbstractLeituraView):
    expediente = True


class OrdemDiaLeituraView(AbstractLeituraView):
    expediente = False


@permission_required('sessao.change_expedientemateria',
                     'sessao.change_ordemdia')
def retirar_leitura(request, pk, iso, oid):
    page = ''
    if 'page' in request.GET:
        page = '?page={}'.format(request.GET['page'])

    is_ordem = bool(int(iso))
    if not is_ordem:
        ordem_expediente = ExpedienteMateria.objects.get(id=oid)
        RegistroLeitura.objects.filter(
            materia=ordem_expediente.materia, expediente=ordem_expediente).delete()
        succ_url = reverse('sapl.sessao:expedientemateria_list',
                           kwargs={'pk': pk}) + page
    else:
        ordem_expediente = OrdemDia.objects.get(id=oid)
        RegistroLeitura.objects.filter(
            materia=ordem_expediente.materia, ordem=ordem_expediente).delete()
        succ_url = reverse('sapl.sessao:ordemdia_list',
                           kwargs={'pk': pk}) + page
    ordem_expediente.resultado = ""
    ordem_expediente.votacao_aberta = False
    ordem_expediente.votacao_aberta_pedido_prazo = False
    ordem_expediente.save()
    return HttpResponseRedirect(succ_url)


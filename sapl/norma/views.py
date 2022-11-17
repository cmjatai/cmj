import logging
import re

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db.models.aggregates import Count
from django.http import JsonResponse
from django.http.response import Http404
from django.shortcuts import redirect, get_object_or_404
from django.urls.base import reverse
from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView, UpdateView, ListView
from django.views.generic.edit import FormView
from django_filters.views import FilterView

from cmj.mixins import BtnCertMixin
from sapl import settings
import sapl
from sapl.base.models import AppConfig
from sapl.compilacao.views import IntegracaoTaView
from sapl.crud.base import (RP_DETAIL, RP_LIST, Crud, CrudAux,
                            MasterDetailCrud, make_pagination)
from sapl.utils import show_results_filter_set, get_client_ip,\
    gerar_pdf_impressos

from .forms import (AnexoNormaJuridicaForm, NormaFilterSet, NormaJuridicaForm,
                    NormaPesquisaSimplesForm, NormaRelacionadaForm, AutoriaNormaForm)
from .models import (AnexoNormaJuridica, AssuntoNorma, NormaJuridica, NormaRelacionada,
                     TipoNormaJuridica, TipoVinculoNormaJuridica, AutoriaNorma, NormaEstatisticas)


# LegislacaoCitadaCrud = Crud.build(LegislacaoCitada, '')
AssuntoNormaCrud = CrudAux.build(AssuntoNorma, 'assunto_norma_juridica',
                                 list_field_names=['assunto', 'descricao'])

AssuntoNormaCrud.ListView.paginate_by = None

TipoNormaCrud = CrudAux.build(
    TipoNormaJuridica, 'tipo_norma_juridica',
    list_field_names=['sigla', 'descricao', 'equivalente_lexml'])
TipoVinculoNormaJuridicaCrud = CrudAux.build(
    TipoVinculoNormaJuridica, '',
    list_field_names=['sigla', 'descricao_ativa', 'descricao_passiva', 'revoga_integralmente'])


class NormaRelacionadaCrud(MasterDetailCrud):
    model = NormaRelacionada
    parent_field = 'norma_principal'
    help_topic = 'norma_juridica'

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['norma_relacionada', 'tipo_vinculo']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = NormaRelacionadaForm

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = NormaRelacionadaForm

        def get_initial(self):
            initial = super(UpdateView, self).get_initial()
            initial['tipo'] = self.object.norma_relacionada.tipo.id
            initial['numero'] = self.object.norma_relacionada.numero
            initial['ano'] = self.object.norma_relacionada.ano
            initial['ementa'] = self.object.norma_relacionada.ementa
            return initial

    class DetailView(MasterDetailCrud.DetailView):
        layout_key = 'NormaRelacionadaDetail'


class NormaDestaquesView(ListView):
    model = NormaJuridica
    template_name = 'norma/normajuridica_destaques.html'
    paginate_by = 1000

    def get_queryset(self):
        return NormaJuridica.objects.filter(norma_de_destaque=True).order_by('tipo__relevancia', '-data')

    @property
    def title(self):
        return 'Normas e Códigos de Destaque'


class NormaPesquisaView(FilterView):
    model = NormaJuridica
    filterset_class = NormaFilterSet
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset()

        qs = qs.extra({
            'nm_i': "CAST(regexp_replace(numero,'[^0-9]','', 'g') AS INTEGER)",
            'norma_letra': "regexp_replace(numero,'[^a-zA-Z]','', 'g')"
        }).order_by('-data', '-nm_i', 'norma_letra')

        return qs

    def get_context_data(self, **kwargs):
        context = super(NormaPesquisaView, self).get_context_data(**kwargs)

        context['title'] = _('Pesquisa de Normas Jurídicas')
        context['bg_title'] = 'bg-green text-white'

        self.filterset.form.fields['o'].label = _('Ordenação')

        qs = self.object_list
        if 'o' in self.request.GET and not self.request.GET['o']:
            qs = qs.order_by('-ano', 'tipo', '-numero')

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

        return context


class AnexoNormaJuridicaCrud(MasterDetailCrud):
    model = AnexoNormaJuridica
    parent_field = 'norma'
    help_topic = 'anexonormajuridica'
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['id', 'anexo_arquivo', 'assunto_anexo']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = AnexoNormaJuridicaForm
        layout_key = 'AnexoNormaJuridica'

        def get_initial(self):
            initial = super(MasterDetailCrud.CreateView, self).get_initial()
            initial['norma'] = NormaJuridica.objects.get(id=self.kwargs['pk'])
            return initial

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = AnexoNormaJuridicaForm
        layout_key = 'AnexoNormaJuridica'

        def get_initial(self):
            initial = super(UpdateView, self).get_initial()
            initial['norma'] = self.object.norma
            initial['anexo_arquivo'] = self.object.anexo_arquivo
            initial['assunto_anexo'] = self.object.assunto_anexo
            initial['ano'] = self.object.ano
            return initial

    class DetailView(MasterDetailCrud.DetailView):
        form_class = AnexoNormaJuridicaForm
        layout_key = 'AnexoNormaJuridica'


class NormaTaView(IntegracaoTaView):
    model = NormaJuridica
    model_type_foreignkey = TipoNormaJuridica
    map_fields = {
        'data': 'data',
        'ementa': 'ementa',
        'observacao': 'observacao',
        'numero': 'numero',
        'ano': 'ano',
        'tipo': 'tipo',
    }

    map_funcs = {
        'publicacao_func': True
    }

    def get(self, request, *args, **kwargs):
        """
        Para manter a app compilacao isolada das outras aplicações,
        este get foi implementado para tratar uma prerrogativa externa
        de usuário.
        """
        from sapl.compilacao.models import STATUS_TA_PUBLIC,\
            STATUS_TA_IMMUTABLE_PUBLIC

        if AppConfig.attr('texto_articulado_norma'):
            norma = get_object_or_404(self.model, pk=kwargs['pk'])

            response = super().get(request, *args, **kwargs)

            perm = self.object.has_view_permission(
                self.request, message=False) if self.object else None

            if perm is None:
                messages.error(self.request, _(
                    '''<strong>O Texto Articulado desta {} está em edição
                            ou ainda não foi cadastrado.</strong><br>{}
                        '''.format(
                        norma._meta.verbose_name,
                        '''
                            No entanto, sua consulta é possível da forma trivial através
                            do Arquivo Digitalizado abaixo.
                            ''' if norma.texto_integral else ''
                    )))

                return redirect(
                    reverse(
                        '{}:{}_detail'.format(
                            norma._meta.app_config.name,
                            norma._meta.model_name
                        ),
                        kwargs={'pk': norma.id}
                    ) + '?display'
                )

            return response
        else:
            return self.get_redirect_deactivated()


class NormaCrud(Crud):
    model = NormaJuridica
    help_topic = 'norma_juridica'
    public = [RP_DETAIL]

    class DetailView(BtnCertMixin, Crud.DetailView):

        layout_key = None

        def btn_check(self):

            btn = []
            if self.request.user.is_superuser:
                btn = [
                    '{}?{}check={}'.format(
                        reverse('sapl.norma:normajuridica_list'),
                        '' if not self.object.checkcheck else 'un',
                        self.object.pk
                    ),
                    'btn-warning',
                    _('UnCheck') if self.object.checkcheck else _('Check')
                ]

            return btn

        @property
        def extras_url(self):
            btns = [self.btn_check(), self.btn_certidao('texto_integral'), ]

            if self.request.user.has_perm('compilacao.add_textoarticulado'):
                if not self.object.texto_articulado.exists():
                    btns = btns + [(
                        reverse('sapl.norma:norma_ta',
                                kwargs={'pk': self.kwargs['pk']}),
                        'btn-primary',
                        _('Criar Texto Articulado')
                    )
                    ]
                elif self.request.user.is_superuser:
                    btns = btns + [(
                        reverse('sapl.compilacao:ta_delete',
                                kwargs={'pk': self.object.texto_articulado.first().pk}),
                        'btn-danger',
                        _('Excluir Texto Articulado')
                    )
                    ]

            btns = list(filter(None, btns))
            return btns

        def get(self, request, *args, **kwargs):
            if not 'display' in request.GET and not request.user.has_perm('norma.change_normajuridica') and \
                    self.get_object().texto_articulado.exists():
                return redirect(reverse('sapl.norma:norma_ta',
                                        kwargs={'pk': self.kwargs['pk']}))

            estatisticas_acesso_normas = AppConfig.objects.first().estatisticas_acesso_normas
            if estatisticas_acesso_normas == 'S':
                NormaEstatisticas.objects.create(usuario=str(self.request.user),
                                                 norma_id=kwargs['pk'],
                                                 ano=timezone.now().year,
                                                 horario_acesso=timezone.now())
            return super().get(request, *args, **kwargs)

        def hook_materia(self, obj):
            if obj.materia:
                return _('Matéria'), '<a href="{}">{}</a>'.format(
                    reverse(
                        'sapl.materia:materialegislativa_detail',
                        kwargs={'pk': obj.materia.id}
                    ),
                    obj.materia)
            else:
                return _('Matéria'), ''

    class DeleteView(Crud.DeleteView):

        def get_success_url(self):
            return self.search_url

    class CreateView(Crud.CreateView):
        form_class = NormaJuridicaForm

        logger = logging.getLogger(__name__)

        @property
        def cancel_url(self):
            return self.search_url

        def get_initial(self):
            initial = super().get_initial()

            initial['user'] = self.request.user
            initial['ip'] = get_client_ip(self.request)

            username = self.request.user.username
            try:
                self.logger.debug(
                    'user=' + username + '. Tentando obter objeto de modelo da esfera da federação.')
                esfera = sapl.base.models.AppConfig.objects.last(
                ).esfera_federacao
                initial['esfera_federacao'] = esfera
            except:
                self.logger.error(
                    'user=' + username + '. Erro ao obter objeto de modelo da esfera da federação.')
                pass
            initial['complemento'] = False
            return initial

        layout_key = 'NormaJuridicaCreate'

    class BaseMixin(Crud.BaseMixin):
        # 'has_texto_articulado')
        list_url = ''

        @property
        def list_field_names(self):
            if self.request.user.is_superuser:
                return ('epigrafe', 'ementa', 'checkcheck')
            else:
                return ('epigrafe', 'ementa')

        @property
        def search_url(self):
            namespace = self.model._meta.app_config.name
            return reverse('%s:%s' % (namespace, 'norma_pesquisa'))

    class ListView(Crud.ListView):  # , RedirectView):
        paginate_by = 100

        def get(self, request, *args, **kwargs):

            check = request.GET.get('check', '')
            uncheck = request.GET.get('uncheck', '')
            if request.user.is_superuser and (check or uncheck):
                try:
                    m = NormaJuridica.objects.get(pk=check or uncheck)
                except:
                    raise Http404
                else:
                    m.checkcheck = True if check else False
                    m.save()
                    return redirect('/norma/check')

            return Crud.ListView.get(self, request, *args, **kwargs)

        def get_queryset(self):
            qs = Crud.ListView.get_queryset(self)
            q = Q(
                checkcheck=False) | Q(
                    texto_articulado__privacidade=89) | Q(
                        texto_articulado__isnull=True, checkcheck=False) | Q(
                        texto_integral__exact='', checkcheck=True)
            qs = qs.filter(q)
            return qs.order_by('-ano', '-numero')

        def hook_ementa(self, obj, ss, url):
            return '''{}<br>{} - {}'''.format(
                obj.ementa,
                '<span class="text-danger">Sem Texto Articulado</span>' if not obj.texto_articulado.exists(
                ) or obj.texto_articulado.first().dispositivos_set.count() < 4 else '',
                '<span class="text-danger">Sem Arquivo</span>' if not obj.texto_integral else ''
            ), ''

        def hook_checkcheck(self, obj, ss, url):
            return 'uncheck' if obj.checkcheck else 'check', f'/norma/check?{"un" if obj.checkcheck else ""}check={obj.id}'

        def hook_header_checkcheck(self):
            return force_text(_('Check'))

        def hook_header_epigrafe(self):
            return force_text(_('Epigrafe'))

        def get_context_data(self, **kwargs):
            context = Crud.ListView.get_context_data(self, **kwargs)

            context['title'] = 'Checagem de Registro das Normas Jurídicas'
            return context

        @classmethod
        def get_url_regex(cls):
            return r'^/check$'

    class UpdateView(Crud.UpdateView):
        form_class = NormaJuridicaForm

        layout_key = 'NormaJuridicaCreate'

        def get_initial(self):
            initial = super().get_initial()
            norma = NormaJuridica.objects.get(id=self.kwargs['pk'])
            if norma.materia:
                initial['tipo_materia'] = norma.materia.tipo
                initial['ano_materia'] = norma.materia.ano
                initial['numero_materia'] = norma.materia.numero
                initial['esfera_federacao'] = norma.esfera_federacao
            return initial

        def form_valid(self, form):
            norma_antiga = NormaJuridica.objects.get(
                pk=self.kwargs['pk']
            )

            # Feito desta forma para que sejam materializados os assuntos
            # antigos
            assuntos_antigos = set(norma_antiga.assuntos.all())

            dict_objeto_antigo = norma_antiga.__dict__
            self.object = form.save()
            dict_objeto_novo = self.object.__dict__

            atributos = ['tipo_id', 'numero', 'ano', 'data', 'esfera_federacao',
                         'complemento', 'materia_id', 'numero',
                         'data_publicacao', 'data_vigencia', 'ementa', 'indexacao',
                         'observacao', 'texto_integral']

            for atributo in atributos:
                if dict_objeto_antigo[atributo] != dict_objeto_novo[atributo]:
                    self.object.user = self.request.user
                    self.object.ip = get_client_ip(self.request)
                    self.object.save()
                    break

            # Campo Assuntos não veio no __dict__, então é comparado
            # separadamente
            assuntos_novos = set(self.object.assuntos.all())
            if assuntos_antigos != assuntos_novos:
                self.object.user = self.request.user
                self.object.ip = get_client_ip(self.request)
                self.object.save()

            return super().form_valid(form)


def recuperar_norma(request):
    logger = logging.getLogger(__name__)
    username = request.user.username

    tipo = TipoNormaJuridica.objects.get(pk=request.GET['tipo'])
    numero = request.GET['numero']
    ano = request.GET['ano']

    try:
        logger.info('user=' + username + '. Tentando obter NormaJuridica (tipo={}, ano={}, numero={}).'
                    .format(tipo, ano, numero))
        norma = NormaJuridica.objects.get(tipo=tipo,
                                          ano=ano,
                                          numero=numero)
        response = JsonResponse({'ementa': norma.ementa,
                                 'id': norma.id})
    except ObjectDoesNotExist:
        logger.error('user=' + username + '. NormaJuridica buscada (tipo={}, ano={}, numero={}) não existe. '
                     'Definida com ementa vazia e id 0.'.format(tipo, ano, numero))
        response = JsonResponse({'ementa': '', 'id': 0})

    return response


def recuperar_numero_norma(request):
    tipo = TipoNormaJuridica.objects.get(pk=request.GET['tipo'])
    ano = request.GET.get('ano', '')
    param = {'tipo': tipo,
             'ano': ano if ano else timezone.now().year
             }
    norma = NormaJuridica.objects.filter(**param).order_by(
        'tipo', 'ano', 'numero').values_list('numero', flat=True)
    if norma:
        numeros = sorted([int(re.sub("[^0-9].*", '', n)) for n in norma])
        next_num = numeros.pop() + 1
        response = JsonResponse({'numero': next_num,
                                 'ano': param['ano']})
    else:
        response = JsonResponse(
            {'numero': 1, 'ano': param['ano']})

    return response


class AutoriaNormaCrud(MasterDetailCrud):
    model = AutoriaNorma
    parent_field = 'norma'
    help_topic = 'despacho_autoria'
    public = [RP_LIST, RP_DETAIL]
    list_field_names = ['autor', 'autor__tipo__descricao', 'primeiro_autor']

    class LocalBaseMixin():
        form_class = AutoriaNormaForm

        @property
        def layout_key(self):
            return None

    class CreateView(LocalBaseMixin, MasterDetailCrud.CreateView):

        def get_initial(self):
            initial = super().get_initial()
            norma = NormaJuridica.objects.get(id=self.kwargs['pk'])
            initial['data_relativa'] = norma.data
            initial['autor'] = []
            return initial

    class UpdateView(LocalBaseMixin, MasterDetailCrud.UpdateView):

        def get_initial(self):
            initial = super().get_initial()
            initial.update({
                'data_relativa': self.object.norma.data_apresentacao,
                'tipo_autor': self.object.autor.tipo.id,
            })
            return initial


class ImpressosView(PermissionRequiredMixin, TemplateView):
    template_name = 'materia/impressos/impressos.html'
    permission_required = ('materia.can_access_impressos', )


class NormaPesquisaSimplesView(PermissionRequiredMixin, FormView):
    form_class = NormaPesquisaSimplesForm
    template_name = 'materia/impressos/impressos_form.html'
    permission_required = ('materia.can_access_impressos', )

    def form_valid(self, form):
        template_norma = 'materia/impressos/normas_pdf.html'

        titulo = form.cleaned_data['titulo']

        kwargs = {}
        if form.cleaned_data.get('tipo_norma'):
            kwargs.update({'tipo': form.cleaned_data['tipo_norma']})

        if form.cleaned_data.get('data_inicial'):
            kwargs.update({'data__gte': form.cleaned_data['data_inicial'],
                           'data__lte': form.cleaned_data['data_final']})

        normas = NormaJuridica.objects.filter(
            **kwargs).order_by('-numero', 'ano')

        quantidade_normas = normas.count()
        normas = normas[:2000] if quantidade_normas > 2000 else normas

        context = {'quantidade': quantidade_normas,
                   'titulo': titulo,
                   'normas': normas}

        return gerar_pdf_impressos(self.request, context, template_norma)

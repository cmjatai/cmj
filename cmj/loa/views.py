from decimal import Decimal
import logging

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.db.models.aggregates import Sum
from django.http.response import Http404
from django.shortcuts import redirect
from django.template import loader
from django.urls.base import reverse_lazy
from django.utils import formats
from django.utils.translation import gettext_lazy as _
from django_filters.views import FilterView

from cmj.core.models import AuditLog
from cmj.loa.forms import LoaForm, EmendaLoaForm, OficioAjusteLoaForm,\
    RegistroAjusteLoaForm, EmendaLoaFilterSet
from cmj.loa.models import Loa, EmendaLoa, EmendaLoaParlamentar, OficioAjusteLoa,\
    RegistroAjusteLoa, RegistroAjusteLoaParlamentar, EmendaLoaRegistroContabil
from sapl.crud.base import Crud, MasterDetailCrud, RP_DETAIL, RP_LIST
from sapl.parlamentares.models import Parlamentar


class LoaContextDataMixin:

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        path = context.get('path', '')
        context['path'] = f'{path} container-loa'
        return context


class LoaCrud(Crud):
    model = Loa
    public = [RP_LIST, RP_DETAIL]
    ordered_list = False
    frontend = Loa._meta.app_label

    class BaseMixin(LoaContextDataMixin, Crud.BaseMixin):

        @property
        def list_field_names(self):
            list_field_names = [
                'ano',
                'receita_corrente_liquida',
                ('disp_total', 'perc_disp_total'),
                ('disp_saude', 'perc_disp_saude'),
                ('disp_diversos', 'perc_disp_diversos'),
            ]

            if not self.request.user.is_anonymous:
                list_field_names.append('publicado')
            return list_field_names

        @property
        def list_url(self):
            url = super().list_url
            if self.request.user.is_anonymous:
                c = Loa.objects.filter(publicado=True).count()
                return url if c > 1 else ''
            return url

    class ListView(Crud.ListView):
        ordered_list = False

        def get(self, request, *args, **kwargs):
            response = super().get(request, *args, **kwargs)

            if self.object_list.count() == 1:
                loa = self.object_list.first()
                return redirect(to=reverse_lazy('cmj.loa:loa_detail',
                                                kwargs={'pk': loa.pk}))
            return response

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            path = context.get('path', '')
            context['path'] = f'{path} loa-list'
            return context

        def get_queryset(self):
            qs = super().get_queryset()

            u = self.request.user

            qsp = qs.filter(publicado=True)
            if u.is_anonymous:
                return qsp

            if u.has_perm('loa.emendaloa_full_editor'):
                return qs

            if u.operadorautor_set.exists():
                qs = qs.filter(
                    Q(materia__normajuridica__isnull=True) | Q(publicado=True)
                ).distinct()
                return qs

            return qsp

        def hook_header_perc_disp_total(self):
            return ''

        def hook_header_perc_disp_saude(self):
            return ''

        def hook_header_perc_disp_diversos(self):
            return ''

        def hook_receita_corrente_liquida(self, *args, **kwargs):
            l = args[0]

            return args[1] if l.ano >= 2023 else '', args[2]

        def hook_ano(self, *args, **kwargs):
            l = args[0]
            return f'LOA {args[1]}', args[2]

        def hook_perc_disp_total(self, *args, **kwargs):
            l = args[0]
            return f' <i>({l.perc_disp_total:3.1f}%)</i>', ''

        def hook_perc_disp_saude(self, *args, **kwargs):
            l = args[0]
            return f' <i>({l.perc_disp_saude:3.1f}%)</i>', ''

        def hook_perc_disp_diversos(self, *args, **kwargs):
            l = args[0]
            return f' <i>({l.perc_disp_diversos:3.1f}%)</i>', ''

    class CreateView(Crud.CreateView):
        form_class = LoaForm

        def form_invalid(self, form):
            r = Crud.CreateView.form_invalid(self, form)

            err_materia = form.errors.get('materia', None)
            if err_materia:
                err_materia = 'Já existe Loa vinculada a Matéria Legislativa selecionada.'

                self.messages.error(err_materia, fail_silently=True)
            return r

    class UpdateView(Crud.UpdateView):
        form_class = LoaForm

        def get_initial(self):
            initial = super().get_initial()
            if self.object.materia:
                initial['tipo_materia'] = self.object.materia.tipo.id
                initial['numero_materia'] = self.object.materia.numero
                initial['ano_materia'] = self.object.materia.ano
            return initial

        def form_invalid(self, form):
            r = Crud.UpdateView.form_invalid(self, form)

            err_materia = form.errors.get('materia', None)
            if err_materia:
                err_materia = 'Já existe Loa vinculada a Matéria Legislativa selecionada.'

                self.messages.error(err_materia, fail_silently=True)
            return r

    class DetailView(Crud.DetailView):
        layout_key = 'LoaDetail'

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            path = context.get('path', '')
            context['path'] = f'{path} loa-detail'
            return context

        def get(self, request, *args, **kwargs):

            pk = int(kwargs['pk'])
            if pk <= 2022:
                self.layout_key = 'LoaDetailATE2022'

            response = super().get(request, *args, **kwargs)
            if not self.object.publicado and request.user.is_anonymous:
                raise Http404
            return response

        def hook_materia_ou_norma(self, l, verbose_name='', field_display=''):
            if l.materia:
                nj = l.materia.normajuridica()
                if not nj:
                    get_column = self.get_column(
                        'materia|fk_urlize_for_detail', '')
                    return get_column['verbose_name'], get_column['text']

                return 'Norma Jurídica', f'''
                    <a href="{reverse_lazy(
                    'sapl.norma:normajuridica_detail',
                    kwargs={'pk': nj.id})}">{nj}</a>
                '''

            return verbose_name, field_display

        def hook_materia(self, l, verbose_name='', field_display=''):
            if l.materia:
                strm = str(l.materia)
                field_display = field_display.replace(
                    strm, l.materia.epigrafe_short)
            return verbose_name, field_display

        def hook_disp_total(self, l, verbose_name='', field_display=''):
            return verbose_name, f'{field_display} <em>({l.perc_disp_total:3.1f}%)</em>'

        def hook_disp_saude(self, l, verbose_name='', field_display=''):
            return verbose_name, f'{field_display} <em>({l.perc_disp_saude:3.1f}%)</em>'

        def hook_disp_diversos(self, l, verbose_name='', field_display=''):
            return verbose_name, f'{field_display} <em>({l.perc_disp_diversos:3.1f}%)</em>'

        def hook_resumo_emendas_impositivas(self, *args, **kwargs):
            l = args[0]

            template = loader.get_template('loa/loaparlamentar_set_list.html')

            loaparlamentares = l.loaparlamentar_set.order_by(
                'parlamentar__nome_parlamentar')

            resumo_emendas_impositivas = []

            totais = {}

            for lp in loaparlamentares:

                resumo_parlamentar = {'loaparlamentar': lp}
                for k, v in EmendaLoa.TIPOEMENDALOA_CHOICE:
                    resumo_parlamentar[k] = {
                        'name': v
                    }

                    if k not in totais:
                        totais[k] = dict(
                            ja_destinado=Decimal('0.00'),
                            impedimento_tecnico=Decimal('0.00'),
                            sem_destinacao=Decimal('0.00'),
                        )

                    if k == EmendaLoa.SAUDE:
                        resumo_parlamentar[k]['sem_destinacao'] = lp.disp_saude
                    elif k == EmendaLoa.DIVERSOS:
                        resumo_parlamentar[k]['sem_destinacao'] = lp.disp_diversos

                    resumo_parlamentar[k]['impedimento_tecnico'] = 0
                    resumo_parlamentar[k]['ja_destinado'] = 0

                    params = dict(
                        parlamentar=lp.parlamentar,
                        emendaloa__loa=self.object,
                        emendaloa__tipo=k
                    )

                    ja_destinado = EmendaLoaParlamentar.objects.filter(
                        **params
                        #).exclude(
                        #    emendaloa__fase=EmendaLoa.IMPEDIMENTO_TECNICO
                    ).aggregate(Sum('valor'))

                    resumo_parlamentar[k]['ja_destinado'] = (
                        ja_destinado['valor__sum'] or Decimal('0.00')
                    )

                    ajustes = RegistroAjusteLoaParlamentar.objects.filter(
                        parlamentar=lp.parlamentar,
                        registro__tipo=k,
                        registro__oficio_ajuste_loa__loa=l,
                    ).aggregate(Sum('valor'))

                    resumo_parlamentar[k]['ja_destinado'] += (
                        ajustes['valor__sum'] or Decimal('0.00')
                    )

                    # ------------------------------------

                    params.update(
                        dict(emendaloa__fase=EmendaLoa.IMPEDIMENTO_TECNICO))
                    impedimento_tecnico = EmendaLoaParlamentar.objects.filter(
                        **params).aggregate(Sum('valor'))
                    resumo_parlamentar[k]['impedimento_tecnico'] = (
                        impedimento_tecnico['valor__sum'] or Decimal('0.00')
                    )

                    ajuste_de_impedimento = RegistroAjusteLoaParlamentar.objects.filter(
                        parlamentar=lp.parlamentar,
                        registro__emendaloa__tipo=k,
                        registro__oficio_ajuste_loa__loa=l,
                        registro__emendaloa__fase=EmendaLoa.IMPEDIMENTO_TECNICO
                    ).aggregate(Sum('valor'))

                    resumo_parlamentar[k]['impedimento_tecnico'] += (
                        ajuste_de_impedimento['valor__sum'] or Decimal('0.00')
                    )

                    resumo_parlamentar[k]['sem_destinacao'] -= (
                        resumo_parlamentar[k]['ja_destinado'] -
                        resumo_parlamentar[k]['impedimento_tecnico']
                    )

                    '''
                    params.update(
                        dict(emendaloa__fase=EmendaLoa.IMPEDIMENTO_TECNICO))
                    impedimento_tecnico = EmendaLoaParlamentar.objects.filter(
                        **params).aggregate(Sum('valor'))

                    resumo_parlamentar[k]['impedimento_tecnico'] = (
                        impedimento_tecnico['valor__sum'] or Decimal('0.00')
                    )

                    ajuste_remanescente = RegistroAjusteLoaParlamentar.objects.filter(
                        parlamentar=lp.parlamentar,
                        registro__oficio_ajuste_loa__loa=l,
                        registro__tipo=k,
                    ).exclude(
                        registro__emendaloa__fase=EmendaLoa.IMPEDIMENTO_TECNICO
                    ).aggregate(Sum('valor'))

                    ajuste_de_impedimento = RegistroAjusteLoaParlamentar.objects.filter(
                        parlamentar=lp.parlamentar,
                        registro__emendaloa__tipo=k,
                        registro__oficio_ajuste_loa__loa=l,
                        registro__emendaloa__fase=EmendaLoa.IMPEDIMENTO_TECNICO
                    ).aggregate(Sum('valor'))

                    resumo_parlamentar[k]['impedimento_tecnico'] += (
                        ajuste_de_impedimento['valor__sum'] or Decimal('0.00')
                    )

                    resumo_parlamentar[k]['ja_destinado'] += (
                        ajuste_remanescente['valor__sum'] or Decimal('0.00')
                    )

                    resumo_parlamentar[k]['sem_destinacao'] = \
                        resumo_parlamentar[k]['sem_destinacao'] - \
                        resumo_parlamentar[k]['ja_destinado'] - \
                        resumo_parlamentar[k]['impedimento_tecnico']
                    '''
                    totais[k]['ja_destinado'] += resumo_parlamentar[k]['ja_destinado']
                    totais[k]['impedimento_tecnico'] += resumo_parlamentar[k]['impedimento_tecnico']
                    totais[k]['sem_destinacao'] += resumo_parlamentar[k]['sem_destinacao']

                resumo_emendas_impositivas.append(resumo_parlamentar)

            is_us = self.request.user.is_superuser

            t10 = EmendaLoa.SAUDE
            t99 = EmendaLoa.DIVERSOS
            # dsjd display_saude_ja_destinado
            dsjd = 1 if totais[t10]['ja_destinado'] or is_us else 0
            dsit = 1 if totais[t10]['impedimento_tecnico'] or is_us else 0
            dssd = 1 if totais[t10]['sem_destinacao'] or is_us else 0

            # ddjd display_diversos_ja_destinado
            ddjd = 1 if totais[t99]['ja_destinado'] or is_us else 0
            ddit = 1 if totais[t99]['impedimento_tecnico'] or is_us else 0
            ddsd = 1 if totais[t99]['sem_destinacao'] or is_us else 0

            context = dict(
                resumo_emendas_impositivas=resumo_emendas_impositivas,
                columns=dict(
                    saude=dict(
                        num_columns=dsjd + dsit + dssd,
                        ja_destinado='Valores<br>Já Destinados' if dsjd else '',
                        impedimento_tecnico='Impedimentos<br>Técnicos' if dsit else '',
                        sem_destinacao=(
                            'Sem Destinação' if not l.materia or l.materia and not l.materia.normajuridica() else 'Remanescente') if dssd else '',
                    ),
                    diversos=dict(
                        num_columns=ddjd + ddit + ddsd,
                        ja_destinado='Valores<br>Já Destinados' if ddjd else '',
                        impedimento_tecnico='Impedimentos<br>Técnicos' if ddit else '',
                        sem_destinacao=(
                            'Sem Destinação' if not l.materia or l.materia and not l.materia.normajuridica() else 'Remanescente') if ddsd else '',
                    )
                )
            )

            rendered = template.render(context, self.request)

            return 'Resumo Geral das Emendas Impositivas Parlamentares', rendered


class EmendaLoaCrud(MasterDetailCrud):
    model = EmendaLoa
    parent_field = 'loa'
    public = [RP_LIST, RP_DETAIL]
    frontend = EmendaLoa._meta.app_label

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        list_field_names = [
            ('finalidade', 'materia'),
            'valor_computado',
            ('tipo', 'fase'),
            'parlamentares'
        ]

        @property
        def create_url(self):
            url = super().create_url
            if not url and \
                    not self.request.user.is_anonymous and (
                    self.request.user.operadorautor_set.exists() or
                    self.request.user.is_superuser
                    ):
                url = self.resolve_url('create', args=(self.kwargs['pk'],))
            return url

        @property
        def update_url(self):

            url = super().update_url
            if url or self.request.user.is_anonymous:
                return url

            if self.request.user.has_perm('loa.emendaloa_full_editor') or \
                    self.request.user.operadorautor_set.exists():
                url = self.resolve_url('update', args=(self.object.id,))

            return url

        @property
        def detail_url(self):

            url = super().update_url
            if url or self.request.user.is_anonymous:
                return url

            if self.request.user.has_perm('loa.emendaloa_full_editor') or \
                    self.request.user.operadorautor_set.exists():
                url = self.resolve_url('detail', args=(self.object.id,))

            return url

        @property
        def layout_display(self):
            l = super().layout_display

            if not self.object.materia:
                l.pop()

            return l

    class ListView(FilterView, MasterDetailCrud.ListView):
        filterset_class = EmendaLoaFilterSet
        paginate_by = 25
        ordered_list = False

        def get(self, request, *args, **kwargs):
            self.loa = Loa.objects.get(pk=kwargs['pk'])
            return FilterView.get(self, request, *args, **kwargs)

        def get_filterset_kwargs(self, filterset_class):
            kw = FilterView.get_filterset_kwargs(self, filterset_class)
            kw['loa'] = self.loa
            return kw

        def get_queryset(self):
            qs = super().get_queryset()
            if self.request.user.is_anonymous:
                qs = qs.filter(loa__publicado=True)
            return qs.order_by('fase', 'id')

        def get_context_data(self, **kwargs):
            context = MasterDetailCrud.ListView.get_context_data(
                self, **kwargs)
            path = context.get('path', '')
            context['path'] = f'{path} emendaloa-list'

            return context

        def hook_header_valor_computado(self, *args, **kwargs):
            return 'Valor Final da Emenda' if self.loa.publicado else 'Valor da Emenda'

        def hook_valor_computado(self, *args, **kwargs):
            return f'<div class="text-nowrap text-center">R$ {args[1]}</div>', args[2]

        def hook_tipo(self, *args, **kwargs):
            el = args[0]
            link_pdf = ''
            if el.fase == EmendaLoa.LIBERACAO_CONTABIL and not el.materia:
                url = reverse_lazy(
                    'sapl.api:loa_emendaloa-view',
                    kwargs={'pk': el.id})

                link_pdf = f'<a href="{url}"><i class="far fa-2x fa-file-pdf"></i></a>'

            return f'{link_pdf}<br>{args[1]}', args[2]

        def hook_fase(self, *args, **kwargs):
            return f'<br><small class="text-nowrap">({args[0].get_fase_display()})</small>', args[2]

        def hook_materia(self, *args, **kwargs):
            if args[0].materia:
                return f'<small class="text-gray"><strong>Matéria Legislativa:</strong> {args[0].materia}<br><i>{args[0].materia.ementa}</i></small>', args[2]
            else:
                return '', args[2]

        def hook_parlamentares(self, *args, **kwargs):
            pls = []

            for elp in args[0].emendaloaparlamentar_set.all():
                pls.append(
                    '<tr><td>{}</td><td align="right">R$ {}</td></tr>'.format(
                        elp.parlamentar.nome_parlamentar,
                        formats.number_format(elp.valor, force_grouping=True)
                    )
                )

            ajustes = []
            for ajuste in args[0].registroajusteloa_set.all():
                url = reverse_lazy(
                    'cmj.loa:oficioajusteloa_detail',
                    kwargs={'pk': ajuste.oficio_ajuste_loa.id})

                descr = ''
                # if ajuste.valor <= Decimal('0.00'):
                descr = ajuste.descricao

                ajustes.append(
                    f'<li><a href="{url}">{ajuste}</a><small class="text-gray"><br>{descr}</small></li>')

            ajustes = "".join(ajustes)
            if ajustes:
                ajustes = f'''
                    <hr class="my-1">
                    <small class="px-2 d-block">
                        <strong>Registros de Ajuste Técnico</strong>
                        <ul class="pl-3  m-0">{ajustes}</ul>
                    </small>
                '''

            return f'''
                    <table class="w-100 text-nowrap">{"".join(pls)}</table>
                    {ajustes}
                    ''', ''

    class CreateView(MasterDetailCrud.CreateView):
        layout_key = None
        form_class = EmendaLoaForm

        def get_success_url(self):
            return self.update_url

        @property
        def cancel_url(self):
            url = super().cancel_url
            if not url and self.request.user.operadorautor_set.exists():
                url = self.resolve_url(
                    'list', args=(self.kwargs['pk'],))
            return url

        def has_permission(self):

            u = self.request.user
            if u.is_anonymous:
                return False

            has_perm = MasterDetailCrud.CreateView.has_permission(self)

            self.loa = Loa.objects.get(pk=self.kwargs['pk'])

            if not has_perm:
                return u.operadorautor_set.exists() and not self.loa.publicado

            return has_perm

        def get_initial(self):
            initial = super().get_initial()
            initial['loa'] = self.loa
            initial['user'] = self.request.user
            initial['creating'] = True
            return initial

        def form_invalid(self, form):
            r = MasterDetailCrud.CreateView.form_invalid(self, form)

            err_materia = form.errors.get('materia', None)
            if err_materia:
                err_materia = 'Já existe registro de valores para a Matéria Legislativa selecionada.'

                self.messages.error(err_materia, fail_silently=True)
            return r

    class UpdateView(MasterDetailCrud.UpdateView):
        layout_key = None
        form_class = EmendaLoaForm
        permission_required = ('loa.emendaloa_full_editor', )

        def get_context_data(self, **kwargs):
            self.loa = Loa.objects.get(pk=kwargs['root_pk'])
            context = super().get_context_data(**kwargs)
            path = context.get('path', '')
            context['path'] = f'{path} emendaloa-update'
            return context

        def get_success_url(self):
            return MasterDetailCrud.UpdateView.get_success_url(self)

        def post(self, request, *args, **kwargs):
            u = request.user
            if not u.is_superuser and not u.is_anonymous:
                if u.operadorautor_set.exists():
                    if self.object.fase > EmendaLoa.PROPOSTA_LIBERADA and \
                    self.object.fase != EmendaLoa.LIBERACAO_CONTABIL:
                        messages.warning(
                            request, f'A Emenda está na fase de "{self.object.get_fase_display()}". Não pode ser editada por usuário de autoria.')
                        return redirect(self.detail_url)

            return MasterDetailCrud.UpdateView.post(self, request, *args, **kwargs)

        def get(self, request, *args, **kwargs):
            u = request.user
            if not u.is_superuser and not u.is_anonymous:
                if u.operadorautor_set.exists():
                    if self.object.fase > EmendaLoa.PROPOSTA_LIBERADA and \
                    self.object.fase != EmendaLoa.LIBERACAO_CONTABIL:
                        messages.warning(
                            request, f'A Emenda está na fase de "{self.object.get_fase_display()}". Não pode ser editada por usuário de autoria.')
                        return redirect(self.detail_url)

                # if u.has_perm('loa.emendaloa_full_editor'):
                #    if self.object.fase < EmendaLoa.PROPOSTA_LIBERADA:
                #        messages.warning(
                #            request, f'A Emenda está na fase de "{self.object.get_fase_display()}". Não liberada para edição contábil.')
                #        return redirect(self.detail_url)

            return MasterDetailCrud.UpdateView.get(self, request, *args, **kwargs)

        def has_permission(self):
            u = self.request.user
            if u.is_anonymous:
                return False

            has_perm = MasterDetailCrud.UpdateView.has_permission(self)

            self.object = self.get_object() if not hasattr(self, 'object') else self.object

            if not has_perm:
                # 1) possui permissão: emendaloa_full_editor
                # 2) é um usuário operador de autor
                # 3) a emenda em edição está na fase de Proposta Legislativa
                # 4) participa da emenda
                # (1 or 2) e 3 e 4

                participa = False
                if u.operadorautor_set.exists():
                    parlamentar = u.operadorautor_set.first().autor.autor_related
                    if isinstance(parlamentar, Parlamentar):
                        participa = self.object.emendaloaparlamentar_set.filter(
                            parlamentar=parlamentar).exists()

                return (
                    u.has_perm('loa.emendaloa_full_editor') and
                    not self.object.materia
                ) or (
                    u.operadorautor_set.exists() and
                    not self.object.materia and
                    participa
                )

            return has_perm

        def get_initial(self):
            initial = super().get_initial()
            initial['loa'] = self.object.loa
            initial['user'] = self.request.user
            initial['creating'] = False
            if self.object.materia:
                initial['tipo_materia'] = self.object.materia.tipo.id
                initial['numero_materia'] = self.object.materia.numero
                initial['ano_materia'] = self.object.materia.ano
            return initial

        @property
        def cancel_url(self):
            url = self.resolve_url('detail', args=(self.kwargs['pk'],))
            return url

    class DetailView(MasterDetailCrud.DetailView):

        @property
        def layout_key(self):
            return 'EmendaLoaDetail'

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            path = context.get('path', '')
            context['path'] = f'{path} emendaloa-detail'
            return context

        def hook_valor_computado(self, el, verbose_name='', field_display=''):
            if not el.materia:
                return '', ''

            return 'Valor Final da Emenda (R$)', field_display

        def hook_materia(self, el, verbose_name='', field_display=''):
            if el.materia:
                strm = str(el.materia)
                field_display = field_display.replace(
                    strm, el.materia.epigrafe_short)
            return verbose_name, field_display

        def hook_registroajusteloa_set(self, el, verbose_name='', field_display=''):

            if not el.materia:
                return '', ''

            ajustes = []
            for ajuste in el.registroajusteloa_set.all():
                url = reverse_lazy(
                    'cmj.loa:registroajusteloa_detail',
                    kwargs={'pk': ajuste.id})

                a_str = f"""
                    <li>
                        <a href="{url}">
                            {ajuste}
                        </a>
                    </li>
                """
                ajustes.append(a_str)

            return verbose_name, f'<ul>{"".join(ajustes)}</ul>'

        def hook_documentos_acessorios(self, el, verbose_name='', field_display=''):

            if not el.materia:
                return '', ''

            docs = []

            qs_docs = [
            ] if not el.materia else el.materia.documentoacessorio_set.order_by('-id')
            for doc in qs_docs:
                doc_template = loader.get_template(
                    'materia/documentoacessorio_widget_itemlist.html')
                context = {}
                context['object'] = doc
                rendered = doc_template.render(context, self.request)

                docs.append(
                    f'<tr><td>{rendered}</td></tr>'
                )

            return 'Documentos da Adicionados à Emenda Impositiva', f'''
                <div class="container-table">
                    <table class="table table-form table-bordered table-hover w-100">
                        {"".join(docs)}
                    </table>
                </div>
                '''

        def hook_parlamentares(self, emendaloa, verbose_name='', field_display=''):
            pls = []

            for elp in emendaloa.emendaloaparlamentar_set.all():
                pls.append(
                    '<tr><td>{}</td><td align="right">R$ {}</td></tr>'.format(
                        elp.parlamentar.nome_parlamentar,
                        formats.number_format(elp.valor, force_grouping=True)
                    )
                )

            return verbose_name, f'''
                <div class="py-3">
                    <table class="table table-form table-bordered table-hover w-100">
                        {"".join(pls)}
                    </table>
                </div>
                '''

        def hook_auditlog(self, emendaloa, verbose_name='', field_display=''):
            if not self.request.user.is_superuser:
                return '', ''
            cts = list(
                ContentType.objects.get_for_models(
                    EmendaLoa,
                    EmendaLoaRegistroContabil,
                    EmendaLoaParlamentar).values()
            )

            al_create = AuditLog.objects.filter(
                content_type=cts[0],
                object_id=emendaloa.id,
            ).order_by('id').first()
            if not al_create:
                return '', ''

            q = Q()
            q |= Q(obj_id=emendaloa.id, model_name='emendaloa')
            q |= Q(obj__0__fields__emendaloa=emendaloa.id)
            models_name = list(map(lambda ct: ct.model, cts))
            als = AuditLog.objects.filter(
                q, model_name__in=models_name).order_by('id')

            result = dict(
                emendaloa=[],
                emendaloaparlamentar=[],
                emendaloaregistrocontabil=[]
            )

            last_fields = dict(
                emendaloa=None,
                emendaloaparlamentar=None,
                emendaloaregistrocontabil=None
            )

            for al in als:

                fields = al.obj[0]["fields"]

                if fields != last_fields[al.model_name] or al.operation in ('C', 'D'):
                    result[al.model_name].append(al)
                    last_fields[al.model_name] = fields

            results = []
            for k, als in result.items():
                results.extend(als)

            results = sorted(results, key=lambda al: -al.id)

            lines = []
            for al in results:
                lines.append(
                    f'{al.timestamp} - {al.operation} - '
                    f'{al.content_type} - {al.user} - {al.obj[0]["pk"]} - {al.obj[0]["fields"]}<br>')

            return verbose_name, ''.join(lines)


class OficioAjusteLoaCrud(MasterDetailCrud):
    model = OficioAjusteLoa
    parent_field = 'loa'
    model_set = 'registroajusteloa_set'
    public = [RP_LIST, RP_DETAIL]
    frontend = OficioAjusteLoa._meta.app_label

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        list_field_names = [
            'epigrafe', 'parlamentares'
        ]

    class CreateView(MasterDetailCrud.CreateView):
        form_class = OficioAjusteLoaForm

        def get_initial(self):
            initial = super().get_initial()
            initial['loa'] = Loa.objects.get(pk=self.kwargs['pk'])
            return initial

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = OficioAjusteLoaForm

        def get_initial(self):
            initial = super().get_initial()
            initial['loa'] = self.object.loa
            return initial

    class ListView(MasterDetailCrud.ListView):
        ordering = 'epigrafe'
        paginate_by = 25

        def get_queryset(self):
            return MasterDetailCrud.ListView.get_queryset(self)

    class DetailView(MasterDetailCrud.DetailView):
        template_name = 'loa/oficioajusteloa_detail.html'
        paginate_by = 100

        @property
        def list_field_names_set(self):
            return 'descricao', 'str_valor', 'tipo'  # , 'emendaloa'

        def hook_header_str_valor(self):
            return 'Valor (R$)'

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            path = context.get('path', '')
            context['path'] = f'{path} oficioajusteloa-detail'
            return context


class RegistroAjusteLoaCrud(MasterDetailCrud):
    model = RegistroAjusteLoa
    parent_field = 'oficio_ajuste_loa__loa'
    public = [RP_LIST, RP_DETAIL]
    frontend = RegistroAjusteLoa._meta.app_label

    class DetailView(MasterDetailCrud.DetailView):
        layout_key = 'RegistroAjusteLoaDetail'

        @property
        def detail_list_url(self):
            return reverse_lazy(
                'cmj.loa:oficioajusteloa_detail',
                kwargs={'pk': self.object.oficio_ajuste_loa_id})

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = RegistroAjusteLoaForm

        def get_initial(self):
            initial = super().get_initial()
            initial['oficioajusteloa'] = self.object.oficio_ajuste_loa
            return initial

        @property
        def cancel_url(self):
            return reverse_lazy(
                'cmj.loa:oficioajusteloa_detail',
                kwargs={'pk': self.kwargs['pk']})

    class CreateView(MasterDetailCrud.CreateView):
        form_class = RegistroAjusteLoaForm

        def get_initial(self):
            initial = super().get_initial()
            initial['oficioajusteloa'] = OficioAjusteLoa.objects.get(
                pk=self.kwargs['pk'])
            return initial

        @property
        def cancel_url(self):
            return reverse_lazy(
                'cmj.loa:oficioajusteloa_detail',
                kwargs={'pk': self.kwargs['pk']})

        def get_success_url(self):
            return reverse_lazy(
                'cmj.loa:oficioajusteloa_detail',
                kwargs={'pk': self.kwargs['pk']})

    class DeleteView(MasterDetailCrud.DeleteView):

        def get_success_url(self):
            return reverse_lazy(
                'cmj.loa:oficioajusteloa_detail',
                kwargs={'pk': self.object.oficio_ajuste_loa.id})

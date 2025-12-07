from decimal import ROUND_DOWN, Decimal
import io
import logging
import re

import fitz
import requests
import tempfile
import zipfile

from urllib.parse import urlencode
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, PermissionDenied
from django.db.models import Q, Max
from django.db.models.aggregates import Sum
from django.http.response import Http404, HttpResponse
from django.shortcuts import redirect
from django.template import loader
from django.template.loader import render_to_string
from django.urls.base import reverse
from django.urls.base import reverse_lazy
from django.utils import formats, timezone
from django.utils.translation import gettext_lazy as _
from django_filters.views import FilterView
from django.core.files import File
from django.utils.text import slugify

from cmj.core.models import AuditLog
from cmj.loa.forms import LoaForm, EmendaLoaForm, OficioAjusteLoaForm, PrestacaoContaLoaForm, PrestacaoContaRegistroForm,\
    RegistroAjusteLoaForm, EmendaLoaFilterSet, AgrupamentoForm
from cmj.loa.models import Entidade, Loa, EmendaLoa, EmendaLoaParlamentar, OficioAjusteLoa, PrestacaoContaLoa, PrestacaoContaRegistro,\
    RegistroAjusteLoa, RegistroAjusteLoaParlamentar, EmendaLoaRegistroContabil,\
    Agrupamento, SubFuncao, UnidadeOrcamentaria, quantize
from cmj.utils import get_client_ip
from cmj.utils_report import make_pdf
from sapl.crud.base import Crud, CrudAux, MasterDetailCrud, RP_DETAIL, RP_LIST
from sapl.materia.models import Proposicao, TipoProposicao
from sapl.parlamentares.models import Legislatura, Parlamentar


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
        def verbose_name(self):
            return _('Lei Orçamentária Anual')

        @property
        def verbose_name_plural(self):
            return _('Leis Orçamentárias Anuais')

        @property
        def list_url(self):
            url = super().list_url
            if self.request.user.is_anonymous:
                c = Loa.objects.filter(publicado=True).count()
                return url if c > 1 else ''
            return url

    class ListView(Crud.ListView):
        ordered_list = False
        paginate_by = 4

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

        def hook_header_btn_lista_emendas(self):
            return ''

        def hook_btn_lista_emendas(self, *args, **kwargs):
            l = args[0]
            return f' <em>(Emendas à LOA)</em>', f'/loa/{l.pk}/emendaloa'

        def hook_receita_corrente_liquida(self, *args, **kwargs):
            l = args[0]
            if l.ano < 2023:
                return ' - ' , args[2]

            ano_atual = timezone.now().year

            rcl_previa = formats.number_format(l.rcl_previa, force_grouping=True)

            if l.ano > ano_atual:
                frase = 'Processo Legislativo em adamento' if not l.materia.normajuridica() else 'LOA Aprovada'
                return f'''
                    {rcl_previa}
                    <small class="text-gray">
                        <small>
                            <em class="text-blue"><strong>{frase}</strong></em>
                            <em>RCL referente ao ano anterior ao Projeto da LOA</em>
                        </small>
                    </small>
                ''', ''

            if l.ano == ano_atual:
                return f'''
                    {args[1]}
                    <small class="text-gray">
                        <small>
                            <em>LOA em fase de Execução</em>
                            <em>RCL referente ao ano anterior à Execução</em>
                ''', ''

            return f'''
                {args[1]}
                <small class="text-gray">
                    <small>
                        <em>LOA executada em {l.ano}</em>
                        <em>RCL referente ao ano anterior à Execução</em>
            ''', ''


        # def hook_header_receita_corrente_liquida(self):
        #     return 'Receita Corrente Líquida - RCL (R$)<br><small class="text-gray">RCL Referente ao ano anterior.</small>'

        def hook_ano(self, *args, **kwargs):
            l = args[0]
            return f'''
            <a href="{args[2]}" title="Detalhes do Cadastro do Orçamento Impositivo">LOA {args[1]}</a><br>
            <a class="small" href="/loa/{l.id}/emendaloa" title="Listagem de Emendas à LOA">
                <i class="fas fa-list"></i>
            </a>
            ''', ''

        def hook_perc_disp_total(self, *args, **kwargs):
            l = args[0]
            return f' <em>({l.perc_disp_total:3.1f}%)</em>', ''

        def hook_perc_disp_saude(self, *args, **kwargs):
            l = args[0]
            return f' <em>({l.perc_disp_saude:3.1f}%)</em>', ''

        def hook_perc_disp_diversos(self, *args, **kwargs):
            l = args[0]
            return f' <em>({l.perc_disp_diversos:3.1f}%)</em>', ''

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

        @property
        def extras_list_url(self):
            btns = []

            btns.extend(
                [
                    (
                        reverse('cmj.loa:emendaloa_list',
                                kwargs={'pk': self.kwargs['pk']}),
                        'btn-primary',
                        _('Listas Emendas Impositivas')
                    )
                ]
            )

            btns = list(filter(None, btns))
            return btns

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


        def hook_receita_corrente_liquida(self, l, verbose_name='', field_display=''):

            em_fase_execucao = l.rcl_previa != l.receita_corrente_liquida
            header = f'RCL de {l.ano - (1 if em_fase_execucao else 2)}'
            valor = formats.number_format(
                l.receita_corrente_liquida if em_fase_execucao else l.rcl_previa,
                force_grouping=True
            )
            return 'Receita Corrente Líquida', f'''
                {valor}
                <hr>
                <small class="text-gray">
                    <em>{header}</em>
                    <em>(RCL referente ao ano anterior { "à Execução" if em_fase_execucao else "ao Projeto" })</em>
                </small>
            '''


        def _hook_disp_generic(self, l, verbose_name='', field_display='', field_type=''):
            """
            Generic function to handle display of disp_* fields

            Parameters:
            - l: Loa object
            - verbose_name: Field verbose name
            - field_display: Field display value
            - field_type: One of 'total', 'saude', or 'diversos'
            - show_per_parliamentarian: Whether to show value per parliamentarian
            """
            percentage_attr = f'perc_disp_{field_type}'
            percentage = getattr(l, percentage_attr, 0)

            result = f'{field_display} <em>({percentage:3.1f}%)</em>'

            legislatura_atual = Legislatura.cache_legislatura_atual()
            materia_in_legislatura_atual = True
            loa_in_legislatura_atual = True

            if l.materia:
                materia_in_legislatura_atual = legislatura_atual['data_inicio'] <= l.materia.data_apresentacao <= legislatura_atual['data_fim']
                loa_in_legislatura_atual = legislatura_atual['data_inicio'].year <= l.ano <= legislatura_atual['data_fim'].year

            lps = l.loaparlamentar_set.all()
            count_lps = lps.count()

            if not loa_in_legislatura_atual or not materia_in_legislatura_atual:
                count_lps = Parlamentar.objects.filter(ativo=True).count()

            if count_lps > 0:
                disp_value = getattr(l, f'disp_{field_type}')
                valor_por_parlamentar = formats.number_format(
                    quantize(
                        disp_value / count_lps,
                        rounding=ROUND_DOWN
                    ),
                    force_grouping=True
                )

                result = f'''
                    {field_display}
                    <em>({percentage:3.1f}%)</em>
                    <small><small class="text-gray"><hr><em>Valor por Parlamentar</em>
                        <strong>R$ {valor_por_parlamentar}</strong>
                    </small></small>
                '''

            return verbose_name, result

        def hook_disp_total(self, l, verbose_name='', field_display=''):
            return self._hook_disp_generic(l, verbose_name, field_display, 'total')

        def hook_disp_saude(self, l, verbose_name='', field_display=''):
            return self._hook_disp_generic(l, verbose_name, field_display, 'saude')

        def hook_disp_diversos(self, l, verbose_name='', field_display=''):
            return self._hook_disp_generic(l, verbose_name, field_display, 'diversos')

        def hook_resumo_emendas_impositivas(self, *args, **kwargs):
            l = args[0]

            loaparlamentares = l.loaparlamentar_set.order_by(
                '-parlamentar__ativo',
                'parlamentar__nome_parlamentar')

            resumo_emendas_impositivas = []

            totais = {}

            for lp in loaparlamentares:

                resumo_parlamentar = {'loaparlamentar': lp}
                for k, v in EmendaLoa.TIPOEMENDALOA_CHOICE[:2]:
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
                        # ).exclude(
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

                    ajustes_negativos_sem_emendas = RegistroAjusteLoaParlamentar.objects.filter(
                        parlamentar=lp.parlamentar,
                        registro__tipo=k,
                        registro__oficio_ajuste_loa__loa=l,
                        registro__emendaloa__isnull=True,
                        valor__lt=0
                    ).aggregate(Sum('valor'))

                    resumo_parlamentar[k]['ja_destinado'] += (
                        (ajustes['valor__sum'] or Decimal('0.00')) - (ajustes_negativos_sem_emendas['valor__sum'] or Decimal('0.00'))
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

                    totais[k]['ja_destinado'] += resumo_parlamentar[k]['ja_destinado']
                    totais[k]['impedimento_tecnico'] += resumo_parlamentar[k]['impedimento_tecnico']
                    totais[k]['sem_destinacao'] += resumo_parlamentar[k]['sem_destinacao']

                resumo_emendas_impositivas.append(resumo_parlamentar)

            resumo_emendas_impositivas.sort(
                key=lambda x: (
                    not x['loaparlamentar'].parlamentar.ativo,
                    # -x[10]['ja_destinado'],
                    x['loaparlamentar'].parlamentar.nome_parlamentar
                )
            )

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

            template = loader.get_template('loa/loaparlamentar_set_list.html')
            rendered = template.render(context, self.request)

            return 'Resumo Geral das Emendas Impositivas Parlamentares', rendered

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

        def hook_resumo_unidades(self, *args, **kwargs):
            l = args[0]

            soma_geral = Decimal('0.00')
            unidades = {}
            for el in EmendaLoa.objects.filter(
                loa=l,
                tipo__gt=0
            ).values(
                'unidade__especificacao',
                'parlamentares__id',
                'parlamentares__nome_parlamentar'
            ).order_by(
                'unidade__especificacao'
            ).annotate(soma_valor=Sum('valor')):
                if el['unidade__especificacao'] not in unidades:
                    unidades[el['unidade__especificacao']] = {
                        'parlamentares': [],
                        'soma_unidade': Decimal('0.00'),
                    }

                unidades[el['unidade__especificacao']]['parlamentares'].append({
                    'id': el['parlamentares__id'],
                    'nome_parlamentar': el['parlamentares__nome_parlamentar'],
                    'soma_valor': el['soma_valor'],
                })

                unidades[el['unidade__especificacao']]['soma_unidade'] += el['soma_valor']

                soma_geral += el['soma_valor']

            context = dict(
                unidades=unidades.items(),
                soma_geral=soma_geral,
                loa=l
            )

            template = loader.get_template('loa/emendaloa_totalize_unidade.html')
            rendered = template.render(context, self.request)

            return 'Resumo Por Unidades Orçamentárias <small>(Totalização na aprovação, sem ajustes por impedimento técnico)</small>', rendered

        def hook_resumo_entidades(self, *args, **kwargs):
            l = args[0]

            soma_geral = Decimal('0.00')
            entidades = {}
            for el in EmendaLoa.objects.filter(
                loa=l,
                tipo__gt=0
            ).values(
                'tipo',
                'entidade__nome_fantasia',
                'unidade__especificacao',
                'parlamentares__id',
                'parlamentares__nome_parlamentar'
            ).order_by(
                'tipo',
                'entidade__nome_fantasia'
            ).annotate(soma_valor=Sum('valor')):
                nom_entidade = el['entidade__nome_fantasia'] or el['unidade__especificacao']
                el['entidade__nome_fantasia'] = nom_entidade.upper()
                if el['entidade__nome_fantasia'] not in entidades:
                    entidades[el['entidade__nome_fantasia']] = {
                        'tipo': el['tipo'],
                        'parlamentares': [],
                        'soma_entidade': Decimal('0.00'),
                    }

                entidades[el['entidade__nome_fantasia']]['parlamentares'].append({
                    'id': el['parlamentares__id'],
                    'nome_parlamentar': el['parlamentares__nome_parlamentar'],
                    'soma_valor': el['soma_valor'],
                })

                entidades[el['entidade__nome_fantasia']]['soma_entidade'] += el['soma_valor']

                soma_geral += el['soma_valor']

            entidades = sorted(entidades.items(), key=lambda x: x[1]['tipo'])

            context = dict(
                entidades=entidades,
                soma_geral=soma_geral,
                loa=l
            )

            template = loader.get_template('loa/emendaloa_totalize_entidade.html')
            rendered = template.render(context, self.request)

            return 'Resumo Por Entidades <small>(Totalização na aprovação, sem ajustes por impedimento técnico)</small>', rendered

class UnidadeOrcamentariaCrud(MasterDetailCrud):
    model = UnidadeOrcamentaria
    parent_field = 'loa'


class SubFuncaoCrud(MasterDetailCrud):
    model = SubFuncao
    parent_field = 'loa'


class AgrupamentoCrud(MasterDetailCrud):
    model = Agrupamento
    parent_field = 'loa'
    public = [RP_LIST, RP_DETAIL]
    frontend = Agrupamento._meta.app_label

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        pass

        @property
        def create_url(self):
            url = super().create_url
            if self.request.user.has_perm('loa.emendaloa_full_editor'):
                url = self.resolve_url('create', args=(self.kwargs['pk'],))
            return url

        @property
        def update_url(self):

            url = super().update_url
            if self.request.user.has_perm('loa.emendaloa_full_editor'):
                url = self.resolve_url('update', args=(self.object.id,))

            return url

        @property
        def delete_url(self):

            url = super().delete_url
            if self.request.user.has_perm('loa.emendaloa_full_editor'):
                url = self.resolve_url('delete', args=(self.object.id,))

            return url

        @property
        def cancel_url(self):
            url = self.resolve_url('detail', args=(self.kwargs['pk'],))
            return url

    class DeleteView(MasterDetailCrud.DeleteView):
        permission_required = ('loa.emendaloa_full_editor', )

    class CreateView(MasterDetailCrud.CreateView):
        permission_required = ('loa.emendaloa_full_editor', )
        layout_key = 'AgrupamentoCreate'

        def get_success_url(self):
            return self.update_url

    class ListView(MasterDetailCrud.ListView):
        def hook_despesas(self, obj, ss, url):
            str_regs = []
            for rc in obj.agrupamentoregistrocontabil_set.order_by('-percentual'):
                src = f'{rc.str_percentual}% - {rc.despesa}'
                str_regs.append(src)
            src = ''.join(map(lambda x: f'<li>{x}</li>', str_regs))

            return f'<ul>{src}</ul>', ''

    class UpdateView(MasterDetailCrud.UpdateView):
        permission_required = ('loa.emendaloa_full_editor', )
        layout_key = None
        form_class = AgrupamentoForm

        def get_context_data(self, **kwargs):
            self.loa = Loa.objects.get(pk=kwargs['root_pk'])
            context = super().get_context_data(**kwargs)
            path = context.get('path', '')
            context['path'] = f'{path} agrupamento-update'
            return context

        def get_initial(self):
            initial = super().get_initial()
            initial['loa'] = self.object.loa
            initial['user'] = self.request.user
            return initial

    class DetailView(MasterDetailCrud.DetailView):

        def hook_despesas(self, obj, verbose_name, field_display):
            str_regs = []
            for rc in obj.agrupamentoregistrocontabil_set.order_by('-percentual'):
                src = f'{rc.str_percentual}% - {rc.despesa}'
                str_regs.append(src)
            src = ''.join(map(lambda x: f'<li>{x}</li>', str_regs))

            return verbose_name, f'<ul>{src}</ul>'


class EmendaLoaCrud(MasterDetailCrud):
    model = EmendaLoa
    parent_field = 'loa'
    public = [RP_LIST, RP_DETAIL]
    frontend = EmendaLoa._meta.app_label

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        list_field_names = [
            ('finalidade'),
            'valor_computado',
            ('tipo', 'fase'),
            'parlamentares'
        ]

        @property
        def ordered_list(self):
            return False

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

            if not url and self.object.fase >= EmendaLoa.EM_TRAMITACAO:
                return ''

            url_perm = self.resolve_url('update', args=(self.object.id,))

            if self.request.user.has_perm('loa.emendaloa_full_editor') and \
                EmendaLoa.PROPOSTA < self.object.fase < EmendaLoa.EM_TRAMITACAO:
                return url_perm
            elif self.request.user.operadorautor_set.exists() and \
                EmendaLoa.PROPOSTA <= self.object.fase < EmendaLoa.EM_TRAMITACAO and \
                    self.object.parlamentares.filter(
                        id__in=self.request.user.operadorautor_set.values_list(
                            'autor__object_id', flat=True)
                    ).exists():
                return url_perm

            return ''

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


        @property
        def extras_url(self):
            if self.request.user.is_anonymous or not self.request.user.operadorautor_set.exists():
                return []


            if not self.get_emendas_criadas_por_operador_mesmo_autor().filter(
                    fase__gte=EmendaLoa.LIBERACAO_CONTABIL
                ).exists():
                return []

            btns = []
            return [
                (reverse_lazy('cmj.loa:emendaloa_list', kwargs={'pk': self.kwargs['pk']}) + '?zip',
                'btn-outline-primary',
                '''
                    <span title="Baixar Emendas Impositivas/Modificativas em arquivo ZIP">
                    <i class="fas fa-file-pdf"></i> Baixar Emendas Liberadas</span>
                '''),
                (reverse_lazy('cmj.loa:emendaloa_list', kwargs={'pk': self.kwargs['pk']}) + '?register',
                'btn-outline-primary',
                '''
                    <span title="Registrar todas as emendas Liberadas no módulo de proposições">
                    <i class="fas fa-file-contract"></i> Registrar Emendas Liberadas</span>
                '''),
            ]

        def get_emendas_criadas_por_operador_mesmo_autor(self):
            if self.request.user.is_anonymous:
                return self.get_queryset().none()
            autor_operado = self.request.user.operadorautor_set.values_list('autor', flat=True)
            OperadorAutor = autor_operado.model

            return self.get_queryset(
                ).filter(
                    loa=self.loa,
                    owner__id__in=OperadorAutor.objects.filter(
                        autor__in=autor_operado
                    ).values_list('user', flat=True)
                )

        @property
        def title(self):
            return f'''Emendas Impositivas/Modificativas à LOA {self.loa.ano} <small>({self.loa.materia.epigrafe_short if self.loa.materia else ''})</small>
                '''


        def get(self, request, *args, **kwargs):
            self.loa = Loa.objects.get(pk=kwargs['pk'])
            return FilterView.get(self, request, *args, **kwargs)

        def render_to_response(self, context, **response_kwargs):
            if 'pdf' in self.request.GET:
                return self.makepdf(context, **response_kwargs)
            elif 'zip' in self.request.GET:
                return self.makezip(context, **response_kwargs)
            return super().render_to_response(context, **response_kwargs)

        def makezip(self, context, **response_kwargs):
            user = self.request.user
            if user.is_anonymous:
                raise PermissionDenied()

            if not user.is_superuser and not user.operadorautor_set.exists():
                raise PermissionDenied()

            req = self.request
            base_url =  f"{req.scheme}://{req.get_host()}"

            emendas = self.get_emendas_criadas_por_operador_mesmo_autor(
                ).filter(
                    fase__gte=EmendaLoa.LIBERACAO_CONTABIL
                )

            if not emendas.exists():
                messages.info(
                    self.request,
                    'Nenhuma Emenda Impositiva/Modificativa disponível para download.'
                )
                return super().render_to_response(context, **response_kwargs)

            autoroperado_id = user.operadorautor_set.values_list('autor', flat=True).first()

            with tempfile.SpooledTemporaryFile(max_size=512000000) as tmp:
                with zipfile.ZipFile(tmp, 'w') as file:

                    for emenda in emendas:
                        response = requests.get(f'{base_url}/api/loa/emendaloa/{emenda.id}/view/')

                        if response.status_code == 200:
                            nome_emenda = f'emendaloa_{emenda.id}_{emenda.loa.ano}'
                            if emenda.materia:
                                nome_emenda = f'emendaloa_{emenda.materia.tipo.sigla}_{emenda.materia.numero}_{emenda.materia.ano}'
                            elif emenda.proposicao:
                                nome_emenda = f'emendaloa_{emenda.proposicao.tipo.descricao}_{emenda.proposicao.numero_proposicao}_{emenda.proposicao.ano}'
                            nome_emenda = slugify(nome_emenda)

                            file.writestr(
                                f'{nome_emenda}.pdf',
                                response.content
                            )
                tmp.seek(0)
                response = HttpResponse(tmp.read(),
                                    content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename="emendaloa_{self.loa.ano}_autor_{autoroperado_id}.zip"'
                response['Cache-Control'] = 'no-cache'
                response['Pragma'] = 'no-cache'
                response['Expires'] = 0
                return response

        def makepdf(self, context, **response_kwargs):
            self.paginate_by = 0
            base_url = self.request.build_absolute_uri()

            try:
                context = self.get_context_data_makepdf()
            except:
                raise ValidationError(
                    'Ocorreu um erro ao processar seus filtros e agrupamentos.')

            template = render_to_string('loa/pdf/emendaloa_list.html', context)
            pdf_file = make_pdf(base_url=base_url, main_template=template)

            response = HttpResponse(
                pdf_file,
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'inline; filename="emendaloa_{self.loa.ano}.pdf"'
            response['Cache-Control'] = 'no-cache'
            response['Pragma'] = 'no-cache'
            response['Expires'] = 0
            return response

        def get_context_data_makepdf(self):

            cd = self.filterset.form.cleaned_data

            title = 'Listagem Geral das Emendas <small>{}</small>'

            filters = []
            if cd.get('parlamentares', ''):
                filtro = f'<strong>Parlamentares:</strong> {" / ".join(map(lambda x: str(x), cd["parlamentares"]))}'
                filters.append(filtro)

            if cd.get('finalidade', ''):
                filtro = f'<strong>Finalidade:</strong> {cd["finalidade"]}'
                filters.append(filtro)

            if cd.get('tipo', ''):
                dt = dict(map(lambda x: (str(x[0]), x[1]),
                          EmendaLoa.TIPOEMENDALOA_CHOICE))
                filtro = f'<strong>Tipos de Emenda:</strong> {" / ".join(map(lambda x: str(dt[x]), cd["tipo"]))}'
                filters.append(filtro)

            if cd.get('fase', ''):
                dt = dict(map(lambda x: (str(x[0]), x[1]),
                          EmendaLoa.FASE_CHOICE))
                filtro = f'<strong>Fases de Emenda:</strong> {" / ".join(map(lambda x: str(dt[x]), cd["fase"]))}'
                filters.append(filtro)

            if filters:
                filters.insert(0, '<strong>FILTROS APLICADOS</strong>')

            context = {
                'object': self.loa,
                'loa': self.loa,
                'tipo_agrupamento': cd.get('tipo_agrupamento', ''),
                'title': title,
                'filters': '<br>'.join(filters),
                'groups': []
            }

            def render_col_emenda(item):

                materia = ''
                if item.materia:
                    materia = f'''
                            <span class="materia">
                                <a href="{reverse('cmj.loa:emendaloa_detail',kwargs={'pk': item.id})}">
                                {item.materia.epigrafe_short}
                                </a>
                            </span> -
                    '''

                col_emenda = f'''

                    <div class="loa-mat">
                        {materia}
                        <small>
                            <strong>Autoria:</strong> {' - '.join(map(lambda x: str(x), item.parlamentares.all()))}
                        </small><br>
                        <span class="indicacao">{item.indicacao}</span>
                        <div>
                            {item.finalidade_format}
                        </div>
                        <ul></ul>
                    </div>
                '''
                return col_emenda

            total = Decimal('0.00')
            if not cd['agrupamento']:

                if not self.object_list.exists():
                    return context

                context['title'] = context['title'].replace('{}', '')

                sub_total = self.object_list.aggregate(Sum('valor'))

                total += sub_total['valor__sum']

                columns = ['Emendas', 'Valores']

                if not cd['tipo'] or len(cd['tipo']) > 1:
                    columns.insert(1, 'Tipos')

                rows = []

                for item in self.object_list:
                    cols = []
                    col_emenda = render_col_emenda(item)
                    cols.append((col_emenda, ''))

                    if not cd['tipo'] or len(cd['tipo']) > 1:
                        cols.append((item.get_tipo_display(), 'text-center'))

                    cols.append((item.str_valor, 'text-right'))

                    rows.append(cols)

                group = {
                    'title': '',
                    'columns': columns,
                    'ncols_menos2': len(columns) - 2,
                    'ncols_menos1': len(columns) - 1,
                    'rows': rows,
                    'sub_total_emendas': formats.number_format(sub_total['valor__sum'], force_grouping=True)
                }
                context['groups'].append(group)

            else:
                agrup = cd['agrupamento'].split('_')

                if agrup[0] == 'model':

                    ct = ContentType.objects.get_by_natural_key(
                        'loa', agrup[1])
                    model = ct.model_class()

                    if agrup[1] == 'unidadeorcamentaria':
                        agrup[1] = 'unidade'

                    via = ''
                    if cd['tipo_agrupamento'] == 'insercao':
                        via = ' - Via dotações de inserção.'
                    elif cd['tipo_agrupamento'] == 'deducao':
                        via = ' - Via dotações de dedução.'

                    context['title'] = context['title'].format(
                        f'<br>* Agrupado por: {model._meta.verbose_name}{via}'
                    )

                    columns = ['Emendas', 'Valores das Emendas']

                    if not cd['tipo'] or len(cd['tipo']) > 1:
                        columns.insert(1, 'Tipos')

                    lookup_ta = 'gt' if cd['tipo_agrupamento'] == 'insercao' else 'lt'
                    for im in model.objects.filter(loa=self.loa):
                        columns = columns[:]

                        if 'sem_registro' in cd['tipo_agrupamento']:
                            object_list = self.object_list.filter(
                                unidade=im
                            )
                        else:
                            try:
                                object_list = self.object_list.filter(
                                    **{f'registrocontabil_set__valor__{lookup_ta}': Decimal('0.00'),
                                        f'registrocontabil_set__despesa__{agrup[1]}': im,
                                       }
                                )
                            except Exception as e:
                                print(e)

                        if not object_list.exists():
                            continue

                        sub_total_emendas = object_list.aggregate(Sum('valor'))

                        total += sub_total_emendas['valor__sum']
                        movimentacao_valores = Decimal('0.00')
                        rows = []
                        for item in object_list:
                            cols = []
                            rows.append(cols)

                            col_emenda = render_col_emenda(item, )
                            cols.append([col_emenda, ''])

                            if not cd['tipo'] or len(cd['tipo']) > 1:
                                cols.append(
                                    (item.get_tipo_display(), 'text-center'))

                            cols.append([item.str_valor, 'text-right'])

                            if 'sem_registro' in cd['tipo_agrupamento']:
                                continue

                            qs_rc = item.registrocontabil_set.order_by('valor')

                            registros = []
                            for rc in qs_rc:

                                rc = str(rc).split(' - ')
                                if '-' not in rc[0]:
                                    rc0_split = rc[0].split(' ')
                                    rc0_split[-1] = f'+{rc0_split[-1]}'
                                    rc[0] = ' '.join(rc0_split)
                                    while len(rc[0]) < 17:
                                        rc[0] = rc[0].replace(' ', '  ', 1)
                                if '-' in rc[0]:
                                    while len(rc[0]) < 18:
                                        rc[0] = rc[0].replace(' ', '  ', 1)

                                rc[0] = rc[0].replace(' ', '&nbsp;')
                                registros.append(f'<li>{" - ".join(rc)}</li>')

                            cols[0][0] = cols[0][0].replace(
                                '<ul></ul>', f'<small class="courier"><small>AÇÕES ORÇAMENTÁRIAS DE ORIGEM(-) E DESTINO(+):</small></small><ul>{"".join(registros)}</ul>')

                            """deducao_insercao = qs_rc.filter(
                                **{
                                    f'valor__{lookup_ta}': Decimal('0.00'),
                                    f'despesa__{agrup[1]}': im
                                }
                            ).aggregate(
                                Sum('valor')
                            ).get('valor__sum', Decimal('0.00'))

                            deducao_insercao = formats.number_format(
                                deducao_insercao, force_grouping=True)
                            cols[-1][0] = f'{cols[-1][0]}<hr>{deducao_insercao}'"""

                        soma_valor_orcamento = im.despesa_set.aggregate(
                            Sum('valor_materia'))
                        soma_valor_orcamento = soma_valor_orcamento.get(
                            'valor_materia__sum'
                        ) or Decimal('0.00')

                        movimentacao_valores = EmendaLoaRegistroContabil.objects.filter(
                            **{f'despesa__{agrup[1]}': im}
                        ).aggregate(Sum('valor')).get('valor__sum') or Decimal('0.00')

                        group = {
                            'title': str(im),
                            'columns': columns,
                            'ncols_menos2': len(columns) - 2,
                            'ncols_menos1': len(columns) - 1,
                            'rows': rows,
                            'soma_valor_orcamento':  formats.number_format(soma_valor_orcamento, force_grouping=True),
                            'saldo_orcamento': formats.number_format(soma_valor_orcamento + movimentacao_valores, force_grouping=True),
                            'movimentacao_valores': formats.number_format(movimentacao_valores, force_grouping=True),
                            'sub_total_emendas': formats.number_format(sub_total_emendas['valor__sum'], force_grouping=True)
                        }
                        context['groups'].append(group)
            context['total'] = formats.number_format(
                total, force_grouping=True)

            return context

        def get_filterset_kwargs(self, filterset_class):
            kw = FilterView.get_filterset_kwargs(self, filterset_class)
            kw['loa'] = self.loa
            return kw

        def get_queryset(self):
            qs = super().get_queryset()
            if self.request.user.is_anonymous:
                qs = qs.filter(loa__publicado=True)
            return qs.order_by('fase', '-tipo', 'materia__numero', '-id')

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
            tipo = args[1] if args[1] else 'EMENDA MODIFICATIVA'
            link_pdf = ''
            link_create_proposicao_pre_preenchida = ''
            link_generate_proposicao = ''

            emendas_mesmo_autor = self.get_emendas_criadas_por_operador_mesmo_autor(
                ).filter(fase__gte=EmendaLoa.LIBERACAO_CONTABIL
                )
            if not emendas_mesmo_autor.filter(id=el.id).exists():
                return f'''
                    {link_pdf}
                    <br>{tipo}
                ''', args[2]

            if el.fase == EmendaLoa.LIBERACAO_CONTABIL and not el.materia :

                url = reverse_lazy('sapl.api:loa_emendaloa-view',kwargs={'pk': el.id})
                link_pdf = f'<a href="{url}" target="_blank"><i class="far fa-2x fa-file-pdf"></i></a>'

                params = dict(
                    descricao=el.ementa_format,
                    tipo_materia=el.loa.materia.tipo.id if el.loa.materia else '',
                    numero_materia=el.loa.materia.numero if el.loa.materia else '',
                    ano_materia=el.loa.materia.ano if el.loa.materia else '',
                    tipo=33 if el.tipo != EmendaLoa.MODIFICATIVA else 5,
                )
                query_params = urlencode(params)
                link_create_proposicao_pre_preenchida = f'''
                    <a target="_blank" href="{reverse_lazy('sapl.materia:proposicao_create')}?{query_params}">

                    </a>
                '''
                # {link_create_proposicao_pre_preenchida} <i class="fas fa-2x fa-magic"></i>

                link_generate_proposicao = f'''
                    <a href="{reverse_lazy('cmj.loa:emendaloa_detail', kwargs={'pk': el.id})}?register" target="_blank" >
                        <i class="fas fa-2x fa-file-contract"></i>
                    </a>
                '''

            return f'''
                {link_pdf} &nbsp; &nbsp; &nbsp;

                {link_generate_proposicao}
                <br>{tipo}
            ''', args[2]

        def hook_fase(self, *args, **kwargs):
            fase_display = f'<br><small class="text-nowrap">({args[0].get_fase_display()})</small>'
            el = args[0]
            link_pdf = ''
            if el.fase == EmendaLoa.IMPEDIMENTO_TECNICO:
                doc_acessorio = el.materia.documentoacessorio_set.order_by('data').first()
                if doc_acessorio:
                    link_pdf = f'<a title="Acesse Impedimento Técnico" href="{doc_acessorio.arquivo.url}"><i class="far fa-2x fa-file-pdf"></i></a>'
                return f'{fase_display}<br>{link_pdf}', args[2]


            return fase_display, args[2]

        def hook_header_finalidade(self, *args, **kwargs):
            return 'Descrição da Emenda'

        def hook_finalidade(self, *args, **kwargs):
            emenda, display_base, url = args

            render = []
            materia = emenda.materia
            if materia:
                render.append(f'<small><strong>Matéria Legislativa:</strong> {materia}</small><br>')

            unidade_orcamentaria = emenda.unidade or emenda.indicacao
            if unidade_orcamentaria:
                render.append(f'<small class="text-gray"><strong>Órgão Executor:</strong> {unidade_orcamentaria}</small><br>')

            registrocontabil_insercao_set = emenda.registrocontabil_set.filter(
                valor__gt=Decimal('0.00')
            )
            for rc in registrocontabil_insercao_set:
                render.append(f'<small class="text-gray"><strong>Ação Orçamentária:</strong> {rc.despesa.acao}</small><br>')


            finalidade = emenda.finalidade_format
            finalidade = f'{finalidade[0].upper()}{finalidade[1:]}'
            finalidade = f'<small class="text-gray"><strong>Entidade/Finalidade:</strong> {finalidade}</small><br>'
            render.append(finalidade)

            return ''.join(render), url

        def hook_parlamentares(self, *args, **kwargs):
            pls = []

            for elp in args[0].emendaloaparlamentar_set.all():
                if elp.emendaloa.tipo:
                    pls.append(
                        '<tr><td>{}</td><td align="right">R$ {}</td></tr>'.format(
                            elp.parlamentar.nome_parlamentar,
                            formats.number_format(
                                elp.valor, force_grouping=True)
                        )
                    )
                else:
                    pls.append(
                        f'<tr><td>{elp.parlamentar.nome_parlamentar}</td>')

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

        def get_context_data(self, **kwargs):
            self.loa = Loa.objects.get(pk=kwargs['root_pk'])
            context = super().get_context_data(**kwargs)
            path = context.get('path', '')
            context['path'] = f'{path} emendaloa-create'
            return context

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
                return u.operadorautor_set.exists() and self.loa.publicado

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
            #context['fluid'] ='-fluid'
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

        def form_valid(self, form):
            u = self.request.user
            if u.has_perm('loa.emendaloa_full_editor'):
                submit_concluir = 'submit_concluir' in self.request.POST
                submit_devolver = 'submit_devolver' in self.request.POST
                if submit_concluir or submit_devolver:
                    form.instance.fase = EmendaLoa.LIBERACAO_CONTABIL if submit_concluir else EmendaLoa.PROPOSTA

            return super().form_valid(form)

        def get(self, request, *args, **kwargs):
            u = request.user
            if not u.is_superuser and not u.is_anonymous:
                if u.operadorautor_set.exists():
                    if self.object.fase > EmendaLoa.PROPOSTA_LIBERADA and \
                            self.object.fase != EmendaLoa.LIBERACAO_CONTABIL:
                        messages.warning(
                            request, f'A Emenda está na fase de "{self.object.get_fase_display()}". Não pode ser editada por usuário de autoria.')
                        return redirect(self.detail_url)

                if u.has_perm('loa.emendaloa_full_editor') and \
                    self.object.fase == EmendaLoa.PROPOSTA_LIBERADA:
                    self.object.fase = EmendaLoa.EDICAO_CONTABIL
                    self.object.save()

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
                            parlamentar=parlamentar,
                            emendaloa__tipo__gt=0
                        ).exists() or self.object.emendaloaparlamentar_set.filter(
                            emendaloa__owner=u,
                            emendaloa__tipo=0
                        ).exists()

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

        @property
        def extras_url(self):
            return []
            if self.request.user.is_anonymous or not self.request.user.operadorautor_set.exists():
                return []

            if self.object.fase < EmendaLoa.LIBERACAO_CONTABIL:
                return []

            params = dict(
                descricao=self.object.ementa_format.strip(),
                tipo_materia=self.object.loa.materia.tipo.id if self.object.loa.materia else '',
                numero_materia=self.object.loa.materia.numero if self.object.loa.materia else '',
                ano_materia=self.object.loa.materia.ano if self.object.loa.materia else '',
                tipo=33 if self.object.tipo != EmendaLoa.MODIFICATIVA else 5,
            )

            query_params = urlencode(params)

            return [
                (reverse_lazy('sapl.materia:proposicao_create') + f'?{query_params}',
                'btn-outline-primary',
                _('Cadastrar Proposição pré-preenchida')
                )
            ]

        def get(self, request, *args, **kwargs):
            self.object = self.get_object()

            if 'register' in request.GET:
                user = request.user
                if user.is_anonymous:
                    raise PermissionDenied()

                autor_operado = self.request.user.operadorautor_set.values_list('autor', flat=True)
                OperadorAutor = autor_operado.model
                if not OperadorAutor.objects.filter(
                        user=self.object.owner,
                        autor__in=autor_operado
                    ).exists():
                    messages.error(
                        request,
                        'Você não tem permissão para registrar a Proposição Legislativa desta Emenda Impositiva/Modificativa.'
                    )
                    return redirect(self.detail_url)

                if self.object.materia:
                    messages.error(
                        request,
                        'A Proposição Legislativa não pode ser gerada novamente pois já foi protocolada e está vinculada a uma Matéria Legislativa.'
                    )
                    return redirect(
                        reverse_lazy(
                            'cmj.loa:emendaloa_detail',
                            kwargs={'pk': self.object.id}
                        )
                    )

                if self.object.fase != EmendaLoa.LIBERACAO_CONTABIL:
                    messages.error(
                        request,
                        'A Proposição Legislativa só pode ser gerada quando a Emenda Impositiva/Modificativa estiver na fase de "Liberado pela Contabilidade e/ou Aguardando Protocolo".'
                    )
                    return redirect(self.detail_url)

                if self.object.proposicao and self.object.proposicao.data_envio and self.object.proposicao.data_recebimento:
                    messages.warning(
                        request,
                        'A Proposição Legislativa já foi registrada e recebida pelo protocolo, não pode ser atualizada via módulo de Orçamento Impositivo.'
                    )
                    return redirect(reverse_lazy('sapl.materia:proposicao_detail', kwargs={'pk': self.object.proposicao.id}))

                if self.object.proposicao and self.object.proposicao.data_envio and not self.object.proposicao.data_recebimento:
                    messages.warning(
                        request,
                        'A Proposição Legislativa já foi registrada e enviada ao protocolo, para ser atualizada é necessário retomar a proposição antes do protocolo autuar.'
                    )
                    return redirect(reverse_lazy('sapl.materia:proposicao_detail', kwargs={'pk': self.object.proposicao.id}))



                try:

                    arq_bytes, arq_name = self.retrieve_file_bytes(request)

                    autor = user.operadorautor_set.first().autor

                    proposicao = self.object.proposicao
                    created = False
                    if not proposicao:
                        np_max = Proposicao.objects.filter(
                            autor=autor,
                            ano=timezone.now().year
                            ).aggregate(np=Max('numero_proposicao'))

                        proposicao = Proposicao()
                        proposicao.numero_proposicao = np_max.get('np', 0) + 1
                        created = True

                    proposicao.autor = autor

                    proposicao.tipo = TipoProposicao.objects.get(
                        id=33 if self.object.tipo != EmendaLoa.MODIFICATIVA else 5,
                    )
                    proposicao.descricao = self.object.ementa_format
                    proposicao.ano = timezone.now().year
                    proposicao.materia_de_vinculo = self.object.loa.materia
                    proposicao.user = user
                    proposicao.ip = get_client_ip(request)
                    proposicao.texto_original = File(arq_bytes, name=arq_name)
                    proposicao.save()

                    self.object.proposicao = proposicao
                    self.object.save()

                    messages.success(
                        request,
                        f'Proposição Legislativa {"criada" if created else "atualizada"} com sucesso.'
                    )
                    return redirect(reverse_lazy('sapl.materia:proposicao_detail', kwargs={'pk': proposicao.id}))
                except Exception as e:
                    messages.error(
                        request,
                        f'Ocorreu um erro ao registrar a Proposição Legislativa: {e}'
                    )

                return redirect(self.detail_url)

            return MasterDetailCrud.DetailView.get(self, request, *args, **kwargs)

        def retrieve_file_bytes(self, request):
            base_url =  f"{request.scheme}://{request.get_host()}"

            pra_frente = True
            while True:
                response = requests.get(f'{base_url}/api/loa/emendaloa/{self.object.id}/view/')
                if response.status_code != 200:
                    raise Exception('Não foi possível gerar o PDF da Emenda.')

                arq_name = response.headers.get('Content-Disposition', f'emenda_loa_{self.object.id}.pdf').split('filename=')[-1].strip('"')

                arq_bytes = io.BytesIO(response.content)
                pdf = fitz.open(stream=arq_bytes, filetype="pdf")

                if pdf.page_count == 0:
                    break

                if pdf.page_count > 1:
                    pra_frente = False

                md = self.object.metadata
                md['style'] = md.get('style', {
                    'lineHeight': 150,
                    'espacoAssinatura': 0,
                })
                md['style']['espacoAssinatura'] = md['style'].get('espacoAssinatura', 0)
                lineHeight = md['style']['lineHeight']

                if lineHeight < 110:
                    break

                if pdf.page_count == 1 and not pra_frente:
                    break

                if pra_frente and lineHeight > 200 and pdf.page_count == 1:
                    break

                if pra_frente:
                    lineHeight += 5
                else:
                    lineHeight -= 1

                md['style']['lineHeight'] = lineHeight
                self.object.metadata = md
                self.object.save()

                if pra_frente:
                    continue

                page2 = pdf.load_page(1)
                text = page2.get_text("text")
                text = text
                if 'A presente emenda fará parte integrante do Projeto' in text:
                    break

            return arq_bytes, arq_name

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            path = context.get('path', '')
            context['path'] = f'{path} emendaloa-detail'
            return context

        def hook_valor_computado(self, el, verbose_name='', field_display=''):
            if not el.materia:
                return '', ''

            return 'Valor Final da Emenda (R$)', field_display

        def hook_tipo(self, el, verbose_name='', field_display=''):
            if el.tipo:
                return verbose_name, field_display

            return 'Emenda Modificativa', 'Emenda Modificativa'

        def hook_indicacao(self, el, verbose_name='', field_display=''):
            return f'{verbose_name} (Unidade Orçamentária)', field_display

        def hook_finalidade(self, el, verbose_name='', field_display=''):
            return verbose_name, el.finalidade_format

        def hook_materia(self, el, verbose_name='', field_display=''):
            if el.materia:
                strm = str(el.materia)
                field_display = field_display.replace(
                    strm, el.materia.epigrafe_short)
            return 'Processo Legislativo da Emenda Impositiva', field_display

        def hook_registroajusteloa_set(self, el, verbose_name='', field_display=''):

            if not el.materia:
                return 'Sem registros de Ajuste Técnico', ''

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

            if not ajustes:
                return verbose_name, 'Esta Emenda não possui registros de Ajuste Técnico'

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

            return 'Documentos Adicionados à Emenda Impositiva', f'''
                <div class="container-table m-0 mx-n3">
                    <table class="table table-form table-bordered table-hover w-100">
                        {"".join(docs)}
                    </table>
                </div>
                '''

        def hook_prestacaocontaregistro_set(self, emendaloa, verbose_name='', field_display=''):
            if not emendaloa.materia:
                return '', ''

            pcs = []

            for pc in emendaloa.prestacaocontaregistro_set.all():
                pc_url = reverse_lazy(
                    'cmj.loa:prestacaocontaloa_detail',
                    kwargs={'pk': pc.prestacao_conta.id}
                )
                pcs.append(
                    f'''<li>
                        <span class="badge badge-secondary p-2">{formats.date_format(pc.prestacao_conta.data_envio, "SHORT_DATE_FORMAT")}</span>
                        <span class="badge badge-secondary p-2">{pc.situacao}</span>
                        <a href="{ pc_url}" class="d-inline-block p-2 font-weight-bold">
                        {pc.prestacao_conta}
                        </a>
                        <span class="text-gray d-block">{pc.detalhamento}</span>
                    </li>'''
                )

            return 'Registros de Prestação de Contas', f'''
                <ul>
                    {"".join(pcs)}
                </ul>
                '''

        def hook_parlamentares(self, emendaloa, verbose_name='', field_display=''):
            pls = []

            for elp in emendaloa.emendaloaparlamentar_set.all():
                if elp.emendaloa.tipo:
                    pls.append(
                        '<tr><td>{}</td><td align="right">R$ {}</td></tr>'.format(
                            elp.parlamentar.nome_parlamentar,
                            formats.number_format(
                                elp.valor, force_grouping=True)
                        )
                    )
                else:
                    pls.append(
                        f'<tr><td>{elp.parlamentar.nome_parlamentar}</td>')

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
        ordered_list = False
        list_field_names = [
            'registros'
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

        def hook_header_registros(self):
            return 'Registros de Ajuste Técnico'

        def hook_registros(self, obj, field_display='', url=''):
            ajustes = []

            url = reverse_lazy(
                'cmj.loa:oficioajusteloa_detail',
                kwargs={'pk': obj.id})

            epigrafe = f'<h2><a class="text-nowrap" href="{url}">{obj.epigrafe}</a></h2>'
            ajustes.append(epigrafe)

            parlamentares = ' - '.join(map(lambda x: str(x), obj.parlamentares.all()))
            ajustes.append(f'<h4><strong>Parlamentares:</strong> {parlamentares}</h4>')

            registros = obj.registroajusteloa_set.all()

            registros_positivos = []
            registros_negativos = []
            registros_zero = []

            for r in registros:
                if r.soma_valor > Decimal('0.00'):
                    registros_positivos.append(r)
                elif r.soma_valor < Decimal('0.00'):
                    registros_negativos.append(r)
                else:
                    registros_zero.append(r)

            registros = list(registros_positivos) + list(registros_negativos) + list(registros_zero)

            for ajuste in registros:
                url = reverse_lazy(
                    'cmj.loa:registroajusteloa_detail',
                    kwargs={'pk': ajuste.id})

                a_str = f'R$ {ajuste.str_valor}'
                if ajuste.soma_valor < Decimal('0.00'):
                    a_str = f'<span class="text-danger">{a_str}</span>'
                elif ajuste.soma_valor == Decimal('0.00'):
                    a_str = f'<span class="text-danger">R$ 0,00</span>'

                emenda_epigrafe = ajuste.emendaloa.materia.epigrafe_short if ajuste.emendaloa else ""
                emenda_epigrafe = f'<strong>Emenda:</strong> {emenda_epigrafe if emenda_epigrafe else "Ajuste sem ligação com emenda impositiva."}<br>'

                a_str = f'''
                    <tr>
                        <td align="right">
                            <a href="{url}">
                                <strong style="white-space: nowrap">
                                    {a_str}
                                </strong>
                            </a>
                        </td>
                        <td>
                          {emenda_epigrafe}
                          <small>
                            <em>{ajuste.descricao}</em>
                          </small>
                        </td>
                    </tr>
                '''

                ajustes.append(a_str)

            return f'<table>{"".join(ajustes)}</table>', ''

    class DetailView(MasterDetailCrud.DetailView):
        template_name = 'loa/oficioajusteloa_detail.html'
        paginate_by = 100

        @property
        def list_field_names_set(self):
            return 'descricao', 'str_valor', 'tipo'  # , 'emendaloa'

        def hook_header_str_valor(self):
            return 'Valor (R$)'

        def hook_str_valor(self, obj, verbose_name='', field_display=''):
            return verbose_name, f'{field_display if field_display != "0" else "0,00"}'

        def hook_descricao(self, obj, verbose_name='', field_display=''):

            emenda_epigrafe = obj.emendaloa.materia.epigrafe_short if obj.emendaloa else ""
            emenda_epigrafe = f'<strong>Emenda:</strong> {emenda_epigrafe if emenda_epigrafe else "Ajuste sem ligação com emenda impositiva."}<br>'

            return verbose_name, f'{emenda_epigrafe}<em>{field_display}</em>'

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

        def hook_emendaloa(self, obj, verbose_name='', field_display=''):
            if not obj.emendaloa:
                return '', ''

            url = reverse_lazy('cmj.loa:emendaloa_detail', kwargs={'pk': obj.emendaloa.id})
            field_display = f'{obj.emendaloa.materia.epigrafe_short} - {obj.emendaloa.indicacao}<br>{obj.emendaloa.finalidade}'
            field_display = f'<a href="{url}">{field_display}</a>'
            return verbose_name, field_display

        def hook_oficio_ajuste_loa(self, obj, verbose_name='', field_display=''):
            field_display = f'<a href="{obj.oficio_ajuste_loa.arquivo.url}">{obj.oficio_ajuste_loa.epigrafe}</a>'
            return verbose_name, field_display

        def hook_prestacaocontaregistro_set(self, obj, verbose_name='', field_display=''):
            pcs = []

            for pc in obj.prestacaocontaregistro_set.all():
                pc_url = reverse_lazy(
                    'cmj.loa:prestacaocontaloa_detail',
                    kwargs={'pk': pc.prestacao_conta.id}
                )
                pcs.append(
                    f'''<li>
                        <span class="badge badge-secondary p-2">{formats.date_format(pc.prestacao_conta.data_envio, "SHORT_DATE_FORMAT")}</span>
                        <span class="badge badge-secondary p-2">{pc.situacao}</span>
                        <a href="{ pc_url}" class="d-inline-block p-2 font-weight-bold">
                        {pc.prestacao_conta}
                        </a>
                        <span class="text-gray d-block">{pc.detalhamento}</span>
                    </li>'''
                )

            return verbose_name, f'''
                <ul>
                    {"".join(pcs)}
                </ul>
                '''

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
                kwargs={'pk': self.object.oficio_ajuste_loa.id})

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


class PrestacaoContaRegistroCrud(MasterDetailCrud):
    model = PrestacaoContaRegistro
    parent_field = 'prestacao_conta__loa'
    public = [RP_LIST, RP_DETAIL]
    frontend = PrestacaoContaRegistro._meta.app_label
    link_return_to_parent_field = True
    ListView = None  # Disable ListView

    class BaseMixin(MasterDetailCrud.BaseMixin):

        @property
        def cancel_url(self):
            if self.object:
                return self.detail_url
            return reverse_lazy(
                'cmj.loa:prestacaocontaloa_detail',
                kwargs={'pk': self.kwargs['pk']})

    class CreateView(MasterDetailCrud.CreateView):
        form_class = PrestacaoContaRegistroForm

        def get_initial(self):
            initial = super().get_initial()
            initial['loa'] = PrestacaoContaLoa.objects.get(
                pk=self.kwargs['pk']).loa
            return initial

        def get_success_url(self):
            return reverse_lazy(
                'cmj.loa:prestacaocontaloa_detail',
                kwargs={'pk': self.object.prestacao_conta.id})

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = PrestacaoContaRegistroForm

        def get_initial(self):
            initial = super().get_initial()
            initial['loa'] = self.object.loa
            return initial

        def get_success_url(self):
            return reverse_lazy(
                'cmj.loa:prestacaocontaloa_detail',
                kwargs={'pk': self.object.prestacao_conta.id})


    class DetailView(MasterDetailCrud.DetailView):
        layout_key = 'PrestacaoContaRegistroDetail'

    class DeleteView(MasterDetailCrud.DeleteView):

        def get_success_url(self):
            return reverse_lazy(
                'cmj.loa:registroajusteloa_detail',
                kwargs={'pk': self.object.registro_ajuste.id})



class PrestacaoContaLoaCrud(MasterDetailCrud):
    model = PrestacaoContaLoa
    parent_field = 'loa'
    model_set = 'prestacaocontaregistro_set'
    public = [RP_LIST, RP_DETAIL]
    frontend = PrestacaoContaLoa._meta.app_label

    class CreateView(MasterDetailCrud.CreateView):

        def get_success_url(self):
            return self.update_url

    class UpdateView(MasterDetailCrud.UpdateView):
        layout_key = 'PrestacaoContaLoaUpdate'
        form_class = PrestacaoContaLoaForm

    class DetailView(MasterDetailCrud.DetailView):
        layout_key = 'PrestacaoContaLoaDetail'
        template_name = 'loa/prestacaocontaloa_detail.html'

        @property
        def list_field_names_set(self):
            return 'situacao', 'emendaloa_registro_ajuste', 'descricao', 'detalhamento'

        def hook_header_descricao(self):
            return 'Descrição do Item da Prestação de Contas'

        def hook_descricao(self, obj, verbose_name='', field_display=''):
            descricao = []
            if obj.emendaloa:
                descricao.append(f'{obj.emendaloa}')
            if obj.registro_ajuste:
                descricao.append(f'{obj.registro_ajuste.descricao}')
            return verbose_name, '<br>'.join(descricao)


        def hook_header_emendaloa_registro_ajuste(self):
            return 'Emenda Impositiva / Registro de Ajuste Técnico'

        def hook_emendaloa_registro_ajuste(self, obj, verbose_name='', field_display=''):
            links = []

            if obj.emendaloa:
                url_emenda = reverse_lazy(
                    'cmj.loa:emendaloa_detail',
                    kwargs={'pk': obj.emendaloa.id})
                links.append(f'''
                    <a href="{url_emenda}">
                        {obj.emendaloa.materia.epigrafe_short}
                    </a>
                ''')

            if obj.registro_ajuste:
                url_ajuste = reverse_lazy(
                    'cmj.loa:registroajusteloa_detail',
                    kwargs={'pk': obj.registro_ajuste.id})
                links.append(f'''
                    <a href="{url_ajuste}">
                        {obj.registro_ajuste.oficio_ajuste_loa.epigrafe}
                    </a>
                ''')

            return verbose_name, '<br>'.join(links)

        def hook_arquivoprestacaocontaloa_set(self, obj, verbose_name='', field_display=''):
            arquivos = []

            qs_arquivos = obj.arquivoprestacaocontaloa_set.order_by('-id')
            for arquivo in qs_arquivos:
                arq_template = f'''
                    <a href="{arquivo.arquivo.url}">
                        <i class="far fa-2x fa-file-pdf"></i>
                        {arquivo.descricao}
                    </a>
                '''
                arquivos.append(
                    f'<tr><td>{arq_template}</td></tr>'
                )

            return 'Arquivos da Prestação de Contas', f'''
                <div class="container-table m-0 mx-n3">
                    <table class="table table-form table-bordered table-hover w-100">
                        {"".join(arquivos)}
                    </table>
                </div>
                '''




class EntidadeCrud(CrudAux):
    model = Entidade
    public = [RP_LIST, RP_DETAIL]
    frontend = Entidade._meta.app_label

    class BaseMixin(CrudAux.BaseMixin):
        list_field_names = [
            'nome_fantasia', ('cnes', 'cpfcnpj'), 'ativo'
        ]

    class DetailView(CrudAux.DetailView):
        layout_key = 'EntidadeDetail'

        def hook_metadata__import_fields(self, obj, verbose_name='', field_display=''):

            import_fields = obj.metadata.get('import_fields', {})

            if not import_fields:
                return verbose_name, 'Nenhum campo de importação definido.'

            lines = []
            for k, v in import_fields.items():
                if v:
                    lines.append(f'<li><strong>{k}:</strong> {v}</li>')

            return _('Dados importados da base do CNES'), f'<ul class="monospace">{"".join(lines)}</ul>'

    class ListView(CrudAux.ListView):
        ordering = ('-ativo', 'nome_fantasia')

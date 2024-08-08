from decimal import Decimal
import logging

from django.db.models.aggregates import Sum
from django.http.response import Http404
from django.template import loader
from django.utils import formats
from django.utils.translation import ugettext_lazy as _

from cmj.loa.forms import LoaForm, EmendaLoaForm
from cmj.loa.models import Loa, EmendaLoa, EmendaLoaParlamentar
from sapl.crud.base import Crud, MasterDetailCrud, RP_DETAIL, RP_LIST


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

    class BaseMixin(LoaContextDataMixin, Crud.BaseMixin):
        list_field_names = [
            'ano',
            'receita_corrente_liquida',
            ('disp_total', 'perc_disp_total'),
            ('disp_saude', 'perc_disp_saude'),
            ('disp_diversos', 'perc_disp_diversos'),
            'publicado'
        ]

    class ListView(Crud.ListView):
        ordered_list = False

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            path = context.get('path', '')
            context['path'] = f'{path} loa-list'
            return context

        def get_queryset(self):
            queryset = super().get_queryset()
            if self.request.user.is_anonymous:
                queryset = queryset.filter(publicado=True)

            return queryset

        def hook_header_perc_disp_total(self):
            return ''

        def hook_header_perc_disp_saude(self):
            return ''

        def hook_header_perc_disp_diversos(self):
            return ''

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

    class UpdateView(Crud.UpdateView):
        form_class = LoaForm

        def get_initial(self):
            initial = super().get_initial()
            if self.object.materia:
                initial['tipo_materia'] = self.object.materia.tipo.id
                initial['numero_materia'] = self.object.materia.numero
                initial['ano_materia'] = self.object.materia.ano
            return initial

    class DetailView(Crud.DetailView):
        layout_key = 'LoaDetail'

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            path = context.get('path', '')
            context['path'] = f'{path} loa-detail'
            return context

        def get(self, request, *args, **kwargs):
            response = super().get(request, *args, **kwargs)
            if not self.object.publicado and request.user.is_anonymous:
                raise Http404
            return response

        def hook_materia(self, l, verbose_name='', field_display=''):
            if l.materia:
                strm = str(l.materia)
                field_display = field_display.replace(
                    strm, l.materia.epigrafe_short)
            return verbose_name, field_display

        def hook_disp_total(self, l, verbose_name='', field_display=''):
            return verbose_name, f'{field_display} <i>({l.perc_disp_total:3.1f}%)</i>'

        def hook_disp_saude(self, l, verbose_name='', field_display=''):
            return verbose_name, f'{field_display} <i>({l.perc_disp_saude:3.1f}%)</i>'

        def hook_disp_diversos(self, l, verbose_name='', field_display=''):
            return verbose_name, f'{field_display} <i>({l.perc_disp_diversos:3.1f}%)</i>'

        def hook_resumo_emendas_impositivas(self, *args, **kwargs):
            l = args[0]
            template = loader.get_template('loa/loaparlamentar_set_list.html')

            loaparlamentares = l.loaparlamentar_set.order_by(
                'parlamentar__nome_parlamentar')

            resumo_emendas_impositivas = []
            for lp in loaparlamentares:

                resumo_parlamentar = {'loaparlamentar': lp}
                for k, v in EmendaLoa.TIPOEMENDALOA_CHOICE:
                    resumo_parlamentar[k] = {
                        'name': v
                    }
                    params = dict(
                        parlamentar=lp.parlamentar,
                        emendaloa__loa=self.object,
                        emendaloa__tipo=k
                    )

                    ja_destinado = EmendaLoaParlamentar.objects.filter(
                        **params).exclude(
                            emendaloa__fase=EmendaLoa.IMPEDIMENTO_TECNICO
                    ).aggregate(Sum('valor'))
                    resumo_parlamentar[k]['ja_destinado'] = ja_destinado['valor__sum'] or Decimal(
                        '0.00')

                    params.update(dict(
                        emendaloa__fase=EmendaLoa.IMPEDIMENTO_TECNICO
                    ))

                    impedimento_tecnico = EmendaLoaParlamentar.objects.filter(
                        **params).aggregate(Sum('valor'))
                    resumo_parlamentar[k]['impedimento_tecnico'] = impedimento_tecnico['valor__sum'] or Decimal(
                        '0.00')

                    if k == EmendaLoa.SAUDE:
                        resumo_parlamentar[k]['sem_destinacao'] = lp.disp_saude
                    elif k == EmendaLoa.DIVERSOS:
                        resumo_parlamentar[k]['sem_destinacao'] = lp.disp_diversos

                    resumo_parlamentar[k]['sem_destinacao'] -= \
                        resumo_parlamentar[k]['ja_destinado'] + \
                        resumo_parlamentar[k]['impedimento_tecnico']

                resumo_emendas_impositivas.append(resumo_parlamentar)
            context = dict(
                resumo_emendas_impositivas=resumo_emendas_impositivas,
            )

            rendered = template.render(context, self.request)

            return 'Resumo Geral das Emendas Impositivas Parlamentares', rendered


class EmendaLoaCrud(MasterDetailCrud):
    model = EmendaLoa
    parent_field = 'loa'
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        list_field_names = [
            ('finalidade', 'materia'),
            'valor',
            ('tipo', 'fase'),
            'parlamentares'
        ]

    class ListView(MasterDetailCrud.ListView):
        paginate_by = 25
        ordered_list = False

        def get_queryset(self):
            qs = super().get_queryset()

            p_id = self.request.GET.get('parlamentar', None)

            if p_id:
                qs = qs.filter(parlamentares=p_id)

            if self.request.user.is_anonymous:
                qs = qs.filter(loa__publicado=True)

            return qs

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            path = context.get('path', '')
            context['path'] = f'{path} emendaloa-list'

            emendaloa = context['object_list'].first()

            context['parlamentares'] = []
            if emendaloa:
                context['parlamentares'] = emendaloa.loa.parlamentares.all()

            p_id = self.request.GET.get('parlamentar', None)
            if p_id:
                p = emendaloa.loa.parlamentares.get(
                    id=p_id
                )
                context['title'] = f'{context["title"]}<br>Autoria: {p.nome_parlamentar}'

            return context

        def hook_fase(self, *args, **kwargs):
            return f'<br><small class="text-nowrap">({args[0].get_fase_display()})</small>', args[2]

        def hook_materia(self, *args, **kwargs):
            return f'<small><strong>Matéria Legislativa:</strong> {args[0].materia}</small>', args[2]

        def hook_parlamentares(self, *args, **kwargs):
            pls = []

            for elp in args[0].emendaloaparlamentar_set.all():
                pls.append(
                    '<tr><td>{}</td><td align="right">R$ {}</td></tr>'.format(
                        elp.parlamentar.nome_parlamentar,
                        formats.number_format(elp.valor)
                    )
                )

            return f'<table class="w-100 text-nowrap">{"".join(pls)}</table>', ''

        def hook_valor(self, *args, **kwargs):
            return f'<div class="text-right font-weight-bold">{args[1]}</div>', None

    class CreateView(MasterDetailCrud.CreateView):
        form_class = EmendaLoaForm

        def get_initial(self):
            initial = super().get_initial()
            initial['loa'] = Loa.objects.get(pk=self.kwargs['pk'])
            return initial

    class UpdateView(MasterDetailCrud.UpdateView):
        layout_key = None
        form_class = EmendaLoaForm

        def get_initial(self):
            initial = super().get_initial()
            initial['loa'] = self.object.loa
            if self.object.materia:
                initial['tipo_materia'] = self.object.materia.tipo.id
                initial['numero_materia'] = self.object.materia.numero
                initial['ano_materia'] = self.object.materia.ano
            return initial

    class DetailView(MasterDetailCrud.DetailView):

        @property
        def detail_list_url(self):
            if self.request.user.is_anonymous:
                return ''
            else:
                return super().detail_create_url

        @property
        def layout_key(self):
            if self.object.emendaloaparlamentar_set.all().count() > 2:
                return 'EmendaLoaDetail2'
            else:
                return 'EmendaLoaDetail'

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            path = context.get('path', '')
            context['path'] = f'{path} emendaloa-detail'
            return context

        def hook_documentos_acessorios(self, emendaloa, verbose_name='', field_display=''):
            docs = []

            for doc in emendaloa.materia.documentoacessorio_set.all():
                doc_template = loader.get_template(
                    'materia/documentoacessorio_widget_itemlist.html')
                context = {}
                context['object'] = doc
                rendered = doc_template.render(context, self.request)

                docs.append(
                    f'<tr><td>{rendered}</td></tr>'
                )

            return verbose_name, f'''
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
                        formats.number_format(elp.valor)
                    )
                )

            return verbose_name, f'''
                <div class="py-3">
                    <table class="table table-form table-bordered table-hover w-100">
                        {"".join(pls)}
                    </table>
                </div>
                '''

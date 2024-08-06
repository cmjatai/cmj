from decimal import Decimal
import logging

from django.db.models.aggregates import Sum
from django.template import loader
from django.utils import formats
from django.utils.translation import ugettext_lazy as _

from cmj.loa.forms import LoaForm, EmendaLoaForm
from cmj.loa.models import Loa, EmendaLoa, EmendaLoaParlamentar
from sapl.crud.base import Crud, MasterDetailCrud


class LoaCrud(Crud):
    model = Loa

    class BaseMixin(Crud.BaseMixin):
        list_field_names = [
            'ano',
            'receita_corrente_liquida',
            ('disp_total', 'perc_disp_total'),
            ('disp_saude', 'perc_disp_saude'),
            ('disp_diversos', 'perc_disp_diversos'),
            'publicado'
        ]

    class ListView(Crud.ListView):

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

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = [
            ('finalidade', 'materia'),
            ('tipo', 'fase'),
            'valor',
            ('parlamentares')
        ]

    class ListView(MasterDetailCrud.ListView):
        paginate_by = 25

        def hook_materia(self, *args, **kwargs):
            return f'<small><strong>Matéria Legislativa:</strong> {args[0].materia}</small>', args[2]

        def hook_parlamentares(self, *args, **kwargs):
            pls = []

            for elp in args[0].emendaloaparlamentar_set.all():
                pls.append(
                    '<tr><td class="py-1">{}</td><td class="py-1" align="right">R$ {}</td></tr>'.format(
                        elp.parlamentar.nome_parlamentar,
                        formats.number_format(elp.valor)
                    )
                )

            return f'<table class="w-100 m-0 text-nowrap">{"".join(pls)}</table>', ''

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
        layout_key = 'EmendaLoaDetail'

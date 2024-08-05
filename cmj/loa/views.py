import logging

from django.template import loader
from django.utils import formats
from django.utils.translation import ugettext_lazy as _

from cmj.loa.forms import LoaForm, EmendaLoaForm
from cmj.loa.models import Loa, EmendaLoa
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
            context = dict(
                loaparlamentar_set=l.loaparlamentar_set.order_by(
                    'parlamentar__nome_parlamentar'),
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

        def hook_materia(self, *args, **kwargs):
            return f'<small><strong>Matéria Legislativa:</strong> {args[0].materia}</small>', args[2]

        def hook_parlamentares(self, *args, **kwargs):
            pls = []

            for elp in args[0].emendaloaparlamentar_set.all():
                pls.append(
                    '<li>{} - R$ {}</li>'.format(
                        elp.parlamentar.nome_parlamentar,
                        formats.number_format(elp.valor)
                    )
                )

            return f'<ul class="m-0 text-nowrap">{"".join(pls)}</ul>', ''

    class CreateView(MasterDetailCrud.CreateView):
        form_class = EmendaLoaForm

        def get_initial(self):
            initial = super().get_initial()

            initial['loa'] = Loa.objects.get(pk=self.kwargs['pk'])
            return initial

    class UpdateView(MasterDetailCrud.UpdateView):
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

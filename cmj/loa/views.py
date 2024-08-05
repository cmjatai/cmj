import logging

from django.template import loader
from django.utils.translation import ugettext_lazy as _

from cmj.loa.forms import LoaForm
from cmj.loa.models import Loa
from sapl.crud.base import Crud


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

    class UpdateView(Crud.UpdateView):
        layout_key = 'Loa'
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
        form_class = LoaForm

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
                loaparlamentar_set=l.loaparlamentar_set.all(),
            )
            rendered = template.render(context, self.request)

            return 'Resumo Geral das Emendas Impositivas Parlamentares', rendered

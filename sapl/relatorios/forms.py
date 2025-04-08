
from crispy_forms.bootstrap import (FormActions)
from crispy_forms.layout import (HTML, Button, Fieldset,
                                 Layout, Submit)
from django import forms
from django.utils.translation import gettext_lazy as _
import django_filters

from sapl.crispy_layout_mixin import form_actions, to_row
from sapl.crispy_layout_mixin import SaplFormHelper
from sapl.materia.models import MateriaLegislativa

from sapl.utils import FilterOverridesMetaMixin, autor_label, autor_modal


class RelatorioMateriasPorAutorFilterSet(django_filters.FilterSet):

    autoria__autor = django_filters.CharFilter(widget=forms.HiddenInput())

    #@property
    # def qs(self):
    #    parent = super().qs
    # return parent.order_by('autoria__autor', '-ano',
    # 'tipo__sequencia_regimental', '-numero').distinct()

    @property
    def qs(self):
        qs = super().qs
        return qs.select_related('tipo').order_by('tipo__sequencia_regimental', '-numero')

    class Meta(FilterOverridesMetaMixin):
        model = MateriaLegislativa
        fields = ['tipo', 'data_apresentacao']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Matéria'

        row1 = to_row(
            [('tipo', 12)])
        row2 = to_row(
            [('data_apresentacao', 12)])
        row3 = to_row(
            [('autoria__autor', 0),
             (Button('pesquisar',
                     'Pesquisar Autor',
                     css_class='btn btn-primary btn-sm'), 2),
             (Button('limpar',
                     'limpar Autor',
                     css_class='btn btn-primary btn-sm'), 10)])

        buttons = FormActions(
            *[
                HTML('''
                        <div class="form-check">
                            <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                            <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                        </div>
                    ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )
        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisar'),
                     row1, row2,
                     HTML(autor_label),
                     HTML(autor_modal),
                     row3,
                     buttons, )
        )

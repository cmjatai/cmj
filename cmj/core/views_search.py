import re

from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from django.utils.translation import ugettext_lazy as _
from haystack.forms import ModelSearchForm
from haystack.views import SearchView

from cmj.crispy_layout_mixin import to_row
from sapl.crispy_layout_mixin import SaplFormLayout


class CmjSearchForm(ModelSearchForm):

    def __init__(self, *args, **kwargs):

        q_field = Div(
            FieldWithButtons(
                Field('q',
                      placeholder=_('Busca Textual'),
                      autocomplete='off',
                      type='search',),
                StrictButton(
                    _('Pesquisar'), css_class='btn-outline-primary',
                    type='submit')
            )
        )

        row = to_row([(q_field, 8), (Div(Field('models')), 5)])

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(*row)

        super().__init__(*args, **kwargs)

        choices = self.fields['models'].choices
        for i, v in enumerate(choices):
            if v[0] == 'sigad.documento':
                choices[i] = (v[0], _('Notícias'))
        self.fields['models'].choices = sorted(choices, key=lambda x: x[1])
        self.fields['models'].label = _('Buscar em conteúdos específicos')

    def search(self):
        sqs = super().search()
        return sqs.order_by('-data')


class CmjSearchView(SearchView):
    results_per_page = 10

    def __init__(self, template=None, load_all=True, form_class=None, searchqueryset=None, results_per_page=None):
        super().__init__(
            template=template,
            load_all=load_all,
            form_class=CmjSearchForm,
            searchqueryset=None,
            results_per_page=results_per_page)

    def get_context(self):
        context = super().get_context()
        context['title'] = _('Pesquisa Textual')

        if 'models' in self.request.GET:
            models = self.request.GET.getlist('models')
        else:
            models = []

        context['models'] = ''

        for m in models:
            context['models'] = context['models'] + '&models=' + m
        return context

import re

from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from django.utils.translation import ugettext_lazy as _
from haystack.forms import ModelSearchForm
from haystack.views import SearchView

from cmj.utils import make_pagination
from sapl.crispy_layout_mixin import to_row


class CmjSearchForm(ModelSearchForm):

    def no_query_found(self):
        return self.searchqueryset.all().order_by('-data')

    def __init__(self, *args, **kwargs):

        q_field = Div(
            FieldWithButtons(
                Field('q',
                      placeholder=_('Busca Textual'),
                      type='search',),
                StrictButton(
                    _('<i class="fas fa-2x fa-search"></i>'), css_class='btn-outline-primary',
                    type='submit')
            )
        )

        row = to_row([(Div(), 2), (q_field, 8), (Div(Field('models')), 12)])

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(*row)

        super().__init__(*args, **kwargs)

        choices = self.fields['models'].choices
        for i, v in enumerate(choices):
            if v[0] == 'sigad.documento':
                choices[i] = (v[0], _('Notícias'))
        self.fields['models'].choices = sorted(choices, key=lambda x: x[1])
        self.fields['models'].label = _('Buscar em conteúdos específicos:')
        self.fields['q'].label = ''

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
        context['is_paginated'] = True

        page_obj = context['page']
        context['page_obj'] = page_obj
        paginator = context['paginator']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        qr = self.request.GET.copy()
        if 'page' in qr:
            del qr['page']
        context['filter_url'] = (
            '&' + qr.urlencode()) if len(qr) > 0 else ''

        for m in models:
            context['models'] = context['models'] + '&models=' + m
        return context

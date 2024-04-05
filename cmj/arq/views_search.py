import re

from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from django import forms
from django.db.models import Q
from django.http.request import QueryDict
from django.urls.base import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from haystack.forms import ModelSearchForm, SearchForm, model_choices
from haystack.query import SearchQuerySet
from haystack.utils.app_loading import haystack_get_model
from haystack.views import SearchView

from cmj.core.models import AreaTrabalho
from cmj.haystack import CMJARQ_ALIAS
from cmj.utils import make_pagination
from sapl.crispy_layout_mixin import to_row


class ArqSearchForm(ModelSearchForm):

    conta_classe_logica = forms.CharField(
        required=False, label=_('Conta'),
        widget=forms.HiddenInput())

    def no_query_found(self):
        return self.searchqueryset.all().order_by('-data')

    def __init__(self, *args, **kwargs):

        self.user = kwargs.pop('user')

        q_field = Div(
            FieldWithButtons(
                Field('q',
                      placeholder=_('O que você procura?'),
                      type='search',),
                StrictButton(
                    '<i class="fas fa-2x fa-search"></i>',
                    css_class='btn-outline-primary',
                    type='submit'),
                css_class='div-search'
            ),
        )

        row = to_row([('conta_classe_logica', 2), (q_field, 8), ])

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_method = 'post'
        self.helper.layout = Layout(*row)

        self.searchqueryset = SearchQuerySet(using=CMJARQ_ALIAS)

        super(ModelSearchForm, self).__init__(*args, **kwargs)
        self.fields['models'] = forms.MultipleChoiceField(
            choices=model_choices(using=CMJARQ_ALIAS),
            required=False,
            label=_('Search In'),
            widget=forms.MultipleHiddenInput)

        self.fields['q'].label = ''

    def search(self):
        sqs = super().search()

        conta_classe_logica = self.cleaned_data.get(
            'conta_classe_logica', None)

        if conta_classe_logica:
            sqs = sqs.filter(
                conta_classe_logica__startswith=conta_classe_logica)

        kwargs = {
            'hl.simple.pre': '<span class="highlighted">',
            'hl.simple.post': '</span>',
            'hl.fragsize': 512
        }

        s = sqs.highlight(**kwargs).order_by('-data', '-last_update')
        return s

    def get_models(self):
        """Return a list of the selected models."""
        search_models = []

        if self.is_valid():
            for model in self.cleaned_data['models']:
                search_models.append(haystack_get_model(*model.split('.')))

        return search_models

        return ModelSearchForm.get_models(self)


class ArqSearchView(SearchView):
    results_per_page = 50
    template = 'arq/search.html'

    def __init__(self, template=None, load_all=True, form_class=None, searchqueryset=None, results_per_page=None):
        super().__init__(
            template=template,
            load_all=load_all,
            form_class=ArqSearchForm,
            searchqueryset=SearchQuerySet(using=CMJARQ_ALIAS),
            results_per_page=results_per_page)

    def build_form(self, form_kwargs=None):

        user = self.request.user
        kwargs = {
            'user': user,
            'load_all': self.load_all,
        }

        if form_kwargs:
            kwargs.update(form_kwargs)

        data = self.request.GET or self.request.POST

        if self.searchqueryset is not None:
            kwargs['searchqueryset'] = self.searchqueryset

        kwargs['data'] = data

        return self.form_class(**kwargs)

    def get_context(self):
        context = super().get_context()
        #context['title'] = _('Pesquisa Textual')

        data = self.request.GET or self.request.POST

        data = data.copy()
        context['q'] = data.get('q', '')

        if 'csrfmiddlewaretoken' in data:
            del data['csrfmiddlewaretoken']

        context['is_paginated'] = True

        page_obj = context['page']
        context['page_obj'] = page_obj
        paginator = context['paginator']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        if 'page' in data:
            del data['page']

        context['filter_url'] = (
            '&' + data.urlencode()) if len(data) > 0 else ''

        return context

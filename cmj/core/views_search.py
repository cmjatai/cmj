import re

from django.utils.translation import ugettext_lazy as _
from haystack.forms import ModelSearchForm
from haystack.views import SearchView


class CmjSearchForm(ModelSearchForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        choices = self.fields['models'].choices
        for i, v in enumerate(choices):
            if v[0] == 'sigad.documento':
                choices[i] = (v[0], _('Notícias'))
        self.fields['models'].choices = sorted(choices, key=lambda x: x[1])

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

from builtins import property

from django.utils.translation import ugettext_lazy as _
from haystack.views import SearchView


class CmjSearchView(SearchView):
    results_per_page = 10

    """def __init__(self, template=None, load_all=True, form_class=None, searchqueryset=None, results_per_page=None):
        super().__init__(
            template=template,
            load_all=load_all,
            form_class=SearchForm,
            searchqueryset=searchqueryset,
            results_per_page=results_per_page)"""

    def get_context(self):
        context = super().get_context()
        context['title'] = _('Pesquisa Textual')
        return context

        if 'models' in self.request.GET:
            models = self.request.GET.getlist('models')
        else:
            models = []

        context['models'] = ''

        for m in models:
            context['models'] = context['models'] + '&models=' + m

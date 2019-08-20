import re

from django.utils.translation import ugettext_lazy as _
from haystack.forms import ModelSearchForm
from haystack.inputs import BaseInput, Exact, Not, Clean
from haystack.query import SearchQuerySet
from haystack.views import SearchView


class CmjQueryArgs(BaseInput):
    input_type_name = 'cmj_query'
    post_process = False
    exact_match_re = re.compile(r'"(?P<phrase>.*?)"')

    def pre_prepare(self, query_obj):
        query_string = super(CmjQueryArgs, self).prepare(query_obj)
        exacts = self.exact_match_re.findall(query_string)
        tokens = []
        query_bits = []

        for rough_token in self.exact_match_re.split(query_string):
            if not rough_token:
                continue
            elif not rough_token in exacts:
                # We have something that's not an exact match but may have more
                # than on word in it.
                tokens.extend(rough_token.split(' '))
            else:
                tokens.append(rough_token)

        return tokens

    def prepare(self, query_obj):

        query_string = super(CmjQueryArgs, self).prepare(query_obj)
        exacts = self.exact_match_re.findall(query_string)
        tokens = []
        query_bits = []

        for rough_token in self.exact_match_re.split(query_string):
            if not rough_token:
                continue
            elif not rough_token in exacts:
                # We have something that's not an exact match but may have more
                # than on word in it.
                tokens.extend(rough_token.split(' '))
            else:
                tokens.append(rough_token)

        for token in tokens:
            if not token:
                continue
            if token in exacts:
                query_bits.append(Exact(token, clean=True).prepare(query_obj))
            elif token.startswith('-') and len(token) > 1:
                # This might break Xapian. Check on this.
                query_bits.append(Not(token[1:]).prepare(query_obj))
            else:
                query_bits.append(Clean(token).prepare(query_obj))
        return u' '.join(query_bits)


class CmjSearchQuerySet(SearchQuerySet):

    def auto_query(self, query_string, fieldname='content'):

        cmj_query = CmjQueryArgs(query_string)
        query_bits = cmj_query.pre_prepare(query_string)

        args = []
        for qb in query_bits:
            args.append(('content', CmjQueryArgs(qb)))
        return self.filter(*args)


class CmjSearchForm(ModelSearchForm):
    def no_query_found(self):
        return self.searchqueryset.all()

    def search(self):
        if not self.is_valid():
            return self.no_query_found()

        if not self.cleaned_data.get('q'):
            return self.no_query_found()

        sqs = self.searchqueryset.auto_query(self.cleaned_data['q'])

        if self.load_all:
            sqs = sqs.load_all()

        return sqs.models(*self.get_models()).filter().order_by('-data')


class CmjSearchView(SearchView):
    results_per_page = 10

    def __init__(self, template=None, load_all=True, form_class=None, searchqueryset=None, results_per_page=None):
        super().__init__(
            template=template,
            load_all=load_all,
            form_class=CmjSearchForm,
            searchqueryset=CmjSearchQuerySet(),
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

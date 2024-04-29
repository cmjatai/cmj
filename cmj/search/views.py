import re

from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from django import forms
from django.db.models import Q
from django.http.request import QueryDict
from django.utils.translation import ugettext_lazy as _
from haystack.forms import ModelSearchForm
from haystack.utils.app_loading import haystack_get_model
from haystack.views import SearchView

from cmj.core.models import AreaTrabalho
from cmj.mixins import AudigLogFilterMixin
from cmj.utils import make_pagination
from sapl.crispy_layout_mixin import to_row
from sapl.utils import RangeWidgetNumber


class RangeIntegerField(forms.IntegerField):
    def clean(self, value):
        vr = []
        for v in value:
            vr.append(forms.IntegerField.clean(self, v))

        # if v[0] and v[1]:
        #    vr.sort()
        return vr


class CmjSearchForm(ModelSearchForm):

    ano = RangeIntegerField(
        required=False,
        label=_('Incluir filtro por ano?'),
        help_text=_('''É opcional limitar a busca em um período específico.<br>
        Você pode informar simultaneamente, formando um período específico, os campos Inicial e Final, ou apenas um, ou nenhum deles.'''),
        widget=RangeWidgetNumber()
    )

    fix_model = forms.CharField(
        required=False, label=_('FixModel'),
        widget=forms.HiddenInput())

    def no_query_found(self):
        return self.searchqueryset.order_by('-data')

    def __init__(self, *args, **kwargs):

        self.workspaces = kwargs.pop('workspaces')
        self.user = kwargs.pop('user')

        q_field = Div(
            'fix_model',
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

        row = to_row([
            (Div(), 2),
            (q_field, 8),
            ('ano', 4),
            (Div(Field('models')), 8),
        ])

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_method = 'post'
        self.helper.layout = Layout(*row)

        super().__init__(*args, **kwargs)

        choices = self.fields['models'].choices
        for i, v in enumerate(choices):
            if v[0] == 'sigad.documento':
                choices[i] = (v[0], _('Notícias'))
            elif v[0] == 'materia.documentoacessorio':
                choices[i] = (
                    v[0], _('Documentos Acessórios vinculados a Matérias Legislativas'))
            elif v[0] == 'protocoloadm.documentoadministrativo':
                if not self.workspaces:
                    choices[i] = (None, None)
                else:
                    if not self.user.is_anonymous and \
                            self.user.areatrabalho_set.exists() and \
                            not self.user.has_perm('protocoloadm.list_documentoadministrativo'):

                        self.workspaces = AreaTrabalho.objects.areatrabalho_publica()
                        #choices[i] = (None, None)
                        # continue

                    choices[i] = (v[0], '%s (%s)' % (
                        v[1], ', '.join(map(str, self.workspaces))
                    ))

        self.fields['models'].choices = sorted(
            filter(lambda x: x[0], choices),

            key=lambda x: x[1])

        self.fields['models'].label = _('Buscar em conteúdos específicos?')
        self.fields['q'].label = ''

        if args and isinstance(args[0], QueryDict):
            query_dict = args[0]
            fix_model = query_dict.get('fix_model', '')
            if fix_model:
                self.fields['models'].widget = forms.MultipleHiddenInput()

    def search(self):
        sqs = super().search()

        if self.workspaces:
            sqs = sqs.filter(
                Q(at=0) |
                Q(at__in=self.workspaces.values_list('id', flat=True)))
        else:
            sqs = sqs.filter(at=0)

        a = self.cleaned_data.get('ano', None)

        if a and a[0] and a[1]:
            sqs = sqs.filter(ano__range=a)
        elif a and a[0]:
            sqs = sqs.filter(ano__gte=a[0])
        elif a and a[1]:
            sqs = sqs.filter(ano__lte=a[1])

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


class CmjSearchView(AudigLogFilterMixin, SearchView):
    results_per_page = 20

    def __call__(self, request):
        self.log(request)
        return SearchView.__call__(self, request)

    def __init__(self, template=None, load_all=True, form_class=None, searchqueryset=None, results_per_page=None):
        super().__init__(
            template=template,
            load_all=load_all,
            form_class=CmjSearchForm,
            searchqueryset=None,
            results_per_page=results_per_page)

    def build_form(self, form_kwargs=None):

        user = self.request.user
        kwargs = {
            'workspaces': None,
            'user': user,
            'load_all': self.load_all,
        }

        if not user.is_anonymous and user.areatrabalho_set.exists():

            at = user.areatrabalho_set.all()
            #.union(
            #   AreaTrabalho.objects.areatrabalho_publica())
            kwargs['workspaces'] = at
        else:
            kwargs['workspaces'] = AreaTrabalho.objects.areatrabalho_publica()

        if form_kwargs:
            kwargs.update(form_kwargs)

        data = self.request.GET or self.request.POST

        if self.searchqueryset is not None:
            kwargs['searchqueryset'] = self.searchqueryset

        return self.form_class(data, **kwargs)

    def get_context(self):
        context = super().get_context()
        #context['title'] = _('Pesquisa Textual')

        data = self.request.GET or self.request.POST

        data = data.copy()
        if 'csrfmiddlewaretoken' in data:
            del data['csrfmiddlewaretoken']

        if 'models' in data:
            models = data.getlist('models')
        else:
            models = []

        context['models'] = ''
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

        for m in models:
            context['models'] = context['models'] + '&models=' + m
        return context

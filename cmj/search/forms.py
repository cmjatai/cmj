from collections import OrderedDict

from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, HTML, Button, Fieldset
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http.request import QueryDict
from django.utils.translation import gettext_lazy as _
from haystack.backends import SQ
from haystack.forms import ModelSearchForm, SearchForm
from haystack.inputs import Raw
from haystack.models import SearchResult
from haystack.utils.app_loading import haystack_get_model

from cmj.core.models import AreaTrabalho
from cmj.utils import NONE_YES_NO_CHOICES
from sapl.crispy_layout_mixin import to_row
from sapl.materia.forms import CHOICE_TRAMITACAO, MateriaLegislativaFilterSet,\
    CHOICE_TIPO_LISTAGEM
from sapl.materia.models import TipoMateriaLegislativa, UnidadeTramitacao,\
    StatusTramitacao, MateriaLegislativa, AssuntoMateria
from sapl.norma.models import TipoNormaJuridica, NormaJuridica, AssuntoNorma
from sapl.utils import RangeWidgetNumber, choice_anos_com_materias, autor_label,\
    autor_modal, choice_anos_com_normas


class RangeIntegerField(forms.IntegerField):
    def clean(self, value):
        vr = []
        for v in value:
            vr.append(forms.IntegerField.clean(self, v))

        # if v[0] and v[1]:
        #    vr.sort()
        return vr


class CmjSearchForm(ModelSearchForm):

    ano_i = RangeIntegerField(
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
        return self.searchqueryset.order_by('-data_dt')

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
            ('ano_i', 4),
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
            at__in = list(self.workspaces.values_list('id', flat=True))
            at__in.append(0)
            sqs = sqs.filter(at__in=at__in)
        else:
            sqs = sqs.filter(at=0)

        a = self.cleaned_data.get('ano_i', None)

        if a and a[0] and a[1]:
            sqs = sqs.filter(ano_i__range=a)
        elif a and a[0]:
            sqs = sqs.filter(ano_i__gte=a[0])
        elif a and a[1]:
            sqs = sqs.filter(ano_i__lte=a[1])

        kwargs = {
            'hl.simple.pre': '<span class="highlighted">',
            'hl.simple.post': '</span>',
            'hl.fragsize': 512
        }
        s = sqs.highlight(**kwargs).order_by('-data_dt', '-last_update')

        # print(str(s.query))
        return s

    def get_models(self):
        """Return a list of the selected models."""
        search_models = []

        if self.is_valid():
            for model in self.cleaned_data['models']:
                search_models.append(haystack_get_model(*model.split('.')))

        return search_models

        return ModelSearchForm.get_models(self)


def CHOICE_ORDENACAO():
    return [
            ('D', 'Mais Recentes'),
            ('R', 'Relevância'),
            ]


class MateriaSearchForm(SearchForm):

    _errors = []

    ano_i = forms.ChoiceField(
        required=False,
        label=_('Ano da Matéria'),
        choices=[(None, _('---------')), ] + choice_anos_com_materias())

    numero_i = forms.IntegerField(
        required=False,
        label=_('Número'),
    )

    em_tramitacao_b = forms.TypedChoiceField(
        required=False,
        label=_('Em tramitação'),
        choices=CHOICE_TRAMITACAO
    )

    ordenacao = forms.TypedChoiceField(
        required=False,
        label=_('Ordenação'),
        choices=CHOICE_ORDENACAO
    )

    tipo_i = forms.ModelMultipleChoiceField(
        required=False,
        queryset=TipoMateriaLegislativa.objects.all(),
        label=_('Tipos de Matéria Legislativa'),
        widget=forms.SelectMultiple(attrs={
            'title': _('Filtrar por um ou mais tipos de matéria?'),
            'class': 'selectpicker',
            'data-actions-box': 'true',
            'data-select-all-text': 'Selecionar Todos',
            'data-deselect-all-text': 'Desmarcar Todos',
            'data-header': 'Tipos de Matéria Legislativa',
            'data-dropup-auto': 'false'
        })
    )

    uta_i = forms.ModelMultipleChoiceField(
        required=False,
        queryset=UnidadeTramitacao.objects.all(),
        label=_('Unidade de tramitação atual'),
        widget=forms.SelectMultiple(attrs={
            'title': _('Filtrar por uma ou mais unidades?'),
            'class': 'selectpicker',
            'data-actions-box': 'true',
            'data-select-all-text': 'Selecionar Todos',
            'data-deselect-all-text': 'Desmarcar Todos',
            'data-header': 'Unidade de tramitação atual',
            'data-dropup-auto': 'false'
        })
    )

    sta_i = forms.ModelMultipleChoiceField(
        required=False,
        queryset=StatusTramitacao.objects.all(),
        label=_('Status da tramitação atual'),
        widget=forms.SelectMultiple(attrs={
            'title': _('Filtrar por um ou mais Status?'),
            'class': 'selectpicker',
            'data-actions-box': 'true',
            'data-select-all-text': 'Selecionar Todos',
            'data-deselect-all-text': 'Desmarcar Todos',
            'data-header': 'Status da tramitação atual',
            'data-dropup-auto': 'false',
            'data-dropdown-align-right': 'auto'
        })
    )

    assuntos_is = forms.ModelMultipleChoiceField(
        required=False,
        queryset=AssuntoMateria.objects.all(),
        label=_('Assuntos'),
        widget=forms.SelectMultiple(attrs={
            'title': _('Filtrar por um ou mais Assuntos?'),
            'class': 'selectpicker',
            'data-actions-box': 'true',
            'data-select-all-text': 'Selecionar Todos',
            'data-deselect-all-text': 'Desmarcar Todos',
            'data-header': 'Assuntos',
            'data-dropup-auto': 'false',
            'data-dropdown-align-right': 'auto'
        })
    )

    tipo_listagem = forms.ChoiceField(
        required=False,
        choices=CHOICE_TIPO_LISTAGEM,
        label=_('Tipo da Pesquisa'))

    autoria_is = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_autoria__autor'}))

    def no_query_found(self):
        if not self.data:
            return super().no_query_found()

        return self.searchqueryset.all()

    def __init__(self, *args, **kwargs):

        q_field = Div(
            FieldWithButtons(
                Field('q',
                      placeholder=_(
                          'O que você procura? '),
                      type='search',),
                StrictButton(
                    '<i class="fas fa-2x fa-search"></i>',
                    css_class='btn-outline-primary',
                    type='submit'),
                css_class='div-search'
            ),
        )

        row1 = to_row([
            (HTML('''
                <small class="text-blue">
                  <strong>
                    O PREENCHIMENTO DOS CAMPOS ABAIXO É OPCIONAL... &nbsp;&nbsp;
                    Clique na lupa após definir seus critérios de pesquisa.
                  </strong>
                </small>'''), 12),

            (Div(), 2),
            (q_field, 8),
            (Div(), 2),

            ('em_tramitacao_b', 2),
            ('tipo_i', 4),
            ('numero_i', 2),
            ('ano_i', 2),
            ('tipo_listagem', 2)
        ])

        row2 = to_row([
            (Div(
                HTML(autor_label),
                HTML(autor_modal),
                to_row([
                    ('autoria_is', 0),
                    (Button('pesquisar',
                            'Selecionar Autor',
                            css_class='btn btn-secondary btn-sm mt-1'), 'pl-4'),
                    (Button('limpar',
                            'limpar Autor',
                            css_class='btn btn-secondary btn-sm mt-1'), 6),
                ]),
                css_class="form-group"
            ), 2),
            ('uta_i', 3),
            ('sta_i', 3),
            ('assuntos_is', 2),
            ('ordenacao', 2),
        ])

        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.layout = Layout(
            Fieldset('',
                     row1,
                     row2)
        )

        super().__init__(*args, **kwargs)

        self.fields['q'].label = ''

        grupos_de_tipos = (
            ('1', 'Mais Acessadas'),
            ('3', ' '),
            ('7', 'Matérias Acessórias'),
            ('9', '  ')
        )
        gtd = {k: v for k, v in grupos_de_tipos}

        grupo_choices = OrderedDict()
        for nivel, valor in grupos_de_tipos:
            if valor not in grupo_choices:
                grupo_choices[valor] = []

        for tml in TipoMateriaLegislativa.objects.order_by('nivel_agrupamento', 'sequencia_regimental'):
            grupo_choices[gtd[tml.nivel_agrupamento]].append(
                (tml.id, f'{tml.sigla} - {tml.descricao}'))

        choices = []
        for g, items in grupo_choices.items():
            choices.append((' ', items,))
        self.fields['tipo_i'].choices = choices

        uta_choices = OrderedDict()
        for uta in UnidadeTramitacao.objects.all():
            uta_obj = uta.comissao or uta.orgao or uta.parlamentar

            grupo = uta_obj._meta.verbose_name_plural
            if grupo not in uta_choices:
                uta_choices[grupo] = []

            uta_choices[grupo].append((uta.id, str(uta)))

        self.fields['uta_i'].choices = uta_choices.items()

    def clean_tipo_i(self, *args, **kwargs):
        tipo_i = self.cleaned_data['tipo_i']
        return tipo_i.values_list('id', flat=True)
        if tipo_i:
            return tipo_i.id

    def clean_em_tramitacao_b(self, *args, **kwargs):
        em_tramitacao_b = self.cleaned_data['em_tramitacao_b']

        if em_tramitacao_b:
            return em_tramitacao_b == '1'
        return None

    def clean_uta_i(self, *args, **kwargs):
        uta_i = self.cleaned_data['uta_i']
        return uta_i.values_list('id', flat=True)

        if uta_i:
            return uta_i.id

    def clean_sta_i(self, *args, **kwargs):
        sta_i = self.cleaned_data['sta_i']
        return sta_i.values_list('id', flat=True)

        if sta_i:
            return sta_i.id

    def clean_ordenacao(self, *args, **kwargs):
        o = self.cleaned_data['ordenacao']
        return o

    def clean_ano_i(self, *args, **kwargs):
        a = self.cleaned_data['ano_i']
        if not a:
            return
        try:
            a = int(a)
            return a
        except:
            raise ValidationError(
                _('O campo "ano da matéria" deve ser um número.'))

    def clean_assuntos_is(self, *args, **kwargs):
        assuntos_is = self.cleaned_data['assuntos_is']

        return assuntos_is.values_list('id', flat=True)

        if assuntos_is:
            return assuntos_is.id

    def search(self):
        sqs = super().search().models(MateriaLegislativa)

        remove = ('q', 'tipo_listagem')

        params = {
            key: self.cleaned_data.get(key, None)
            for key in self.changed_data if key not in remove
        }

        if params and 'tipo_i' in params:
            params['tipo_i__in'] = params['tipo_i']
            del params['tipo_i']

        if params and 'uta_i' in params:
            params['uta_i__in'] = params['uta_i']
            del params['uta_i']

        if params and 'sta_i' in params:
            params['sta_i__in'] = params['sta_i']
            del params['sta_i']

        if params and 'assuntos_is' in params:
            params['assuntos_is__in'] = params['assuntos_is']
            del params['assuntos_is']

        ord = '-data_dt'
        if params and 'ordenacao' in params:
            ord = self.cleaned_data.get('ordenacao', 'D')
            ord = '-data_dt' if ord == 'D' else '-score'
            del params['ordenacao']

        if params:
            sqs = sqs.filter(**params)

        kwargs = {
            'hl.simple.pre': '<span class="highlighted">',
            'hl.simple.post': '</span>',
            'hl.fragsize': 512
        }

        s = sqs.highlight(**kwargs).order_by(
            ord,
            '-pk_i',
            '-last_update'
        )
        return s


class NormaSearchForm(SearchForm):

    _errors = []

    ano_i = forms.ChoiceField(
        required=False,
        label=_('Ano da Norma'),
        choices=[(None, _('---------')), ] + choice_anos_com_normas())

    numero_s = forms.CharField(
        required=False,
        label=_('Número'),
    )

    tipo_i = forms.ModelChoiceField(
        required=False,
        queryset=TipoNormaJuridica.objects.all(),
        label=_('Tipo de Norma Jurídica'),
    )

    assuntos_is = forms.ModelChoiceField(
        required=False,
        queryset=AssuntoNorma.objects.all(),
        label=_('Assuntos'),
    )

    ordenacao = forms.TypedChoiceField(
        required=False,
        label=_('Ordenação'),
        choices=CHOICE_ORDENACAO
    )

    def no_query_found(self):
        if not self.data:
            return super().no_query_found()

        return self.searchqueryset.order_by('-data_dt')

    def __init__(self, *args, **kwargs):

        q_field = Div(
            FieldWithButtons(
                Field('q',
                      placeholder=_(
                          'O que você procura? '),
                      type='search',),
                StrictButton(
                    '<i class="fas fa-2x fa-search"></i>',
                    css_class='btn-outline-primary',
                    type='submit'),
                css_class='div-search'
            ),
        )

        row1 = to_row([
            (HTML('''
                <small class="text-blue">
                  <strong>
                    O PREENCHIMENTO DOS CAMPOS ABAIXO É OPCIONAL... &nbsp;&nbsp;
                    Clique na lupa após definir seus critérios de pesquisa.
                  </strong>
                </small>'''), 12),

            (Div(), 2),
            (q_field, 8),
            (Div(), 2),

            ('tipo_i', 3),
            ('numero_s', 2),
            ('ano_i', 2),
            ('assuntos_is', 3),
            ('ordenacao', 2),
        ])

        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.layout = Layout(
            Fieldset('',
                     row1)
        )

        super().__init__(*args, **kwargs)

        self.fields['q'].label = ''
        #self.fields['models'].widget = forms.MultipleHiddenInput()

    def clean_tipo_i(self, *args, **kwargs):
        tipo_i = self.cleaned_data['tipo_i']

        if tipo_i:
            return tipo_i.id

    def clean_numero_s(self, *args, **kwargs):
        numero_s = self.cleaned_data['numero_s']

        if numero_s:
            return f'{numero_s:>06}'

    def clean_assuntos_is(self, *args, **kwargs):
        assuntos_is = self.cleaned_data['assuntos_is']

        if assuntos_is:
            return assuntos_is.id

    def clean_ano_i(self, *args, **kwargs):
        a = self.cleaned_data['ano_i']
        if not a:
            return
        try:
            a = int(a)
            return a
        except:
            raise ValidationError(
                _('O campo "Ano da Norma" deve ser um número.'))

    def search(self):
        sqs = super().search().models(NormaJuridica)

        remove = ('q',)

        params = {
            key: self.cleaned_data.get(key, None)
            for key in self.changed_data if key not in remove
        }

        ord = '-data_dt'
        if params and 'ordenacao' in params:
            ord = self.cleaned_data.get('ordenacao', 'D')
            ord = '-data_dt' if ord == 'D' else '-score'
            del params['ordenacao']

        if params:
            sqs = sqs.filter(**params)

        kwargs = {
            'hl.simple.pre': '<span class="highlighted">',
            'hl.simple.post': '</span>',
            'hl.fragsize': 512
        }

        s = sqs.highlight(**kwargs).order_by(
            ord,
            '-numero_s',
            '-last_update'
        )
        return s

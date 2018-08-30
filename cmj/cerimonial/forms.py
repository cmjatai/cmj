from _functools import reduce
from datetime import date, timedelta
import datetime
import decimal
import operator

from crispy_forms.bootstrap import InlineRadios, FieldWithButtons, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Row, Layout, Fieldset, Div, Button,\
    Submit, BaseInput
from crispy_forms.templatetags.crispy_forms_field import css_class
from crispy_forms.utils import get_template_pack
from dateutil.relativedelta import relativedelta
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.expressions import Func
from django.forms import widgets
from django.forms.models import ModelForm, ModelMultipleChoiceField
from django.http.request import QueryDict
from django.utils.translation import ugettext_lazy as _
from django_filters.filters import CharFilter, ChoiceFilter, NumberFilter,\
    ModelChoiceFilter, RangeFilter,\
    MultipleChoiceFilter, ModelMultipleChoiceFilter, Filter
from django_filters.filterset import FilterSet, STRICTNESS
from sapl.crispy_layout_mixin import to_column, SaplFormLayout, to_fieldsets,\
    form_actions, to_row

from cmj import settings
from cmj.cerimonial.models import LocalTrabalho, Endereco,\
    TipoAutoridade, PronomeTratamento, Contato, Perfil, Processo,\
    IMPORTANCIA_CHOICE, AssuntoProcesso, StatusProcesso, ProcessoContato,\
    GrupoDeContatos, TopicoProcesso
from cmj.core.forms import ListWithSearchForm
from cmj.core.models import Municipio, Trecho, ImpressoEnderecamento
from cmj.utils import normalize, YES_NO_CHOICES


class ListTextWidget(forms.TextInput):

    def __init__(self, data_list, name, *args, **kwargs):
        super(ListTextWidget, self).__init__(*args, **kwargs)
        self._name = name
        self._list = data_list
        self.attrs.update({'list': 'list__%s' % self._name})

    def render(self, name, value, attrs=None):
        text_html = super(ListTextWidget, self).render(
            name, value, attrs=attrs)
        data_list = '<datalist id="list__%s">' % self._name
        for item in self._list:
            data_list += '<option value="%s">' % item
        data_list += '</datalist>'

        return (text_html + data_list)


class LocalTrabalhoPerfilForm(ModelForm):

    class Meta:
        model = LocalTrabalho
        fields = ['nome',
                  'nome_social',
                  'data_inicio',
                  'data_fim',
                  'tipo',
                  'trecho',
                  'endereco',
                  'numero',
                  'complemento',
                  'distrito',
                  'regiao_municipal',
                  'cep',
                  'bairro',
                  'municipio',
                  'uf',
                  'preferencial', 'cargo']

    def __init__(self, *args, **kwargs):

        instance = None
        super(LocalTrabalhoPerfilForm, self).__init__(*args, **kwargs)

        if isinstance(self.instance, LocalTrabalho):
            instance = self.instance

        if not instance:
            self.fields['uf'].initial = settings.INITIAL_VALUE_FORMS_UF
            self.fields['cep'].initial = settings.INITIAL_VALUE_FORMS_CEP
            self.fields['municipio'].initial = Municipio.objects.get(
                pk=settings.INITIAL_VALUE_FORMS_MUNICIPIO)

        self.fields['cep'].widget.attrs['class'] = 'cep'
        self.fields['endereco'].widget.attrs['autocomplete'] = 'off'
        self.fields['trecho'].queryset = Trecho.objects.all()
        self.fields['trecho'].widget = forms.HiddenInput()

        # Utilizando template bootstrap3 customizado
        self.fields['preferencial'].widget = forms.RadioSelect()
        self.fields['preferencial'].inline_class = True


class LocalTrabalhoForm(ModelForm):

    class Meta:
        model = LocalTrabalho
        fields = ['nome',
                  'nome_social',
                  'data_inicio',
                  'data_fim',
                  'tipo',
                  'trecho',
                  'endereco',
                  'numero',
                  'complemento',
                  'distrito',
                  'regiao_municipal',
                  'cep',
                  'bairro',
                  'municipio',
                  'uf',
                  'preferencial',
                  'cargo']

    def __init__(self, *args, **kwargs):

        instance = None
        super(LocalTrabalhoForm, self).__init__(*args, **kwargs)

        if isinstance(self.instance, LocalTrabalho):
            instance = self.instance

        if not instance:
            self.fields['uf'].initial = settings.INITIAL_VALUE_FORMS_UF
            self.fields['cep'].initial = settings.INITIAL_VALUE_FORMS_CEP
            self.fields['municipio'].initial = Municipio.objects.get(
                pk=settings.INITIAL_VALUE_FORMS_MUNICIPIO)

        self.fields['cep'].widget.attrs['class'] = 'cep'
        self.fields['endereco'].widget.attrs['autocomplete'] = 'off'
        self.fields['trecho'].queryset = Trecho.objects.all()
        self.fields['trecho'].widget = forms.HiddenInput()

        # Utilizando template bootstrap3 customizado
        self.fields['preferencial'].widget = forms.RadioSelect()
        self.fields['preferencial'].inline_class = True


class ContatoForm(ModelForm):

    class Meta:
        model = Contato
        fields = ['nome',
                  'nome_social',
                  'apelido',
                  'data_nascimento',
                  'estado_civil',
                  'sexo',
                  'identidade_genero',
                  'nivel_instrucao',
                  'naturalidade',
                  'tem_filhos',
                  'quantos_filhos',
                  'profissao',
                  'pronome_tratamento',
                  'tipo_autoridade',
                  'nome_pai',
                  'nome_mae',
                  'numero_sus',
                  'cpf',
                  'titulo_eleitor',
                  'rg',
                  'rg_orgao_expedidor',
                  'rg_data_expedicao',
                  'ativo',
                  'observacoes',
                  'cargo',
                  'grupodecontatos_set'
                  ]

    grupodecontatos_set = ModelMultipleChoiceField(
        queryset=GrupoDeContatos.objects.all(),
        required=False,
        label='',
        widget=FilteredSelectMultiple('grupodecontatos_set', False),
    )

    def __init__(self, *args, **kwargs):

        instance = None
        super(ContatoForm, self).__init__(*args, **kwargs)

        if isinstance(self.instance, Contato):
            instance = self.instance

        if 'tipo_autoridade' in self.fields:
            self.fields['tipo_autoridade'].widget.attrs.update(
                {'onchange': 'atualizaPronomes(event)'})

        self.fields['pronome_tratamento'].widget = forms.RadioSelect()
        self.fields['pronome_tratamento'].queryset = \
            PronomeTratamento.objects.order_by(
                'prefixo_nome_singular_m', 'nome_por_extenso')

        if 'tipo_autoridade' in self.fields and\
                instance and instance.tipo_autoridade:
            pronomes_choice = instance.tipo_autoridade.pronomes.order_by(
                'prefixo_nome_singular_m', 'nome_por_extenso')
        else:
            pronomes_choice = self.fields['pronome_tratamento'].queryset

        self.fields['pronome_tratamento'].choices = [
            (p.pk, '%s, %s - %s - %s - %s - %s - %s - %s' % (
                p.prefixo_nome_singular_m,
                p.prefixo_nome_singular_f,
                p.nome_por_extenso,
                p.abreviatura_singular_m,
                p.abreviatura_plural_m,
                p.vocativo_direto_singular_m,
                p.vocativo_indireto_singular_m,
                p.enderecamento_singular_m))
            for p in pronomes_choice]

        self.fields[
            'grupodecontatos_set'].widget = forms.CheckboxSelectMultiple()
        self.fields['grupodecontatos_set'].inline_class = True
        self.fields['grupodecontatos_set'].queryset = \
            GrupoDeContatos.objects.filter(workspace=self.initial['workspace'])
        if self.instance and self.instance.pk:
            self.fields['grupodecontatos_set'].initial = list(
                self.instance.grupodecontatos_set.all())

    def clean(self):
        pronome = self.cleaned_data['pronome_tratamento']
        if 'tipo_autoridade' in self.cleaned_data:
            tipo_autoridade = self.cleaned_data['tipo_autoridade']

            if tipo_autoridade and not pronome:
                self._errors['pronome_tratamento'] = [
                    _('Tendo sido selecionado um tipo de autoridade, \
                    o campo pronome de tratamento se torna obrigatório.')]


class PerfilForm(ContatoForm):

    class Meta:
        model = Perfil
        fields = ['nome',
                  'nome_social',
                  'apelido',
                  'data_nascimento',
                  'estado_civil',
                  'sexo',
                  'identidade_genero',
                  'nivel_instrucao',
                  'naturalidade',
                  'tem_filhos',
                  'quantos_filhos',
                  'profissao',
                  'pronome_tratamento',
                  'cargo'
                  ]

    def __init__(self, *args, **kwargs):

        super(PerfilForm, self).__init__(*args, **kwargs)
        self.fields['pronome_tratamento'].help_text = ''


class ContatoFragmentPronomesForm(forms.Form):

    pronome_tratamento = forms.ModelChoiceField(
        label=Contato._meta.get_field('pronome_tratamento').verbose_name,
        queryset=PronomeTratamento.objects.all(),
        required=False)

    def __init__(self, *args, **kwargs):

        super(ContatoFragmentPronomesForm, self).__init__(
            *args, **kwargs)

        self.fields['pronome_tratamento'].widget = forms.RadioSelect()

        if 'instance' in self.initial:
            self.fields['pronome_tratamento'].queryset = self.initial[
                'instance'].pronomes.order_by(
                'prefixo_nome_singular_m', 'nome_por_extenso')
        else:
            self.fields['pronome_tratamento'].queryset = \
                PronomeTratamento.objects.order_by(
                'prefixo_nome_singular_m', 'nome_por_extenso')

        self.fields['pronome_tratamento'].choices = [
            (p.pk, '%s, %s - %s - %s - %s - %s - %s - %s' % (
                p.prefixo_nome_singular_m,
                p.prefixo_nome_singular_f,
                p.nome_por_extenso,
                p.abreviatura_singular_m,
                p.abreviatura_plural_m,
                p.vocativo_direto_singular_m,
                p.vocativo_indireto_singular_m,
                p.enderecamento_singular_m))
            for p in self.fields['pronome_tratamento'].queryset]

        self.fields['pronome_tratamento'].help_text = _('O pronome de \
        tratamento é opcional, mas será \
        obrigatório caso seja selecionado um tipo de autoridade.')

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True


class EnderecoForm(ModelForm):

    class Meta:
        model = Endereco
        fields = ['tipo',
                  'trecho',
                  'endereco',
                  'numero',
                  'complemento',
                  'distrito',
                  'regiao_municipal',
                  'cep',
                  'bairro',
                  'municipio',
                  'uf',
                  'preferencial',
                  'observacoes',
                  'ponto_referencia']

    def __init__(self, *args, **kwargs):

        super(EnderecoForm, self).__init__(*args, **kwargs)

        self.fields['uf'].initial = settings.INITIAL_VALUE_FORMS_UF
        self.fields[
            'municipio'].initial = Municipio.objects.get(
            pk=settings.INITIAL_VALUE_FORMS_MUNICIPIO)

        self.fields['cep'].widget.attrs['class'] = 'cep'
        self.fields['endereco'].widget.attrs['autocomplete'] = 'off'

        self.fields['trecho'].queryset = Trecho.objects.all()
        self.fields['trecho'].widget = forms.HiddenInput()

        # Utilizando template bootstrap3 customizado
        self.fields['preferencial'].widget = forms.RadioSelect()
        self.fields['preferencial'].inline_class = True


class TipoAutoridadeForm(ModelForm):

    class Meta:
        model = TipoAutoridade
        fields = ['descricao',
                  'pronomes']

    def __init__(self, *args, **kwargs):

        super(TipoAutoridadeForm, self).__init__(*args, **kwargs)

        self.fields[
            'pronomes'].widget = forms.CheckboxSelectMultiple()

        self.fields['pronomes'].choices = [
            (p.pk, '%s, %s - %s - %s - %s - %s - %s - %s' % (
                p.prefixo_nome_singular_m,
                p.prefixo_nome_singular_f,
                p.nome_por_extenso,
                p.abreviatura_singular_m,
                p.abreviatura_plural_m,
                p.vocativo_direto_singular_m,
                p.vocativo_indireto_singular_m,
                p.enderecamento_singular_m))
            for p in self.fields[
                'pronomes'].queryset.order_by(
                'prefixo_nome_singular_m', 'nome_por_extenso')]
        """
        self.fields['pronomes'] = Field(
            'pronomes',
            template="cerimonial/layout/pronometratamento_checkbox.html")
        """


class ProcessoForm(ModelForm):
    q = forms.CharField(
        required=False,
        label='Busca por Contatos',
        widget=forms.TextInput(
            attrs={'type': 'search'}))

    class Meta:
        model = Processo
        fields = ['data',
                  'titulo',
                  'importancia',
                  'status',
                  'descricao',
                  'classificacoes',
                  'observacoes',
                  'solucao',
                  'q',
                  'contatos',
                  'topicos',
                  'assuntos']

    def __init__(self, *args, **kwargs):
        yaml_layout = kwargs.pop('yaml_layout')

        q_field = Div(
            FieldWithButtons(
                Field('q',
                      placeholder=_('Filtrar Lista'),
                      autocomplete='off',
                      type='search',
                      onkeypress='atualizaContatos(event)'),
                StrictButton(
                    _('Filtrar'), css_class='btn-default',
                    type='button', onclick='atualizaContatos(event)')),
            Div(css_class='form-group-contato-search '
                'controls-radio-checkbox')
        )

        q = [_('Seleção de Contatos'),
             [(q_field, 5),
              (Div(Field('contatos'), css_class='form-group-contatos'), 7)]
             ]
        yaml_layout.append(q)

        for fieldset in yaml_layout:
            for linha in fieldset:
                for idx, field in enumerate(linha):
                    if field[0] == 'importancia':
                        linha[idx] = (InlineRadios('importancia'), field[1])

        self.helper = FormHelper()

        self.helper.field_class = 'controls'
        self.helper.layout = SaplFormLayout(*yaml_layout)

        super(ProcessoForm, self).__init__(*args, **kwargs)

        if not self.instance.pk:
            self.fields['data'].initial = date.today()

        self.fields['q'].help_text = _('Digite parte do nome, nome social ou '
                                       'apelido do Contato que você procura.')

        self.fields['topicos'].widget = forms.SelectMultiple(
            attrs={'size': '8'})
        self.fields['topicos'].queryset = TopicoProcesso.objects.all()

        self.fields['assuntos'].widget = forms.SelectMultiple(
            attrs={'size': '8'})
        self.fields['assuntos'].queryset = AssuntoProcesso.objects.filter(
            workspace=self.initial['workspace'])

        # Utilizando template bootstrap3 customizado
        self.fields['importancia'].widget = forms.RadioSelect()
        self.fields['importancia'].choices = IMPORTANCIA_CHOICE

        self.fields['status'].widget = forms.RadioSelect()
        # self.fields['status'].inline_class = True
        self.fields['status'].choices = [
            (ass.pk, ass) for ass in StatusProcesso.objects.order_by('id')]

        self.fields['classificacoes'].widget = forms.CheckboxSelectMultiple()
        # self.fields['classificacoes'].inline_class = True

        self.fields['contatos'].widget = forms.CheckboxSelectMultiple()
        self.fields['contatos'].queryset = Contato.objects.all()
        self.fields['contatos'].choices = [
            (c.pk, c) for c in self.instance.contatos.order_by('nome')]\
            if self.instance.pk else []
        self.fields['contatos'].help_text = _(
            'Procure por Contatos na caixa de buscas e arraste '
            'para esta caixa os Contatos interessados neste Processo.')


class ProcessoContatoForm(ModelForm):

    class Meta:
        model = ProcessoContato
        fields = ['data',
                  'titulo',
                  'importancia',
                  'status',
                  'descricao',
                  'classificacoes',
                  'observacoes',
                  'solucao',
                  'topicos',
                  'assuntos']

    def __init__(self, *args, **kwargs):
        super(ProcessoContatoForm, self).__init__(*args, **kwargs)

        if not self.instance.pk:
            self.fields['data'].initial = date.today()

        self.fields['topicos'].widget = forms.SelectMultiple(
            attrs={'size': '8'})
        self.fields['topicos'].queryset = TopicoProcesso.objects.all()

        self.fields['assuntos'].widget = forms.SelectMultiple(
            attrs={'size': '8'})
        self.fields['assuntos'].queryset = AssuntoProcesso.objects.filter(
            workspace=self.initial['workspace'])

        # Utilizando template bootstrap3 customizado
        self.fields['importancia'].widget = forms.RadioSelect()
        self.fields['importancia'].inline_class = True
        self.fields['importancia'].choices = IMPORTANCIA_CHOICE

        self.fields['status'].widget = forms.RadioSelect()
        # self.fields['status'].inline_class = True
        self.fields['status'].choices = [
            (ass.pk, ass) for ass in StatusProcesso.objects.order_by('id')]

        self.fields['classificacoes'].widget = forms.CheckboxSelectMultiple()
        # self.fields['classificacoes'].inline_class = True


class ContatoFragmentSearchForm(forms.Form):
    """q = forms.CharField(
        required=False,
        label='Busca por Contatos',
        widget=forms.TextInput(
            attrs={'type': 'search'}))"""

    contatos_search = forms.ModelChoiceField(
        label='',
        queryset=Contato.objects.all(),
        required=False)

    def __init__(self, *args, **kwargs):

        super(ContatoFragmentSearchForm, self).__init__(*args, **kwargs)

        """q_field = FieldWithButtons(
            Field('q',
                  placeholder=_('Filtrar Lista'),
                  autocomplete='off'),
            StrictButton(
                _('Filtrar'), css_class='btn-default',
                type='button', onclick='atualizaContatos(event)'))"""

        self.fields['contatos_search'].widget = forms.CheckboxSelectMultiple(
        )

        queryset = Contato.objects.filter(
            workspace=self.initial['workspace']).exclude(
            pk__in=self.initial['pks_exclude'])

        query = normalize(self.initial['q'])

        query = query.split(' ')
        if query:
            q = Q()
            for item in query:
                if not item:
                    continue
                q = q & Q(search__icontains=item)

            if q:
                queryset = queryset.filter(q)

        queryset = queryset[:10]
        self.fields['contatos_search'].queryset = queryset

        self.fields['contatos_search'].choices = [(c.pk, c) for c in queryset]

        self.helper = FormHelper()
        self.helper.field_class = 'controls'
        self.helper.layout = Layout(
            Div(
                Field('contatos_search'),
                css_class='form-group-contatos-search '
                'controls-radio-checkbox'))
        self.helper.form_tag = False
        self.helper.disable_csrf = True


class RangeWidgetNumber(forms.MultiWidget):

    def __init__(self, attrs=None):
        widgets = (forms.NumberInput(
            attrs={'class': 'numberinput form-control',
                   'placeholder': 'Inicial'}),
                   forms.NumberInput(
            attrs={'class': 'numberinput form-control',
                   'placeholder': 'Final'}))
        super(RangeWidgetNumber, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.start, value.stop]
        return [None, None]

    def render(self, name, value, attrs=None, renderer=None):
        rendered_widgets = []
        for i, x in enumerate(self.widgets):
            rendered_widgets.append(
                x.render(
                    '%s_%d' % (name, i), value[i] if value else ''
                )
            )

        html = '<div class="col-sm-6">%s</div><div class="col-sm-6">%s</div>'\
            % tuple(rendered_widgets)
        return '<div class="row">%s</div>' % html


class RangeWidgetOverride(forms.MultiWidget):

    def __init__(self, attrs=None):
        widgets = (forms.DateInput(format='%d/%m/%Y',
                                   attrs={'class': 'dateinput form-control',
                                          'placeholder': 'Inicial'}),
                   forms.DateInput(format='%d/%m/%Y',
                                   attrs={'class': 'dateinput form-control',
                                          'placeholder': 'Final'}))
        super(RangeWidgetOverride, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.start, value.stop]
        return []

    def render(self, name, value, attrs=None, renderer=None):
        rendered_widgets = []
        for i, x in enumerate(self.widgets):
            rendered_widgets.append(
                x.render(
                    '%s_%d' % (name, i), value[i] if value else ''
                )
            )

        html = '<div class="col-sm-6">%s</div><div class="col-sm-6">%s</div>'\
            % tuple(rendered_widgets)
        return '<div class="row">%s</div>' % html


class SubmitFilterPrint(BaseInput):

    input_type = 'submit'

    def __init__(self, *args, **kwargs):
        self.field_classes = 'btn'
        super(SubmitFilterPrint, self).__init__(*args, **kwargs)


class DataRangeFilter(Filter):
    field_class = forms.Field

    def filter(self, queryset, value):

        if not value[0] or not value[1]:
            return queryset

        inicial = datetime.datetime.strptime(value[0], "%d/%m/%Y").date()
        final = datetime.datetime.strptime(value[1], "%d/%m/%Y").date()
        if inicial > final:
            inicial, final = final, inicial

        params = {
            self.field_name + '__range': [inicial, final]}

        range_select = Q(**params)

        # Run the query.
        return queryset.filter(range_select)


class ImpressoEnderecamentoContatoFilterSet(FilterSet):

    FEMININO = 'F'
    MASCULINO = 'M'
    AMBOS = ''
    SEXO_CHOICE = ((AMBOS, _('Ambos')),
                   (FEMININO, _('Feminino')),
                   (MASCULINO, _('Masculino')))

    DEPOIS_PRONOME = 'DP'
    LINHA_NOME = 'LN'
    DEPOIS_NOME = 'DN'
    LOCAL_CARGO_CHOICE = ((DEPOIS_PRONOME, _('Depois do Pronome '
                                             'de tratamento')),
                          (LINHA_NOME, _('Antes do Nome do Contato')),
                          (DEPOIS_NOME, _('Entre o Nome do Contato '
                                          'e seu Endereço')))

    FILHOS_CHOICE = [(None, _('Ambos'))] + YES_NO_CHOICES

    search = CharFilter(method='filter_search')
    sexo = ChoiceFilter(choices=SEXO_CHOICE)
    tem_filhos = ChoiceFilter(
        label=_('Com filhos?'),
        choices=FILHOS_CHOICE)

    idade = RangeFilter(
        label=_('Idade entre:'),
        widget=RangeWidgetNumber,
        method='filter_idade')

    impresso = ModelChoiceFilter(
        label=ImpressoEnderecamento._meta.verbose_name_plural,
        required=True,
        queryset=ImpressoEnderecamento.objects.all(),
        method='filter_impresso')

    grupo = ChoiceFilter(
        label=_('Contatos Agrupados'),
        required=False,
        method='filter_grupo')

    imprimir_pronome = ChoiceFilter(
        label=_('Imprimir Pronome?'),
        choices=YES_NO_CHOICES,
        required=True,
        initial=False,
        method='filter_imprimir_pronome')
    imprimir_cargo = ChoiceFilter(
        label=_('Imprimir Cargo?'),
        required=True,
        empty_label=None,
        choices=YES_NO_CHOICES, initial=False,
        method='filter_imprimir_cargo')

    fontsize = NumberFilter(
        label=_('Tamanho da Fonte'), initial='',
        max_value=100, min_value=0, max_digits=3, decimal_places=0,
        method='filter_fontsize'
    )

    nome_maiusculo = ChoiceFilter(
        label=_('Nome Maiúsculo'),
        choices=YES_NO_CHOICES, initial=False,
        method='filter_nome_maiusculo')

    local_cargo = ChoiceFilter(
        label=_('Local para imprimir o Cargo'),
        choices=LOCAL_CARGO_CHOICE, initial=False,
        method='filter_local_cargo')

    def filter_impresso(self, queryset, field_name, value):
        return queryset

    def filter_fontsize(self, queryset, field_name, value):
        return queryset

    def filter_grupo(self, queryset, field_name, value):
        if value == '0':
            queryset = queryset.filter(grupodecontatos_set__isnull=True)
        elif value != '':
            queryset = queryset.filter(grupodecontatos_set=value)
        return queryset

    def filter_local_cargo(self, queryset, field_name, value):
        return queryset

    def filter_imprimir_pronome(self, queryset, field_name, value):
        return queryset

    def filter_imprimir_cargo(self, queryset, field_name, value):
        return queryset

    def filter_nome_maiusculo(self, queryset, field_name, value):
        return queryset

    def filter_idade(self, queryset, field_name, value):
        idi = int(value.start) if value.start is not None else 0
        idf = int(
            value.stop) if value.stop is not None else date.today().year - 2

        if idi > idf:
            a = idi
            idi = idf
            idf = a

        # lim inicial-dt.mais antiga
        li = date.today() - relativedelta(years=idf + 1)
        # lim final - dt. mais nova
        lf = date.today() - relativedelta(years=idi)

        return queryset.filter(data_nascimento__gt=li,
                               data_nascimento__lte=lf)

    def filter_search(self, queryset, field_name, value):

        query = normalize(value)

        query = query.split(' ')
        if query:
            q = Q()
            for item in query:
                if not item:
                    continue
                q = q & Q(search__icontains=item)

            if q:
                queryset = queryset.filter(q)
        return queryset

    def filter_data_nascimento(self, queryset, field_name, value):
        #_where = "date_part('year', age(timestamp '%s', data_nascimento)) != date_part('year', age(timestamp '%s', data_nascimento))"
        # return queryset.extra(where=_where, params=value)

        if not value[0] or not value[1]:
            return queryset

        now = datetime.datetime.strptime(value[0], "%d/%m/%Y").date()
        then = datetime.datetime.strptime(value[1], "%d/%m/%Y").date()
        if now > then:
            a = now
            now = then
            then = a

        # Build the list of month/day tuples.
        monthdays = [(now.month, now.day)]
        while now <= then:
            monthdays.append((now.month, now.day))
            now += timedelta(days=1)

        # Tranform each into queryset keyword args.
        monthdays = (dict(zip(("data_nascimento__month",
                               "data_nascimento__day"), t))
                     for t in monthdays)

        # Compose the djano.db.models.Q objects together for a single query.
        query = reduce(operator.or_, (Q(**d) for d in monthdays))

        # Run the query.
        return queryset.extra(select={
            'month': 'extract( month from data_nascimento )',
            'day': 'extract( day from data_nascimento )', }
        ).order_by('month', 'day', 'nome').filter(query)

    data_nascimento = DataRangeFilter(widget=RangeWidgetOverride,
                                      method='filter_data_nascimento')

    class Meta:
        model = Contato
        fields = ['search',
                  'sexo',
                  'tem_filhos',
                  'data_nascimento',
                  'tipo_autoridade']
        """filter_overrides = {
            models.DateField: {
                'filter_class': DataRangeFilter,
                'extra': lambda f: {
                    'label': '%s (%s)' % (f.verbose_name, _('Inicial - Final')),
                    'widget': RangeWidgetOverride
                }
            }
        }"""

    def __init__(self, data=None,
                 queryset=None, prefix=None, strict=None, **kwargs):

        workspace = kwargs.pop('workspace')

        super(ImpressoEnderecamentoContatoFilterSet, self).__init__(
            data=data,
            queryset=queryset, prefix=prefix, strict=strict, **kwargs)

        col1 = to_row([
            ('search', 6),
            ('sexo', 3),
            ('tem_filhos', 3),
            ('data_nascimento', 6),
            ('idade', 6),
            ('tipo_autoridade', 6),
            ('grupo', 6),
        ])

        col2 = to_row([
            ('impresso', 12),
            ('fontsize', 4),
            ('nome_maiusculo', 4),
            ('imprimir_pronome', 4),
            ('imprimir_cargo', 5),
            ('local_cargo', 7),

        ])

        row = to_row(
            [(Fieldset(
                _('Informações para Seleção de Contatos'),
                col1,
                to_row([(SubmitFilterPrint(
                    'filter',
                    value=_('Filtrar'), css_class='btn-default pull-right',
                    type='submit'), 12)])), 6),
             (Fieldset(
                 _('Informações para Impressão'),
                 col2,
                 to_row([(SubmitFilterPrint(
                     'print',
                     value=_('Imprimir'), css_class='btn-primary pull-right',
                     type='submit'), 12)])), 6)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            row,
        )

        self.form.fields['search'].label = _(
            'Nome/Nome Social/Apelido')
        self.form.fields['data_nascimento'].label = '%s (%s)' % (
            _('Aniversário'), _('Inicial - Final'))

        self.form.fields['tem_filhos'].choices.choices[0] = (None, _('Ambos'))

        self.form.fields['grupo'].choices = [
            ('0', _('Apenas Contatos sem Grupo')),
        ] + [(g.pk, str(g)) for g in GrupoDeContatos.objects.filter(
            workspace=workspace)]


class ContatoAgrupadoPorProcessoFilterSet(FilterSet):

    AGRUPADO_POR_NADA = 'sem_agrupamento'
    AGRUPADO_POR_TITULO = 'titulo'
    AGRUPADO_POR_IMPORTANCIA = 'importancia'
    AGRUPADO_POR_TOPICO = 'topicos__descricao'
    AGRUPADO_POR_ASSUNTO = 'assuntos__descricao'
    AGRUPADO_POR_STATUS = 'status__descricao'
    AGRUPADO_POR_CLASSIFICACAO = 'classificacoes__descricao'

    AGRUPAMENTO_CHOICE = (
        (AGRUPADO_POR_NADA, _('Sem Agrupamento')),
        (AGRUPADO_POR_TITULO, _('Por Título de Processos')),
        (AGRUPADO_POR_IMPORTANCIA,
         _('Por Importância')),
        (AGRUPADO_POR_TOPICO,
         _('Por Tópicos')),
        (AGRUPADO_POR_ASSUNTO,
         _('Por Assuntos')),
        (AGRUPADO_POR_STATUS,
         _('Por Status')),
        (AGRUPADO_POR_CLASSIFICACAO,
         _('Por Classificação')),
    )

    search = CharFilter(method='filter_search')

    agrupamento = ChoiceFilter(
        required=False,
        empty_label=None,
        choices=AGRUPAMENTO_CHOICE,
        method='filter_agrupamento')

    importancia = MultipleChoiceFilter(
        required=False,
        choices=IMPORTANCIA_CHOICE,
        method='filter_importancia')

    status = ModelMultipleChoiceFilter(
        required=False,
        queryset=StatusProcesso.objects.all(),
        method='filter_status')

    def filter_agrupamento(self, queryset, field_name, value):
        return queryset

    def filter_importancia(self, queryset, field_name,  value):
        if not value:
            return queryset

        q = None
        for i in value:
            q = q | Q(importancia=i) if q else Q(importancia=i)
        return queryset.filter(q)

    def filter_status(self, queryset, field_name,  value):
        if not value:
            return queryset

        q = None
        for sta in value:
            q = q | Q(status=sta) if q else Q(status=sta)
        return queryset.filter(q)

    def filter_search(self, queryset, field_name,  value):

        query = normalize(value)

        query = query.split(' ')
        if query:
            q = Q()
            for item in query:
                if not item:
                    continue
                q = q & Q(search__icontains=item)

            if q:
                queryset = queryset.filter(q)
        return queryset

    class Meta:
        model = Processo
        fields = ['search',
                  'data',
                  'topicos',
                  'importancia',
                  'classificacoes',
                  'assuntos',
                  'status', ]
        filter_overrides = {models.DateField: {
            'filter_class': DataRangeFilter,
            'extra': lambda f: {
                'label': '%s (%s)' % (f.verbose_name, _('Inicial - Final')),
                'widget': RangeWidgetOverride}
        }}

    def __init__(self, data=None,
                 queryset=None, prefix=None, strict=None, **kwargs):

        workspace = kwargs.pop('workspace')

        super(ContatoAgrupadoPorProcessoFilterSet, self).__init__(
            data=data,
            queryset=queryset, prefix=prefix, strict=strict, **kwargs)

        c1_row1 = to_row([
            ('search', 7),
            ('data', 5),
            ('importancia', 4),
            ('status', 4),
            ('classificacoes', 4),
            ('topicos', 6),
            ('assuntos', 6),
        ])

        col1 = Fieldset(
            _('Informações para Seleção de Processos'),
            c1_row1,
            to_row([
                (SubmitFilterPrint(
                    'filter',
                    value=_('Filtrar'),
                    css_class='btn-default pull-right',
                    type='submit'), 12)
            ]))

        col2 = Fieldset(
            _('Inf p/ Impressão'),
            'agrupamento',

            SubmitFilterPrint(
                'print',
                value=_('Imprimir'),
                css_class='btn-primary pull-right',
                type='submit')
        )

        rows = to_row([
            (col1, 9),
            (col2, 3),
        ])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            rows,
        )

        self.form.fields['search'].label = _('Filtrar Títulos de Processos')

        self.form.fields['topicos'].widget = forms.SelectMultiple(
            attrs={'size': '7'})
        self.form.fields['topicos'].queryset = TopicoProcesso.objects.all()

        self.form.fields['assuntos'].widget = forms.SelectMultiple(
            attrs={'size': '7'})
        self.form.fields['assuntos'].queryset = AssuntoProcesso.objects.filter(
            workspace=workspace)

        self.form.fields['importancia'].widget = forms.CheckboxSelectMultiple()
        #self.form.fields['importancia'].inline_class = True

        self.form.fields[
            'classificacoes'].widget = forms.CheckboxSelectMultiple()

        self.form.fields['status'].widget = forms.CheckboxSelectMultiple()
        """#self.form.fields['status'].inline_class = True
        self.form.fields['status'].choices = list(
            self.form.fields['status'].choices)
        del self.form.fields['status'].choices[0]"""

        self.form.fields['agrupamento'].label = _(
            'Agrupar Contatos')
        self.form.fields['agrupamento'].widget = forms.RadioSelect()


class ListWithSearchProcessoForm(ListWithSearchForm):

    assunto = forms.ModelChoiceField(
        label=_('Filtrar por Assunto'),
        queryset=AssuntoProcesso.objects.all(),
        required=False)

    class Meta(ListWithSearchForm.Meta):
        fields = ['q', 'o', 'assunto']
        pass

    def __init__(self, *args, **kwargs):
        super(ListWithSearchProcessoForm, self).__init__(*args, **kwargs)

        self.helper.layout.fields.append(Field('assunto'))

        self.fields['assunto'].queryset = AssuntoProcesso.objects.filter(
            workspace=self.initial['workspace'])


class GrupoDeContatosForm(ModelForm):
    q = forms.CharField(
        required=False,
        label='Busca por Contatos',
        widget=forms.TextInput(
            attrs={'type': 'search'}))

    class Meta:
        model = GrupoDeContatos
        fields = ['nome',
                  'q',
                  'contatos', ]

    def __init__(self, *args, **kwargs):
        yaml_layout = kwargs.pop('yaml_layout')

        q_field = Div(
            FieldWithButtons(
                Field('q',
                      placeholder=_('Filtrar Lista'),
                      autocomplete='off',
                      type='search',
                      onkeypress='atualizaContatos(event)'),
                StrictButton(
                    _('Filtrar'), css_class='btn-default',
                    type='button', onclick='atualizaContatos(event)')),
            Div(css_class='form-group-contato-search')
        )

        q = [_('Seleção de Contatos'),
             [(q_field, 5),
              (Div(Field('contatos'), css_class='form-group-contatos'), 7)]
             ]
        yaml_layout.append(q)

        self.helper = FormHelper()
        self.helper.field_class = 'controls'
        self.helper.layout = SaplFormLayout(*yaml_layout)

        super(GrupoDeContatosForm, self).__init__(*args, **kwargs)

        self.fields['q'].help_text = _('Digite parte do nome, nome social ou '
                                       'apelido do Contato que você procura.')

        self.fields['contatos'].widget = forms.CheckboxSelectMultiple()

        self.fields['contatos'].queryset = Contato.objects.all()

        self.fields['contatos'].choices = [
            (c.pk, c) for c in self.instance.contatos.order_by('nome')]\
            if self.instance.pk else []

        self.fields['contatos'].help_text = _(
            'Procure por Contatos na caixa de buscas e arraste '
            'para esta caixa os Contatos interessados neste Processo.')


class ContatoAgrupadoPorGrupoFilterSet(FilterSet):

    municipio = ModelChoiceFilter(
        required=False,
        label=Municipio._meta.verbose_name,
        queryset=Municipio.objects.all(),
        method='filter_municipio')

    grupo = ModelMultipleChoiceFilter(
        required=False,
        label=GrupoDeContatos._meta.verbose_name_plural,
        queryset=GrupoDeContatos.objects.all(),
        method='filter_grupo')

    def filter_municipio(self, queryset, field_name,  value):
        queryset = queryset.filter(endereco_set__municipio=value)
        return queryset

    def filter_grupo(self, queryset, field_name, value):
        queryset = queryset.filter(grupodecontatos_set__in=value)

        return queryset.order_by('grupodecontatos_set__nome', 'nome')

    class Meta:
        model = Contato
        fields = ('municipio', 'grupo')

    def __init__(self, data=None,
                 queryset=None, prefix=None, strict=None, **kwargs):

        workspace = kwargs.pop('workspace')

        super(ContatoAgrupadoPorGrupoFilterSet, self).__init__(
            data=data,
            queryset=queryset, prefix=prefix, strict=strict, **kwargs)

        c1_row1 = to_row([
            ('municipio', 7),
            ('grupo', 7),
        ])

        col1 = Fieldset(
            _('Informações para Seleção de Contados'),
            c1_row1,
            to_row([
                (SubmitFilterPrint(
                    'filter',
                    value=_('Filtrar'),
                    css_class='btn-default pull-right',
                    type='submit'), 12)
            ]))

        col2 = Fieldset(
            _('Inf p/ Impressão'),

            SubmitFilterPrint(
                'print',
                value=_('Imprimir'),
                css_class='btn-primary pull-right',
                type='submit')
        )

        rows = to_row([
            (col1, 9),
            (col2, 3),
        ])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            rows,
        )

        self.form.fields['grupo'].queryset = GrupoDeContatos.objects.filter(
            workspace=workspace)
        self.form.fields['municipio'].queryset = Municipio.objects.all()

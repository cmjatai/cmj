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
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.expressions import Func
from django.forms import widgets
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _
from django_filters.filters import CharFilter, ChoiceFilter, NumberFilter,\
    MethodFilter, DateFromToRangeFilter, ModelChoiceFilter, RangeFilter
from django_filters.filterset import FilterSet, STRICTNESS
from sapl.crispy_layout_mixin import to_column, SaplFormLayout, to_fieldsets,\
    form_actions, to_row
from sapl.parlamentares.models import Municipio

from cmj import settings
from cmj.cerimonial.models import LocalTrabalho, Endereco,\
    TipoAutoridade, PronomeTratamento, Contato, Perfil, Processo,\
    IMPORTANCIA_CHOICE, AssuntoProcesso, StatusProcesso, ProcessoContato
from cmj.core.models import Trecho, ImpressoEnderecamento
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
                  'cargo'
                  ]

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
            PronomeTratamento.objects.order_by('nome_por_extenso')

        if 'tipo_autoridade' in self.fields and\
                instance and instance.tipo_autoridade:
            pronomes_choice = instance.tipo_autoridade.pronomes.order_by(
                'nome_por_extenso')
        else:
            pronomes_choice = self.fields['pronome_tratamento'].queryset

        self.fields['pronome_tratamento'].choices = [
            (p.pk, '%s - %s - %s - %s - %s - %s' % (
                p.nome_por_extenso,
                p.abreviatura_singular_m,
                p.abreviatura_plural_m,
                p.vocativo_direto_singular_m,
                p.vocativo_indireto_singular_m,
                p.enderecamento_singular_m))
            for p in pronomes_choice]

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
                'instance'].pronomes.order_by('nome_por_extenso')
        else:
            self.fields['pronome_tratamento'].queryset = \
                PronomeTratamento.objects.order_by('nome_por_extenso')

        self.fields['pronome_tratamento'].choices = [
            (p.pk, '%s - %s - %s - %s - %s - %s' % (
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

        self.fields[
            'pronomes'].choices = [
            (p.pk, '%s - %s - %s - %s - %s - %s' % (
                p.nome_por_extenso,
                p.abreviatura_singular_m,
                p.abreviatura_plural_m,
                p.vocativo_direto_singular_m,
                p.vocativo_indireto_singular_m,
                p.enderecamento_singular_m))
            for p in self.fields[
                'pronomes'].queryset.order_by('nome_por_extenso')]
        """
        self.fields['pronomes'] = Field(
            'pronomes',
            template="cerimonial/layout/pronometratamento_checkbox.html")
        """


class ListWithSearchForm(forms.Form):
    q = forms.CharField(required=False, label='',
                        widget=forms.TextInput(
                            attrs={'type': 'search'}))

    class Meta:
        fields = ['q']

    def __init__(self, *args, **kwargs):
        super(ListWithSearchForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.form_class = 'form-inline'
        self.helper.form_method = 'GET'
        self.helper.layout = Layout(
            FieldWithButtons(
                Field('q',
                      placeholder=_('Filtrar Lista'),
                      css_class='input-lg'),
                StrictButton(
                    _('Filtrar'), css_class='btn-default btn-lg',
                    type='submit'))
        )


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
            Div(css_class='form-group-contato-search')
        )

        q = [_('Seleção de Contatos'),
             [(q_field, 6),
              (Div(Field('contatos'), css_class='form-group-contatos'), 6)]
             ]
        yaml_layout.append(q)

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(*yaml_layout)

        super(ProcessoForm, self).__init__(*args, **kwargs)

        if not self.instance.pk:
            self.fields['data'].initial = date.today()

        self.fields['q'].help_text = _('Digite parte do nome, nome social ou '
                                       'apelido do Contato que você procura.')

        self.fields['descricao'].widget = forms.Textarea(
            attrs={'rows': '8'})

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

        self.fields['descricao'].widget = forms.Textarea(
            attrs={'rows': '8'})

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

        self.fields['contatos_search'].widget = forms.CheckboxSelectMultiple()

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
        self.helper.layout = Layout(
            Div(
                Field('contatos_search'),
                css_class='form-group-contatos-search'))
        self.helper.form_tag = False
        self.helper.disable_csrf = True


class RangeWidgetNumber(forms.MultiWidget):

    def __init__(self, attrs=None):
        widgets = (forms.NumberInput(
            attrs={'class': 'numberinput',
                   'placeholder': 'Inicial'}),
                   forms.NumberInput(
            attrs={'class': 'numberinput',
                   'placeholder': 'Final'}))
        super(RangeWidgetNumber, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.start, value.stop]
        return [None, None]

    def format_output(self, rendered_widgets):
        html = '<div class="col-sm-6">%s</div><div class="col-sm-6">%s</div>'\
            % tuple(rendered_widgets)
        return '<div class="row">%s</div>' % html


class RangeWidgetOverride(forms.MultiWidget):

    def __init__(self, attrs=None):
        widgets = (forms.DateInput(format='%d/%m/%Y',
                                   attrs={'class': 'dateinput',
                                          'placeholder': 'Inicial'}),
                   forms.DateInput(format='%d/%m/%Y',
                                   attrs={'class': 'dateinput',
                                          'placeholder': 'Final'}))
        super(RangeWidgetOverride, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.start, value.stop]
        return [None, None]

    def format_output(self, rendered_widgets):
        html = '<div class="col-sm-6">%s</div><div class="col-sm-6">%s</div>'\
            % tuple(rendered_widgets)
        return '<div class="row">%s</div>' % html


class MethodRangeFilter(MethodFilter, RangeFilter):
    pass


class SubmitFilterPrint(BaseInput):

    input_type = 'submit'

    def __init__(self, *args, **kwargs):
        self.field_classes = 'btn'
        super(SubmitFilterPrint, self).__init__(*args, **kwargs)


def filter_impresso(queryset, value):
    return queryset


class ImpressoEnderecamentoContatoFilterSet(FilterSet):

    filter_overrides = {models.DateField: {
        'filter_class': MethodFilter,
        'extra': lambda f: {
            'label': '%s (%s)' % (f.verbose_name, _('Inicial - Final')),
            'widget': RangeWidgetOverride}
    }}

    FEMININO = 'F'
    MASCULINO = 'M'
    AMBOS = ''
    SEXO_CHOICE = ((AMBOS, _('Ambos')),
                   (FEMININO, _('Feminino')),
                   (MASCULINO, _('Masculino')))

    FILHOS_CHOICE = [(None, _('Ambos'))] + YES_NO_CHOICES

    search = MethodFilter()
    sexo = ChoiceFilter(choices=SEXO_CHOICE)
    tem_filhos = ChoiceFilter(choices=FILHOS_CHOICE)

    impresso = ModelChoiceFilter(required=True,
                                 queryset=ImpressoEnderecamento.objects.all(),
                                 action=filter_impresso)
    idade = MethodRangeFilter(
        label=_('Idade entre:'),
        widget=RangeWidgetNumber)

    strict = STRICTNESS.IGNORE

    def clean_idade(self):
        pass

    def filter_idade(self, queryset, value):
        idi = int(value.start) if value.start is not None else 0
        idf = int(value.stop) if value.stop is not None else 2014

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

    def filter_search(self, queryset, value):

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

    def filter_data_nascimento(self, queryset, value):
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
        monthdays = (dict(zip(("data_nascimento__month", "data_nascimento__day"), t))
                     for t in monthdays)

        # Compose the djano.db.models.Q objects together for a single query.
        query = reduce(operator.or_, (Q(**d) for d in monthdays))

        # Run the query.
        return queryset.extra(select={
            'month': 'extract( month from data_nascimento )',
            'day': 'extract( day from data_nascimento )', }
        ).order_by('month', 'day', 'nome').filter(query)

    class Meta:
        model = Contato
        fields = ['search',
                  'sexo',
                  'tem_filhos',
                  'data_nascimento',
                  'tipo_autoridade', ]

    def __init__(self, data=None, queryset=None, prefix=None, strict=None):

        super(ImpressoEnderecamentoContatoFilterSet, self).__init__(
            data=data, queryset=queryset, prefix=prefix, strict=strict)

        row1 = to_row([
            ('search', 4),
            ('sexo', 2),
            ('tem_filhos', 2),
            ('data_nascimento', 4)])

        row_action = to_row([
            ('tipo_autoridade', 3),
            ('impresso', 3),
            ('idade', 3),
            (Div(SubmitFilterPrint(
                'filter',
                value=_('Filtrar'), css_class='btn-default',
                type='submit'),
                SubmitFilterPrint(
                'print',
                value=_('Imprimir'), css_class='btn-primary',
                type='submit'), css_class='btn-group pull-right'), 3),
        ])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            row1,
            row_action
        )

        self.form.fields['search'].label = _(
            'Filtrar por Nome/Nome Social/Apelido')
        self.form.fields['data_nascimento'].label = '%s (%s)' % (
            _('Data de Aniversário'), _('Inicial - Final'))

        self.form.fields['tem_filhos'].label = _('Com filhos?')
        self.form.fields['tem_filhos'].choices[0] = (None, _('Ambos'))

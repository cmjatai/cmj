from crispy_forms.bootstrap import InlineRadios
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field
from django import forms
from django.forms import widgets
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _
from sapl.parlamentares.models import Municipio

from cmj import settings
from cmj.cerimonial.models import LocalTrabalho, Endereco, OperadorAreaTrabalho,\
    TipoAutoridade, PronomeTratamento
from cmj.core.models import Trecho


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
                  'preferencial',
                  'pronome_tratamento',
                  'cargo']

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

        self.fields['pronome_tratamento'].widget = forms.RadioSelect()
        self.fields['pronome_tratamento'].queryset = \
            PronomeTratamento.objects.order_by('nome_por_extenso')


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
                  'pronome_tratamento',
                  'tipo_autoridade',
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

        self.fields['tipo_autoridade'].widget.attrs.update(
            {'onchange': 'atualizaPronomes(event)'})

        self.fields['pronome_tratamento'].widget = forms.RadioSelect()
        self.fields['pronome_tratamento'].queryset = \
            PronomeTratamento.objects.order_by('nome_por_extenso')

        if instance and instance.tipo_autoridade:
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
        tipo_autoridade = self.cleaned_data['tipo_autoridade']

        if tipo_autoridade and not pronome:
            self._errors['pronome_tratamento'] = [
                _('Tendo sido selecionado um tipo de autoridade, \
                o campo pronome de tratamento se torna obrigatório.')]


class LocalTrabalhoFragmentPronomesForm(forms.Form):

    pronome_tratamento = forms.ModelChoiceField(
        label=LocalTrabalho._meta.get_field('pronome_tratamento').verbose_name,
        queryset=PronomeTratamento.objects.all(),
        required=False)

    def __init__(self, *args, **kwargs):

        super(LocalTrabalhoFragmentPronomesForm, self).__init__(
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
                  'uf']

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


class OperadorAreaTrabalhoForm(ModelForm):

    class Meta:
        model = OperadorAreaTrabalho
        fields = ['user',
                  'grupos_associados']

    def __init__(self, *args, **kwargs):

        super(OperadorAreaTrabalhoForm, self).__init__(*args, **kwargs)
        self.fields[
            'grupos_associados'].widget = forms.CheckboxSelectMultiple()
        self.fields['grupos_associados'].queryset = self.fields[
            'grupos_associados'].queryset.order_by('name')


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

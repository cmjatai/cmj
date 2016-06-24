from django import forms
from django.forms import widgets
from django.forms.models import ModelForm
from sapl.parlamentares.models import Municipio

from cmj import settings
from cmj.cerimonial.models import LocalTrabalho, Endereco
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


class LocalTrabalhoForm(ModelForm):

    class Meta:
        model = LocalTrabalho
        fields = ['forma_tratamento',
                  'nome',
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
                  'uf']

    def __init__(self, *args, **kwargs):

        super(LocalTrabalhoForm, self).__init__(*args, **kwargs)

        self.fields['uf'].initial = settings.INITIAL_VALUE_FORMS_UF
        self.fields[
            'municipio'].initial = Municipio.objects.get(
            pk=settings.INITIAL_VALUE_FORMS_MUNICIPIO)

        self.fields['cep'].widget.attrs['class'] = 'cep'
        self.fields['endereco'].widget.attrs['autocomplete'] = 'off'
        self.fields['trecho'].queryset = Trecho.objects.all()
        self.fields['trecho'].widget = forms.HiddenInput()


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

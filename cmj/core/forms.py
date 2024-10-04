
from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm, UserChangeForm as BaseUserChangeForm
from django.core.exceptions import ValidationError
from django.forms.models import ModelForm
from django.utils.translation import gettext_lazy as _
import django_filters
from django_filters.filterset import FilterSet
from image_cropping.widgets import ImageCropWidget, CropWidget

from cmj.core.models import Trecho, TipoLogradouro, User, OperadorAreaTrabalho,\
    ImpressoEnderecamento
from cmj.globalrules import WORKSPACE_GROUPS
from cmj.sigad.models import UrlShortener
from sapl.crispy_layout_mixin import to_row


class UrlShortenerForm(ModelForm):

    class Meta:
        model = UrlShortener
        fields = 'url_long',

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_url_long(self):

        url = self.cleaned_data['url_long']

        if not url.startswith('http'):
            raise ValidationError(
                _('A url a ser encurtada deve iniciar com "http" ou "https".'))

        return url

    def save(self, commit=True):

        instance = ModelForm.save(self, commit=False)
        return UrlShortener.objects.get_or_create_short(
            url_long=instance.url_long,
            automatico=False,
            link_absoluto=True
        )


class OperadorAreaTrabalhoForm(ModelForm):

    class Meta:
        model = OperadorAreaTrabalho
        fields = ['user',
                  'grupos_associados']

    def __init__(self, *args, **kwargs):

        super(OperadorAreaTrabalhoForm, self).__init__(*args, **kwargs)
        self.fields[
            'grupos_associados'].widget = forms.CheckboxSelectMultiple()
        # self.fields['grupos_associados'].queryset = self.fields[
        #    'grupos_associados'].queryset.filter(
        #        name__in=WORKSPACE_GROUPS).order_by('name')
        self.fields['grupos_associados'].queryset = self.fields[
            'grupos_associados'].queryset.all().order_by('name')


class ImpressoEnderecamentoForm(ModelForm):

    class Meta:
        model = ImpressoEnderecamento
        fields = ['nome',
                  'tipo',
                  'largura_pagina',
                  'altura_pagina',
                  'margem_esquerda',
                  'margem_superior',
                  'colunasfolha',
                  'linhasfolha',
                  'larguraetiqueta',
                  'alturaetiqueta',
                  'entre_colunas',
                  'entre_linhas',
                  'fontsize',
                  'rotate'
                  ]

    def __init__(self, *args, **kwargs):

        super(ImpressoEnderecamentoForm, self).__init__(*args, **kwargs)
        self.fields['rotate'].widget = forms.RadioSelect()
        self.fields['rotate'].inline_class = True


class ListWithSearchForm(forms.Form):
    q = forms.CharField(required=False, label='',
                        widget=forms.TextInput(
                            attrs={'type': 'search'}))

    o = forms.CharField(required=False, label='',
                        widget=forms.HiddenInput())

    class Meta:
        fields = ['q', 'o']

    def __init__(self, *args, **kwargs):
        super(ListWithSearchForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.form_class = 'form-inline'
        self.helper.form_method = 'GET'
        self.helper.layout = Layout(
            Field('o'),
            FieldWithButtons(
                Field('q',
                      placeholder=_('Filtrar Lista'),
                      css_class='input-lg'),
                StrictButton(
                    _('Filtrar'), css_class='btn-outline-primary btn-lg',
                    type='submit'))
        )

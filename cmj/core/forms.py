
from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm, UserChangeForm as BaseUserChangeForm
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _
from django_filters.filterset import FilterSet

from image_cropping.widgets import ImageCropWidget, CropWidget
from sapl.crispy_layout_mixin import to_row
import django_filters

from cmj.core.models import Trecho, TipoLogradouro, User, OperadorAreaTrabalho,\
    ImpressoEnderecamento


class LoginForm(AuthenticationForm):

    username = forms.CharField(
        label="Username", max_length=254,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'name': 'username',
                'placeholder': _('Digite seu Endereço de email')}))
    password = forms.CharField(
        label="Password", max_length=30,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'name': 'password',
                'placeholder': _('Digite sua Senha')}))


class UserCreationForm(BaseUserCreationForm):

    class Meta(BaseUserCreationForm.Meta):
        model = User
        fields = ('email',)


class UserChangeForm(BaseUserChangeForm):

    class Meta(BaseUserChangeForm.Meta):
        model = User


class RegistrationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        fields = ('email', 'first_name', 'last_name')


class CustomImageCropWidget(ImageCropWidget):
    """
    Custom ImageCropWidget that doesn't show the initial value of the field.
    We use this trick, and place it right under the CropWidget so that
    it looks like the user is seeing the image and clearing the image.
    """
    template_with_initial = (
        # '%(initial_text)s: <a href="%(initial_url)s">%(initial)s</a> '
        '%(clear_template)s<br />%(input_text)s: %(input)s'
    )


class UserForm(UserChangeForm):
    # We don't have a password field
    password = None

    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'avatar', 'cropping')
        widgets = {
            'avatar': CustomImageCropWidget(),
            'cropping': CropWidget(),
        }


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
                    _('Filtrar'), css_class='btn-default btn-lg',
                    type='submit'))
        )

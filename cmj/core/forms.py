
from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Fieldset
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm, UserChangeForm as BaseUserChangeForm
from django.core.exceptions import ValidationError
from django.forms.models import ModelForm
from django.utils.translation import gettext_lazy as _
from django_filters.filterset import FilterSet
from image_cropping.widgets import ImageCropWidget, CropWidget
import django_filters

from cmj.core.models import Trecho, TipoLogradouro, User, OperadorAreaTrabalho,\
    ImpressoEnderecamento, AuditLog
from cmj.globalrules import WORKSPACE_GROUPS
from cmj.sigad.models import UrlShortener
from sapl.crispy_layout_mixin import to_row, SaplFormHelper, form_actions


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


def get_username():
    try:
        return [(u.pk, f'{u.get_full_name()} ({u.email})') for u in
                get_user_model().objects.all()]
    except:
        return []


def get_models():
    return [(m, m) for m in
            AuditLog.objects.distinct('model_name').order_by('model_name').values_list('model_name', flat=True)]


class AuditLogFilterSet(django_filters.FilterSet):
    OPERATION_CHOICES = (
        ('U', 'Atualizado'),
        ('C', 'Criado'),
        ('D', 'Excluído'),
        ('P', 'Pesquisa'),
    )

    user = django_filters.ChoiceFilter(
        choices=get_username(), label=_('Usuário'))
    busca = django_filters.CharFilter(
        label=_('Filtrar Campo'),
        method='filter_busca'

    )
    operation = django_filters.ChoiceFilter(
        choices=OPERATION_CHOICES, label=_('Operação'))
    model_name = django_filters.ChoiceFilter(
        choices=get_models, label=_('Tipo de Registro'))
    timestamp = django_filters.DateRangeFilter(label=_('Período'))

    class Meta:
        model = AuditLog
        fields = ['user', 'operation',
                  'model_name', 'timestamp', 'busca']

    def filter_busca(self, qs, field, value):
        value = value.split(',')
        value = list(map(lambda x: x.strip().split('='), value))

        params = {}
        for k, v in value:
            if k == 'id':
                params['object_id'] = v
                continue
            try:
                v = int(v)
                params[f'obj__0__fields__{k}'] = v
            except:
                params[f'obj__0__fields__{k}'] = v

        qsf = qs.filter(**params)
        if not qsf:
            params = {}
            for k, v in value:
                try:
                    v = int(v)
                    params[f'obj__0__fields__{k}'] = v
                except:
                    params[f'obj__0__fields__{k}__icontains'] = v

            qsf = qs.filter(**params)
        return qsf

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        row0 = to_row([('user', 2),
                       ('operation', 2),
                       ('model_name', 4),
                       ('busca', 2),
                       ('timestamp', 2)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Filtros'),
                     row0,
                     form_actions(label='Aplicar Filtro')))

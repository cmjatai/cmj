from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset
from django import forms
from django.db.models import Q
from django.forms import widgets
from django.forms.models import ModelForm, ModelMultipleChoiceField
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from cmj.crispy_layout_mixin import to_row, SaplFormLayout
from cmj.sigad import models
from cmj.sigad.models import Classe, Documento, Revisao, CaixaPublicacao,\
    CLASSE_DOC_MANAGER_CHOICE, CaixaPublicacaoClasse,\
    CaixaPublicacaoRelationship
from cmj.sigad.templatetags.sigad_filters import caixa_publicacao
from cmj.utils import YES_NO_CHOICES
from sapl.parlamentares.models import Parlamentar


class UpLoadImportFileForm(forms.Form):
    import_file = forms.FileField(
        required=True,
        label=_('Arquivo formato ODF para Importanção')
    )

    def __init__(self, *args, **kwargs):
        super(UpLoadImportFileForm, self).__init__(*args, **kwargs)
        self.fields['import_file'].widget.attrs.update(
            {'multiple': 'multiple'})


error_messages = {
    'required': _('Este campo é obrigatório'),
    'invalid': _('Formato inválido.')
}


class ClasseForm(ModelForm):

    visibilidade = forms.ChoiceField(
        label=Classe._meta.get_field('visibilidade').verbose_name,
        choices=Documento.VISIBILIDADE_STATUS)
    perfil = forms.ChoiceField(
        label=Classe._meta.get_field('perfil').verbose_name,
        choices=models.PERFIL_CLASSE)
    descricao = forms.CharField(
        label=Classe._meta.get_field('descricao').verbose_name,
        widget=forms.Textarea,
        required=False)

    parent = forms.ModelChoiceField(
        queryset=Classe.objects.all(),
        widget=forms.HiddenInput(),
        required=False)

    class Meta:
        model = Classe
        fields = [
            'codigo',
            'titulo',
            'visibilidade',
            'perfil',
            'descricao',
            'parent',
            'tipo_doc_padrao',
            'template_doc_padrao',
            'template_classe',
            'parlamentar'
        ]

    def __init__(self, *args, **kwargs):

        row1 = to_row([
            ('codigo', 2),
            ('titulo', 4),
            ('perfil', 3),
            ('parlamentar', 3),
        ])

        row2 = to_row([
            ('visibilidade', 2),
            ('template_classe', 3),
            ('tipo_doc_padrao', 4),
            ('template_doc_padrao', 3),
        ])
        row3 = to_row([
            ('descricao', 12),
        ])

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Identificação Básica'),
                     row1, row2, row3))

        super(ClasseForm, self).__init__(*args, **kwargs)


class DocumentoForm(ModelForm):

    parlamentares = ModelMultipleChoiceField(
        queryset=Parlamentar.objects.filter(ativo=True), required=False,
        label=Parlamentar._meta.verbose_name_plural,
        widget=forms.SelectMultiple(attrs={'size': '10'})
    )
    public_date = forms.DateTimeField(
        widget=forms.HiddenInput(), required=False,)

    tipo = forms.ChoiceField(choices=Documento.tipo_parte_doc['documentos'])

    capa = forms.TypedChoiceField(label=_('Capa de sua Classe'),
                                  choices=YES_NO_CHOICES,
                                  coerce=lambda x: x == 'True')

    class Meta:
        model = Documento
        fields = ['titulo',
                  'template_doc',
                  'descricao',
                  'visibilidade',
                  'parlamentares',
                  'public_date',
                  'tipo',
                  'listar',
                  'capa'
                  ]

    def __init__(self, *args, **kwargs):

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            to_row([
                ('titulo', 7), ('visibilidade', 3), ('listar', 2)
            ]),
            to_row([
                ('tipo', 4), ('template_doc', 4), ('capa', 4),
            ]),
            to_row([
                ('descricao', 8),
                ('parlamentares', 4)
            ]),
        )

        super(DocumentoForm, self).__init__(*args, **kwargs)

        self.fields['parlamentares'].choices = [
            ('0', '--------------')] + list(
            self.fields['parlamentares'].choices)

        self.fields['capa'].initial = self.instance == self.instance.classe.capa

    def save(self, commit=True):
        inst = self.instance

        if inst.visibilidade != Documento.STATUS_PUBLIC:
            inst.public_date = None
            inst.public_end_date = None
        else:
            if not inst.public_date:
                inst.public_date = timezone.now()

        inst = super().save(commit)

        if not inst.childs.exists():
            container = Documento()
            container.titulo = ''
            container.descricao = ''
            container.classe = inst.classe
            container.tipo = Documento.TPD_CONTAINER_SIMPLES
            container.owner = inst.owner
            container.parent = inst
            container.ordem = 1
            container.visibilidade = inst.visibilidade
            container.save()

        classe = inst.classe
        classe.capa = inst if self.cleaned_data['capa'] else None
        classe.save()

        return inst


class CaixaPublicacaoForm(forms.ModelForm):

    documentos = forms.ModelMultipleChoiceField(
        queryset=Documento.objects.all(),
        widget=widgets.CheckboxSelectMultiple,
        required=False

    )

    class Meta:
        model = CaixaPublicacaoClasse
        fields = ['nome', 'key', 'documentos']

    def __init__(self, *args, **kwargs):
        classe = kwargs['initial'].pop('classe', None)

        if classe:
            tmpl = classe.template_classe
            qs = getattr(classe.documento_set, CLASSE_DOC_MANAGER_CHOICE[tmpl])
            qs = qs()
        else:
            qs = Documento.objects.qs_news().filter(
                nodes__midia__isnull=False
            )
        qs = qs.distinct()

        super(CaixaPublicacaoForm, self).__init__(*args, **kwargs)

        self.fields['documentos'].choices = [
            (d.id, '%s%s' % (
                d,
                (' - (%s)' % ', '.join(d.caixapublicacao_set.values_list(
                    'nome', flat=True))
                 ) if d.caixapublicacao_set.exclude(
                    id=self.instance.pk).exists() else '')
             ) for d in qs[:100]
        ]

        if self.instance.pk:
            self.fields['nome'].widget.attrs = {'readonly': True}
            self.fields['key'].widget.attrs = {'readonly': True}

    def save(self, commit=False):

        inst = super().save(commit=False)
        inst.save()
        inst.documentos.clear()
        for doc in self.cleaned_data['documentos']:
            CaixaPublicacaoRelationship.objects.create(
                caixapublicacao=inst,
                documento=doc)

        inst.reordene()
        return inst

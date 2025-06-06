from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset
from django import forms
from django.forms import widgets
from django.forms.models import ModelForm, ModelMultipleChoiceField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from cmj.sigad import models
from cmj.sigad.models import Classe, Documento, CaixaPublicacaoRelationship, \
    CaixaPublicacaoClasse
from cmj.utils import YES_NO_CHOICES
from sapl.crispy_layout_mixin import to_row, SaplFormLayout
from sapl.materia.models import MateriaLegislativa
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
        choices=Classe.PERFIL_CLASSE)
    descricao = forms.CharField(
        label=Classe._meta.get_field('descricao').verbose_name,
        widget=forms.Textarea,
        required=False)

    parent = forms.ModelChoiceField(
        queryset=Classe.objects.all(),
        label=_('Classe Ascendente'),
        required=False)

    url_redirect = forms.CharField(
        label=Classe._meta.get_field('url_redirect').verbose_name,
        required=False)

    atricon = forms.CharField(
        label=Classe._meta.get_field('atricon').verbose_name,
        required=False)

    class Meta:
        model = Classe
        fields = [
            'codigo',
            'atricon',
            'titulo',
            'apelido',
            'visibilidade',
            'perfil',
            'descricao',
            'subtitle',
            'parent',
            'tipo_doc_padrao',
            'template_doc_padrao',
            'template_classe',
            'parlamentar',
            'list_in_mapa',
            'list_in_inf',
            'list_in_menu',
            'menu_lateral',
            'url_redirect'
        ]

    def __init__(self, *args, **kwargs):

        row1 = to_row([
            ('visibilidade', 2),
            ('parent', 3),
            ('codigo', 1),
            ('atricon', 1),
            ('parlamentar', 2),
            ('list_in_mapa', 3),
        ])

        row2 = to_row([
            ('template_classe', 3),
            ('tipo_doc_padrao', 3),
            ('template_doc_padrao', 3),
            ('list_in_inf', 3),
        ])
        row3 = to_row([
            ('perfil', 4),
            ('url_redirect', 5),
            ('list_in_menu', 3),
        ])
        row4 = to_row([
            ('titulo', 4),
            ('apelido', 5),
            ('menu_lateral', 3),
            ('descricao', 12),
            ('subtitle', 12)
        ])

        self.helper = FormHelper()
        self.helper.attrs.update({
            'class': 'form-compact'
            })
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Identificação Básica'),
                     row1, row2, row3, row4))

        super(ClasseForm, self).__init__(*args, **kwargs)

        #print(self.fields['parent'].choices)

        pc = []

        def get_pc_order_by(nd=None):

            if not nd:
                pc.append(('', '--------------'))
                childs = Classe.objects.filter(
                    parent__isnull=True)
            else:
                pc.append((nd.id, str(nd)))
                childs = nd.childs.all()

            for c in childs.order_by('titulo'):
                get_pc_order_by(c)

        get_pc_order_by()
        self.fields['parent'].choices = pc
        l = list(self.fields['parent'].choices)
        return


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

    materias = ModelMultipleChoiceField(
        queryset=MateriaLegislativa.objects.order_by(
            '-data_apresentacao'),
        required=False,
        label=MateriaLegislativa._meta.verbose_name_plural,
        widget=forms.SelectMultiple(attrs={'size': '10'})
    )

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
                  'capa',
                  'materias'
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
            to_row([
                ('materias', 12),
            ]),
        )

        super(DocumentoForm, self).__init__(*args, **kwargs)

        self.fields['parlamentares'].choices = [
            ('0', '--------------')] + list(
            self.fields['parlamentares'].choices)

        self.fields['materias'].choices = [
            ('0', '--------------')] + [(m.id, str(m) + ' - ' + m.ementa) for m in self.fields['materias'].queryset[:200]]

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
            qs = classe.documento_set.public_all_docs()
            # qs = getattr(classe.documento_set, CLASSE_DOC_MANAGER_CHOICE[tmpl])
            # qs = qs()
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

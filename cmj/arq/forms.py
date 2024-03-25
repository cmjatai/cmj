from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset
from django import forms
from django.core.files.base import File
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _

from cmj.arq.models import ArqClasse, PERFIL_ARQCLASSE, ArqDoc, ARQCLASSE_FISICA,\
    ARQCLASSE_LOGICA, DraftMidia
from cmj.utils import YES_NO_CHOICES
from sapl.crispy_layout_mixin import to_row, SaplFormLayout


class ArqClasseForm(ModelForm):

    perfil = forms.ChoiceField(
        label=ArqClasse._meta.get_field('perfil').verbose_name,
        choices=PERFIL_ARQCLASSE)
    descricao = forms.CharField(
        label=ArqClasse._meta.get_field('descricao').verbose_name,
        widget=forms.Textarea,
        required=False)

    parent = forms.ModelChoiceField(
        queryset=ArqClasse.objects.all(),
        widget=forms.HiddenInput(),
        required=False)

    class Meta:
        model = ArqClasse
        fields = [
            'codigo',
            'titulo',
            'perfil',
            'descricao',
            'parent',
            'render_tree2'

        ]

    def __init__(self, *args, **kwargs):

        row1 = to_row([
            ('codigo', 2),
            ('titulo', 7),
            ('perfil', 3),
        ])

        row2 = to_row([
            ('descricao', 12),
        ])

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Identificação Básica'),
                     row1, row2,))

        super(ArqClasseForm, self).__init__(*args, **kwargs)


class ArqDocForm(ModelForm):

    classe_logica = forms.ModelChoiceField(
        queryset=ArqClasse.objects.filter(perfil=ARQCLASSE_LOGICA),
        required=False)

    classe_estrutural = forms.ModelChoiceField(
        queryset=ArqClasse.objects.filter(perfil=ARQCLASSE_FISICA),
        required=True)

    draftmidia = forms.ModelChoiceField(
        queryset=DraftMidia.objects.all(),
        label=_('Utilizar arquivo do Draft'),
        required=False)

    class Meta:
        model = ArqDoc
        fields = [
            'codigo',
            'data',
            'titulo',
            'descricao',
            'classe_logica',
            'classe_estrutural',
            'arquivo',
            'draftmidia'
        ]

    def __init__(self, *args, **kwargs):

        self._request_user = kwargs['initial'].get('request_user', None)

        row1 = to_row([
            ('codigo', 2),
            ('data', 3),
            ('titulo', 7),
        ])

        row2 = to_row([
            ('classe_logica', 5),
            ('classe_estrutural', 7),
        ])

        row3 = to_row([
            ('arquivo', 12),
            ('draftmidia', 12),
        ])

        row4 = to_row([
            ('descricao', 12),
        ])

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Identificação Básica'),
                     row1, row2, row3, row4,))

        super(ArqDocForm, self).__init__(*args, **kwargs)

        pc = []

        def get_pc_order_by(nd=None):

            if not nd:
                pc.append(('', '--------------'))
                childs = ArqClasse.objects.filter(
                    parent__isnull=True)
            else:
                pc.append((nd.id, str(nd)))
                childs = nd.childs.all()

            for c in childs.order_by('codigo'):
                get_pc_order_by(c)

        get_pc_order_by()

        self.fields['classe_estrutural'].choices = pc

        if not self.instance.pk:
            dmc = []
            dmc.append(('', '--------------'))
            for dm in DraftMidia.objects.filter(
                draft__owner=self._request_user,
                metadata__ocrmypdf__pdfa=DraftMidia.METADATA_PDFA_PDFA
            ):
                name_file_midia = dm.metadata['uploadedfile']['name']
                dmc.append((dm.id, f'{str(dm.draft)} - {name_file_midia}'))
            self.fields['draftmidia'].choices = dmc
        else:
            self.fields['draftmidia'].widget = forms.HiddenInput()

    def save(self, commit=True):

        cd = self.cleaned_data
        dm = cd['draftmidia']

        inst = self.instance

        if not inst.pk:
            inst.owner = self._request_user
        inst.modifier = self._request_user

        inst = ModelForm.save(self, commit=commit)

        if dm:
            path = dm.arquivo.path
            f = open(path, 'rb')
            f = File(f)
            inst.arquivo.save(path.split('/')[-1], f)
            inst.save()
            dm.delete()

        return inst

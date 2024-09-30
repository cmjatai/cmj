import logging

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Div, HTML
from django import forms
from django.core.exceptions import ValidationError
from django.core.files.base import File
from django.forms import widgets
from django.forms.forms import Form
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _

from cmj.arq.models import ArqClasse, PERFIL_ARQCLASSE, ArqDoc, ARQCLASSE_FISICA,\
    ARQCLASSE_LOGICA, DraftMidia
from cmj.utils import YES_NO_CHOICES
from sapl.crispy_layout_mixin import to_row, SaplFormLayout


logger = logging.getLogger(__name__)


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

    render_tree2 = forms.TypedChoiceField(
        label=_('Renderização Tree2'),
        required=False,
        choices=YES_NO_CHOICES)

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
        parent = None
        if 'initial' in kwargs:
            self.parent = kwargs['initial'].get('parent', None)

        row1 = to_row([
            ('codigo', 2),
            ('titulo', 'col-md'),
            ('perfil', 3),
            ('render_tree2', f'col-md-{0 if parent else 2}'),
        ])

        row2 = to_row([
            ('descricao', 12),
        ])

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Identificação Básica'),
                     row1, row2,))

        super(ArqClasseForm, self).__init__(*args, **kwargs)

        if self.parent:
            self.fields['render_tree2'].widget = forms.HiddenInput()
        else:
            self.fields['render_tree2'].widget = widgets.CheckboxInput()

    def clean_render_tree2(self):
        rt = self.cleaned_data.get('render_tree2', False) or False
        return rt

    def clean_perfil(self):
        perfil = self.cleaned_data.get('perfil', None)
        if perfil != str(self.parent.perfil):
            raise ValidationError(
                f"""Os perfis das SubArqClasses devem ser iguais!""")
        return perfil

    def clean_parent(self):
        parent = self.parent
        if parent and parent.checkcheck:
            raise ValidationError(
                f"""Para criar/editar itens em {parent.titulo}, é necessário que ela não esteja trancada!""")
        return parent


class ArqDocForm(ModelForm):

    classe_logica = forms.ModelChoiceField(
        queryset=ArqClasse.objects.filter(perfil=ARQCLASSE_LOGICA),
        required=True)

    classe_estrutural = forms.ModelChoiceField(
        queryset=ArqClasse.objects.filter(perfil=ARQCLASSE_FISICA),
        required=True)

    draftmidia = forms.ModelChoiceField(
        queryset=DraftMidia.objects.all(),
        label=_('Arquivo do Draft a ser utilizado'),
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

        inst = kwargs.get('instance', None)

        if not inst:

            dmc = []
            dmc.append(('', '--------------'))
            for dm in DraftMidia.objects.filter(
                draft__owner=self._request_user,
                metadata__ocrmypdf__pdfa=DraftMidia.METADATA_PDFA_PDFA
            ).order_by('draft__descricao', 'draft_id', 'sequencia'):
                name_file_midia = dm.metadata['uploadedfile']['name']
                dmc.append((dm.id, f'{str(dm.draft)} - {name_file_midia}'))

            if len(dmc) > 1:
                kwargs['initial']['draftmidia'] = dmc[1]

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

        row_form = to_row([
            ([row1, row2, row3, row4, ], 8),
            (HTML('''
            <a id="link_open_draftmidia" target="_blank">
                <img id="img_preview_arqdoc_create" class="embed-responsive" />
            </a>
            '''), 4)
        ])

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Identificação Básica'),
                     row_form))

        super(ArqDocForm, self).__init__(*args, **kwargs)

        pc = {
            100: [],
            200: []
        }

        def get_pc_order_by(perfil, nd=None, only_opened=None):
            params = {
                'perfil': perfil
            }

            if only_opened:
                params['checkcheck'] = False

            if not nd:
                pc[perfil].append(('', '--------------'))
                params['parent__isnull'] = True
                childs = ArqClasse.objects.filter(**params)
            else:
                pc[perfil].append((nd.id, str(nd)))
                childs = nd.childs.filter(**params)

            for c in childs.order_by('codigo'):
                get_pc_order_by(perfil, nd=c)

        get_pc_order_by(100, only_opened=True)
        get_pc_order_by(200)

        self.fields['classe_estrutural'].choices = pc[100]
        self.fields['classe_logica'].choices = pc[200]
        if not self.instance.pk:
            self.fields['draftmidia'].choices = dmc
            if self._request_user.is_superuser:
                self.fields['arquivo'].widget = forms.HiddenInput()
        else:
            self.fields['draftmidia'].widget = forms.HiddenInput()

    def save(self, commit=True):

        cd = self.cleaned_data
        dm = cd['draftmidia']

        inst = self.instance

        if not inst.pk:
            inst.owner = self._request_user

        inst.modifier = self._request_user

        inst.editado = True
        inst = ModelForm.save(self, commit=commit)

        if dm:
            path = dm.arquivo.path
            f = open(path, 'rb')
            f = File(f)
            inst.arquivo.save(path.split('/')[-1], f)
            inst.save()
            dm.delete()

        return inst


class ArqDocBulkCreateForm(ModelForm):

    classe_logica = forms.ModelChoiceField(
        queryset=ArqClasse.objects.filter(perfil=ARQCLASSE_LOGICA),
        required=True)

    classe_estrutural = forms.ModelChoiceField(
        queryset=ArqClasse.objects.filter(perfil=ARQCLASSE_FISICA),
        required=True)

    draftmidia = forms.ModelMultipleChoiceField(
        queryset=DraftMidia.objects.all(),
        label=_('Arquivos do Draft a serem utilizados'),
        required=False,
        widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = ArqDoc
        fields = [
            'data',
            'classe_logica',
            'classe_estrutural',
            'draftmidia'
        ]

    def __init__(self, *args, **kwargs):

        self._request_user = kwargs['initial'].get('request_user', None)

        dmc = []
        dm = DraftMidia.objects.filter(
            draft__owner=self._request_user,
            metadata__ocrmypdf__pdfa=DraftMidia.METADATA_PDFA_PDFA
        ).order_by('draft__descricao', 'draft_id', 'sequencia').first()

        draft = dm.draft if dm else None

        for dm in DraftMidia.objects.filter(
            draft=draft,
            draft__owner=self._request_user,
            metadata__ocrmypdf__pdfa=DraftMidia.METADATA_PDFA_PDFA
        ).order_by('draft__descricao', 'draft_id', 'sequencia'):
            name_file_midia = dm.metadata['uploadedfile']['name']
            dmc.append((dm.id, f'{str(dm.draft)} - {name_file_midia}'))

        row1 = to_row([
            ('data', 3),
            ('classe_logica', 9),
            ('classe_estrutural', 12),
        ])

        row3 = to_row([
            (
                HTML(f'''
                <div class="controls">
                    <div class="checkbox">
                        <label for="id_check_all">
                            <input type="checkbox" id="id_check_all" onchange="checkAll(this)" /> Marcar/Desmarcar Todos 
                            // <em>Draft a Importar: {draft}</em> 
                        </label>
                    </div>
                </div>
            '''),
                12),
            ('draftmidia', 7), (HTML('''
            <a id="link_open_draftmidia" target="_blank">
                <img id="img_preview_arqdoc_create" class="embed-responsive" />
            </a>
            '''), 5)
        ])

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Geração de ArqDocumentos em série '), row1, row3))

        super(ArqDocBulkCreateForm, self).__init__(*args, **kwargs)

        pc = {
            100: [],
            200: []
        }

        def get_pc_order_by(perfil, nd=None, only_opened=None):
            params = {
                'perfil': perfil
            }

            if only_opened:
                params['checkcheck'] = False

            if not nd:
                pc[perfil].append(('', '--------------'))
                params['parent__isnull'] = True
                childs = ArqClasse.objects.filter(**params)
            else:
                pc[perfil].append((nd.id, str(nd)))
                childs = nd.childs.filter(**params)

            for c in childs.order_by('codigo'):
                get_pc_order_by(perfil, nd=c)

        get_pc_order_by(100, only_opened=True)
        get_pc_order_by(200)

        self.fields['classe_estrutural'].choices = pc[100]
        self.fields['classe_logica'].choices = pc[200]
        self.fields['draftmidia'].choices = dmc

    def save(self, commit=True):

        codigo_init = self.initial['codigo']

        cd = self.cleaned_data
        dm_qs = cd['draftmidia']

        inst = self.instance
        inst.owner = self._request_user
        inst.modifier = self._request_user
        inst.editado = False
        inst.checkcheck = True

        draft = None
        for dm in dm_qs.all():
            try:
                draft = dm.draft
                inst.id = None
                inst.codigo = codigo_init
                inst.titulo = f'{dm.draft.descricao} - {dm.metadata["uploadedfile"]["name"]}'
                inst.descricao = 'Documento digitalizado, aplicado OCR, transformado em PDF/A e incluído automaticamente para indexação e pesquisas.'

                inst.save()
                path = dm.arquivo.path
                f = open(path, 'rb')
                f = File(f)
                inst.arquivo.save(path.split('/')[-1], f)
                dm.delete()
                codigo_init += 1
            except Exception as e:
                logger.ERROR(e)

        if not draft.draftmidia_set.exists():
            draft.delete()

        return inst

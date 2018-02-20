from crispy_forms.bootstrap import Alert
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div
from django import forms
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _
from sapl.crispy_layout_mixin import SaplFormLayout, to_row, form_actions

from cmj.context_processors import areatrabalho
from cmj.core.models import AreaTrabalho, Notificacao
from cmj.ouvidoria.models import Solicitacao


class DenunciaForm(ModelForm):

    areatrabalho_parlamentar = forms.ModelMultipleChoiceField(
        label=_('Encaminhar Denúncia para parlamentar'),
        required=False,
        queryset=AreaTrabalho.objects.areatrabalho_de_parlamentares(),
        widget=forms.CheckboxSelectMultiple,
        help_text=_('Você pode preferir encaminhar sua denúncia para um '
                    'ou mais parlamentares. '
                    'Eles serão isoladamente notificados com sua manifestação.'
                    '<br>Caso não selecione nenhum parlamentar, sua denúncia '
                    'será encaminhada para o setor responsável pela Ouvidoria '
                    'Institucional.'
                    ))

    class Meta:
        model = Solicitacao
        fields = ('titulo', 'descricao',)
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 16})}

    def __init__(self, *args, **kwargs):

        rows = to_row(
            [
                (Div(
                    to_row([('titulo', 12),
                            ('descricao', 12), ])
                ), 7),
                (Div(
                    to_row([('areatrabalho_parlamentar', 12)])
                ), 5),

            ]
        )

        if 'logged_user' in kwargs['initial'] and \
                kwargs['initial']['logged_user']:
            rows.insert(
                0, Alert(
                    _('<strong>Atenção, você foi desconectado!!!</strong><br>'
                      'Ao escolher fazer uma denúncia anônima, '
                      'o Portal da Câmara Municipal de Jataí desconectou seu '
                      'usuário para que sua manifestação não tenha nenhuma '
                      'relação com você. '
                      'Assim podemos garantir que sua denûncia é anônima '
                      'e não mantemos registro sobre você.<br>'
                      'Para voltar a utilizar das funções que você possuia '
                      'ao estar logado, é só se conectar novamente.'),
                    css_class="alert-info"))

        super(DenunciaForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            *rows,
            actions=form_actions(label=_('Enviar'))
        )

    def save(self, commit=True):

        cd = self.cleaned_data

        at_list = cd['areatrabalho_parlamentar']

        if not at_list.exists():
            at_list = AreaTrabalho.objects.areatrabalho_da_instituicao()

        for at in at_list:
            denuncia = Solicitacao()
            denuncia.titulo = self.instance.titulo
            denuncia.descricao = self.instance.descricao
            denuncia.tipo = Solicitacao.TIPO_DENUNCIA
            denuncia.areatrabalho = at
            denuncia.save()

            # TODO: criar grupo e enviar apenas para usuários no grupo
            for operador in at.operadorareatrabalho_set.all():
                nt = Notificacao()
                nt.content_object = denuncia
                nt.user = operador.user
                nt.save()

            # TODO: Enviar por email

        return

    def clean(self):
        pass

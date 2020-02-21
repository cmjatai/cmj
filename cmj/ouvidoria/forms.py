from crispy_forms.bootstrap import Alert
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _

from cmj.context_processors import areatrabalho
from cmj.core.models import AreaTrabalho, Notificacao
from cmj.ouvidoria.models import Solicitacao, MensagemSolicitacao
from sapl.crispy_layout_mixin import SaplFormLayout, to_row, form_actions,\
    to_column


class DenunciaForm(ModelForm):

    # areatrabalho_parlamentar = forms.ModelMultipleChoiceField(
    #    label=_('Encaminhar Denúncia para parlamentar'),
    #    required=False,
    #    queryset=AreaTrabalho.objects.areatrabalho_de_parlamentares(),
    #    widget=forms.CheckboxSelectMultiple,
    #    help_text=_('Você pode preferir encaminhar sua denúncia para um '
    #                'ou mais parlamentares. '
    #                'Eles serão isoladamente notificados com sua manifestação.'
    #                '<br>Caso não selecione nenhum parlamentar, sua denúncia '
    #                'será encaminhada para o setor responsável pela Ouvidoria '
    #                'Institucional.'
    #                ))

    class Meta:
        model = Solicitacao
        fields = ('titulo', 'descricao',)
        widgets = {
            'descricao': forms.Textarea()}

    def __init__(self, *args, **kwargs):

        rows = [Div(
            to_column((
                to_row([
                    ('titulo', 8),
                    (Div(
                        css_class="g-recaptcha" if not settings.DEBUG else '',
                        data_sitekey=settings.GOOGLE_RECAPTCHA_SITE_KEY
                    ), 4),
                    ('descricao', 12),
                    (Alert(_(
                        """<strong>Aviso</strong><br>
                            Ao enviar uma Denúncia Anônima, você receberá
                            um link para acompanhar sua denúncia.<br>
                            Só será
                            possível acompanhar e interagir com a ouvidoria
                            através deste link.<br>
                            Veja que este link será como um código 
                            privativo seu sem sua identificação, 
                            no entanto, se você compartilhar esse link, 
                            quem possuí-lo verá sua denúncia 
                            e poderá interagir também.
                            """),
                        css_class="alert-warning",
                        dismiss=False), 12)
                ]),
                12)),

            # to_column((
            #    to_row([('areatrabalho_parlamentar', 12)]),
            #    4)),

            css_class="row"
        )]

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

        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            *rows,
            actions=form_actions(label=_('Enviar'))
        )

    def save(self, commit=True):

        cd = self.cleaned_data

        #at_list = cd['areatrabalho_parlamentar']

        # if not at_list.exists():
        at_list = AreaTrabalho.objects.areatrabalho_da_instituicao()

        for at in at_list:
            denuncia = Solicitacao()
            denuncia.titulo = self.instance.titulo
            denuncia.descricao = self.instance.descricao
            denuncia.tipo = Solicitacao.TIPO_DENUNCIA
            denuncia.areatrabalho = at
            denuncia.save()

            for operador in at.operadorareatrabalho_set.all():
                nt = Notificacao()
                nt.content_object = denuncia
                nt.user = operador.user
                nt.areatrabalho = at
                nt.save()

        return denuncia  # TODO: retorno incorreto, corrigir se existir mais de uma area de trabalho de instituição

    def clean(self):

        cd = self.cleaned_data
        if settings.DEBUG:
            return cd

        recaptcha = self.data.get('g-recaptcha-response', '')
        if not recaptcha:
            raise ValidationError(
                _('Verificação do reCAPTCHA não efetuada.'))

        import urllib3
        import json

        #encoded_data = json.dumps(fields).encode('utf-8')

        url = ('https://www.google.com/recaptcha/api/siteverify?'
               'secret=%s'
               '&response=%s' % (settings.GOOGLE_RECAPTCHA_SECRET_KEY,
                                 recaptcha))

        http = urllib3.PoolManager()
        try:
            r = http.request('POST', url)
            data = r.data.decode('utf-8')
            jdata = json.loads(data)
        except Exception as e:
            raise ValidationError(
                _('Ocorreu um erro na validação do reCAPTCHA.'))

        if jdata['success']:
            return cd
        else:
            raise ValidationError(
                _('Ocorreu um erro na validação do reCAPTCHA.'))

        return cd


class SolicitacaoForm(ModelForm):

    # areatrabalho_parlamentar = forms.ModelChoiceField(
    #    label=_('Prefere se Comunicar Diretamente com um Parlamentar?'),
    #    required=False,
    #    queryset=AreaTrabalho.objects.areatrabalho_de_parlamentares(),
    #    help_text=_('Você pode preferir encaminhar seu Registro de '
    #                'Solicitação diretamente para um parlamentar. '
    #                'Seu Gabinete será notificado com sua manifestação '
    #                'e poderá te responder diretamente aqui pelo portal.<br>'
    #                'Você receberá um e-mail sempre que a assessoria de seu '
    #                'Parlamentar ou a Ouvidoria '
    #                'te encaminhar uma mensagem.<br>'
    #                '<strong>Caso opte por Registrar uma Solicitação para um '
    #                'Parlamentar, seu registro é privado entre você e '
    #                'o Parlamentar.<br>Portanto, se assim proceder você, '
    #                'a Ouvidoria Institucional da Câmara Municipal de Jataí '
    #                'não tomará conhecimento de sua solcitação.</strong><br>'
    #                'Para Registrar Solicitações Institucionais basta '
    #                'não selecionar Parlamentar na caixa acima.'
    #                ))

    class Meta:
        model = Solicitacao
        fields = ('titulo', 'descricao', 'tipo')
        widgets = {
            'tipo': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):

        row = Div(
            to_column((
                to_row([('titulo', 10), ('tipo', 2),
                        ('descricao', 12), ]),
                12)),
            # to_column((
            #    to_row([('areatrabalho_parlamentar', 12)]),
            #    4)),
            css_class="row")

        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            row,
            actions=form_actions(label=_('Enviar'))
        )

        self.instance.owner = kwargs['initial']['owner']

    def save(self, commit=True):

        cd = self.cleaned_data

        # at_list = cd['areatrabalho_parlamentar']

        # if not at_list:
        at_list = AreaTrabalho.objects.areatrabalho_da_instituicao()
        # else:
        #    at_list = (at_list, )

        for at in at_list:
            solicitacao = Solicitacao()
            solicitacao.owner = self.instance.owner
            solicitacao.titulo = self.instance.titulo
            solicitacao.descricao = self.instance.descricao
            solicitacao.tipo = self.instance.tipo
            solicitacao.areatrabalho = at
            solicitacao.save()

            for operador in at.operadorareatrabalho_set.all():
                nt = Notificacao()
                nt.content_object = solicitacao
                nt.user = operador.user
                nt.user_origin = self.instance.owner
                nt.areatrabalho = at
                nt.save()

        return solicitacao


class MensagemSolicitacaoForm(ModelForm):

    descricao = forms.CharField(
        label='',
        widget=forms.Textarea())

    class Meta:
        model = MensagemSolicitacao
        fields = ('descricao', 'anexo')

    def __init__(self, *args, **kwargs):

        rows = [('descricao', 12), ]

        if kwargs['initial']['owner']:
            rows.append(('anexo', 12))

        rows = to_row(rows)

        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            *rows,
            actions=form_actions(label=_('Enviar'))
        )

        self.instance.owner = kwargs['initial']['owner']
        self.instance.solicitacao = kwargs['initial']['solicitacao']

    def save(self, commit=True):
        inst = super().save(commit)

        # o dono da solicitação é notificado se ele não é o dono da mensagem
        if inst.owner != inst.solicitacao.owner and \
                not inst.solicitacao.owner is None:
            nt = Notificacao()
            nt.content_object = inst
            nt.user = inst.solicitacao.owner
            nt.user_origin = inst.owner
            nt.save()

        # todos os membros da área de trabalho receberão notificação de que
        # houve interação de um membro da área de trabalho ou do dono da solic

        areatrabalho = inst.solicitacao.areatrabalho
        for operador in areatrabalho.operadorareatrabalho_set.exclude(
                user=inst.owner):
            nt = Notificacao()
            nt.content_object = inst
            nt.user = operador.user
            nt.user_origin = inst.owner
            nt.areatrabalho = areatrabalho
            nt.save()

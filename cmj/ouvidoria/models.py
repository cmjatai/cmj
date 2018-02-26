
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models import Q, F
from django.db.models.deletion import PROTECT
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from cmj.core.models import AreaTrabalho, Notificacao
from cmj.utils import CmjChoices, get_settings_auth_user_model


class Solicitacao(models.Model):

    STATUS_RESTRICT = 1
    STATUS_PUBLIC = 0

    VISIBILIDADE_STATUS = CmjChoices(
        (STATUS_RESTRICT, 'status_restrict', _('Restrito')),
        (STATUS_PUBLIC, 'status_public', _('Público')),
    )

    TIPO_ACESSO_INFORMACAO = 10
    TIPO_ELOGIO = 20
    TIPO_SUGESTAO = 30
    TIPO_RECLAMACAO = 40
    TIPO_DENUNCIA = 900

    TIPO_SOLICITACAO_CHOICE = CmjChoices(
        (TIPO_ACESSO_INFORMACAO, 'tipo_acesso', _('Acesso a Informação')),
        (TIPO_ELOGIO, 'tipo_elogio', _('Elogio')),
        (TIPO_SUGESTAO, 'tipo_sugestao', _('Sugestão')),
        (TIPO_RECLAMACAO, 'tipo_reclamacao', _('Reclamação')),
        (TIPO_DENUNCIA, 'tipo_denuncia', _('Denúncia')),
    )

    created = models.DateTimeField(
        verbose_name=_('created'), editable=False, auto_now_add=True)

    owner = models.ForeignKey(
        get_settings_auth_user_model(),
        blank=True, null=True, default=None,
        on_delete=PROTECT,
        verbose_name=_('owner'), related_name='+')

    titulo = models.CharField(
        default='', max_length=254, verbose_name=_('Título'))

    descricao = models.TextField(
        default='', verbose_name=_('Descrição'))

    visibilidade = models.IntegerField(
        _('Visibilidade'),
        choices=VISIBILIDADE_STATUS,
        default=STATUS_RESTRICT)

    areatrabalho = models.ForeignKey(
        AreaTrabalho,
        verbose_name=_('Área de Trablho'))

    tipo = models.IntegerField(
        _('Tipo de Solicitação'),
        choices=TIPO_SOLICITACAO_CHOICE,
        default=TIPO_ACESSO_INFORMACAO)

    notificacoes = GenericRelation(
        Notificacao, related_query_name='notificacoes')

    class Meta:
        verbose_name = _('Solicitação')
        verbose_name_plural = _('Solicitações')

    def __str__(self):
        return self.titulo


class MensagemSolicitacao(models.Model):

    created = models.DateTimeField(
        verbose_name=_('created'), editable=False, auto_now_add=True)

    owner = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('owner'), related_name='+')

    descricao = models.TextField(
        default='',  verbose_name=_('Descrição'))

    solicitacao = models.ForeignKey(
        Solicitacao,
        verbose_name=_('Solicitação'),
        related_name='mensagemsolicitacao_set')

    notificacoes = GenericRelation(
        Notificacao, related_query_name='notificacoes')

    class Meta:
        ordering = ('created', )
        verbose_name = _('Mensagem de Solicitação')
        verbose_name_plural = _('Mensagens de Solicitação')

    def __str__(self):
        return self.descricao

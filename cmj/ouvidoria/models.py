
import hashlib

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields.jsonb import JSONField
from django.core.files.base import File
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Q, F
from django.db.models.deletion import PROTECT
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from cmj.core.models import AreaTrabalho, Notificacao
from cmj.mixins import CmjChoices
from cmj.utils import get_settings_auth_user_model,\
    restringe_tipos_de_arquivo_midias, TIPOS_MIDIAS_PERMITIDOS,\
    media_protected_storage


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
        verbose_name=_('Área de Trablho'),
        on_delete=PROTECT)

    tipo = models.IntegerField(
        _('Tipo de Solicitação'),
        choices=TIPO_SOLICITACAO_CHOICE,
        default=TIPO_ACESSO_INFORMACAO)

    hash_code = models.TextField(
        verbose_name=_('Hash de Acesso Anônimo'),
        max_length=200,
        blank=True)

    notificacoes = GenericRelation(
        Notificacao, related_query_name='notificacoes')

    class Meta:
        verbose_name = _('Solicitação')
        verbose_name_plural = _('Solicitações')
        ordering = ['id']

    def __str__(self):
        return self.titulo

    @property
    def email_notify(self):
        if self.owner:
            return {
                'subject': _('Solicitação (%s) de %s') % (
                    self.get_tipo_display(), self.owner),
            }
        else:
            return {
                'subject': _('Denuncia Anônima'),
            }

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.hash_code:
            md5 = hashlib.md5()
            data = '{}{}{}'.format(
                timezone.now(),
                self.titulo,
                self.descricao)

            md5.update(data.encode())
            self.hash_code = md5.hexdigest()

        return models.Model.save(self, force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)


def anexo_ouvidoria_path(instance, filename):
    return './ouvidoria/mensagem/%s/%s' % (
        instance.id,
        filename)


class MensagemSolicitacao(models.Model):

    FIELDFILE_NAME = ('anexo', )

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    created = models.DateTimeField(
        verbose_name=_('created'), editable=False, auto_now_add=True)

    owner = models.ForeignKey(
        get_settings_auth_user_model(),
        blank=True, null=True, default=None,
        verbose_name=_('owner'), related_name='+',
        on_delete=PROTECT)

    descricao = models.TextField(
        default='',  verbose_name=_('Descrição'))

    solicitacao = models.ForeignKey(
        Solicitacao,
        verbose_name=_('Solicitação'),
        related_name='mensagemsolicitacao_set',
        on_delete=PROTECT)

    notificacoes = GenericRelation(
        Notificacao, related_query_name='notificacoes')

    anexo = models.FileField(
        blank=True,
        null=True,
        storage=media_protected_storage,
        upload_to=anexo_ouvidoria_path,
        verbose_name=_('Anexo'),
        validators=[restringe_tipos_de_arquivo_midias],
        help_text=_('Envie um arquivo em anexo a sua mensagem.'))

    content_type = models.CharField(
        max_length=250,
        default='')

    class Meta:
        ordering = ('created', )
        verbose_name = _('Mensagem de Solicitação')
        verbose_name_plural = _('Mensagens de Solicitação')

    def delete(self, using=None, keep_parents=False):
        if self.anexo:
            self.anexo.delete()

        return models.Model.delete(
            self, using=using, keep_parents=keep_parents)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and self.anexo:
            anexo = self.anexo
            self.anexo = None
            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)
            self.anexo = anexo
            self.content_type = self.anexo.file.content_type

            if self.anexo.file.content_type in TIPOS_MIDIAS_PERMITIDOS:
                name_file = 'anexo.%s' % TIPOS_MIDIAS_PERMITIDOS[self.content_type]
                self.anexo.save(name_file, self.anexo.file)

        models.Model.save(self, force_insert=force_insert,
                          force_update=force_update, using=using, update_fields=update_fields)

    @property
    def email_notify(self):
        return {
            'subject': self.solicitacao.email_notify['subject'],
        }

        """'body': ('Solicitação: ' + self.solicitacao.titulo, self.descricao),
        'owner': self.owner,
        'created': self.created"""

    def __str__(self):
        return self.descricao

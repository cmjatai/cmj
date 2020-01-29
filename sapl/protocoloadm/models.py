from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields.jsonb import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.deletion import PROTECT
from django.urls.base import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices
import reversion

from cmj.core.models import AreaTrabalho, CertidaoPublicacao
from sapl.base.models import Autor
from sapl.materia.models import TipoMateriaLegislativa, UnidadeTramitacao,\
    MateriaLegislativa
from sapl.utils import (RANGE_ANOS, YES_NO_CHOICES, texto_upload_path,
                        get_settings_auth_user_model,
                        OverwriteStorage, PortalFileField)


@reversion.register()
class TipoDocumentoAdministrativo(models.Model):
    sigla = models.CharField(max_length=5, verbose_name=_('Sigla'))
    descricao = models.CharField(max_length=100, verbose_name=_('Descrição'))

    workspace = models.ForeignKey(
        AreaTrabalho,
        verbose_name=_('Área de Trabalho'),
        related_name='tipodocumentoadministrativo_set',
        blank=True, null=True, on_delete=PROTECT)

    class Meta:
        verbose_name = _('Tipo de Documento Administrativo')
        verbose_name_plural = _('Tipos de Documento Administrativo')
        ordering = ['descricao']

    def __str__(self):
        return self.descricao


"""
uuid4 + filenames diversos apesar de tornar url de um arquivo praticamente
impossível de ser localizado não está controlando o acesso.
Exemplo: o SAPL está configurado para ser docs adm restritivo porém
alguem resolve perga o link e mostrar o tal arquivo para um amigo, ou um
vizinho de departamento que não possui acesso... ou mesmo alguem que nem ao
menos está logado... este arquivo estará livre

outro caso, um funcionário bem intencionado, mas com um computador infectado
que consegue pegar todos os links da página que ele está acessando e esse
funcionário possui permissão para ver arquivos de docs administrativos.
Consequentemente os arquivos se tornarão públicos pois podem ser acessados
via url sem controle de acesso.

* foi aberta uma issue no github para rever a questão de arquivos privados:
https://github.com/interlegis/sapl/issues/751

a solução dela deverá dar o correto tratamento a essa questão.


def texto_upload_path(instance, filename):
    return '/'.join([instance._meta.model_name, str(uuid4()), filename])
"""


@reversion.register()
class Protocolo(models.Model):
    numero = models.PositiveIntegerField(
        blank=False, null=False, verbose_name=_('Número de Protocolo'))
    ano = models.PositiveSmallIntegerField(blank=False,
                                           null=False,
                                           choices=RANGE_ANOS,
                                           verbose_name=_('Ano do Protocolo'))
    data = models.DateField(null=True, blank=True,
                            verbose_name=_('Data do Protocolo'),
                            help_text=_('Informado manualmente'))
    hora = models.TimeField(null=True, blank=True,
                            verbose_name=_('Hora do Protocolo'),
                            help_text=_('Informado manualmente'))
    timestamp_data_hora_manual = models.DateTimeField(default=timezone.now)
    user_data_hora_manual = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('IP'),
        help_text=_('Usuário que está realizando Protocolo e informando '
                    'data e hora manualmente.'))
    ip_data_hora_manual = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('IP'),
        help_text=_('Endereço IP da estação de trabalho '
                    'do usuário que está realizando Protocolo e informando '
                    'data e hora manualmente.'))

    # Não foi utilizado auto_now_add=True em timestamp porque
    # ele usa datetime.now que não é timezone aware.
    timestamp = models.DateTimeField(
        default=timezone.now, null=True, blank=True)
    tipo_protocolo = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Tipo de Protocolo'))
    tipo_processo = models.PositiveIntegerField()
    interessado = models.CharField(
        max_length=200, blank=True, verbose_name=_('Interessado'))
    autor = models.ForeignKey(Autor,
                              blank=True,
                              null=True,
                              on_delete=models.PROTECT)
    assunto_ementa = models.TextField(blank=True)
    tipo_documento = models.ForeignKey(
        TipoDocumentoAdministrativo,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_('Tipo de Documento'))
    tipo_materia = models.ForeignKey(
        TipoMateriaLegislativa,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_('Tipo de Matéria'))
    numero_paginas = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Número de Páginas'))
    observacao = models.TextField(
        blank=True, verbose_name=_('Observação'))
    anulado = models.BooleanField(default=False)
    user_anulacao = models.CharField(max_length=1000, blank=True)
    ip_anulacao = models.CharField(max_length=15, blank=True)
    justificativa_anulacao = models.CharField(
        max_length=260, blank=True, verbose_name=_('Motivo'))
    timestamp_anulacao = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = _('Protocolo')
        verbose_name_plural = _('Protocolos')
        permissions = (
            ('action_anular_protocolo', _('Permissão para Anular Protocolo')),
        )

    def __str__(self):
        return _('%(numero)s/%(ano)s') % {
            'numero': self.numero, 'ano': self.ano
        }

    def materia_vinculada(self):
        try:
            materia = MateriaLegislativa.objects.get(
                tipo=self.tipo_materia,
                ano=self.ano,
                numero_protocolo=self.numero
            )
        except:
            return None
        return materia


@reversion.register()
class DocumentoAdministrativo(models.Model):
    tipo = models.ForeignKey(
        TipoDocumentoAdministrativo, on_delete=models.PROTECT,
        verbose_name=_('Tipo Documento'))
    numero = models.PositiveIntegerField(verbose_name=_('Número'))
    ano = models.PositiveSmallIntegerField(verbose_name=_('Ano'),
                                           choices=RANGE_ANOS)
    protocolo = models.ForeignKey(
        Protocolo,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_('Protocolo'))

    materia = models.ForeignKey(
        MateriaLegislativa,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name='documentoadministrativo_set',
        verbose_name=_('Matéria Vinculada')
    )

    data = models.DateField(verbose_name=_('Data'))

    temp_migracao_doc_acessorio = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Field temporário para migração dos docs acessórios da procuradoria'))

    temp_migracao_sislegis = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Field temporário para migração dos docs adms do sislegis'))

    old_path = models.TextField(
        verbose_name=_('Path antigo para Sislegis - Publicações'),
        blank=True, null=True, default=None)

    old_json = JSONField(
        verbose_name=_('Json from origin import'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    epigrafe = models.CharField(
        max_length=1000, blank=True, verbose_name=_('Epigrafe / Título'))
    interessado = models.CharField(
        max_length=1000, blank=True, verbose_name=_('Interessado'))
    autor = models.ForeignKey(Autor, blank=True, null=True,
                              on_delete=models.PROTECT)

    dias_prazo = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Dias Prazo'))
    data_fim_prazo = models.DateField(
        blank=True, null=True, verbose_name=_('Data Fim Prazo'))

    data_vencimento = models.DateField(
        blank=True, null=True, verbose_name=_('Data de Vencimento'))

    tramitacao = models.BooleanField(
        verbose_name=_('Em Tramitação?'),
        choices=YES_NO_CHOICES,
        default=False)
    assunto = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Assunto'))
    numero_externo = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Número Externo'))
    observacao = models.TextField(
        blank=True, verbose_name=_('Resumo'))
    texto_integral = PortalFileField(
        blank=True,
        null=True,
        storage=OverwriteStorage(),
        upload_to=texto_upload_path,
        verbose_name=_('Texto Integral'),
        max_length=512)

    anexados = models.ManyToManyField(
        'self',
        blank=True,
        through='Anexado',
        symmetrical=False,
        related_name='anexo_de',
        through_fields=(
            'documento_principal',
            'documento_anexado'
        )
    )

    workspace = models.ForeignKey(
        AreaTrabalho,
        verbose_name=_('Área de Trabalho'),
        related_name='documentoadministrativo_set',
        blank=True, null=True, on_delete=PROTECT)

    data_ultima_atualizacao = models.DateTimeField(
        blank=True, null=True,
        auto_now=True,
        verbose_name=_('Data'))

    _certidao = GenericRelation(
        CertidaoPublicacao, related_query_name='documentoadministrativo_cert')

    class Meta:
        verbose_name = _('Documento Administrativo')
        verbose_name_plural = _('Documentos Administrativos')

    @property
    def certidao(self):
        return self._certidao.all().first()

    @property
    def __descr__(self):
        return self.assunto

    def __str__(self):
        if self.epigrafe:
            return '%s' % self.epigrafe

        return _('%(sigla)s - %(tipo)s nº %(numero)s/%(ano)s %(interessado)s') % {
            'sigla': self.tipo.sigla,
            'tipo': self.tipo,
            'numero': self.numero,
            'ano': self.ano,
            'interessado': ('(%s)' % self.interessado) if self.interessado else ''
        }

    def delete(self, using=None, keep_parents=False):
        texto_integral = self.texto_integral

        result = models.Model.delete(
            self, using=using, keep_parents=keep_parents)

        if texto_integral:
            texto_integral.delete(save=False)

        return result

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and self.texto_integral:
            texto_integral = self.texto_integral
            self.texto_integral = None
            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)
            self.texto_integral = texto_integral

        return models.Model.save(self, force_insert=force_insert,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)


@reversion.register()
class DocumentoAcessorioAdministrativo(models.Model):
    documento = models.ForeignKey(DocumentoAdministrativo,
                                  on_delete=models.PROTECT)
    tipo = models.ForeignKey(
        TipoDocumentoAdministrativo,
        on_delete=models.PROTECT,
        verbose_name=_('Tipo'))
    nome = models.CharField(max_length=30, verbose_name=_('Nome'))
    arquivo = PortalFileField(
        blank=True,
        null=True,
        upload_to=texto_upload_path,
        storage=OverwriteStorage(),
        verbose_name=_('Arquivo'),
        max_length=512)
    data = models.DateField(blank=True, null=True, verbose_name=_('Data'))
    autor = models.CharField(
        max_length=50, blank=True, verbose_name=_('Autor'))
    assunto = models.TextField(
        blank=True, verbose_name=_('Assunto'))
    indexacao = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Documento Acessório')
        verbose_name_plural = _('Documentos Acessórios')

    def __str__(self):
        return self.nome

    def delete(self, using=None, keep_parents=False):
        if self.arquivo:
            self.arquivo.delete()

        return models.Model.delete(
            self, using=using, keep_parents=keep_parents)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and self.arquivo:
            arquivo = self.arquivo
            self.arquivo = None
            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)
            self.arquivo = arquivo

        return models.Model.save(self, force_insert=force_insert,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)


@reversion.register()
class StatusTramitacaoAdministrativo(models.Model):
    INDICADOR_CHOICES = Choices(
        ('F', 'fim', _('Fim')),
        ('R', 'retorno', _('Retorno')),
    )

    workspace = models.ForeignKey(
        AreaTrabalho,
        verbose_name=_('Área de Trabalho'),
        related_name='statustramitacaoadministrativo_set',
        blank=True, null=True, on_delete=PROTECT)

    sigla = models.CharField(max_length=10, verbose_name=_('Sigla'))
    descricao = models.CharField(max_length=60, verbose_name=_('Descrição'))
    # TODO make specific migration considering both ind_fim_tramitacao,
    # ind_retorno_tramitacao
    indicador = models.CharField(
        max_length=1, verbose_name=_('Indicador da Tramitação'),
        choices=INDICADOR_CHOICES)

    class Meta:
        verbose_name = _('Status de Tramitação de Documentos Administrativos')
        verbose_name_plural = _(
            'Status de Tramitação de Documentos Administrativos')

    def __str__(self):
        return self.descricao


@reversion.register()
class TramitacaoAdministrativo(models.Model):
    status = models.ForeignKey(
        StatusTramitacaoAdministrativo,
        on_delete=models.PROTECT,
        verbose_name=_('Status'))
    documento = models.ForeignKey(DocumentoAdministrativo,
                                  on_delete=models.PROTECT)
    timestamp = models.DateTimeField(default=timezone.now)
    data_tramitacao = models.DateField(
        verbose_name=_('Data Tramitação'))
    unidade_tramitacao_local = models.ForeignKey(
        UnidadeTramitacao,
        related_name='adm_tramitacoes_origem',
        on_delete=models.PROTECT,
        verbose_name=_('Unidade Local'))
    data_encaminhamento = models.DateField(
        blank=True, null=True, verbose_name=_('Data Encaminhamento'))
    unidade_tramitacao_destino = models.ForeignKey(
        UnidadeTramitacao,
        related_name='adm_tramitacoes_destino',
        on_delete=models.PROTECT,
        verbose_name=_('Unidade Destino'))
    urgente = models.BooleanField(verbose_name=_('Urgente ?'),
                                  choices=YES_NO_CHOICES,
                                  default=False)
    texto = models.TextField(verbose_name=_('Texto da Ação'))
    data_fim_prazo = models.DateField(
        blank=True, null=True, verbose_name=_('Data Fim do Prazo'))
    user = models.ForeignKey(get_settings_auth_user_model(),
                             verbose_name=_('Usuário'),
                             on_delete=models.PROTECT,
                             null=True,
                             blank=True)
    ip = models.CharField(verbose_name=_('IP'),
                          max_length=30,
                          blank=True,
                          default='')

    class Meta:
        verbose_name = _('Tramitação de Documento Administrativo')
        verbose_name_plural = _('Tramitações de Documento Administrativo')
        ordering = ('-data_tramitacao', '-id')

    def __str__(self):
        return _('%(documento)s - %(status)s') % {
            'documento': self.documento, 'status': self.status
        }


@reversion.register()
class Anexado(models.Model):
    documento_principal = models.ForeignKey(
        DocumentoAdministrativo, related_name='documento_principal_set',
        on_delete=models.CASCADE,
        verbose_name=_('Documento Principal')
    )
    documento_anexado = models.ForeignKey(
        DocumentoAdministrativo, related_name='documento_anexado_set',
        on_delete=models.CASCADE,
        verbose_name=_('Documento Anexado')
    )
    data_anexacao = models.DateField(verbose_name=_('Data Anexação'))
    data_desanexacao = models.DateField(
        blank=True, null=True, verbose_name=_('Data Desanexação')
    )

    class Meta:
        verbose_name = _('Anexado')
        verbose_name_plural = _('Anexados')
        ordering = ('-data_anexacao',
                    '-documento_anexado___certidao__created')

    def __str__(self):
        return _('Anexado: %(documento_anexado_tipo)s %(documento_anexado_numero)s'
                 '/%(documento_anexado_ano)s\n') % {
                     'documento_anexado_tipo': self.documento_anexado.tipo,
                     'documento_anexado_numero': self.documento_anexado.numero,
                     'documento_anexado_ano': self.documento_anexado.ano
        }


@reversion.register()
class AcompanhamentoDocumento(models.Model):
    usuario = models.CharField(max_length=50)
    documento = models.ForeignKey(
        DocumentoAdministrativo, on_delete=models.CASCADE)
    email = models.EmailField(
        max_length=100, verbose_name=_('E-mail'))
    data_cadastro = models.DateField(auto_now_add=True)
    hash = models.CharField(max_length=8)
    confirmado = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Acompanhamento de Documento')
        verbose_name_plural = _('Acompanhamentos de Documento')

    def __str__(self):
        if self.data_cadastro is None:
            return _('%(documento)s - %(email)s') % {
                'documento': self.documento,
                'email': self.email
            }
        else:
            return _('%(documento)s - %(email)s - Registrado em: %(data)s') % {
                'documento': self.documento,
                'email': self.email,
                'data': str(self.data_cadastro.strftime('%d/%m/%Y'))
            }

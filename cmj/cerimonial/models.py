from django.db import models
from django.db.models.deletion import SET_NULL, PROTECT, CASCADE
from django.utils.translation import ugettext_lazy as _
from sapl.parlamentares.models import Parlamentar

from cmj.core.models import CmjModelMixin
from cmj.utils import YES_NO_CHOICES, NONE_YES_NO_CHOICES


class DescricaoAbstractModel(models.Model):
    descricao = models.CharField(
        default='', max_length=254, verbose_name=_('Nome / Discrição'))

    class Meta:
        abstract = True

    def __str__(self):
        return self.descricao


class StatusVisita(DescricaoAbstractModel):

    class Meta:
        verbose_name = _('Status da Visita')
        verbose_name_plural = _('Status das Visitas')


class TipoTelefone(DescricaoAbstractModel):

    class Meta:
        verbose_name = _('Tipo de Telefone')
        verbose_name_plural = _('Tipos de Telefone')


class TipoEndereco(DescricaoAbstractModel):

    class Meta:
        verbose_name = _('Tipo de Endereço')
        verbose_name_plural = _('Tipos de Endereço')


class TipoEmail(DescricaoAbstractModel):

    class Meta:
        verbose_name = _('Tipo de Email')
        verbose_name_plural = _('Tipos de Email')


class Parentesco(DescricaoAbstractModel):

    class Meta:
        verbose_name = _('Parentesco')
        verbose_name_plural = _('Parentescos')


class EstadoCivil(DescricaoAbstractModel):

    class Meta:
        verbose_name = _('Estado Civil')
        verbose_name_plural = _('Estados Civis')


class TipoAutoridade(DescricaoAbstractModel):

    class Meta:
        verbose_name = _('Tipo de Autoridade')
        verbose_name_plural = _('Tipos de Autoridade')


class TipoLocalTrabalho(DescricaoAbstractModel):

    class Meta:
        verbose_name = _('Tipo do Local de Trabalho')
        verbose_name_plural = _('Tipos de Local de Trabalho')


class NivelInstrucao(DescricaoAbstractModel):

    class Meta:
        verbose_name = _('Nível Instrução')
        verbose_name_plural = _('Níveis Instrução')


class OperadoraTelefonia(DescricaoAbstractModel):

    class Meta:
        verbose_name = _('Operadora de Telefonia')
        verbose_name_plural = _('Operadoras de Telefonia')
        permissions = (
            ("list_operadoratelefonia",
             _('Pode visualizar lista das operadoras de telefonia.')),
            ("detail_operadoratelefonia",
             _('Pode visualizar detalhes das operadoras de telefonia.')),
        )


class Pessoa(CmjModelMixin):
    FEMININO = 'F'
    MASCULINO = 'M'
    SEXO_CHOICE = ((FEMININO, _('Feminino')),
                   (MASCULINO, _('Masculino')))

    nome = models.CharField(max_length=100, verbose_name=_('Nome'))

    data_nascimento = models.DateField(
        blank=True, null=True, verbose_name=_('Data de Nascimento'))

    sexo = models.CharField(
        max_length=1, blank=True, verbose_name=_('Sexo'), choices=SEXO_CHOICE)

    tem_filhos = models.NullBooleanField(
        choices=NONE_YES_NO_CHOICES,
        default=None, verbose_name=_('Tem Filhos?'))

    quantos_filhos = models.PositiveSmallIntegerField(
        default=0,  blank=True, verbose_name=_('Quantos Filhos?'))

    estado_civil = models.ForeignKey(
        EstadoCivil,
        related_name='pessoas_set',
        blank=True, null=True, on_delete=SET_NULL,
        verbose_name=_('Estado Civil'))

    nivel_instrucao = models.ForeignKey(
        NivelInstrucao,
        related_name='pessoas_set',
        blank=True, null=True, on_delete=SET_NULL,
        verbose_name=_('Nivel de Instrução'))

    naturalidade = models.CharField(
        max_length=50, blank=True, verbose_name=_('Naturalidade'))

    nome_pai = models.CharField(
        max_length=100, blank=True, verbose_name=_('Nome do Pai'))
    nome_mae = models.CharField(
        max_length=100, blank=True, verbose_name=_('Nome da Mãe'))

    numero_sus = models.CharField(
        max_length=100, blank=True, verbose_name=_('Número do SUS'))
    cpf = models.CharField(max_length=15, blank=True, verbose_name=_('CPF'))
    titulo_eleitor = models.CharField(
        max_length=15,
        blank=True,
        verbose_name=_('Título de Eleitor'))
    rg = models.CharField(max_length=30, blank=True, verbose_name=_('RG'))
    rg_orgao_expedidor = models.CharField(
        max_length=20, blank=True, verbose_name=_('Órgão Expedidor'))
    rg_data_expedicao = models.DateField(
        blank=True, null=True, verbose_name=_('Data de Expedição'))

    ativo = models.BooleanField(choices=YES_NO_CHOICES,
                                default=True, verbose_name=_('Ativo?'))

    parlamentar = models.ForeignKey(
        Parlamentar,
        verbose_name='Parlamentar Associado',
        related_name='pessoas_set',
        blank=True, null=True, on_delete=CASCADE)

    class Meta:
        verbose_name = _('Pessoa')
        verbose_name_plural = _('Pessoas')
        ordering = ['nome']
        permissions = (
            ("list_pessoa",
             _('Pode visualizar lista de Pessas.')),
            ("detail_pessoa",
             _('Pode visualizar detalhes do Cadastro de Pessoas.')),
        )

    def __str__(self):
        return self.nome


class Telefone(models.Model):

    pessoa = models.ForeignKey(
        Pessoa, on_delete=CASCADE, verbose_name=_('Pessoa'))
    operadora = models.ForeignKey(
        OperadoraTelefonia, on_delete=SET_NULL,
        related_name='telefones_set',
        blank=True, null=True,
        verbose_name=_('Operadora de Telefonia'))
    tipo = models.ForeignKey(
        TipoTelefone, on_delete=PROTECT, verbose_name='Tipo')
    ddd = models.CharField(max_length=3, verbose_name='DDD')
    numero = models.CharField(max_length=20, verbose_name='Número')

    proprio = models.BooleanField(choices=YES_NO_CHOICES,
                                  default=True, verbose_name=_('Próprio?'))

    de_quem_e = models.CharField(
        max_length=40, verbose_name='De quem é?', blank=True,
        help_text=_('Se não é próprio, de quem é?'))

    @property
    def numero_nome_pessoa(self):
        return str(self)

    class Meta:
        verbose_name = _('Telefone')
        verbose_name_plural = _('Telefones')
        permissions = (
            ("list_telefone",
             _('Pode visualizar lista de Telefones.')),
            ("detail_telefone",
             _('Pode visualizar detalhes do Cadastro de Telefones.')),
        )

    def __str__(self):
        return '(%s) %s - (%s)' % (self.ddd, self.numero, self.pessoa.nome)


class Email(models.Model):

    pessoa = models.ForeignKey(
        Pessoa, on_delete=CASCADE, verbose_name=_('Pessoa'))
    tipo = models.ForeignKey(
        TipoEmail,
        blank=True, null=True,
        on_delete=PROTECT, verbose_name='Tipo')
    email = models.EmailField(verbose_name='Email')

    preferencial = models.BooleanField(
        choices=YES_NO_CHOICES,
        default=True, verbose_name=_('Preferêncial?'))

    class Meta:
        verbose_name = _('Email')
        verbose_name_plural = _("Email's")
        permissions = (
            ("list_email",
             _('Pode visualizar lista de Emails.')),
            ("detail_email",
             _('Pode visualizar detalhes do Cadastro de Emails.')),
        )

    def __str__(self):
        return self.email

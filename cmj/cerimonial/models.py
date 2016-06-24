from django.db import models
from django.db.models.deletion import SET_NULL, PROTECT, CASCADE
from django.utils.translation import ugettext_lazy as _, string_concat
from sapl.parlamentares.models import Parlamentar, Municipio
from sapl.utils import UF

from cmj.core.models import CmjModelMixin, Trecho, Distrito, RegiaoMunicipal
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


class PronomeTratamento(DescricaoAbstractModel):

    nome = models.CharField(
        default='', max_length=254, verbose_name=_('Nome'))

    abreviatura = models.CharField(
        default='', max_length=254, verbose_name=_('Abreviatura'))

    class Meta:
        verbose_name = _('Pronome de Tratamento')
        verbose_name_plural = _('Pronomes de tratamento')

    def __str__(self):
        return self.nome

PronomeTratamento._meta.get_field('descricao').verbose_name = _('Descrição')
PronomeTratamento._meta.get_field('descricao').blank = True
PronomeTratamento._meta.get_field('descricao').default = ''


class TipoAutoridade(DescricaoAbstractModel):

    pronome_tratamento = models.ForeignKey(
        PronomeTratamento,
        verbose_name=_('Pronome de Tratamento'),
        related_name='tipo_autoridade_set',
        blank=True, null=True, on_delete=SET_NULL)

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


class Contato(CmjModelMixin):
    FEMININO = 'F'
    MASCULINO = 'M'
    SEXO_CHOICE = ((FEMININO, _('Feminino')),
                   (MASCULINO, _('Masculino')))

    nome = models.CharField(max_length=100, verbose_name=_('Nome'))

    nome_social = models.CharField(
        blank=True, default='', max_length=100, verbose_name=_('Nome Social'))

    apelido = models.CharField(
        blank=True, default='', max_length=100, verbose_name=_('Apelido'))

    data_nascimento = models.DateField(
        blank=True, null=True, verbose_name=_('Data de Nascimento'))

    sexo = models.CharField(
        max_length=1, blank=True,
        verbose_name=_('Sexo Biológico'), choices=SEXO_CHOICE)

    identidade_genero = models.CharField(
        blank=True, default='',
        max_length=100, verbose_name=_('Como se reconhece?'))

    tem_filhos = models.NullBooleanField(
        choices=NONE_YES_NO_CHOICES,
        default=None, verbose_name=_('Tem Filhos?'))

    quantos_filhos = models.PositiveSmallIntegerField(
        default=0,  blank=True, verbose_name=_('Quantos Filhos?'))

    estado_civil = models.ForeignKey(
        EstadoCivil,
        related_name='contatos_set',
        blank=True, null=True, on_delete=SET_NULL,
        verbose_name=_('Estado Civil'))

    nivel_instrucao = models.ForeignKey(
        NivelInstrucao,
        related_name='contatos_set',
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
        verbose_name=_('Parlamentar Associado'),
        related_name='contatos_set',
        blank=True, null=True, on_delete=CASCADE)

    profissao = models.CharField(
        max_length=254, blank=True, verbose_name=_('Profissão'))

    forma_tratamento = models.ForeignKey(
        PronomeTratamento,
        verbose_name=_('Forma de Tratamento'),
        related_name='contatos_set',
        blank=True, null=True, on_delete=SET_NULL)

    class Meta:
        verbose_name = _('Contato')
        verbose_name_plural = _('Contatos')
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Telefone(CmjModelMixin):

    contato = models.ForeignKey(
        Contato, on_delete=CASCADE, verbose_name=_('Contato'))
    operadora = models.ForeignKey(
        OperadoraTelefonia, on_delete=SET_NULL,
        related_name='telefones_set',
        blank=True, null=True,
        verbose_name=OperadoraTelefonia._meta.verbose_name)
    tipo = models.ForeignKey(
        TipoTelefone, on_delete=PROTECT, verbose_name='Tipo')
    ddd = models.CharField(max_length=3, verbose_name='DDD')
    numero = models.CharField(max_length=20, verbose_name='Número')

    proprio = models.BooleanField(choices=YES_NO_CHOICES,
                                  default=True, verbose_name=_('Próprio?'))

    de_quem_e = models.CharField(
        max_length=40, verbose_name='De quem é?', blank=True,
        help_text=_('Se não é próprio, de quem é?'))

    preferencial = models.BooleanField(
        choices=YES_NO_CHOICES,
        default=True, verbose_name=_('Preferêncial?'))

    @property
    def numero_nome_contato(self):
        return str(self)

    class Meta:
        verbose_name = _('Telefone')
        verbose_name_plural = _('Telefones')

    def __str__(self):
        return '(%s) %s - (%s)' % (self.ddd, self.numero, self.contato.nome)


class Email(CmjModelMixin):

    contato = models.ForeignKey(
        Contato, on_delete=CASCADE, verbose_name=_('Contato'))
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

    def __str__(self):
        return self.email


class Dependente(CmjModelMixin):
    FEMININO = 'F'
    MASCULINO = 'M'
    SEXO_CHOICE = ((FEMININO, _('Feminino')),
                   (MASCULINO, _('Masculino')))

    parentesco = models.ForeignKey(Parentesco, verbose_name=_('Parentesco'))
    contato = models.ForeignKey(Contato,
                                verbose_name=('Contato'),
                                related_name='dependentes_set',
                                on_delete=CASCADE)
    nome = models.CharField(max_length=100, verbose_name=_('Nome'))

    nome_social = models.CharField(
        blank=True, default='', max_length=100, verbose_name=_('Nome Social'))

    apelido = models.CharField(
        blank=True, default='', max_length=100, verbose_name=_('Apelido'))
    sexo = models.CharField(
        blank=True, max_length=1, verbose_name=_('Sexo'), choices=SEXO_CHOICE)
    data_nascimento = models.DateField(
        blank=True, null=True, verbose_name=_('Data Nascimento'))

    identidade_genero = models.CharField(
        blank=True, default='',
        max_length=100, verbose_name=_('Como você se reconhece?'))

    nivel_instrucao = models.ForeignKey(
        NivelInstrucao,
        related_name='dependentes_set',
        blank=True, null=True, on_delete=SET_NULL,
        verbose_name=_('Nivel de Instrução'))

    parentesco = models.ForeignKey(
        Parentesco,
        related_name='dependentes_set',
        blank=True, null=True, on_delete=SET_NULL,
        verbose_name=_('Parentesco'))

    class Meta:
        verbose_name = _('Dependente')
        verbose_name_plural = _('Dependentes')

    def __str__(self):
        return self.nome


class LocalTrabalho(CmjModelMixin):
    contato = models.ForeignKey(Contato,
                                verbose_name=('Contato'),
                                related_name='locais_trabalho_set',
                                on_delete=CASCADE)
    nome = models.CharField(
        max_length=254, verbose_name=_('Nome / Razão Social'))

    nome_social = models.CharField(
        blank=True, default='', max_length=254,
        verbose_name=_('Nome Fantasia'))

    tipo = models.ForeignKey(
        TipoLocalTrabalho,
        related_name='locais_trabalho_set',
        blank=True, null=True, on_delete=SET_NULL,
        verbose_name=_('Tipo do Local de Trabalho'))

    trecho = models.ForeignKey(
        Trecho,
        verbose_name=_('Trecho'),
        related_name='locais_trabalho_set',
        blank=True, null=True, on_delete=SET_NULL)

    uf = models.CharField(max_length=2, blank=True, choices=UF,
                          verbose_name=_('Estado'))

    municipio = models.ForeignKey(
        Municipio,
        verbose_name=Municipio._meta.verbose_name,
        related_name='locais_trabalho_set',
        blank=True, null=True, on_delete=SET_NULL)

    cep = models.CharField(max_length=9, blank=True, default='',
                           verbose_name=_('CEP'))

    endereco = models.CharField(
        max_length=254, blank=True, default='',
        verbose_name=_('Endereço'),
        help_text=_('O campo endereço também é um campo de busca, nele '
                    'você pode digitar qualquer informação, inclusive '
                    'digitar o cep para localizar o endereço, e vice-versa!'))

    numero = models.CharField(max_length=50, blank=True, default='',
                              verbose_name=_('Número'))

    bairro = models.CharField(max_length=254, blank=True, default='',
                              verbose_name=_('Bairro'))
    distrito = models.ForeignKey(
        Distrito,
        verbose_name=Distrito._meta.verbose_name,
        related_name='locais_trabalho_set',
        blank=True, null=True, on_delete=SET_NULL)
    regiao_municipal = models.ForeignKey(
        RegiaoMunicipal,
        verbose_name=RegiaoMunicipal._meta.verbose_name,
        related_name='locais_trabalho_set',
        blank=True, null=True, on_delete=SET_NULL)

    complemento = models.CharField(max_length=30, blank=True, default='',
                                   verbose_name=_('Complemento'))

    forma_tratamento = models.ForeignKey(
        PronomeTratamento,
        verbose_name=_('Forma de Tratamento neste Local'),
        related_name='locais_trabalho_set',
        blank=True, null=True, on_delete=SET_NULL)

    data_inicio = models.DateField(
        blank=True, null=True, verbose_name=_('Data de Início'))

    data_fim = models.DateField(
        blank=True, null=True, verbose_name=_('Data de Fim'))

    class Meta:
        verbose_name = _('Local de Trabalho')
        verbose_name_plural = _('Locais de Trabalho')

    def __str__(self):
        return self.nome


class Endereco(CmjModelMixin):
    contato = models.ForeignKey(Contato,
                                verbose_name=('Contato'),
                                related_name='enderecos_set',
                                on_delete=CASCADE)

    tipo = models.ForeignKey(
        TipoEndereco,
        related_name='enderecos_set',
        blank=True, null=True, on_delete=SET_NULL,
        verbose_name=_('Tipo do Endereço'))

    trecho = models.ForeignKey(
        Trecho,
        verbose_name=_('Trecho'),
        related_name='enderecos_set',
        blank=True, null=True, on_delete=SET_NULL)

    uf = models.CharField(max_length=2, blank=True, choices=UF,
                          verbose_name=_('Estado'))

    municipio = models.ForeignKey(
        Municipio,
        verbose_name=_('Município'),
        related_name='enderecos_set',
        blank=True, null=True, on_delete=SET_NULL)

    cep = models.CharField(max_length=9, blank=True, default='',
                           verbose_name=_('CEP'))

    endereco = models.CharField(
        max_length=254, blank=True, default='',
        verbose_name=_('Endereço'),
        help_text=_('O campo endereço também é um campo de busca, nele '
                    'você pode digitar qualquer informação, inclusive '
                    'digitar o cep para localizar o endereço, e vice-versa!'))

    numero = models.CharField(max_length=50, blank=True, default='',
                              verbose_name=_('Número'))

    bairro = models.CharField(max_length=254, blank=True, default='',
                              verbose_name=_('Bairro'))
    distrito = models.ForeignKey(
        Distrito,
        verbose_name=Distrito._meta.verbose_name,
        related_name='enderecos_set',
        blank=True, null=True, on_delete=SET_NULL)
    regiao_municipal = models.ForeignKey(
        RegiaoMunicipal,
        verbose_name=RegiaoMunicipal._meta.verbose_name,
        related_name='enderecos_set',
        blank=True, null=True, on_delete=SET_NULL)

    complemento = models.CharField(max_length=30, blank=True, default='',
                                   verbose_name=_('Complemento'))

    class Meta:
        verbose_name = _('Endereço')
        verbose_name_plural = _('Endereços')

    def __str__(self):
        numero = (' - ' + self.numero) if self.numero else ''
        return self.endereco + numero

app_models = list(Contato._meta.app_config.get_models())
for m in app_models:
    permissions = (
        ("list_" + m._meta.model_name,
         string_concat(
             _('Visualizaçao da lista de'), ' ', m._meta.verbose_name_plural)),
        ("detail_" + m._meta.model_name,
         string_concat(
             _('Visualização dos detalhes de'), ' ',
             m._meta.verbose_name_plural)),
    )
    m._meta.permissions = tuple(list(permissions) + list(m._meta.permissions))

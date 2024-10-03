
from django.db.models.fields.json import JSONField
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from image_cropping.fields import ImageCropField, ImageRatioField
from model_utils import Choices

from sapl.base.models import Autor
from sapl.decorators import vigencia_atual
from sapl.utils import (LISTA_DE_UFS, YES_NO_CHOICES, SaplGenericRelation,
                        get_settings_auth_user_model,
                        intervalos_tem_intersecao,
                        restringe_tipos_de_arquivo_img, texto_upload_path)


class Legislatura(models.Model):
    numero = models.PositiveIntegerField(verbose_name=_('Número'))
    data_inicio = models.DateField(verbose_name=_('Data Início'))
    data_fim = models.DateField(verbose_name=_('Data Fim'))
    data_eleicao = models.DateField(verbose_name=_('Data Eleição'))

    class Meta:
        ordering = ['-data_inicio']
        verbose_name = _('Legislatura')
        verbose_name_plural = _('Legislaturas')

    def atual(self):
        current_year = timezone.now().year
        if not self.data_fim:
            self.data_fim = timezone.now().date()
        return self.data_inicio.year <= current_year <= self.data_fim.year

    @classmethod
    def cache_legislatura_atual(cls):
        value = cache.get('sapl_legislatura_atual')
        if not value is None:
            return value

        current_year = timezone.now().year
        value = list(Legislatura.objects.filter(
            data_inicio__year__lte=current_year,
            data_fim__year__gte=current_year
        ).values()[:1])

        value = [] if not value else value[0]

        cache.set('sapl_legislatura_atual', value, 86400)

        return value

    @vigencia_atual
    def __str__(self):
        if not self.data_fim:
            self.data_fim = timezone.now().date()
        return _('%(numero)sª (%(start)s - %(end)s)') % {
            'numero': self.numero,
            'start': self.data_inicio.year,
            'end': self.data_fim.year}


class SessaoLegislativa(models.Model):
    TIPO_SESSAO_CHOICES = Choices(
        ('O', 'ordinaria', _('Ordinária')),
        ('E', 'extraordinaria', _('Extraordinária')),
    )

    legislatura = models.ForeignKey(
        Legislatura,
        on_delete=models.PROTECT,
        verbose_name=Legislatura._meta.verbose_name)
    numero = models.PositiveIntegerField(verbose_name=_('Número'))
    tipo = models.CharField(
        max_length=1, verbose_name=_('Tipo'), choices=TIPO_SESSAO_CHOICES)
    data_inicio = models.DateField(verbose_name=_('Data Início'))
    data_fim = models.DateField(verbose_name=_('Data Fim'))
    data_inicio_intervalo = models.DateField(
        blank=True, null=True, verbose_name=_('Início Intervalo'))
    data_fim_intervalo = models.DateField(
        blank=True, null=True, verbose_name=_('Fim Intervalo'))

    class Meta:
        verbose_name = _('Sessão Legislativa')
        verbose_name_plural = _('Sessões Legislativas')
        ordering = ['-data_inicio', '-data_fim']

    @vigencia_atual
    def __str__(self):
        return _('%(numero)sº (%(inicio)s - %(fim)s)') % {
            'numero': self.numero,
            'inicio': self.data_inicio.year,
            'fim': self.data_fim.year}


class Coligacao(models.Model):
    legislatura = models.ForeignKey(Legislatura,
                                    on_delete=models.PROTECT,
                                    verbose_name=_('Legislatura'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))
    numero_votos = models.PositiveIntegerField(
        blank=True, null=True,
        verbose_name=_('Nº Votos Recebidos (Coligação)'))

    class Meta:
        verbose_name = _('Coligação')
        verbose_name_plural = _('Coligações')
        ordering = ['id']

    def __str__(self):
        return self.nome


def get_logo_media_path(instance, subpath, filename):
    return './sapl/partidos/%s/%s/%s' % (instance, subpath, filename)


def logo_upload_path(instance, filename):
    return get_logo_media_path(instance, 'logo', filename)


class Partido(models.Model):

    FIELDFILE_NAME = ('logo_partido', )

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    sigla = models.CharField(
        max_length=100,
        verbose_name=_('Sigla')
    )
    nome = models.CharField(
        max_length=100,
        verbose_name=_('Nome')
    )
    data_criacao = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Data Criação')
    )
    data_extincao = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Data Extinção')
    )
    logo_partido = models.ImageField(
        blank=True,
        null=True,
        upload_to=logo_upload_path,
        verbose_name=_('Logo Partido'),
        validators=[restringe_tipos_de_arquivo_img]
    )
    observacao = models.TextField(
        blank=True,
        verbose_name=_('Observação')
    )

    class Meta:
        verbose_name = _('Partido')
        verbose_name_plural = _('Partidos')
        ordering = ['sigla', 'nome']

    def __str__(self):
        return _('%(sigla)s - %(nome)s') % {
            'sigla': self.sigla, 'nome': self.nome
        }


class HistoricoPartido(models.Model):

    FIELDFILE_NAME = ('logo_partido', )

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    sigla = models.CharField(
        max_length=9,
        verbose_name=_('Sigla')
    )
    nome = models.CharField(
        max_length=50,
        verbose_name=_('Nome')
    )
    inicio_historico = models.DateField(
        verbose_name=_('Data Alteração')
    )

    fim_historico = models.DateField(
        verbose_name=_('Data Alteração')
    )

    logo_partido = models.ImageField(
        blank=True,
        null=True,
        upload_to=logo_upload_path,
        verbose_name=_('Logo Partido'),
        validators=[restringe_tipos_de_arquivo_img]
    )

    partido = models.ForeignKey(Partido, on_delete=models.PROTECT)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return _('%(sigla)s - %(nome)s') % {
            'sigla': self.sigla, 'nome': self.nome
        }


class ComposicaoColigacao(models.Model):
    # TODO M2M
    partido = models.ForeignKey(Partido,
                                on_delete=models.CASCADE,
                                verbose_name=_('Partidos da Coligação'))
    coligacao = models.ForeignKey(Coligacao, on_delete=models.PROTECT)

    class Meta:
        verbose_name = (_('Composição Coligação'))
        verbose_name_plural = (_('Composição Coligações'))
        ordering = ['id']

    def __str__(self):
        return _('%(partido)s - %(coligacao)s') % {
            'partido': self.partido, 'coligacao': self.coligacao
        }


class NivelInstrucao(models.Model):
    descricao = models.CharField(
        max_length=50, verbose_name=_('Nível de Instrução'))

    class Meta:
        ordering = ['descricao']
        verbose_name = _('Nível Instrução')
        verbose_name_plural = _('Níveis Instrução')

    def __str__(self):
        return self.descricao


class SituacaoMilitar(models.Model):
    descricao = models.CharField(
        max_length=50, verbose_name=_('Situação Militar'))

    class Meta:
        verbose_name = _('Tipo Situação Militar')
        verbose_name_plural = _('Tipos Situações Militares')
        ordering = ['descricao']

    def __str__(self):
        return self.descricao


def foto_upload_path(instance, filename):
    return texto_upload_path(instance, filename, subpath='')


def capa_upload_path(instance, filename):
    return texto_upload_path(instance, filename, subpath='capa', pk_first=True)


def true_false_none(x):
    if x == 'True':
        return True
    elif x == 'False':
        return False
    else:
        return None


class ParlamentarManager(models.Manager):

    use_for_related_fields = True

    def isonly_sexo_feminino(self):
        qs = self.get_queryset()
        sexos = qs.values_list('sexo', flat=True).order_by('sexo').distinct()
        return len(sexos) == 1 and sexos[0] == 'F'


class Parlamentar(models.Model):

    objects = ParlamentarManager()

    FIELDFILE_NAME = ('capa', 'fotografia', )

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    FEMININO = 'F'
    MASCULINO = 'M'
    SEXO_CHOICE = ((FEMININO, _('Feminino')),
                   (MASCULINO, _('Masculino')))

    nivel_instrucao = models.ForeignKey(
        NivelInstrucao,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_('Nível Instrução'))
    situacao_militar = models.ForeignKey(
        SituacaoMilitar,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_('Situação Militar'))
    nome_completo = models.CharField(
        max_length=50, verbose_name=_('Nome Completo'))
    nome_parlamentar = models.CharField(
        max_length=50,
        verbose_name=_('Nome Parlamentar'))
    sexo = models.CharField(
        max_length=1, verbose_name=_('Sexo'), choices=SEXO_CHOICE)
    data_nascimento = models.DateField(
        blank=True, null=True, verbose_name=_('Data Nascimento'))
    cpf = models.CharField(
        max_length=14, blank=True, verbose_name=_('C.P.F'))
    rg = models.CharField(
        max_length=15, blank=True, verbose_name=_('R.G.'))
    titulo_eleitor = models.CharField(
        max_length=15,
        blank=True,
        verbose_name=_('Título de Eleitor'))
    numero_gab_parlamentar = models.CharField(
        max_length=10, blank=True, verbose_name=_('Nº Gabinete'))
    telefone = models.CharField(
        max_length=50, blank=True, verbose_name=_('Telefone'))
    fax = models.CharField(
        max_length=50, blank=True, verbose_name=_('Fax'))
    endereco_residencia = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Endereço Residencial'))
    municipio_residencia = models.CharField(
        max_length=50, blank=True, verbose_name=_('Município'))
    uf_residencia = models.CharField(
        max_length=2, blank=True, choices=LISTA_DE_UFS, verbose_name=_('UF'))
    cep_residencia = models.CharField(
        max_length=9, blank=True, verbose_name=_('CEP'))
    telefone_residencia = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Telefone Residencial'))
    fax_residencia = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Fax Residencial'))
    endereco_web = models.URLField(
        max_length=100, blank=True, verbose_name=_('HomePage'))
    profissao = models.CharField(
        max_length=50, blank=True, verbose_name=_('Profissão'))
    email = models.EmailField(
        max_length=100,
        blank=True,
        verbose_name=_('E-mail'))
    locais_atuacao = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Locais de Atuação'))
    ativo = models.BooleanField(
        db_index=True,
        default=False,
        choices=YES_NO_CHOICES,
        verbose_name=_('Ativo na Casa?'))
    biografia = models.TextField(
        blank=True, verbose_name=_('Biografia'))
    fotografia = ImageCropField(
        verbose_name=_('Fotografia'), upload_to=foto_upload_path, null=True, blank=True)  # validators=[restringe_tipos_de_arquivo_img],
    fotografia_cropping = ImageRatioField(
        'fotografia', '128x128', verbose_name=_('Avatar'), size_warning=True,
        help_text=_('A configuração do Avatar '
                    'é possível após a atualização da fotografia.'))

    capa = ImageCropField(
        verbose_name=_('Imagem de Capa'), upload_to=capa_upload_path, null=True, blank=True)  # validators=[restringe_tipos_de_arquivo_img]

    capa_cropping = ImageRatioField(
        'capa', '280x105', verbose_name=_('Capa'), size_warning=True,
        help_text=_('A configuração da capa '
                    'é possível após a atualização.'))

    # campo conceitual de reversão genérica para o model Autor que dá a
    # o meio possível de localização de tipos de autores.
    autor = SaplGenericRelation(
        Autor,
        related_query_name='parlamentar_set',
        fields_search=(
            # na primeira posição dever ser campo simples sem __
            ('nome_completo', '__icontains'),
            ('nome_parlamentar', '__icontains'),
            ('filiacao__partido__sigla', '__icontains'),
        ))

    class Meta:
        verbose_name = _('Parlamentar')
        verbose_name_plural = _('Parlamentares')
        ordering = ['nome_parlamentar']

    def __str__(self):
        return self.nome_parlamentar

    @property
    def filiacao_atual(self):
        ultima_filiacao = self.filiacao_set.order_by('-data').first()
        if ultima_filiacao and not ultima_filiacao.data_desfiliacao:
            return ultima_filiacao.partido.sigla
        else:
            return _('Sem Partido')

    @property
    def avatar_html(self):
        return '<img class="avatar-parlamentar" src='\
            + self.fotografia.url + '>'if self.fotografia else ''

    def delete(self, using=None, keep_parents=False):

        r = models.Model.delete(
            self, using=using, keep_parents=keep_parents)

        if self.fotografia:
            self.fotografia.delete()

        if self.capa:
            self.capa.delete()

        return r

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk:
            fotografia = None
            capa = None
            if self.fotografia:
                fotografia = self.fotografia
                self.fotografia = None

            if self.capa:
                capa = self.capa
                self.capa = None

            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)

            self.fotografia = fotografia
            self.capa = capa

        return models.Model.save(self, force_insert=force_insert,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)


class TipoDependente(models.Model):
    descricao = models.CharField(max_length=150, verbose_name=_('Descrição'))

    class Meta:
        verbose_name = _('Tipo de Dependente')
        verbose_name_plural = _('Tipos de Dependente')
        ordering = ['descricao']

    def __str__(self):
        return self.descricao


class Dependente(models.Model):
    FEMININO = 'F'
    MASCULINO = 'M'
    SEXO_CHOICE = ((FEMININO, _('Feminino')),
                   (MASCULINO, _('Masculino')))

    tipo = models.ForeignKey(TipoDependente, on_delete=models.PROTECT,
                             verbose_name=_('Tipo'))
    parlamentar = models.ForeignKey(Parlamentar, on_delete=models.CASCADE)
    nome = models.CharField(max_length=150, verbose_name=_('Nome'))
    sexo = models.CharField(
        max_length=1, verbose_name=_('Sexo'), choices=SEXO_CHOICE)
    data_nascimento = models.DateField(
        blank=True, null=True, verbose_name=_('Data Nascimento'))
    cpf = models.CharField(
        max_length=14, blank=True, verbose_name=_('CPF'))
    rg = models.CharField(
        max_length=15, blank=True, verbose_name=_('RG'))
    titulo_eleitor = models.CharField(
        max_length=15,
        blank=True,
        verbose_name=_('Nº Título Eleitor'))

    class Meta:
        verbose_name = _('Dependente')
        verbose_name_plural = _('Dependentes')
        ordering = ['id']

    def __str__(self):
        return self.nome


class Filiacao(models.Model):
    data = models.DateField(verbose_name=_('Data Filiação'))
    parlamentar = models.ForeignKey(Parlamentar, on_delete=models.CASCADE)
    partido = models.ForeignKey(Partido,
                                on_delete=models.PROTECT,
                                verbose_name=_('Partido'),
                                related_name='filiacao_set')
    data_desfiliacao = models.DateField(
        blank=True, null=True, verbose_name=_('Data Desfiliação'))

    class Meta:
        verbose_name = _('Filiação')
        verbose_name_plural = _('Filiações')
        # A ordenação descrescente por data é importante para listagem de
        # parlamentares e tela de Filiações do Parlamentar
        ordering = ('parlamentar', '-data', '-data_desfiliacao')

    def nome_partido_ano(self, ano):
        historico = HistoricoPartido.objects.filter(partido=self.partido)
        for h in historico:
            if h.inicio_historico.year <= ano <= h.fim_historico.year:
                return h
        return self.partido

    def __str__(self):
        return _('%(parlamentar)s - %(partido)s') % {
            'parlamentar': self.parlamentar, 'partido': self.partido
        }


class TipoAfastamento(models.Model):
    descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))
    indicador = models.CharField(
        max_length=1, verbose_name=_('Indicador'), default='F',
        choices=[('A', _('Afastamento')),
                 ('F', _('Fim de Mandato')), ])
    dispositivo = models.CharField(
        max_length=50, blank=True, verbose_name=_('Dispositivo'))

    class Meta:
        verbose_name = _('Tipo de Afastamento')
        verbose_name_plural = _('Tipos de Afastamento')
        ordering = ['descricao']

    def __str__(self):
        return self.descricao


class Mandato(models.Model):
    parlamentar = models.ForeignKey(
        Parlamentar,
        on_delete=models.CASCADE,
    )
    tipo_afastamento = models.ForeignKey(TipoAfastamento,
                                         blank=True,
                                         null=True,
                                         on_delete=models.PROTECT,
                                         verbose_name=_('Tipo de Afastamento'))

    legislatura = models.ForeignKey(Legislatura, on_delete=models.PROTECT,
                                    verbose_name=_('Legislatura'))
    coligacao = models.ForeignKey(
        Coligacao, blank=True, null=True,
        on_delete=models.PROTECT, verbose_name=_('Coligação'))
    # TODO what is this field??????
    tipo_causa_fim_mandato = models.PositiveIntegerField(blank=True, null=True)
    data_inicio_mandato = models.DateField(verbose_name=_('Início do Mandato'),
                                           blank=False,
                                           null=True)
    data_fim_mandato = models.DateField(verbose_name=_('Fim do Mandato'),
                                        blank=True,
                                        null=True)
    votos_recebidos = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Votos Recebidos (Mandato)'))
    data_expedicao_diploma = models.DateField(blank=True,
                                              null=True,
                                              verbose_name=_('Expedição do Diploma'))
    titular = models.BooleanField(
        db_index=True,
        default=True,
        choices=YES_NO_CHOICES,
        verbose_name=_('Parlamentar Titular'))

    observacao = models.TextField(
        blank=True, verbose_name=_('Observação'))

    class Meta:
        verbose_name = _('Mandato')
        verbose_name_plural = _('Mandatos')
        ordering = ['id']

    def __str__(self):
        return _('%(parlamentar)s %(legislatura)s') % {
            'parlamentar': self.parlamentar, 'legislatura': self.legislatura
        }

    def get_partidos(self):
        filicacoes = Filiacao.objects.filter(
            parlamentar=self.parlamentar).order_by('data')
        return [f.partido.sigla
                for f in filicacoes
                if intervalos_tem_intersecao(
                    self.legislatura.data_inicio,
                    self.legislatura.data_fim,
                    f.data,
                    f.data_desfiliacao or timezone.datetime.max.date())]


class CargoMesa(models.Model):
    # TODO M2M ????
    descricao = models.CharField(
        max_length=50, verbose_name=_('Cargo na Mesa'))
    unico = models.BooleanField(
        choices=YES_NO_CHOICES, verbose_name=_('Cargo Único'), default=True)

    class Meta:
        verbose_name = _('Cargo na Mesa')
        verbose_name_plural = _('Cargos na Mesa')
        ordering = ['id']

    def __str__(self):
        return self.descricao


class ComposicaoMesa(models.Model):
    # TODO M2M ???? Ternary?????
    parlamentar = models.ForeignKey(Parlamentar, on_delete=models.PROTECT)
    sessao_legislativa = models.ForeignKey(SessaoLegislativa,
                                           on_delete=models.PROTECT)
    cargo = models.ForeignKey(CargoMesa, on_delete=models.PROTECT)

    class Meta:
        verbose_name = _('Ocupação de cargo na Mesa')
        verbose_name_plural = _('Ocupações de cargo na Mesa')
        ordering = ['id']

    def __str__(self):
        return _('%(parlamentar)s - %(cargo)s') % {
            'parlamentar': self.parlamentar, 'cargo': self.cargo
        }


class Frente(models.Model):
    '''
        * Uma frente agrupa vários parlamentares
        * Cada parlamentar pode fazer parte de uma ou mais frentes
        * Uma frente pode existir por mais de uma legislatura?
    '''
    nome = models.CharField(
        max_length=80,
        verbose_name=_('Nome da Frente'))
    parlamentares = models.ManyToManyField(Parlamentar,
                                           blank=True,
                                           verbose_name=_('Parlamentares'))
    data_criacao = models.DateField(verbose_name=_('Data Criação'))
    data_extincao = models.DateField(
        blank=True, null=True, verbose_name=_('Data Dissolução'))
    descricao = models.TextField(blank=True, verbose_name=_('Descrição'))

    # campo conceitual de reversão genérica para o model Autor que dá a
    # o meio possível de localização de tipos de autores.
    autor = SaplGenericRelation(
        Autor,
        related_query_name='frente_set',
        fields_search=(
            ('nome', '__icontains'),
            ('descricao', '__icontains'),
            ('parlamentares__filiacao__partido__sigla', '__icontains'),
            ('parlamentares__filiacao__partido__nome', '__icontains'),
        ))

    class Meta:
        verbose_name = _('Frente Parlamentar')
        verbose_name_plural = _('Frentes Parlamentares')
        ordering = ['id']

    def get_parlamentares(self):
        return Parlamentar.objects.filter(ativo=True)

    def __str__(self):
        return self.nome


class Votante(models.Model):
    parlamentar = models.ForeignKey(
        Parlamentar, verbose_name=_('Parlamentar'),
        on_delete=models.PROTECT, related_name='parlamentar')
    user = models.ForeignKey(
        get_settings_auth_user_model(), on_delete=models.PROTECT,
        verbose_name=_('User'), related_name='user')
    data = models.DateTimeField(
        verbose_name=_('Data'), auto_now_add=True,
        max_length=30, null=True, blank=True)

    class Meta:
        verbose_name = _('Usuário Votante')
        verbose_name_plural = _('Usuários Votantes')
        permissions = (
            ('can_vote', _('Can Vote')),
        )
        ordering = ['id']

    def __str__(self):
        return self.user.username


class Bloco(models.Model):
    '''
        * blocos podem existir por mais de uma legislatura
    '''
    nome = models.CharField(
        max_length=80, verbose_name=_('Nome do Bloco'))
    partidos = models.ManyToManyField(
        Partido, blank=True, verbose_name=_('Partidos'))
    data_criacao = models.DateField(
        blank=False, null=True, verbose_name=_('Data Criação'))
    data_extincao = models.DateField(
        blank=True, null=True, verbose_name=_('Data Dissolução'))
    descricao = models.TextField(blank=True, verbose_name=_('Descrição'))

    # campo conceitual de reversão genérica para o model Autor que dá a
    # o meio possível de localização de tipos de autores.
    autor = SaplGenericRelation(Autor,
                                related_query_name='bloco_set',
                                fields_search=(
                                    ('nome', '__icontains'),
                                    ('descricao', '__icontains'),
                                    ('partidos__sigla', '__icontains'),
                                    ('partidos__nome', '__icontains'),
                                ))

    class Meta:
        verbose_name = _('Bloco Parlamentar')
        verbose_name_plural = _('Blocos Parlamentares')
        ordering = ['id']

    def __str__(self):
        return self.nome


class Bancada(models.Model):
    legislatura = models.ForeignKey(Legislatura,
                                    on_delete=models.PROTECT,
                                    verbose_name=_('Legislatura'))
    nome = models.CharField(
        max_length=80,
        verbose_name=_('Nome da Bancada'))
    partido = models.ForeignKey(Partido,
                                blank=True,
                                null=True,
                                on_delete=models.PROTECT,
                                verbose_name=_('Partido'))
    data_criacao = models.DateField(blank=False, null=True,
                                    verbose_name=_('Data Criação'))
    data_extincao = models.DateField(blank=True, null=True,
                                     verbose_name=_('Data Extinção'))
    descricao = models.TextField(blank=True, verbose_name=_('Descrição'))

    # campo conceitual de reversão genérica para o model Autor que dá a
    # o meio possível de localização de tipos de autores.
    autor = SaplGenericRelation(Autor, related_query_name='bancada_set',
                                fields_search=(
                                    ('nome', '__icontains'),
                                    ('descricao', '__icontains'),
                                    ('partido__sigla', '__icontains'),
                                    ('partido__nome', '__icontains'),
                                ))

    class Meta:
        db_table = 'parlamentares_bancada'
        verbose_name = _('Bancada Partidária')
        verbose_name_plural = _('Bancadas Partidárias')
        ordering = ('-legislatura__numero', '-data_extincao',
                    'data_criacao', 'partido__nome')

    def __str__(self):
        return self.nome


class CargoBloco(models.Model):
    class Meta:
        verbose_name = _('Cargo de Bloco')
        verbose_name_plural = _('Cargos de Bloco')
        ordering = ['nome']

    nome = models.CharField(
        max_length=80, verbose_name=_('Nome do Cargo'))
    unico = models.BooleanField(
        choices=YES_NO_CHOICES, verbose_name=_('Cargo Único'), default=True)
    descricao = models.TextField(blank=True, verbose_name=_('Descrição'))

    def __str__(self):
        return self.nome


class CargoBancada(models.Model):
    nome_cargo = models.CharField(max_length=80,
                                  verbose_name=_('Cargo de Bancada'))

    cargo_unico = models.BooleanField(default=False,
                                      choices=YES_NO_CHOICES,
                                      verbose_name=_('Cargo Único ?'))

    class Meta:
        verbose_name = _('Cargo de Bancada')
        verbose_name_plural = _('Cargos de Bancada')
        ordering = ['id']

    def __str__(self):
        return self.nome_cargo


class CargoBlocoPartido(models.Model):
    class Meta:
        verbose_name = _('Vinculo bloco parlamentar')
        verbose_name_plural = _('Vinculos bloco parlamentar')
        ordering = ['data_inicio']

    bloco = models.ForeignKey(
        Bloco,
        on_delete=models.PROTECT,
        related_name='cargoblocopartido_set')

    cargo = models.ForeignKey(
        CargoBloco,
        on_delete=models.PROTECT)

    parlamentar = models.ForeignKey(
        Parlamentar,
        on_delete=models.PROTECT)

    data_inicio = models.DateField(verbose_name=_('Data Início'))
    data_fim = models.DateField(
        blank=True, null=True, verbose_name=_('Data Fim'))

    def __str__(self):
        return '{} - {}'.format(self.parlamentar, self.cargo)


class AfastamentoParlamentar(models.Model):
    parlamentar = models.ForeignKey(Parlamentar, on_delete=models.CASCADE)
    mandato = models.ForeignKey(Mandato, on_delete=models.CASCADE,
                                verbose_name=_('Mandato'))
    tipo_afastamento = models.ForeignKey(TipoAfastamento,
                                         on_delete=models.PROTECT,
                                         verbose_name=_('Tipo de Afastamento'),
                                         blank=True,
                                         null=True)
    data_inicio = models.DateField(verbose_name=_('Início do Afastamento'),
                                   blank=False,
                                   null=True)
    data_fim = models.DateField(verbose_name=_('Fim do Afastamento'),
                                blank=True,
                                null=True)
    observacao = models.TextField(verbose_name=_('Observação'),
                                  blank=True)

    class Meta:
        verbose_name = _('Afastamento')
        verbose_name_plural = _('Afastamentos')
        ordering = ['id']

    def __str__(self):
        return _('%(parlamentar)s %(legislatura)s') % {
            'parlamentar': self.parlamentar, 'legislatura': self.mandato.legislatura
        }

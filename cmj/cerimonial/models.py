from django.db import models


"""
class Pessoa(CmjModelMixin):
    cpf = models.CharField(max_length=15, blank=True)
    nome = models.CharField(max_length=10000, blank=True)

    logradouro = models.CharField(max_length=10000, blank=True)
    complemento = models.CharField(max_length=30, blank=True)
    cep = models.CharField(max_length=9, blank=True)
    bairro = models.CharField(max_length=10000, blank=True)
    cidade = models.CharField(max_length=30, blank=True)
    estado = models.CharField(max_length=2, blank=True)
    # Field name made lowercase.
    telefonefixo = models.CharField(
        db_column='telefoneFixo', max_length=10000, blank=True)
    # Field name made lowercase.
    telefonecelular = models.CharField(
        db_column='telefoneCelular', max_length=20, blank=True)
    email = models.CharField(max_length=50, blank=True)
    rg = models.CharField(max_length=30, blank=True)
    orgaorg = models.CharField(max_length=20, blank=True)
    nomepai = models.CharField(max_length=50, blank=True)
    nomemae = models.CharField(max_length=50, blank=True)
    naturalidade = models.CharField(max_length=50, blank=True)
    # Field name made lowercase.
    alteradopor = models.ForeignKey(
        'Usuario', models.DO_NOTHING,
        db_column='alteradoPor',
        blank=True,
        related_name="pessoas_set")
    # Field name made lowercase.
    alteradoem = models.DateTimeField(
        db_column='alteradoEm', blank=True)
    dataexprg = models.DateTimeField(blank=True)
    datanascimento = models.DateTimeField(blank=True)
    excluido = models.NullBooleanField()
    ativo = models.NullBooleanField()
    foto = models.BinaryField(blank=True)
    # Field name made lowercase.
    estadocivil = models.CharField(
        db_column='estadoCivil', max_length=1, blank=True)
    parentesco = models.IntegerField(blank=True)
    sexo = models.CharField(max_length=1, blank=True)
    numsus = models.CharField(max_length=10000, blank=True)
    visitado = models.ForeignKey(
        'Usuario', models.DO_NOTHING, db_column='visitado', blank=True,
        related_name="sisitados_set")
    empresa = models.CharField(max_length=50, blank=True)
    # Field name made lowercase.
    telefonecomercial = models.CharField(
        db_column='telefoneComercial', max_length=20, blank=True)
    cargo = models.CharField(max_length=10000, blank=True)
    # Field name made lowercase.
    enderecocomercial = models.CharField(
        db_column='enderecoComercial', max_length=10000, blank=True)
    # Field name made lowercase.
    bairrocomercial = models.CharField(
        db_column='bairroComercial', max_length=10000, blank=True)
    # Field name made lowercase.
    cidadecomercial = models.CharField(
        db_column='cidadeComercial', max_length=50, blank=True)
    # Field name made lowercase.
    estadocomercial = models.CharField(
        db_column='estadoComercial', max_length=2, blank=True)
    # Field name made lowercase.
    cepcomercial = models.CharField(
        db_column='cepComercial', max_length=9, blank=True)
    # Field name made lowercase.
    complementocomercial = models.CharField(
        db_column='complementoComercial', max_length=15, blank=True)
    pronome_tratamento = models.CharField(
        max_length=10000, blank=True)
    tipo_autoridade = models.CharField(max_length=10000, blank=True)
    tratamento_prefixo = models.CharField(
        max_length=10000, blank=True)

    class Meta:


class Telefone(models.Model):
    TELEFONE_TIPO_CHOICES = (
        (u'residencial', u'Residencial'),
        (u'celular', u'Celular'),
        (u'comercial', u'Comercial'),
    )
    contato = models.ForeignKey(Pessoa, verbose_name=_('Pessoa'))
    tipo = models.CharField(
        max_length=15, choices=TELEFONE_TIPO_CHOICES, verbose_name='Tipo')
    numero = models.CharField(max_length=135, verbose_name='Número')

    class Meta:
        verbose_name = _('Telefone')
        verbose_name_plural = _('Telefones')

    def __str__(self):
        return self.numero"""
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or
# field names.
from __future__ import unicode_literals

from django.db import models


class Abastecimento(models.Model):
    # Field name made lowercase.
    iddeslocamento = models.ForeignKey(
        'Deslocamento', models.DO_NOTHING, db_column='idDeslocamento', blank=True, null=True)
    data = models.DateTimeField(blank=True, null=True)
    nf = models.CharField(max_length=10000, blank=True, null=True)
    posto = models.CharField(max_length=10000, blank=True, null=True)
    cidade = models.CharField(max_length=10000, blank=True, null=True)
    litro = models.DecimalField(
        max_digits=10, decimal_places=3, blank=True, null=True)
    valor = models.DecimalField(
        max_digits=10, decimal_places=3, blank=True, null=True)
    # Field name made lowercase.
    alteradopor = models.ForeignKey(
        'Usuario', models.DO_NOTHING, db_column='alteradoPor', blank=True, null=True)
    # Field name made lowercase.
    alteradoem = models.DateTimeField(
        db_column='alteradoEm', blank=True, null=True)
    excluido = models.NullBooleanField()
    km = models.DecimalField(
        max_digits=10, decimal_places=3, blank=True, null=True)
    cb = models.CharField(max_length=10000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Abastecimento'


class Ajuda(models.Model):
    # Field name made lowercase.
    idservico = models.ForeignKey(
        'Servico', models.DO_NOTHING, db_column='idServico', blank=True, null=True)
    # Field name made lowercase.
    descrprincipal = models.CharField(
        db_column='descrPrincipal', max_length=10000, blank=True, null=True)
    # Field name made lowercase.
    descralternativa = models.CharField(
        db_column='descrAlternativa', max_length=10000, blank=True, null=True)
    # Field name made lowercase.
    alteradoem = models.DateTimeField(
        db_column='alteradoEm', blank=True, null=True)
    # Field name made lowercase.
    alteradopor = models.DateTimeField(
        db_column='alteradoPor', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Ajuda'


class Anexo(models.Model):
    id = models.IntegerField(primary_key=True)
    descr = models.CharField(max_length=10000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Anexo'


class Automovel(models.Model):
    nome = models.CharField(max_length=10000, blank=True, null=True)
    placa = models.CharField(unique=True, max_length=8, blank=True, null=True)
    marca = models.CharField(max_length=10000, blank=True, null=True)
    cor = models.CharField(max_length=10000, blank=True, null=True)
    ano = models.CharField(max_length=10000, blank=True, null=True)
    # Field name made lowercase.
    alteradopor = models.ForeignKey(
        'Usuario', models.DO_NOTHING, db_column='alteradoPor', blank=True, null=True)
    # Field name made lowercase.
    alteradoem = models.DateTimeField(
        db_column='alteradoEm', blank=True, null=True)
    ativo = models.NullBooleanField()
    excluido = models.NullBooleanField()
    observacoes = models.CharField(max_length=10000, blank=True, null=True)
    combustivel = models.CharField(max_length=10000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Automovel'


class Curriculo(models.Model):
    cpf = models.BigIntegerField(unique=True)
    # Field name made lowercase.
    datanascimento = models.DateField(
        db_column='dataNascimento', blank=True, null=True)
    fone = models.CharField(max_length=10000)
    nome = models.CharField(max_length=10000, blank=True, null=True)
    sexo = models.CharField(max_length=1)
    estado = models.CharField(max_length=2)
    cidade = models.CharField(max_length=10000)
    # Field name made lowercase.
    pretencaosalarial = models.DecimalField(
        db_column='pretencaoSalarial', max_digits=10, decimal_places=2)
    file = models.BinaryField(blank=True, null=True)
    # Field name made lowercase.
    alteradoem = models.DateTimeField(
        db_column='alteradoEm', blank=True, null=True)
    excluido = models.NullBooleanField()
    namefile = models.CharField(max_length=10000, blank=True, null=True)
    senha = models.CharField(max_length=10000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Curriculo'


class Departamento(models.Model):
    nome = models.CharField(max_length=10000, blank=True, null=True)
    ativo = models.NullBooleanField()
    excluido = models.NullBooleanField()
    # Field name made lowercase.
    alteradoem = models.DateTimeField(
        db_column='alteradoEm', blank=True, null=True)
    # Field name made lowercase.
    alteradopor = models.ForeignKey(
        'Usuario', models.DO_NOTHING, db_column='alteradoPor', blank=True, null=True)
    sigla = models.CharField(
        unique=True, max_length=10000, blank=True, null=True)
    observacoes = models.CharField(max_length=10000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Departamento'


class Deslocamento(models.Model):
    # Field name made lowercase.
    idautomovel = models.ForeignKey(
        Automovel, models.DO_NOTHING, db_column='idAutomovel', blank=True, null=True)
    # Field name made lowercase.
    datasaida = models.DateTimeField(
        db_column='dataSaida', blank=True, null=True)
    # Field name made lowercase.
    datachegada = models.DateTimeField(
        db_column='dataChegada', blank=True, null=True)
    # Field name made lowercase.
    kmsaida = models.DecimalField(
        db_column='kmSaida', max_digits=10, decimal_places=3, blank=True, null=True)
    # Field name made lowercase.
    kmchegada = models.DecimalField(
        db_column='kmChegada', max_digits=10, decimal_places=3, blank=True, null=True)
    # Field name made lowercase.
    autorizadopor = models.CharField(
        db_column='autorizadoPor', max_length=10000, blank=True, null=True)
    # Field name made lowercase.
    solicitadopor = models.CharField(
        db_column='solicitadoPor', max_length=10000, blank=True, null=True)
    # Field name made lowercase.
    idmotorista = models.ForeignKey(
        'Motorista', models.DO_NOTHING, db_column='idMotorista', blank=True, null=True)
    observacoes = models.CharField(max_length=10000, blank=True, null=True)
    # Field name made lowercase.
    emtransito = models.NullBooleanField(db_column='emTransito')
    excluido = models.NullBooleanField()
    # Field name made lowercase.
    alteradopor = models.ForeignKey(
        'Usuario', models.DO_NOTHING, db_column='alteradoPor', blank=True, null=True)
    # Field name made lowercase.
    alteradoem = models.DateTimeField(
        db_column='alteradoEm', blank=True, null=True)
    encerrado = models.NullBooleanField()
    servicos = models.CharField(max_length=10000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Deslocamento'


class Dptosala(models.Model):
    # Field name made lowercase.
    idsala = models.ForeignKey(
        'Sala', models.DO_NOTHING, db_column='idSala', blank=True, null=True)
    # Field name made lowercase.
    iddepartamento = models.ForeignKey(
        Departamento, models.DO_NOTHING, db_column='idDepartamento', blank=True, null=True)
    observacoes = models.CharField(max_length=10000, blank=True, null=True)
    ativo = models.NullBooleanField()
    excluido = models.NullBooleanField()
    # Field name made lowercase.
    alteradoem = models.DateTimeField(
        db_column='alteradoEm', blank=True, null=True)
    # Field name made lowercase.
    alteradopor = models.ForeignKey(
        'Usuario', models.DO_NOTHING, db_column='alteradoPor', blank=True, null=True)
    # Field name made lowercase.
    dataini = models.DateTimeField(db_column='dataIni', blank=True, null=True)
    # Field name made lowercase.
    datafim = models.DateTimeField(db_column='dataFim', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'DptoSala'


class Dptosalafunc(models.Model):
    # Field name made lowercase.
    iddptosala = models.ForeignKey(
        Dptosala, models.DO_NOTHING, db_column='idDptoSala', blank=True, null=True)
    # Field name made lowercase.
    idfuncionario = models.ForeignKey(
        'Funcionario', models.DO_NOTHING, db_column='idFuncionario', blank=True, null=True)
    responsavel = models.NullBooleanField()
    excluido = models.NullBooleanField()
    # Field name made lowercase.
    alteradoem = models.DateTimeField(
        db_column='alteradoEm', blank=True, null=True)
    # Field name made lowercase.
    alteradopor = models.ForeignKey(
        'Usuario', models.DO_NOTHING, db_column='alteradoPor', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'DptoSalaFunc'


class Empresas(models.Model):
    cnpj = models.CharField(max_length=10000, blank=True, null=True)
    senha = models.CharField(max_length=10000, blank=True, null=True)
    fone = models.CharField(max_length=10000, blank=True, null=True)
    rs = models.CharField(max_length=10000, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    cidade = models.CharField(max_length=10000, blank=True, null=True)
    nomefantasia = models.CharField(max_length=10000, blank=True, null=True)
    # Field name made lowercase.
    alteradoem = models.DateTimeField(
        db_column='alteradoEm', blank=True, null=True)
    email = models.CharField(max_length=10000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Empresas'


class Etiqueta(models.Model):
    label = models.CharField(max_length=10000, blank=True, null=True)
    # Field name made lowercase.
    largurafolha = models.DecimalField(
        db_column='larguraFolha', max_digits=5, decimal_places=2, blank=True, null=True)
    # Field name made lowercase.
    alturafolha = models.DecimalField(
        db_column='alturaFolha', max_digits=5, decimal_places=2, blank=True, null=True)
    # Field name made lowercase.
    margemesquerdafolha = models.DecimalField(
        db_column='margemEsquerdaFolha', max_digits=5, decimal_places=2, blank=True, null=True)
    # Field name made lowercase.
    margemsuperiorfolha = models.DecimalField(
        db_column='margemSuperiorFolha', max_digits=5, decimal_places=2, blank=True, null=True)
    # Field name made lowercase.
    colunasfolha = models.DecimalField(
        db_column='colunasFolha', max_digits=5, decimal_places=2, blank=True, null=True)
    # Field name made lowercase.
    linhasfolha = models.DecimalField(
        db_column='linhasFolha', max_digits=5, decimal_places=2, blank=True, null=True)
    # Field name made lowercase.
    larguraetiqueta = models.DecimalField(
        db_column='larguraEtiqueta', max_digits=5, decimal_places=2, blank=True, null=True)
    # Field name made lowercase.
    alturaetiqueta = models.DecimalField(
        db_column='alturaEtiqueta', max_digits=5, decimal_places=2, blank=True, null=True)
    # Field name made lowercase.
    distentrecolunas = models.DecimalField(
        db_column='distEntreColunas', max_digits=5, decimal_places=2, blank=True, null=True)
    # Field name made lowercase.
    distentrelinhas = models.DecimalField(
        db_column='distEntreLinhas', max_digits=5, decimal_places=2, blank=True, null=True)
    # Field name made lowercase.
    fontesizebase = models.DecimalField(
        db_column='fonteSizeBase', max_digits=5, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Etiqueta'


class Fornecedor(models.Model):
    cnpj = models.CharField(unique=True, max_length=14)
    # Field name made lowercase.
    razaosocial = models.CharField(
        db_column='razaoSocial', max_length=80, blank=True, null=True)
    # Field name made lowercase.
    nomefantasia = models.CharField(
        db_column='nomeFantasia', max_length=50, blank=True, null=True)
    # Field name made lowercase.
    respempresa = models.CharField(
        db_column='respEmpresa', max_length=50, blank=True, null=True)
    # Field name made lowercase.
    inscrestadual = models.CharField(
        db_column='inscrEstadual', max_length=20, blank=True, null=True)
    # Field name made lowercase.
    fornserv = models.NullBooleanField(db_column='fornServ')
    # Field name made lowercase.
    forncons = models.NullBooleanField(db_column='fornCons')
    # Field name made lowercase.
    fornperm = models.NullBooleanField(db_column='fornPerm')
    endereco = models.CharField(max_length=80, blank=True, null=True)
    bairro = models.CharField(max_length=80, blank=True, null=True)
    cep1 = models.CharField(max_length=5, blank=True, null=True)
    cep2 = models.CharField(max_length=3, blank=True, null=True)
    cidade = models.CharField(max_length=80, blank=True, null=True)
    email = models.CharField(max_length=80, blank=True, null=True)
    # Field name made lowercase.
    datacadastro = models.DateTimeField(
        db_column='dataCadastro', blank=True, null=True)
    fone1 = models.CharField(max_length=12, blank=True, null=True)
    # Field name made lowercase.
    contatofone1 = models.CharField(
        db_column='contatoFone1', max_length=20, blank=True, null=True)
    fone2 = models.CharField(max_length=12, blank=True, null=True)
    # Field name made lowercase.
    contatofone2 = models.CharField(
        db_column='contatoFone2', max_length=20, blank=True, null=True)
    cel1 = models.CharField(max_length=12, blank=True, null=True)
    # Field name made lowercase.
    contatocel1 = models.CharField(
        db_column='contatoCel1', max_length=20, blank=True, null=True)
    # Field name made lowercase.
    contatocel2 = models.CharField(
        db_column='contatoCel2', max_length=20, blank=True, null=True)
    cel2 = models.CharField(max_length=12, blank=True, null=True)
    fax = models.CharField(max_length=12, blank=True, null=True)
    # Field name made lowercase.
    contatofax = models.CharField(
        db_column='contatoFax', max_length=20, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    ativo = models.NullBooleanField()
    excluido = models.NullBooleanField()
    # Field name made lowercase.
    alteradoem = models.DateTimeField(
        db_column='alteradoEm', blank=True, null=True)
    # Field name made lowercase.
    alteradopor = models.ForeignKey(
        'Usuario', models.DO_NOTHING, db_column='alteradoPor', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Fornecedor'


class Funcaocurriculo(models.Model):
    # Field name made lowercase.
    idcurriculo = models.ForeignKey(
        Curriculo, models.DO_NOTHING, db_column='idCurriculo')
    # Field name made lowercase.
    idocupacao = models.ForeignKey(
        'Ocupacao', models.DO_NOTHING, db_column='idOcupacao')
    exper = models.IntegerField(blank=True, null=True)
    listou = models.IntegerField(blank=True, null=True)
    baixou = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'FuncaoCurriculo'


class Funcionario(models.Model):
    cpf = models.CharField(max_length=15, blank=True, null=True)
    nome = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=50, blank=True, null=True)
    complemento = models.CharField(max_length=15, blank=True, null=True)
    cep = models.CharField(max_length=9, blank=True, null=True)
    bairro = models.CharField(max_length=30, blank=True, null=True)
    cidade = models.CharField(max_length=30, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    # Field name made lowercase.
    telefonefixo = models.CharField(
        db_column='telefoneFixo', max_length=20, blank=True, null=True)
    # Field name made lowercase.
    telefonecelular = models.CharField(
        db_column='telefoneCelular', max_length=20, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    rg = models.CharField(max_length=20, blank=True, null=True)
    orgaorg = models.CharField(max_length=15, blank=True, null=True)
    nomepai = models.CharField(max_length=50, blank=True, null=True)
    nomemae = models.CharField(max_length=50, blank=True, null=True)
    # Field name made lowercase.
    alteradopor = models.ForeignKey(
        'Usuario', models.DO_NOTHING, db_column='alteradoPor', blank=True, null=True)
    # Field name made lowercase.
    alteradoem = models.DateTimeField(
        db_column='alteradoEm', blank=True, null=True)
    dataexprg = models.DateTimeField(blank=True, null=True)
    datanascimento = models.DateTimeField(blank=True, null=True)
    excluido = models.NullBooleanField()
    ativo = models.NullBooleanField()
    foto = models.BinaryField(blank=True, null=True)
    matricula = models.CharField(max_length=10000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Funcionario'


class Log(models.Model):
    # Field name made lowercase.
    idusuario = models.ForeignKey(
        'Usuario', models.DO_NOTHING, db_column='idUsuario', blank=True, null=True)
    # Field name made lowercase.
    idservico = models.ForeignKey(
        'Servico', models.DO_NOTHING, db_column='idServico', blank=True, null=True)
    data = models.DateTimeField(blank=True, null=True)
    descricao = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Log'


class Motorista(models.Model):
    nome = models.CharField(max_length=10000, blank=True, null=True)
    ativo = models.NullBooleanField()
    excluido = models.NullBooleanField()
    # Field name made lowercase.
    alteradoem = models.DateTimeField(
        db_column='alteradoEm', blank=True, null=True)
    # Field name made lowercase.
    alteradopor = models.ForeignKey(
        'Usuario', models.DO_NOTHING, db_column='alteradoPor', blank=True, null=True)
    observacoes = models.CharField(max_length=10000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Motorista'


class Ocupacao(models.Model):
    nome = models.CharField(max_length=10000, blank=True, null=True)
    # Field name made lowercase.
    idfamilia = models.IntegerField(
        db_column='idFamilia', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Ocupacao'


class Permissoes(models.Model):
    # Field name made lowercase.
    idservico = models.ForeignKey(
        'Servico', models.DO_NOTHING, db_column='idServico', blank=True, null=True)
    # Field name made lowercase.
    idusuario = models.ForeignKey(
        'Usuario', models.DO_NOTHING, db_column='idUsuario', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Permissoes'


class Pessoa(models.Model):
    # ok
    cpf = models.CharField(max_length=15, blank=True, null=True)
    # ok
    nome = models.CharField(max_length=10000, blank=True, null=True)
    # ok
    logradouro = models.CharField(max_length=10000, blank=True, null=True)
    # ok
    complemento = models.CharField(max_length=30, blank=True, null=True)
    # ok
    cep = models.CharField(max_length=9, blank=True, null=True)
    # ok
    bairro = models.CharField(max_length=10000, blank=True, null=True)
    # ok
    cidade = models.CharField(max_length=30, blank=True, null=True)
    # ok
    estado = models.CharField(max_length=2, blank=True, null=True)

    # Field name made lowercase.
    # ok
    telefonefixo = models.CharField(
        db_column='telefoneFixo', max_length=10000, blank=True, null=True)
    # Field name made lowercase.
    # ok
    telefonecelular = models.CharField(
        db_column='telefoneCelular', max_length=20, blank=True, null=True)

    # ok
    email = models.CharField(max_length=50, blank=True, null=True)

    # ok
    rg = models.CharField(max_length=30, blank=True, null=True)
    # ok
    orgaorg = models.CharField(max_length=20, blank=True, null=True)
    # ok
    nomepai = models.CharField(max_length=50, blank=True, null=True)
    # ok
    nomemae = models.CharField(max_length=50, blank=True, null=True)
    # ok
    naturalidade = models.CharField(max_length=50, blank=True, null=True)

    # Field name made lowercase.
    # ok
    alteradopor = models.ForeignKey(
        'Usuario', models.DO_NOTHING,
        db_column='alteradoPor',
        blank=True, null=True,
        related_name="pessoas_set")
    # Field name made lowercase.
    # ok
    alteradoem = models.DateTimeField(
        db_column='alteradoEm', blank=True, null=True)

    # ok
    dataexprg = models.DateTimeField(blank=True, null=True)
    # ok
    datanascimento = models.DateTimeField(blank=True, null=True)

    # ok
    excluido = models.NullBooleanField()
    # ok
    ativo = models.NullBooleanField()
    # ok
    foto = models.BinaryField(blank=True, null=True)
    # Field name made lowercase.
    # ok
    estadocivil = models.CharField(
        db_column='estadoCivil', max_length=1, blank=True, null=True)

    # ok
    parentesco = models.IntegerField(blank=True, null=True)

    # ok
    sexo = models.CharField(max_length=1, blank=True, null=True)
    # ok
    numsus = models.CharField(max_length=10000, blank=True, null=True)

    # ok
    visitado = models.ForeignKey(
        'Usuario', models.DO_NOTHING, db_column='visitado', blank=True, null=True,
        related_name="sisitados_set")

    empresa = models.CharField(max_length=50, blank=True, null=True)
    # Field name made lowercase.
    telefonecomercial = models.CharField(
        db_column='telefoneComercial', max_length=20, blank=True, null=True)
    cargo = models.CharField(max_length=10000, blank=True, null=True)
    # Field name made lowercase.
    enderecocomercial = models.CharField(
        db_column='enderecoComercial', max_length=10000, blank=True, null=True)
    # Field name made lowercase.
    bairrocomercial = models.CharField(
        db_column='bairroComercial', max_length=10000, blank=True, null=True)
    # Field name made lowercase.
    cidadecomercial = models.CharField(
        db_column='cidadeComercial', max_length=50, blank=True, null=True)
    # Field name made lowercase.
    estadocomercial = models.CharField(
        db_column='estadoComercial', max_length=2, blank=True, null=True)
    # Field name made lowercase.
    cepcomercial = models.CharField(
        db_column='cepComercial', max_length=9, blank=True, null=True)
    # Field name made lowercase.
    complementocomercial = models.CharField(
        db_column='complementoComercial', max_length=15, blank=True, null=True)
    pronome_tratamento = models.CharField(
        max_length=10000, blank=True, null=True)
    tipo_autoridade = models.CharField(max_length=10000, blank=True, null=True)
    tratamento_prefixo = models.CharField(
        max_length=10000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Pessoa'


class Produto(models.Model):
    nome = models.CharField(max_length=10000, blank=True, null=True)
    # Field name made lowercase.
    idtipomaterial = models.ForeignKey(
        'Tipomaterial', models.DO_NOTHING, db_column='idTipoMaterial', blank=True, null=True)
    excluido = models.NullBooleanField()
    ativo = models.NullBooleanField()
    # Field name made lowercase.
    alteradoem = models.DateTimeField(
        db_column='alteradoEm', blank=True, null=True)
    # Field name made lowercase.
    alteradopor = models.ForeignKey(
        'Usuario', models.DO_NOTHING, db_column='alteradoPor', blank=True, null=True)
    observacoes = models.CharField(max_length=10000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Produto'


class Sala(models.Model):
    nome = models.CharField(max_length=10000, blank=True, null=True)
    ativo = models.NullBooleanField()
    excluido = models.NullBooleanField()
    # Field name made lowercase.
    alteradoem = models.DateTimeField(
        db_column='alteradoEm', blank=True, null=True)
    # Field name made lowercase.
    alteradopor = models.ForeignKey(
        'Usuario', models.DO_NOTHING, db_column='alteradoPor', blank=True, null=True)
    sigla = models.CharField(
        unique=True, max_length=10000, blank=True, null=True)
    observacoes = models.CharField(max_length=10000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Sala'


class Servico(models.Model):
    descricao = models.CharField(max_length=100, blank=True, null=True)
    ativo = models.NullBooleanField()
    sigla = models.CharField(max_length=30, blank=True, null=True)
    autenticar = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'Servico'


class Statusvisitas(models.Model):
    id = models.IntegerField(primary_key=True)
    nome = models.CharField(max_length=10000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'StatusVisitas'


class Tipomaterial(models.Model):
    # Field name made lowercase.
    idanexo = models.ForeignKey(Anexo, models.DO_NOTHING, db_column='idAnexo')
    tipo = models.CharField(max_length=10000, blank=True, null=True)
    descr = models.CharField(max_length=10000, blank=True, null=True)
    ativo = models.NullBooleanField()
    excluido = models.NullBooleanField()
    # Field name made lowercase.
    alteradoem = models.DateTimeField(
        db_column='alteradoEm', blank=True, null=True)
    # Field name made lowercase.
    alteradopor = models.ForeignKey(
        'Usuario', models.DO_NOTHING, db_column='alteradoPor', blank=True, null=True)
    codigo = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TipoMaterial'


class Usuario(models.Model):
    nome = models.CharField(max_length=50, blank=True, null=True)
    usuario = models.CharField(max_length=13, blank=True, null=True)
    senha = models.CharField(max_length=100, blank=True, null=True)
    ativo = models.NullBooleanField()
    excluido = models.NullBooleanField()
    # Field name made lowercase.
    expiraem = models.IntegerField(db_column='expiraEm', blank=True, null=True)
    # Field name made lowercase.
    ultimoacesso = models.DateTimeField(
        db_column='ultimoAcesso', blank=True, null=True)
    logado = models.NullBooleanField()
    tipo = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Usuario'


class Visitas(models.Model):
    # ok
    data = models.DateTimeField()
    # ok
    assunto = models.CharField(max_length=10000, blank=True, null=True)
    # ok
    status = models.ForeignKey(
        Statusvisitas, models.DO_NOTHING, db_column='status')

    # ok
    descricao = models.CharField(max_length=10000, blank=True, null=True)
    # ok
    observacao = models.CharField(max_length=10000, blank=True, null=True)

    # ok
    # Field name made lowercase.
    alteradoem = models.DateTimeField(
        db_column='alteradoEm', blank=True, null=True)

    # ok
    excluido = models.NullBooleanField()

    # ok
    # Field name made lowercase.
    idpessoa = models.ForeignKey(
        Pessoa, models.DO_NOTHING, db_column='idPessoa', blank=True, null=True)

    # Field name made lowercase.
    # ok
    alteradopor = models.ForeignKey(
        Usuario, models.DO_NOTHING, db_column='alteradoPor', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Visitas'

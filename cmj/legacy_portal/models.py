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


class Arquivo(models.Model):
    nome = models.TextField(blank=True, null=True)
    descr = models.TextField(blank=True, null=True)
    cod_arquivo = models.TextField(unique=True)

    class Meta:
        managed = False
        db_table = 'arquivo'


class Assuntos(models.Model):
    documento = models.ForeignKey(
        'Documento', models.DO_NOTHING, db_column='documento')
    tipo = models.ForeignKey('Tipolei', models.DO_NOTHING, db_column='tipo')
    sugestoes = models.IntegerField(blank=True, null=True)
    oficial = models.NullBooleanField()
    excluir = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'assuntos'
        unique_together = (('documento', 'tipo'),)


class Catalogo(models.Model):
    id_dicionario = models.ForeignKey(
        'Dicionario', models.DO_NOTHING, db_column='id_dicionario', blank=True, null=True)
    id_dic_indexes = models.ForeignKey(
        'DicIndexes', models.DO_NOTHING, db_column='id_dic_indexes', blank=True, null=True)
    id_origem = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'catalogo'


class DicIndexes(models.Model):
    tabela = models.CharField(max_length=10000, blank=True, null=True)
    campo = models.CharField(max_length=10000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'dic_indexes'
        unique_together = (('tabela', 'campo'),)


class DicStops(models.Model):
    palavra = models.CharField(
        unique=True, max_length=10000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'dic_stops'


class Dicionario(models.Model):
    # This field type is a guess.
    chave = models.TextField(unique=True, blank=True, null=True)
    palavra = models.CharField(max_length=10000, blank=True, null=True)
    # This field type is a guess.
    chave1 = models.TextField(blank=True, null=True)
    a = models.FloatField(blank=True, null=True)
    b = models.FloatField(blank=True, null=True)
    c = models.FloatField(blank=True, null=True)
    d = models.FloatField(blank=True, null=True)
    e = models.FloatField(blank=True, null=True)
    f = models.FloatField(blank=True, null=True)
    g = models.FloatField(blank=True, null=True)
    h = models.FloatField(blank=True, null=True)
    i = models.FloatField(blank=True, null=True)
    j = models.FloatField(blank=True, null=True)
    k = models.FloatField(blank=True, null=True)
    l = models.FloatField(blank=True, null=True)
    n = models.FloatField(blank=True, null=True)
    o = models.FloatField(blank=True, null=True)
    p = models.FloatField(blank=True, null=True)
    q = models.FloatField(blank=True, null=True)
    r = models.FloatField(blank=True, null=True)
    s = models.FloatField(blank=True, null=True)
    t = models.FloatField(blank=True, null=True)
    u = models.FloatField(blank=True, null=True)
    v = models.FloatField(blank=True, null=True)
    w = models.FloatField(blank=True, null=True)
    x = models.FloatField(blank=True, null=True)
    y = models.FloatField(blank=True, null=True)
    z = models.FloatField(blank=True, null=True)
    m = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'dicionario'


class Docdestaque(models.Model):
    id_doc = models.ForeignKey('Documento', models.DO_NOTHING,
                               db_column='id_doc', unique=True, blank=True, null=True)
    titulo = models.CharField(max_length=10000, blank=True, null=True)
    ordem = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'docdestaque'


class Documento(models.Model):
    numero = models.IntegerField(blank=True, null=True)
    epigrafe = models.CharField(max_length=10000, blank=True, null=True)
    ementa = models.CharField(max_length=10000, blank=True, null=True)
    preambulo = models.CharField(max_length=10000, blank=True, null=True)
    enunciado = models.CharField(max_length=10000, blank=True, null=True)
    indicacao = models.CharField(max_length=10000, blank=True, null=True)
    id_tipolei = models.ForeignKey(
        'Tipolei', models.DO_NOTHING, db_column='id_tipolei', blank=True, null=True)
    data_inclusao = models.DateTimeField(blank=True, null=True)
    data_lei = models.DateTimeField(blank=True, null=True)
    data_alteracao = models.DateTimeField(blank=True, null=True)
    consultas = models.IntegerField(blank=True, null=True)
    texto_final = models.CharField(max_length=10000, blank=True, null=True)
    assinatura = models.CharField(max_length=10000, blank=True, null=True)
    cargo_assinante = models.CharField(max_length=10000, blank=True, null=True)
    arqdigital = models.BinaryField(blank=True, null=True)
    possuiarqdigital = models.NullBooleanField()
    id_arquivo = models.ForeignKey(
        Arquivo, models.DO_NOTHING, db_column='id_arquivo', blank=True, null=True)
    id_revogador = models.IntegerField(blank=True, null=True)
    link_revogador = models.CharField(max_length=10000, blank=True, null=True)
    id_doc_principal = models.IntegerField(blank=True, null=True)
    cod_certidao = models.IntegerField(blank=True, null=True)
    publicado = models.NullBooleanField()
    content_type = models.CharField(max_length=10000, blank=True, null=True)
    name_file = models.CharField(max_length=10000, blank=True, null=True)
    size_bytes_files = models.IntegerField(blank=True, null=True)
    timestamp = models.DateTimeField()
    descr_auditoria = models.TextField(blank=True, null=True)
    data_vencimento = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'documento'


class Itemlei(models.Model):
    id_lei = models.ForeignKey(
        Documento, models.DO_NOTHING, db_column='id_lei', blank=True, null=True)
    numero = models.IntegerField()
    parte = models.IntegerField()
    livro = models.IntegerField()
    titulo = models.IntegerField()
    capitulo = models.IntegerField()
    secao = models.IntegerField()
    subsecao = models.IntegerField()
    artigo = models.IntegerField()
    paragrafo = models.IntegerField()
    inciso = models.IntegerField()
    alinea = models.IntegerField()
    texto = models.CharField(max_length=10000, blank=True, null=True)
    id_dono = models.IntegerField()
    revogado = models.NullBooleanField()
    alterado = models.NullBooleanField()
    incluido = models.NullBooleanField()
    data_inclusao = models.DateTimeField(blank=True, null=True)
    data_alteracao = models.DateTimeField(blank=True, null=True)
    artigovar = models.IntegerField()
    nivel = models.IntegerField()
    id_alterador = models.IntegerField()
    link_alterador = models.CharField(max_length=10000, blank=True, null=True)
    item = models.IntegerField()
    anexo = models.IntegerField()
    capitulovar = models.IntegerField()
    secaovar = models.IntegerField()
    subitem = models.IntegerField()
    subsubitem = models.IntegerField()
    itemsecao = models.IntegerField()
    incisovar = models.IntegerField()
    incisovarvar = models.IntegerField()
    # This field type is a guess.
    texto_fts = models.TextField(blank=True, null=True)
    artigovarvar = models.IntegerField()
    visibilidade_no_alterador = models.NullBooleanField()
    txt = models.CharField(max_length=10000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'itemlei'
        unique_together = (('numero', 'anexo', 'parte', 'livro', 'titulo', 'capitulo', 'capitulovar', 'secao', 'secaovar', 'subsecao', 'itemsecao', 'artigo', 'artigovar',
                            'artigovarvar', 'paragrafo', 'inciso', 'incisovar', 'incisovarvar', 'alinea', 'item', 'subitem', 'subsubitem', 'id_alterador', 'nivel', 'id_dono'),)


class Tipodoc(models.Model):
    descr = models.CharField(max_length=10000, blank=True, null=True)
    ordem = models.IntegerField(blank=True, null=True)
    intranet = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'tipodoc'


class Tipolei(models.Model):
    descr = models.CharField(max_length=10000, blank=True, null=True)
    # Field name made lowercase.
    idtipodoc = models.ForeignKey(
        Tipodoc, models.DO_NOTHING, db_column='idTipoDoc', blank=True, null=True)
    ordem = models.IntegerField(blank=True, null=True)
    localidade = models.CharField(max_length=10000, blank=True, null=True)
    autoridade = models.CharField(max_length=10000, blank=True, null=True)
    tipo = models.CharField(max_length=10000, blank=True, null=True)
    # Field name made lowercase.
    linkalternativo = models.CharField(
        db_column='linkAlternativo', max_length=10000, blank=True, null=True)
    classif_assuntos = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'tipolei'

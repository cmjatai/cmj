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


class Tipodoc(models.Model):
    descr = models.TextField(blank=True, null=True)
    ordem = models.IntegerField(blank=True, null=True)
    intranet = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'tipodoc'


class Tipolei(models.Model):
    descr = models.TextField(blank=True, null=True)
    # Field name made lowercase.
    idtipodoc = models.ForeignKey(
        Tipodoc, models.DO_NOTHING, db_column='idTipoDoc', blank=True, null=True)
    ordem = models.IntegerField(blank=True, null=True)
    localidade = models.TextField(blank=True, null=True)
    autoridade = models.TextField(blank=True, null=True)
    tipo = models.TextField(blank=True, null=True)
    # Field name made lowercase.
    linkalternativo = models.TextField(
        db_column='linkAlternativo', blank=True, null=True)
    classif_assuntos = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'tipolei'


class Documento(models.Model):
    numero = models.IntegerField(blank=True, null=True)
    epigrafe = models.TextField(blank=True, null=True)
    ementa = models.TextField(blank=True, null=True)
    preambulo = models.TextField(blank=True, null=True)
    enunciado = models.TextField(blank=True, null=True)
    indicacao = models.TextField(blank=True, null=True)
    id_tipolei = models.ForeignKey(
        Tipolei, models.DO_NOTHING, db_column='id_tipolei', blank=True, null=True)
    data_inclusao = models.DateTimeField(blank=True, null=True)
    data_lei = models.DateTimeField(blank=True, null=True)
    data_alteracao = models.DateTimeField(blank=True, null=True)
    consultas = models.IntegerField(blank=True, null=True)
    texto_final = models.TextField(blank=True, null=True)
    assinatura = models.TextField(blank=True, null=True)
    cargo_assinante = models.TextField(blank=True, null=True)
    arqdigital = models.BinaryField(blank=True, null=True)
    possuiarqdigital = models.NullBooleanField()
    id_revogador = models.IntegerField(blank=True, null=True)
    link_revogador = models.TextField(blank=True, null=True)
    id_doc_principal = models.IntegerField(blank=True, null=True)
    publicado = models.NullBooleanField()
    content_type = models.TextField(blank=True, null=True)
    name_file = models.TextField(blank=True, null=True)
    size_bytes_files = models.IntegerField(blank=True, null=True)
    cod_certidao = models.IntegerField()
    timestamp = models.DateTimeField(blank=True, null=True)
    descr_auditoria = models.TextField(blank=True, null=True)
    data_vencimento = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'documento'


class Itemdoc(models.Model):
    id = models.BigAutoField(primary_key=True)
    iddoc = models.IntegerField(blank=True, null=True)
    coditem = models.IntegerField(blank=True, null=True)
    pai = models.IntegerField(blank=True, null=True)
    idestrutura = models.IntegerField(blank=True, null=True)
    revoga = models.NullBooleanField()
    altera = models.NullBooleanField()
    inclui = models.NullBooleanField()
    texto = models.TextField(blank=True, null=True)
    vinculo = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'itemdoc'


class Itemlei(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_lei = models.ForeignKey(
        Documento, models.DO_NOTHING, db_column='id_lei', blank=True, null=True)
    numero = models.IntegerField(primary_key=True)
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
    texto = models.TextField(blank=True, null=True)
    id_dono = models.IntegerField()
    revogado = models.NullBooleanField()
    alterado = models.NullBooleanField()
    incluido = models.NullBooleanField()
    data_inclusao = models.DateTimeField(blank=True, null=True)
    data_alteracao = models.DateTimeField(blank=True, null=True)
    artigovar = models.IntegerField()
    nivel = models.IntegerField()
    id_alterador = models.IntegerField()
    link_alterador = models.TextField(blank=True, null=True)
    item = models.IntegerField()
    anexo = models.IntegerField()
    capitulovar = models.IntegerField()
    secaovar = models.IntegerField()
    subitem = models.IntegerField()
    subsubitem = models.IntegerField()
    itemsecao = models.IntegerField()
    incisovar = models.IntegerField()
    incisovarvar = models.IntegerField()
    artigovarvar = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'itemlei'
        unique_together = (('numero', 'anexo', 'parte', 'livro', 'titulo', 'capitulo', 'capitulovar', 'secao', 'secaovar', 'subsecao', 'itemsecao',
                            'artigo', 'artigovar', 'paragrafo', 'inciso', 'incisovar', 'incisovarvar', 'alinea', 'item', 'subitem', 'subsubitem', 'id_alterador', 'nivel'),)

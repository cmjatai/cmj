# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals

from django.db import models


class Ac(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ac'


class Al(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'al'


class Am(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'am'


class Ap(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ap'


class Ba(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ba'


class Ce(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ce'


class CepLogIndex(models.Model):
    cep5 = models.CharField(max_length=5)
    uf = models.CharField(max_length=2)

    class Meta:
        managed = False
        db_table = 'cep_log_index'


class CepUnico(models.Model):
    seq = models.BigIntegerField(db_column='Seq', primary_key=True)  # Field name made lowercase.
    nome = models.CharField(db_column='Nome', max_length=50)  # Field name made lowercase.
    nomesemacento = models.CharField(db_column='NomeSemAcento', max_length=50, blank=True, null=True)  # Field name made lowercase.
    cep = models.CharField(db_column='Cep', max_length=9, blank=True, null=True)  # Field name made lowercase.
    uf = models.CharField(db_column='UF', max_length=2)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'cep_unico'


class Df(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'df'


class Es(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'es'


class Go(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'go'


class Ma(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ma'


class Mg(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mg'


class Ms(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ms'


class Mt(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mt'


class Pa(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pa'


class Pb(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pb'


class Pe(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pe'


class Pi(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pi'


class Pr(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pr'


class Rj(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rj'


class Rn(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rn'


class Ro(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ro'


class Rr(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rr'


class Rs(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rs'


class Sc(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sc'


class Se(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'se'


class Sp(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sp'


class To(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    logradouro = models.CharField(max_length=70, blank=True, null=True)
    bairro = models.CharField(max_length=72, blank=True, null=True)
    cep = models.CharField(max_length=9)
    tp_logradouro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'to'


class Uf(models.Model):
    uf = models.CharField(db_column='UF', primary_key=True, max_length=2)  # Field name made lowercase.
    nome = models.CharField(db_column='Nome', max_length=72)  # Field name made lowercase.
    cep1 = models.CharField(db_column='Cep1', max_length=5)  # Field name made lowercase.
    cep2 = models.CharField(db_column='Cep2', max_length=5)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'uf'

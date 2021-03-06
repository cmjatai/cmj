# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-06-18 16:36
from __future__ import unicode_literals

import cmj.diarios.models
from django.db import migrations, models
import django.db.models.deletion
import sapl.utils


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DiarioOficial',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('edicao', models.PositiveIntegerField(default=0, verbose_name='Edição')),
                ('descricao', models.CharField(max_length=250, verbose_name='Descrição')),
                ('data', models.DateField(blank=True, null=True, verbose_name='Data')),
                ('arquivo', models.FileField(blank=True, null=True, upload_to=cmj.diarios.models.diario_upload_path, validators=[sapl.utils.restringe_tipos_de_arquivo_txt], verbose_name='Arquivo Digital do Diário')),
            ],
            options={
                'verbose_name': 'Diário Oficial',
                'verbose_name_plural': 'Diários Oficiais',
            },
        ),
        migrations.CreateModel(
            name='TipoDeDiario',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(max_length=50, verbose_name='Descrição')),
            ],
            options={
                'verbose_name': 'Tipo de Diário',
                'verbose_name_plural': 'Tipos de Diário',
            },
        ),
        migrations.AddField(
            model_name='diariooficial',
            name='tipo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='diarios.TipoDeDiario', verbose_name='Tipo do Diário'),
        ),
    ]

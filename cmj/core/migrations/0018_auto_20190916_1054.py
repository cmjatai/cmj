# -*- coding: utf-8 -*-
# Generated by Django 1.11.24 on 2019-09-16 13:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_auto_20190905_0113'),
    ]

    operations = [
        migrations.AlterField(
            model_name='areatrabalho',
            name='tipo',
            field=models.IntegerField(choices=[(10, 'Gabinete Parlamentar'), (20, 'Setor Administrativo'), (30, 'Institucional'), (99, 'Documentos Públicos')], default=10, verbose_name='Tipo da Área de Trabalho'),
        ),
    ]

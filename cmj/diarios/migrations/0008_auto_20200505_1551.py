# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-05-05 18:51
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('diarios', '0007_diariooficial_metadata'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='diariooficial',
            options={'ordering': ('-data', 'edicao'), 'verbose_name': 'Diário Oficial', 'verbose_name_plural': 'Diários Oficiais'},
        ),
    ]

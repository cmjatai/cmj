# -*- coding: utf-8 -*-
# Generated by Django 1.11.24 on 2019-09-17 00:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('protocoloadm', '0028_documentoadministrativo_temp_migracao_doc_acessorio'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentoadministrativo',
            name='interessado',
            field=models.CharField(blank=True, max_length=1000, verbose_name='Interessado'),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-09-05 04:28
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_auto_20190905_0113'),
        ('protocoloadm', '0023_merge_20190802_1117'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentoadministrativo',
            name='workspace',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='documentoadministrativo_set', to='core.AreaTrabalho', verbose_name='Área de Trabalho'),
        ),
    ]
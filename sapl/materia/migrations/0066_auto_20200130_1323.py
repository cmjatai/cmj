# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-01-30 16:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0065_auto_20200129_1037'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentoacessorio',
            name='_paginas',
            field=models.IntegerField(default=0, verbose_name='Número de Páginas'),
        ),
        migrations.AlterField(
            model_name='materialegislativa',
            name='_paginas',
            field=models.IntegerField(default=0, verbose_name='Número de Páginas'),
        ),
    ]
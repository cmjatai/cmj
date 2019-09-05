# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2017-05-04 17:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0003_auto_20170403_1505'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assuntomateria',
            name='dispositivo',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Descrição do Dispositivo Legal'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='materiaassunto',
            name='assunto',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='materia.AssuntoMateria', verbose_name='Assunto'),
        ),
        migrations.AlterField(
            model_name='materiaassunto',
            name='materia',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='materia.MateriaLegislativa', verbose_name='Matéria'),
        ),
    ]
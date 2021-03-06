# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-01-30 17:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('core', '0024_bi'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='bi',
            options={'ordering': ('-ano', 'content_type'), 'verbose_name': 'Bi', 'verbose_name_plural': 'Bi'},
        ),
        migrations.AddField(
            model_name='bi',
            name='ano',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Ano'),
        ),
        migrations.AlterField(
            model_name='bi',
            name='content_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType'),
        ),
        migrations.AlterUniqueTogether(
            name='bi',
            unique_together=set([('ano', 'content_type')]),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-04-07 03:34
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0040_auto_20200406_1038'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='autor',
            name='user',
        ),
    ]

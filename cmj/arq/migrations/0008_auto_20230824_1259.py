# Generated by Django 2.2.28 on 2023-08-24 15:59

import cmj.arq.models
from django.db import migrations
import sapl.utils


class Migration(migrations.Migration):

    dependencies = [
        ('arq', '0007_arqclasse'),
    ]

    operations = [
        migrations.AlterField(
            model_name='draftmidia',
            name='arquivo',
            field=sapl.utils.PortalFileField(blank=True, max_length=512, null=True, upload_to=cmj.arq.models.draftmidia_path, verbose_name='Arquivo'),
        ),
    ]
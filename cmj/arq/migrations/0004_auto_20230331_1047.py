# Generated by Django 2.2.28 on 2023-03-31 13:47

import cmj.arq.models
from django.db import migrations
import sapl.utils


class Migration(migrations.Migration):

    dependencies = [
        ('arq', '0003_auto_20230330_1439'),
    ]

    operations = [
        migrations.AlterField(
            model_name='draftmidia',
            name='arquivo',
            field=sapl.utils.PortalFileField(blank=True, null=True, upload_to=cmj.arq.models.draftmidia_path, verbose_name='Arquivo'),
        ),
    ]
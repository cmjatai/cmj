# Generated by Django 4.2.16 on 2024-10-03 20:09

import django.core.serializers.json
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ouvidoria', '0013_auto_20240325_1346'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mensagemsolicitacao',
            name='metadata',
            field=models.JSONField(blank=True, default=None, encoder=django.core.serializers.json.DjangoJSONEncoder, null=True, verbose_name='Metadados'),
        ),
    ]
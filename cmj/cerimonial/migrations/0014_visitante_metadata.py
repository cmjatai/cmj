# Generated by Django 2.2.28 on 2024-06-03 19:25

import django.contrib.postgres.fields.jsonb
import django.core.serializers.json
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cerimonial', '0013_auto_20240325_1346'),
    ]

    operations = [
        migrations.AddField(
            model_name='visitante',
            name='metadata',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=None, encoder=django.core.serializers.json.DjangoJSONEncoder, null=True, verbose_name='Metadados'),
        ),
    ]

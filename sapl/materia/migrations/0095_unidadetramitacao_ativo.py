# Generated by Django 4.2.18 on 2025-01-27 20:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0094_alter_assuntomateria_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='unidadetramitacao',
            name='ativo',
            field=models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=True, verbose_name='Ativo ?'),
        ),
    ]

# Generated by Django 4.2.16 on 2024-10-03 20:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0020_urlizereferencia_chave_automatica'),
    ]

    operations = [
        migrations.AlterField(
            model_name='textoarticulado',
            name='participacao_social',
            field=models.BooleanField(blank=True, choices=[(None, 'Padrão definido no Tipo'), (True, 'Sim'), (False, 'Não')], default=None, null=True, verbose_name='Participação Social'),
        ),
    ]

# Generated by Django 2.2.28 on 2024-04-23 13:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0088_auto_20240325_1346'),
    ]

    operations = [
        migrations.AddField(
            model_name='regimetramitacao',
            name='sequencia_regimental',
            field=models.PositiveIntegerField(default=0, help_text='A sequência regimental diz respeito ao que define o regimento da Casa Legislativa sobre qual a ordem de entrada das proposições nas Sessões Plenárias.', verbose_name='Sequência Regimental'),
        ),
    ]
# Generated by Django 2.2.20 on 2021-06-07 12:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('norma', '0039_tiponormajuridica_origem_processo_legislativo'),
    ]

    operations = [
        migrations.AddField(
            model_name='normajuridica',
            name='checkcheck',
            field=models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=False, verbose_name='Registro de Norma Jurídica Auditado?'),
        ),
    ]
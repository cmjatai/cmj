# Generated by Django 2.2.26 on 2022-02-17 12:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0046_auto_20200520_2037'),
    ]

    operations = [
        migrations.AddField(
            model_name='operadorautor',
            name='visibilidade_restrita',
            field=models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=False, verbose_name='Ver apenas proposições criadas por este usuário'),
        ),
    ]

# Generated by Django 4.2.18 on 2025-02-19 14:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0043_alter_user_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='certidaopublicacao',
            name='revogado',
            field=models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=False, verbose_name='Certidão Revogada'),
        ),
    ]

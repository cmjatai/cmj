# Generated by Django 4.2.16 on 2024-11-06 11:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loa', '0050_emendaloa_unidade'),
    ]

    operations = [
        migrations.AddField(
            model_name='unidadeorcamentaria',
            name='recebe_emenda_impositiva',
            field=models.BooleanField(default=False, verbose_name='Elegível'),
        ),
    ]

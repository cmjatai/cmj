# Generated by Django 2.2.28 on 2024-03-25 16:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('diarios', '0013_auto_20201016_0853'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tipodediario',
            options={'ordering': ['id'], 'verbose_name': 'Tipo de Diário', 'verbose_name_plural': 'Tipos de Diário'},
        ),
    ]

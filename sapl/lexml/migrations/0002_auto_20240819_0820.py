# Generated by Django 2.2.28 on 2024-08-19 11:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexml', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='lexmlprovedor',
            options={'ordering': ['id'], 'verbose_name': 'Provedor Lexml', 'verbose_name_plural': 'Provedores Lexml'},
        ),
        migrations.AlterModelOptions(
            name='lexmlpublicador',
            options={'ordering': ['id'], 'verbose_name': 'Publicador Lexml', 'verbose_name_plural': 'Publicadores Lexml'},
        ),
    ]
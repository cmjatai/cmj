# Generated by Django 2.2.28 on 2024-03-25 16:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0050_appconfig_mostrar_voto'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='casalegislativa',
            options={'ordering': ['id'], 'verbose_name': 'Casa Legislativa', 'verbose_name_plural': 'Casa Legislativa'},
        ),
        migrations.AlterModelOptions(
            name='metadata',
            options={'ordering': ['id'], 'verbose_name': 'Metadado', 'verbose_name_plural': 'Metadados'},
        ),
        migrations.AlterModelOptions(
            name='operadorautor',
            options={'ordering': ['id'], 'verbose_name': 'Operador do Autor', 'verbose_name_plural': 'Operadores do Autor'},
        ),
    ]
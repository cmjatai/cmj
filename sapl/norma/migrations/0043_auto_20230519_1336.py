# Generated by Django 2.2.28 on 2023-05-19 16:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('norma', '0042_auto_20230205_1438'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='anexonormajuridica',
            options={'ordering': ('assunto_anexo',), 'verbose_name': 'Anexo da Norma Jurídica', 'verbose_name_plural': 'Anexos da Norma Jurídica'},
        ),
    ]

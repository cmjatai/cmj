# Generated by Django 2.2.28 on 2024-05-08 18:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('norma', '0046_auto_20240325_1346'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='normajuridica',
            options={'ordering': ['-data', '-id'], 'verbose_name': 'Norma Jurídica', 'verbose_name_plural': 'Normas Jurídicas'},
        ),
    ]
# Generated by Django 5.2.3 on 2025-06-23 19:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0047_rename_iaquotas_iaquota'),
    ]

    operations = [
        migrations.AlterField(
            model_name='iaquota',
            name='modelo',
            field=models.CharField(max_length=100, unique=True, verbose_name='Modelo'),
        ),
    ]

# Generated by Django 2.2.24 on 2021-08-12 15:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sigad', '0054_auto_20200623_0805'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='midia',
            name='revisao',
        ),
    ]

# Generated by Django 2.2.24 on 2021-10-16 22:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0008_pullexec_data_exec'),
    ]

    operations = [
        migrations.AddField(
            model_name='pullexec',
            name='quota',
            field=models.PositiveIntegerField(default=1, verbose_name='Quota'),
        ),
        migrations.AlterField(
            model_name='pullexec',
            name='data_exec',
            field=models.DateTimeField(auto_now_add=True, verbose_name='data_exec'),
        ),
    ]
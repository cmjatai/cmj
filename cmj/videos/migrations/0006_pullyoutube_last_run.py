# Generated by Django 2.2.24 on 2021-10-15 17:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0005_auto_20211010_0028'),
    ]

    operations = [
        migrations.AddField(
            model_name='pullyoutube',
            name='last_run',
            field=models.DateTimeField(auto_now=True, verbose_name='last_run'),
        ),
    ]
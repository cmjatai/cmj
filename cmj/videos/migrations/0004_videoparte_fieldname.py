# Generated by Django 2.2.24 on 2021-10-08 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0003_auto_20211008_1213'),
    ]

    operations = [
        migrations.AddField(
            model_name='videoparte',
            name='fieldname',
            field=models.CharField(blank=True, default='', max_length=250, null=True),
        ),
    ]
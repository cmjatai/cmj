# Generated by Django 2.2.24 on 2021-12-03 16:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0009_auto_20211016_1921'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pullexec',
            name='pull',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pullyoutube_set', to='videos.PullYoutube', verbose_name='PullYoutube'),
        ),
    ]

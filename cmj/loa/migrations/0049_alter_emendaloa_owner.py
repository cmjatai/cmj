# Generated by Django 4.2.16 on 2024-11-05 17:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('loa', '0048_emendaloa_owner'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emendaloa',
            name='owner',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Cadastrado Por'),
        ),
    ]

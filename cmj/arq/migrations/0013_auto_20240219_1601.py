# Generated by Django 2.2.28 on 2024-02-19 19:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('arq', '0012_auto_20240202_1645'),
    ]

    operations = [
        migrations.AddField(
            model_name='arqclasse',
            name='arquivado',
            field=models.BooleanField(default=False, verbose_name='Arquivado'),
        ),
        migrations.AddField(
            model_name='arqdoc',
            name='arquivado',
            field=models.BooleanField(default=False, verbose_name='Arquivado'),
        ),
        migrations.AlterField(
            model_name='arqclasse',
            name='raiz',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='nodes', to='arq.ArqClasse', verbose_name='Raiz'),
        ),
        migrations.AlterField(
            model_name='arqdoc',
            name='raiz',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='nodes', to='arq.ArqDoc', verbose_name='Raiz'),
        ),
    ]
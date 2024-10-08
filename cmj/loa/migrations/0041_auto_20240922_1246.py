# Generated by Django 2.2.28 on 2024-09-22 15:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('loa', '0040_despesapaga_natureza'),
    ]

    operations = [
        migrations.AddField(
            model_name='despesapaga',
            name='cpfcnpj',
            field=models.TextField(blank=True, default=None, null=True, verbose_name='CpfCNPJ'),
        ),
        migrations.AddField(
            model_name='despesapaga',
            name='fonte',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='despesapaga_set', to='loa.Fonte', verbose_name='Fonte'),
        ),
        migrations.AddField(
            model_name='despesapaga',
            name='historico',
            field=models.TextField(blank=True, default=None, null=True, verbose_name='Histórico'),
        ),
        migrations.AddField(
            model_name='despesapaga',
            name='nome',
            field=models.TextField(blank=True, default=None, null=True, verbose_name='Nome'),
        ),
    ]

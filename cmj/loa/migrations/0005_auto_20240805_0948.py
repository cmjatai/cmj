# Generated by Django 2.2.28 on 2024-08-05 12:48

from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0090_tipomaterialegislativa_nivel_agrupamento'),
        ('parlamentares', '0045_auto_20240420_1344'),
        ('loa', '0004_auto_20240802_1753'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmendaLoa',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.PositiveSmallIntegerField(choices=[(10, 'Saúde'), (99, 'Áreas Diversas')], default=0, verbose_name='Área de aplicação')),
                ('finalidade', models.TextField(verbose_name='Finalidade')),
                ('valor', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=14, verbose_name='Valor Global da Emenda (R$)')),
            ],
            options={
                'verbose_name': 'Emenda Impositiva',
                'verbose_name_plural': 'Emendas Impositivas',
                'ordering': ['id'],
            },
        ),
        migrations.AlterModelOptions(
            name='loa',
            options={'ordering': ['-id'], 'verbose_name': 'Loa - Emendas Impositivas', 'verbose_name_plural': 'Loa - Emendas Impositivas'},
        ),
        migrations.AlterModelOptions(
            name='loaparlamentar',
            options={'ordering': ['id'], 'verbose_name': 'Valores do Parlamentar', 'verbose_name_plural': 'Valores dos Parlamentares'},
        ),
        migrations.CreateModel(
            name='EmendaLoaParlamentar',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valor', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=14, verbose_name='Valor por Parlamentar (R$)')),
                ('emendaloa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='emendaloaparlamentar_set', to='loa.EmendaLoa', verbose_name='Emenda Impositiva')),
                ('parlamentar', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='emendaloaparlamentar_set', to='parlamentares.Parlamentar', verbose_name='Parlamentar')),
            ],
            options={
                'verbose_name': 'Participação Parlamentar na Emenda Impositiva',
                'verbose_name_plural': 'Participações Parlamentares na Emenda Impositiva',
                'ordering': ['id'],
            },
        ),
        migrations.AddField(
            model_name='emendaloa',
            name='loa',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='emendaloa_set', to='loa.Loa', verbose_name='Loa - Emendas Impositivas'),
        ),
        migrations.AddField(
            model_name='emendaloa',
            name='materia',
            field=models.OneToOneField(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='materia.MateriaLegislativa', verbose_name='Matéria Legislativa'),
        ),
        migrations.AddField(
            model_name='emendaloa',
            name='parlamentares',
            field=models.ManyToManyField(related_name='emendaloa_set', through='loa.EmendaLoaParlamentar', to='parlamentares.Parlamentar', verbose_name='Parlamentares'),
        ),
    ]
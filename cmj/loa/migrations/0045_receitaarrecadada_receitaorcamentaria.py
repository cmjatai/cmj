# Generated by Django 2.2.28 on 2024-09-25 19:19

from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('loa', '0044_delete_receitaarrecadada'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReceitaOrcamentaria',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.TextField(verbose_name='Código')),
                ('historico', models.TextField(blank=True, default=None, null=True, verbose_name='Histórico')),
                ('valor', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=14, verbose_name='Valor (R$)')),
                ('orgao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receitaorcamentaria_set', to='loa.Orgao', verbose_name='Órgão')),
            ],
            options={
                'verbose_name': 'Receita Orçamentária',
                'verbose_name_plural': 'Receitas Orçamentárias',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='ReceitaArrecadada',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.DateField(blank=True, null=True, verbose_name='Data')),
                ('tipo', models.TextField(blank=True, default=None, null=True, verbose_name='Tipo')),
                ('valor', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=14, verbose_name='Valor (R$)')),
                ('receita', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receitaarrecadada_set', to='loa.ReceitaOrcamentaria', verbose_name='Receita Orçamentária')),
            ],
            options={
                'verbose_name': 'Receita Arrecadada',
                'verbose_name_plural': 'Receitas Arrecadadas',
                'ordering': ['id'],
            },
        ),
    ]

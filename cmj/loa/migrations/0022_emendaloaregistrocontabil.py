# Generated by Django 2.2.28 on 2024-09-01 18:46

from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('loa', '0021_emendaloa_metadata'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmendaLoaRegistroContabil',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valor', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=14, verbose_name='Valor (R$)')),
                ('despesa', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='registrocontabil_set', to='loa.Despesa', verbose_name='Despesa')),
                ('emendaloa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registrocontabil_set', to='loa.EmendaLoa', verbose_name='Emenda Impositiva')),
                ('natureza', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='registrocontabil_set', to='loa.Natureza', verbose_name='Natureza')),
                ('orgao', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='registrocontabil_set', to='loa.Orgao', verbose_name='Órgão')),
                ('unidade', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='registrocontabil_set', to='loa.UnidadeOrcamentaria', verbose_name='Unidade Orçamentária')),
            ],
            options={
                'verbose_name': 'Registro Contábeis de Dedução e Inserção em Emendas',
                'verbose_name_plural': 'Registro Contábeis de Dedução e Inserção em Emendas',
                'ordering': ['id'],
            },
        ),
    ]
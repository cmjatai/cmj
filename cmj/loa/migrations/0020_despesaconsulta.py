# Generated by Django 2.2.28 on 2024-08-28 18:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loa', '0019_cria_view_despesa_consulta'),
    ]

    operations = [
        migrations.CreateModel(
            name='DespesaConsulta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.TextField(verbose_name='Código')),
                ('especificacao', models.TextField(verbose_name='Especificação')),
                ('cod_orgao', models.TextField(verbose_name='Código do Órgão')),
                ('esp_orgao', models.TextField(verbose_name='Órgão')),
                ('cod_unidade', models.TextField(verbose_name='Código da Unidade')),
                ('esp_unidade', models.TextField(verbose_name='Unidade Orçamentária')),
                ('cod_natureza', models.TextField(verbose_name='Natureza da Despesa')),
                ('cod_fonte', models.TextField(verbose_name='Fonte')),
            ],
            options={
                'db_table': 'loa_despesa_consulta',
                'ordering': ('cod_orgao', 'cod_unidade', 'codigo', 'cod_natureza'),
                'managed': False,
            },
        ),
    ]

# Generated by Django 5.2.1 on 2025-05-15 00:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0057_alter_autor_operadores'),
        ('materia', '0099_tipodocumento_limite_minimo_coletivo_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='materialegislativa',
            name='anexadas',
            field=models.ManyToManyField(blank=True, related_name='anexo_de', through='materia.Anexada', through_fields=('materia_principal', 'materia_anexada'), to='materia.materialegislativa'),
        ),
        migrations.AlterField(
            model_name='materialegislativa',
            name='assuntos',
            field=models.ManyToManyField(blank=True, through='materia.MateriaAssunto', through_fields=('materia', 'assunto'), to='materia.assuntomateria'),
        ),
        migrations.AlterField(
            model_name='materialegislativa',
            name='autores',
            field=models.ManyToManyField(through='materia.Autoria', through_fields=('materia', 'autor'), to='base.autor'),
        ),
        migrations.CreateModel(
            name='AnaliseSimilaridade',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('analise', models.TextField(blank=True, null=True, verbose_name='Análise de Similaridade')),
                ('data_analise', models.DateTimeField(blank=True, null=True, verbose_name='Data da Análise')),
                ('ia_name', models.CharField(blank=True, max_length=50, null=True, verbose_name='Nome do Algoritmo de IA')),
                ('similaridade', models.PositiveSmallIntegerField(default=0, verbose_name='Similaridade')),
                ('materia_1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='materia_1_set', to='materia.materialegislativa', verbose_name='Matéria 1')),
                ('materia_2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='materia_2_set', to='materia.materialegislativa', verbose_name='Matéria 2')),
            ],
            options={
                'verbose_name': 'Análise de Similaridade',
                'verbose_name_plural': 'Análises de Similaridade',
                'ordering': ['id'],
            },
        ),
        migrations.AddField(
            model_name='materialegislativa',
            name='similaridades',
            field=models.ManyToManyField(blank=True, related_name='similaridade_set', through='materia.AnaliseSimilaridade', through_fields=('materia_1', 'materia_2'), to='materia.materialegislativa'),
        ),
    ]

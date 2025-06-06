# Generated by Django 4.2.18 on 2025-01-29 17:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0097_materiaemtramitacao'),
    ]

    operations = [
        migrations.AddField(
            model_name='tipomaterialegislativa',
            name='limite_minimo_coletivo',
            field=models.PositiveIntegerField(blank=True, default=0, null=True, verbose_name='Não Impõe Limites de Protocolo acima deste valor'),
        ),
        migrations.AddField(
            model_name='tipomaterialegislativa',
            name='limite_por_autor_tramitando',
            field=models.PositiveIntegerField(blank=True, default=0, null=True, verbose_name='Limitar Protocolo por Autor'),
        ),
    ]

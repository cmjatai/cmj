# Generated by Django 4.2.18 on 2025-01-22 00:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0093_tipomaterialegislativa_prompt'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='assuntomateria',
            options={'ordering': ['assunto'], 'verbose_name': 'Assunto de Matéria', 'verbose_name_plural': 'Assuntos de Matéria'},
        ),
        migrations.AlterModelOptions(
            name='materiaassunto',
            options={'ordering': ['assunto__assunto'], 'verbose_name': 'Relação Matéria - Assunto', 'verbose_name_plural': 'Relações Matéria - Assunto'},
        ),
        migrations.AddField(
            model_name='materialegislativa',
            name='assuntos',
            field=models.ManyToManyField(blank=True, through='materia.MateriaAssunto', to='materia.assuntomateria'),
        ),
    ]

# Generated by Django 2.2.24 on 2021-10-06 20:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0079_tipomaterialegislativa_turnos_aprovacao'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tramitacao',
            name='turno',
            field=models.CharField(blank=True, choices=[('P', 'Primeiro'), ('S', 'Segundo'), ('U', 'Único')], max_length=1, verbose_name='Turno'),
        ),
    ]

# Generated by Django 2.2.28 on 2024-03-25 16:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('agenda', '0007_evento_caracteristica'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='programacao',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='tipoevento',
            options={'ordering': ['id'], 'verbose_name': 'Tipo de Evento', 'verbose_name_plural': 'Tipos de Eventos'},
        ),
    ]

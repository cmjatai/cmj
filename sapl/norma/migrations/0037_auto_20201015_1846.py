# Generated by Django 2.2.16 on 2020-10-15 21:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('norma', '0036_auto_20201015_0846'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='normajuridica',
            name='pagina_fim_publicacao',
        ),
        migrations.RemoveField(
            model_name='normajuridica',
            name='pagina_inicio_publicacao',
        ),
        migrations.RemoveField(
            model_name='normajuridica',
            name='veiculo_publicacao',
        ),
    ]
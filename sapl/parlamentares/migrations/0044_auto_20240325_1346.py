# Generated by Django 2.2.28 on 2024-03-25 16:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0043_auto_20201218_0858'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='afastamentoparlamentar',
            options={'ordering': ['id'], 'verbose_name': 'Afastamento', 'verbose_name_plural': 'Afastamentos'},
        ),
        migrations.AlterModelOptions(
            name='bloco',
            options={'ordering': ['id'], 'verbose_name': 'Bloco Parlamentar', 'verbose_name_plural': 'Blocos Parlamentares'},
        ),
        migrations.AlterModelOptions(
            name='cargobancada',
            options={'ordering': ['id'], 'verbose_name': 'Cargo de Bancada', 'verbose_name_plural': 'Cargos de Bancada'},
        ),
        migrations.AlterModelOptions(
            name='cargomesa',
            options={'ordering': ['id'], 'verbose_name': 'Cargo na Mesa', 'verbose_name_plural': 'Cargos na Mesa'},
        ),
        migrations.AlterModelOptions(
            name='coligacao',
            options={'ordering': ['id'], 'verbose_name': 'Coligação', 'verbose_name_plural': 'Coligações'},
        ),
        migrations.AlterModelOptions(
            name='composicaocoligacao',
            options={'ordering': ['id'], 'verbose_name': 'Composição Coligação', 'verbose_name_plural': 'Composição Coligações'},
        ),
        migrations.AlterModelOptions(
            name='composicaomesa',
            options={'ordering': ['id'], 'verbose_name': 'Ocupação de cargo na Mesa', 'verbose_name_plural': 'Ocupações de cargo na Mesa'},
        ),
        migrations.AlterModelOptions(
            name='dependente',
            options={'ordering': ['id'], 'verbose_name': 'Dependente', 'verbose_name_plural': 'Dependentes'},
        ),
        migrations.AlterModelOptions(
            name='frente',
            options={'ordering': ['id'], 'verbose_name': 'Frente Parlamentar', 'verbose_name_plural': 'Frentes Parlamentares'},
        ),
        migrations.AlterModelOptions(
            name='historicopartido',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='mandato',
            options={'ordering': ['id'], 'verbose_name': 'Mandato', 'verbose_name_plural': 'Mandatos'},
        ),
        migrations.AlterModelOptions(
            name='votante',
            options={'ordering': ['id'], 'permissions': (('can_vote', 'Can Vote'),), 'verbose_name': 'Usuário Votante', 'verbose_name_plural': 'Usuários Votantes'},
        ),
    ]

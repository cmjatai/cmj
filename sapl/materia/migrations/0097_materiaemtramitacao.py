# Generated by Django 4.2.18 on 2025-01-27 20:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0096_auto_20250127_1713'),
    ]

    operations = [
        migrations.CreateModel(
            name='MateriaEmTramitacao',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'db_table': 'materia_materiaemtramitacao',
                'ordering': ('-id',),
                'managed': False,
            },
        ),
    ]

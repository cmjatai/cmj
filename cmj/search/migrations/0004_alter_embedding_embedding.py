# Generated by Django 4.2.17 on 2025-01-01 11:59

from django.db import migrations
import pgvector.django.vector


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0003_alter_embedding_embedding'),
    ]

    operations = [
        migrations.AlterField(
            model_name='embedding',
            name='embedding',
            field=pgvector.django.vector.VectorField(),
        ),
    ]
# Generated by Django 2.2.28 on 2023-04-14 12:55

from django.conf import settings
import django.contrib.postgres.fields.jsonb
import django.core.serializers.json
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('arq', '0006_draftmidia_created'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArqClasse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('metadata', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=None, encoder=django.core.serializers.json.DjangoJSONEncoder, null=True, verbose_name='Metadados')),
                ('codigo', models.PositiveIntegerField(default=0, verbose_name='Código')),
                ('titulo', models.CharField(blank=True, default='', max_length=250, null=True, verbose_name='Título')),
                ('descricao', models.TextField(blank=True, default=None, null=True, verbose_name='Descrição')),
                ('perfil', models.IntegerField(choices=[(0, 'Classe Estrutural'), (1, 'Classe de Conteúdo'), (2, 'Classe Mista')], default=0, verbose_name='Perfil da Classe')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='owner')),
                ('parent', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='childs', to='arq.ArqClasse', verbose_name='Filhos')),
                ('raiz', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='nodes', to='arq.ArqClasse', verbose_name='Containers')),
            ],
            options={
                'verbose_name': 'Classe',
                'verbose_name_plural': 'Classes',
                'ordering': ('codigo',),
            },
        ),
    ]

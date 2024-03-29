# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-03-25 11:14
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import sapl.parlamentares.models
import sapl.utils


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CargoMesa',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(max_length=50, verbose_name='Cargo na Mesa')),
                ('unico', models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], verbose_name='Cargo Único')),
            ],
            options={
                'verbose_name': 'Cargo na Mesa',
                'verbose_name_plural': 'Cargos na Mesa',
            },
        ),
        migrations.CreateModel(
            name='Coligacao',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
                ('numero_votos', models.PositiveIntegerField(blank=True, null=True, verbose_name='Nº Votos Recebidos')),
            ],
            options={
                'verbose_name': 'Coligação',
                'verbose_name_plural': 'Coligações',
            },
        ),
        migrations.CreateModel(
            name='ComposicaoColigacao',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coligacao', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='parlamentares.Coligacao')),
            ],
            options={
                'verbose_name': 'Composição Coligação',
                'verbose_name_plural': 'Composição Coligações',
            },
        ),
        migrations.CreateModel(
            name='ComposicaoMesa',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cargo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='parlamentares.CargoMesa')),
            ],
            options={
                'verbose_name': 'Ocupação de cargo na Mesa',
                'verbose_name_plural': 'Ocupações de cargo na Mesa',
            },
        ),
        migrations.CreateModel(
            name='Dependente',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
                ('sexo', models.CharField(choices=[('F', 'Feminino'), ('M', 'Masculino')], max_length=1, verbose_name='Sexo')),
                ('data_nascimento', models.DateField(blank=True, null=True, verbose_name='Data Nascimento')),
                ('cpf', models.CharField(blank=True, max_length=14, verbose_name='CPF')),
                ('rg', models.CharField(blank=True, max_length=15, verbose_name='RG')),
                ('titulo_eleitor', models.CharField(blank=True, max_length=15, verbose_name='Nº Título Eleitor')),
            ],
            options={
                'verbose_name': 'Dependente',
                'verbose_name_plural': 'Dependentes',
            },
        ),
        migrations.CreateModel(
            name='Filiacao',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.DateField(verbose_name='Data Filiação')),
                ('data_desfiliacao', models.DateField(blank=True, null=True, verbose_name='Data Desfiliação')),
            ],
            options={
                'ordering': ('parlamentar', '-data', '-data_desfiliacao'),
                'verbose_name': 'Filiação',
                'verbose_name_plural': 'Filiações',
            },
        ),
        migrations.CreateModel(
            name='Frente',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=80, verbose_name='Nome da Frente')),
                ('data_criacao', models.DateField(verbose_name='Data Criação')),
                ('data_extincao', models.DateField(blank=True, null=True, verbose_name='Data Dissolução')),
                ('descricao', models.TextField(blank=True, verbose_name='Descrição')),
            ],
            options={
                'verbose_name': 'Frente',
                'verbose_name_plural': 'Frentes',
            },
        ),
        migrations.CreateModel(
            name='Legislatura',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.PositiveIntegerField(verbose_name='Número')),
                ('data_inicio', models.DateField(verbose_name='Data Início')),
                ('data_fim', models.DateField(verbose_name='Data Fim')),
                ('data_eleicao', models.DateField(verbose_name='Data Eleição')),
            ],
            options={
                'ordering': ['-data_inicio'],
                'verbose_name': 'Legislatura',
                'verbose_name_plural': 'Legislaturas',
            },
        ),
        migrations.CreateModel(
            name='Mandato',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_causa_fim_mandato', models.PositiveIntegerField(blank=True, null=True)),
                ('data_fim_mandato', models.DateField(verbose_name='Fim do Mandato')),
                ('votos_recebidos', models.PositiveIntegerField(blank=True, null=True, verbose_name='Votos Recebidos')),
                ('data_expedicao_diploma', models.DateField(verbose_name='Expedição do Diploma')),
                ('titular', models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], db_index=True, default=True, verbose_name='Vereador Titular')),
                ('observacao', models.TextField(blank=True, verbose_name='Observação')),
                ('coligacao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='parlamentares.Coligacao', verbose_name='Coligação')),
                ('legislatura', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='parlamentares.Legislatura', verbose_name='Legislatura')),
            ],
            options={
                'verbose_name': 'Mandato',
                'verbose_name_plural': 'Mandatos',
            },
        ),
        migrations.CreateModel(
            name='Municipio',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(blank=True, max_length=50)),
                ('uf', models.CharField(blank=True, choices=[('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'), ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'), ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'), ('PR', 'Paraná'), ('PB', 'Paraíba'), ('PA', 'Pará'), ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'), ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'), ('SE', 'Sergipe'), ('SP', 'São Paulo'), ('TO', 'Tocantins'), ('EX', 'Exterior')], max_length=2)),
                ('regiao', models.CharField(blank=True, choices=[('CO', 'Centro-Oeste'), ('NE', 'Nordeste'), ('NO', 'Norte'), ('SE', 'Sudeste'), ('SL', 'Sul'), ('EX', 'Exterior')], max_length=2)),
            ],
            options={
                'verbose_name': 'Município',
                'verbose_name_plural': 'Municípios',
            },
        ),
        migrations.CreateModel(
            name='NivelInstrucao',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(max_length=50, verbose_name='Nível de Instrução')),
            ],
            options={
                'verbose_name': 'Nível Instrução',
                'verbose_name_plural': 'Níveis Instrução',
            },
        ),
        migrations.CreateModel(
            name='Parlamentar',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_completo', models.CharField(max_length=50, verbose_name='Nome Completo')),
                ('nome_parlamentar', models.CharField(max_length=50, verbose_name='Nome Parlamentar')),
                ('sexo', models.CharField(choices=[('F', 'Feminino'), ('M', 'Masculino')], max_length=1, verbose_name='Sexo')),
                ('data_nascimento', models.DateField(blank=True, null=True, verbose_name='Data Nascimento')),
                ('cpf', models.CharField(blank=True, max_length=14, verbose_name='C.P.F')),
                ('rg', models.CharField(blank=True, max_length=15, verbose_name='R.G.')),
                ('titulo_eleitor', models.CharField(blank=True, max_length=15, verbose_name='Título de Eleitor')),
                ('numero_gab_parlamentar', models.CharField(blank=True, max_length=10, verbose_name='Nº Gabinete')),
                ('telefone', models.CharField(blank=True, max_length=50, verbose_name='Telefone')),
                ('fax', models.CharField(blank=True, max_length=50, verbose_name='Fax')),
                ('endereco_residencia', models.CharField(blank=True, max_length=100, verbose_name='Endereço Residencial')),
                ('cep_residencia', models.CharField(blank=True, max_length=9, verbose_name='CEP')),
                ('telefone_residencia', models.CharField(blank=True, max_length=50, verbose_name='Telefone Residencial')),
                ('fax_residencia', models.CharField(blank=True, max_length=50, verbose_name='Fax Residencial')),
                ('endereco_web', models.URLField(blank=True, max_length=100, verbose_name='HomePage')),
                ('profissao', models.CharField(blank=True, max_length=50, verbose_name='Profissão')),
                ('email', models.EmailField(blank=True, max_length=100, verbose_name='E-mail')),
                ('locais_atuacao', models.CharField(blank=True, max_length=100, verbose_name='Locais de Atuação')),
                ('ativo', models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], db_index=True, default=False, verbose_name='Ativo na Casa?')),
                ('biografia', models.TextField(blank=True, verbose_name='Biografia')),
                ('fotografia', models.ImageField(blank=True, null=True, upload_to=sapl.parlamentares.models.foto_upload_path, validators=[sapl.utils.restringe_tipos_de_arquivo_img], verbose_name='Fotografia')),
                ('municipio_residencia', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='parlamentares.Municipio', verbose_name='Município')),
                ('nivel_instrucao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='parlamentares.NivelInstrucao', verbose_name='Nível Instrução')),
            ],
            options={
                'ordering': ['nome_parlamentar'],
                'verbose_name': 'Parlamentar',
                'verbose_name_plural': 'Parlamentares',
            },
        ),
        migrations.CreateModel(
            name='Partido',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sigla', models.CharField(max_length=9, verbose_name='Sigla')),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
                ('data_criacao', models.DateField(blank=True, null=True, verbose_name='Data Criação')),
                ('data_extincao', models.DateField(blank=True, null=True, verbose_name='Data Extinção')),
                ('logo_partido', models.ImageField(blank=True, null=True, upload_to=sapl.parlamentares.models.logo_upload_path, validators=[sapl.utils.restringe_tipos_de_arquivo_img], verbose_name='Logo Partido')),
            ],
            options={
                'verbose_name': 'Partido',
                'verbose_name_plural': 'Partidos',
            },
        ),
        migrations.CreateModel(
            name='SessaoLegislativa',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.PositiveIntegerField(verbose_name='Número')),
                ('tipo', models.CharField(choices=[('O', 'Ordinária'), ('E', 'Extraordinária')], max_length=1, verbose_name='Tipo')),
                ('data_inicio', models.DateField(verbose_name='Data Início')),
                ('data_fim', models.DateField(verbose_name='Data Fim')),
                ('data_inicio_intervalo', models.DateField(blank=True, null=True, verbose_name='Início Intervalo')),
                ('data_fim_intervalo', models.DateField(blank=True, null=True, verbose_name='Fim Intervalo')),
                ('legislatura', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='parlamentares.Legislatura', verbose_name='Legislatura')),
            ],
            options={
                'ordering': ['-data_inicio', '-data_fim'],
                'verbose_name': 'Sessão Legislativa',
                'verbose_name_plural': 'Sessões Legislativas',
            },
        ),
        migrations.CreateModel(
            name='SituacaoMilitar',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(max_length=50, verbose_name='Situação Militar')),
            ],
            options={
                'verbose_name': 'Tipo Situação Militar',
                'verbose_name_plural': 'Tipos Situações Militares',
            },
        ),
        migrations.CreateModel(
            name='TipoAfastamento',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(max_length=50, verbose_name='Descrição')),
                ('indicador', models.CharField(choices=[('A', 'Afastamento'), ('F', 'Fim de Mandato')], default='F', max_length=1, verbose_name='Indicador')),
                ('dispositivo', models.CharField(blank=True, max_length=50, verbose_name='Dispositivo')),
            ],
            options={
                'verbose_name': 'Tipo de Afastamento',
                'verbose_name_plural': 'Tipos de Afastamento',
            },
        ),
        migrations.CreateModel(
            name='TipoDependente',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(max_length=50, verbose_name='Descrição')),
            ],
            options={
                'verbose_name': 'Tipo de Dependente',
                'verbose_name_plural': 'Tipos de Dependente',
            },
        ),
        migrations.CreateModel(
            name='Votante',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.DateTimeField(auto_now_add=True, max_length=30, null=True, verbose_name='Data')),
                ('parlamentar', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='parlamentar', to='parlamentares.Parlamentar', verbose_name='Parlamentar')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='user', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'permissions': (('can_vote', 'Can Vote'),),
                'verbose_name': 'Usuário',
                'verbose_name_plural': 'Usuários',
            },
        ),
        migrations.AddField(
            model_name='parlamentar',
            name='situacao_militar',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='parlamentares.SituacaoMilitar', verbose_name='Situação Militar'),
        ),
        migrations.AddField(
            model_name='mandato',
            name='parlamentar',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='parlamentares.Parlamentar'),
        ),
        migrations.AddField(
            model_name='mandato',
            name='tipo_afastamento',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='parlamentares.TipoAfastamento'),
        ),
        migrations.AddField(
            model_name='frente',
            name='parlamentares',
            field=models.ManyToManyField(blank=True, to='parlamentares.Parlamentar', verbose_name='Parlamentares'),
        ),
        migrations.AddField(
            model_name='filiacao',
            name='parlamentar',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='parlamentares.Parlamentar'),
        ),
        migrations.AddField(
            model_name='filiacao',
            name='partido',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='parlamentares.Partido', verbose_name='Partido'),
        ),
        migrations.AddField(
            model_name='dependente',
            name='parlamentar',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='parlamentares.Parlamentar'),
        ),
        migrations.AddField(
            model_name='dependente',
            name='tipo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='parlamentares.TipoDependente', verbose_name='Tipo'),
        ),
        migrations.AddField(
            model_name='composicaomesa',
            name='parlamentar',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='parlamentares.Parlamentar'),
        ),
        migrations.AddField(
            model_name='composicaomesa',
            name='sessao_legislativa',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='parlamentares.SessaoLegislativa'),
        ),
        migrations.AddField(
            model_name='composicaocoligacao',
            name='partido',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='parlamentares.Partido', verbose_name='Partidos da Coligação'),
        ),
        migrations.AddField(
            model_name='coligacao',
            name='legislatura',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='parlamentares.Legislatura', verbose_name='Legislatura'),
        ),

        migrations.AddField(
            model_name='partido',
            name='metadata',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=None, encoder=django.core.serializers.json.DjangoJSONEncoder, null=True, verbose_name='Metadados'),
        ),
    ]

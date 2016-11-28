from datetime import datetime
from random import random
import csv
import os

from django.utils.dateparse import parse_date
import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmj.settings")
django.setup()


# Shell Plus Model Imports
# Shell Plus Django Imports

if __name__ == "__main__":

    from django.conf import settings
    from django.contrib.admin.models import LogEntry
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.sessions.models import Session
    from django.core.cache import cache
    from django.core.urlresolvers import reverse
    from django.db import transaction
    from django.db.models import Avg, Count, F, Max, Min, Sum, Q, Prefetch, Case, When
    from django.utils import timezone
    from easy_thumbnails.models import Source, Thumbnail, ThumbnailDimensions
    from sapl.base.models import CasaLegislativa, ProblemaMigracao
    from sapl.comissoes.models import CargoComissao, Comissao, Composicao, Participacao, Periodo, TipoComissao
    from sapl.compilacao.models import Dispositivo, Nota, PerfilEstruturalTextoArticulado, Publicacao, TextoArticulado, TipoDispositivo, TipoDispositivoRelationship, TipoNota, TipoPublicacao, TipoTextoArticulado, TipoVide, VeiculoPublicacao, Vide
    from sapl.lexml.models import LexmlProvedor, LexmlPublicador
    from sapl.materia.models import AcompanhamentoMateria, Anexada, AssuntoMateria, Autor, Autoria, DespachoInicial, DocumentoAcessorio, MateriaAssunto, MateriaLegislativa, Numeracao, Orgao, Origem, Parecer, Proposicao, RegimeTramitacao, Relatoria, StatusTramitacao, TipoAutor, TipoDocumento, TipoFimRelatoria, TipoMateriaLegislativa, TipoProposicao, Tramitacao, UnidadeTramitacao
    from sapl.norma.models import AssuntoNorma, AssuntoNormaRelationship, LegislacaoCitada, NormaJuridica, TipoNormaJuridica, VinculoNormaJuridica
    from sapl.painel.models import Cronometro, Painel
    from sapl.parlamentares.models import CargoMesa, Coligacao, ComposicaoColigacao, ComposicaoMesa, Dependente, Filiacao, Legislatura, Mandato, Municipio, NivelInstrucao, Parlamentar, Partido, SessaoLegislativa, SituacaoMilitar, TipoAfastamento, TipoDependente
    from sapl.protocoloadm.models import DocumentoAcessorioAdministrativo, DocumentoAdministrativo, Protocolo, StatusTramitacaoAdministrativo, TipoDocumentoAdministrativo, TipoInstituicao, TramitacaoAdministrativo
    from sapl.sessao.models import Bancada, CargoBancada, ExpedienteMateria, ExpedienteSessao, IntegranteMesa, Orador, OradorExpediente, OrdemDia, PresencaOrdemDia, RegistroVotacao, SessaoPlenaria, SessaoPlenariaPresenca, TipoExpediente, TipoResultadoVotacao, TipoSessaoPlenaria, VotoParlamentar
    from social.apps.django_app.default.models import Association, Code, Nonce, UserSocialAuth
    from taggit.models import Tag, TaggedItem
    from wagtail.wagtailcore.models import Collection, GroupCollectionPermission, GroupPagePermission, Page, PageRevision, PageViewRestriction, Site
    from wagtail.wagtaildocs.models import Document
    from wagtail.wagtailembeds.models import Embed
    from wagtail.wagtailforms.models import FormSubmission
    from wagtail.wagtailimages.models import Filter, Image, Rendition
    from wagtail.wagtailredirects.models import Redirect
    from wagtail.wagtailsearch.models import Query, QueryDailyHits
    from wagtail.wagtailusers.models import UserProfile

    from cmj.cerimonial.models import AssuntoProcesso, ClassificacaoProcesso, Contato, Dependente, DependentePerfil, Email, EmailPerfil, Endereco, EnderecoPerfil, EstadoCivil, FiliacaoPartidaria, GrupoDeContatos, LocalTrabalho, LocalTrabalhoPerfil, NivelInstrucao, OperadoraTelefonia, Parentesco, Perfil, Processo, ProcessoContato, PronomeTratamento, StatusProcesso, Telefone, TelefonePerfil, TipoAutoridade, TipoEmail, TipoEndereco, TipoLocalTrabalho, TipoTelefone, TopicoProcesso
    from cmj.core.models import AreaTrabalho, Bairro, Cep, Distrito, ImpressoEnderecamento, Logradouro, OperadorAreaTrabalho, RegiaoMunicipal, TipoLogradouro, Trecho, User
    from cmj.home.models import HomePage

    import re

    at = AreaTrabalho.objects.get(pk=6)

    contatos = list(Contato.objects.all())
    enderecos = list(Endereco.objects.all())

    grupos = list(GrupoDeContatos.objects.filter(workspace_id=at.pk))

    for i in range(1000):
        print(i)

        c = contatos[int(len(contatos) * random())]
        c.pk = None
        c.nome = '%s-%s' % (c.nome, i)
        c.workspace = at
        c.save()

        end = enderecos[int(len(enderecos) * random())]
        end.pk = None
        end.contato = c
        end.municipio_id = 4106902
        end.save()

        grupos[i % len(grupos)].contatos.add(c)

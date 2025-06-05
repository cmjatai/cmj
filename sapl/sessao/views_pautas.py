from re import sub

from django.conf import settings
from django.http.response import HttpResponseRedirect
from django.urls.base import reverse
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView

from sapl.materia.models import Autoria
from sapl.sessao.filterviews import PesquisarSessaoPlenariaView

from .forms import (PautaSessaoFilterSet, PautaComissaoFilterSet,)
from .models import (ExpedienteMateria, ExpedienteSessao, OradorExpediente, OrdemDia,
                     SessaoPlenaria, TipoSessaoPlenaria)


class PautaSessaoView(TemplateView):
    model = SessaoPlenaria
    template_name = "sessao/pauta_inexistente.html"

    def get_sessao_mais_recente(self, tipo__tipogeral):
        sessao = SessaoPlenaria.objects.filter(
            tipo__tipogeral=tipo__tipogeral
        ).order_by("-data_inicio", "-id").first()
        return sessao

    def get(self, request, *args, **kwargs):
        sessao = self.get_sessao_mais_recente(TipoSessaoPlenaria.TIPOGERAL_SESSAO)
        if not sessao:
            return self.render_to_response({})

        return HttpResponseRedirect(
            reverse('sapl.sessao:pauta_sessao_detail', kwargs={'pk': sessao.pk}))


class PautaComissaoView(PautaSessaoView):

    def get(self, request, *args, **kwargs):
        sessao = self.get_sessao_mais_recente(TipoSessaoPlenaria.TIPOGERAL_REUNIAO)
        if not sessao:
            return self.render_to_response({})

        return HttpResponseRedirect(
            reverse('sapl.sessao:pauta_comissao_detail', kwargs={'pk': sessao.pk}))


class PautaSessaoDetailView(DetailView):
    template_name = "sessao/pauta_sessao_detail.html"
    model = SessaoPlenaria

    @property
    def search_url(self):
        return reverse('sapl.sessao:pesquisar_pauta')

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        # =====================================================================
        # Identificação Básica
        abertura = self.object.data_inicio.strftime('%d/%m/%Y')
        if self.object.data_fim:
            encerramento = self.object.data_fim.strftime('%d/%m/%Y')
        else:
            encerramento = ""

        context.update({'basica': [
            _('Tipo de Sessão: %(tipo)s') % {'tipo': self.object.tipo},
            _('Abertura: %(abertura)s') % {'abertura': abertura},
            _('Encerramento: %(encerramento)s') % {
                'encerramento': encerramento},
        ]})
        # =====================================================================
        # Matérias Expediente
        materias = ExpedienteMateria.objects.filter(
            sessao_plenaria_id=self.object.id,
            parent__isnull=True
        ).order_by('numero_ordem', 'materia', 'resultado')

        materias_expediente = []
        for m in materias:
            ementa = m.materia.ementa
            titulo = m.materia
            numero = m.numero_ordem

            tramitacao_item_sessao = m.tramitacao
            if not tramitacao_item_sessao:
                ultima_tramitacao = m.materia.tramitacao_set.first()
                situacao = ultima_tramitacao if ultima_tramitacao else None
            else:
                situacao = tramitacao_item_sessao

            if situacao is None:
                situacao = _("Não informada")
            else:
                situacao = f'{situacao.status}<br><em>{situacao.texto}</em>'
            rv = m.registrovotacao_set.all()
            if rv:
                resultado = rv[0].tipo_resultado_votacao.nome
                resultado_observacao = rv[0].observacao
            else:
                resultado = _('Matéria não votada')
                resultado_observacao = _(' ')

            autoria = Autoria.objects.filter(materia_id=m.materia_id)
            autor = [str(x.autor) for x in autoria]

            mat = {'id': m.materia_id,
                   'ementa': ementa,
                   'observacao': m.observacao,
                   'titulo': titulo,
                   'numero': numero,
                   'resultado': resultado,
                   'resultado_observacao': resultado_observacao,
                   'situacao': situacao,
                   'autor': autor
                   }
            materias_expediente.append(mat)

        context.update({'materia_expediente': materias_expediente})
        # =====================================================================
        # Expedientes
        expediente = ExpedienteSessao.objects.filter(
            sessao_plenaria_id=self.object.id)

        expedientes = []
        for e in expediente:
            tipo = e.tipo
            conteudo = sub(
                '&nbsp;', ' ', strip_tags(e.conteudo.replace('<br/>', '\n')))

            ex = {'tipo': tipo, 'conteudo': conteudo}
            expedientes.append(ex)

        context.update({'expedientes': expedientes})
        # =====================================================================
        # Orador Expediente
        oradores = OradorExpediente.objects.filter(
            sessao_plenaria_id=self.object.id).order_by('numero_ordem')
        context.update({'oradores': oradores})
        # =====================================================================
        # Matérias Ordem do Dia
        ordem = OrdemDia.objects.filter(
            sessao_plenaria_id=self.object.id,
            parent__isnull=True
        ).order_by('numero_ordem', 'materia', 'resultado')

        materias_ordem = []
        for o in ordem:
            ementa = o.materia.ementa
            titulo = o.materia
            numero = o.numero_ordem

            tramitacao_item_sessao = o.tramitacao
            if not tramitacao_item_sessao:
                ultima_tramitacao = o.materia.tramitacao_set.first()
                situacao = ultima_tramitacao.status if ultima_tramitacao else None
            else:
                situacao = tramitacao_item_sessao.status

            if situacao is None:
                situacao = _("Não informada")
            # Verificar resultado
            rv = o.registrovotacao_set.all()
            if rv:
                resultado = rv[0].tipo_resultado_votacao.nome
                resultado_observacao = rv[0].observacao
            else:
                resultado = _('Matéria não votada')
                resultado_observacao = _(' ')

            autoria = Autoria.objects.filter(
                materia_id=o.materia_id)
            autor = [str(x.autor) for x in autoria]

            mat = {'id': o.materia_id,
                   'ementa': ementa,
                   'observacao': o.observacao,
                   'titulo': titulo,
                   'numero': numero,
                   'resultado': resultado,
                   'resultado_observacao': resultado_observacao,
                   'situacao': situacao,
                   'autor': autor,
                   'materia': o.materia
                   }
            materias_ordem.append(mat)

        context.update({'materias_ordem': materias_ordem})
        context.update({'subnav_template_name': ''})

        return self.render_to_response(context)

class PautaComissaoDetailView(PautaSessaoDetailView):

    @property
    def search_url(self):
        return reverse('sapl.sessao:pesquisar_comissao_pauta')


class PesquisarPautaSessaoView(PesquisarSessaoPlenariaView):
    filterset_class = PautaSessaoFilterSet
    template_name = 'sessao/pauta_sessao_filter.html'

    viewname = 'sapl.sessao:pesquisar_pauta'

    fields_base_report = [
        'id',
        'data_inicio',
        'hora_inicio',
        'data_fim',
        'hora_fim',
        'url_pauta',
        '',
    ]

    fields_report = {
        'csv': fields_base_report,
        'xlsx': fields_base_report,
        'json': fields_base_report,
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Pesquisar Pauta de Sessão')
        context['bg_title'] = ''
        return context

    def hook_header_url_pauta(self):
        return 'Link para a Pauta'

    def hook_url_pauta(self, obj):
        url_reverse = reverse('sapl.sessao:pauta_sessao_detail', kwargs={'pk': obj.pk})
        return f'{settings.SITE_URL}{url_reverse}'

class PesquisarPautaComissaoView(PesquisarSessaoPlenariaView):
    filterset_class = PautaComissaoFilterSet
    template_name = 'sessao/pauta_comissao_filter.html'

    viewname = 'sapl.sessao:pesquisar_comissao_pauta'

    fields_base_report = [
        'id',
        'data_inicio',
        'hora_inicio',
        'data_fim',
        'hora_fim',
        'url_pauta',
        '',
    ]

    fields_report = {
        'csv': fields_base_report,
        'xlsx': fields_base_report,
        'json': fields_base_report,
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Pesquisar Pauta das Comissões')
        context['bg_title'] = ''
        return context

    def hook_header_url_pauta(self):
        return 'Link para a Pauta'

    def hook_url_pauta(self, obj):
        url_reverse = reverse('sapl.sessao:pauta_comissao_detail', kwargs={'pk': obj.pk})
        return f'{settings.SITE_URL}{url_reverse}'

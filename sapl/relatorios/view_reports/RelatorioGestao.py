from django.db.models.aggregates import Count

from cmj.core.views_estatisticas import get_redessociais
from sapl.comissoes.models import Composicao, Participacao
from sapl.norma.models import TipoNormaJuridica
from sapl.parlamentares.models import ComposicaoMesa, Legislatura
from sapl.relatorios.view_reports.mixins import RelatorioMixin
from django.views.generic import TemplateView
import markdown as md
from django.utils import timezone
from markdown.extensions.toc import slugify_unicode
from markdown.extensions.toc import TocExtension as makeTocExtension

markstyles = '''<style>
</style>
'''
class View(RelatorioMixin, TemplateView):

    def get_markdown(self):
        self.ano = self.kwargs.get('ano', None)
        try:
            self.ano = int(self.ano)
        except ValueError:
            self.ano = timezone.now().year
        if self.ano < 1900 or self.ano > 2100:
            self.ano = timezone.now().year

        mark = (
            self.get_capa(),
            self.get_comissoes(),
            self.get_normas()
        )

        html = []
        for i, mt in enumerate(mark):
            cols = []
            for m in mt:
                css_class = ''
                tipo = 'html'
                if isinstance(m, tuple):
                    m, css_class, tipo = m
                if tipo == 'markdown':

                    m = md.markdown(m, extensions=[
                        makeTocExtension(slugify=slugify_unicode), #TOC
                    ])
                cols.append(f'<div class="{css_class}">{m}</div>')
            row = f'<div class="row {"page-break" if i else ""}">{"".join(cols)}</div>'
            html.append(row)

        mdr = [f'{markstyles}<div class="container container-bi container-show">{h}</div>' for h in html]

        return ''.join(mdr)

    def get_normas(self):

        mark = [f'## Atos Normativos e Legislativos de {self.ano}']
        tipos = TipoNormaJuridica.objects.filter(
            normajuridica_set__data__year=2024
        ).annotate(Count('normajuridica_set')).order_by('relevancia')
        for t in tipos:
            mark.append('')
            mark.append(f'* [{t.descricao} ({t.normajuridica_set__count})](http://www.jatai.go.leg.br/pesquisar/norma?tipo_i={t.pk}&ano_i={self.ano})')

        mark.append('')
        mark.append('##### _Clique no tipo de norma para acessar a listagem dos atos referente ao ano {self.ano}._')

        mark.append(f'### Assuntos tratados nos Atos Normativos e Legislativos de {self.ano}')


        return (
            ('\n'.join(mark), 'container-atos-normativos col-md-12', 'markdown'),
        )

    def get_comissoes(self):
        """
        Retorna a página de comissões do relatório
        """
        mark = [f'## Comissões']
        participacoes = Participacao.objects.filter(
            composicao__periodo__data_inicio__year__lte=self.ano,
            composicao__periodo__data_fim__year__gte=self.ano,
        ).order_by(
            'composicao__comissao__nome',
            'cargo_id'
        )

        comissao_atual = None
        for participacao in participacoes:
            if participacao.composicao.comissao != comissao_atual:
                comissao_atual = participacao.composicao.comissao
                mark.append('')
                mark.append(f'#### {comissao_atual.sigla} - {comissao_atual.nome}')

            mark.append(f'* {participacao.cargo.nome.upper()}: **{participacao.parlamentar.nome_parlamentar}**')

        return (
            ('\n'.join(mark), 'col-md-12', 'markdown'),
        )

    def get_capa(self):
        """
        Retorna a página de capa do relatório
        """

        html0 = f'''
            <div class="capa">
                Relatório Anual
                <br>
                de Atividades Legislativas
                <br>
                <span class="capa-ano">
                {self.ano}
                </div>'''

        mark1 = []


        legislatura = Legislatura.objects.filter(
            data_inicio__year__lte=self.ano,
            data_fim__year__gte=self.ano
        ).first()
        mark1.append(f'# {legislatura.nome}')


        mark1.append(f'## Mesa Diretora')
        membros_da_mesa = ComposicaoMesa.objects.filter(
            sessao_legislativa__data_inicio__year__lte=self.ano,
            sessao_legislativa__data_fim__year__gte=self.ano,
        ).order_by(
            'cargo_id'
        )
        for m in membros_da_mesa:
            mark1.append(f'* {m.cargo.descricao.upper()}: **{m.parlamentar.nome_parlamentar}**')

        mark1.append(f'## Parlamentares')
        parlamentares = legislatura.mandato_set.values_list(
            'parlamentar__nome_parlamentar', flat=True
        ).order_by('parlamentar__nome_parlamentar').distinct()
        for p in parlamentares:
            mark1.append(f'* **{p}**')

        return (
            (html0, 12, 'html'),
            ('\n'.join(mark1), 'col-md-12', 'markdown')
        )

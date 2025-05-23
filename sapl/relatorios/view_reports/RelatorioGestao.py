from django.conf import settings
from django.db.models.aggregates import Count

from cmj.core.views_estatisticas import get_redessociais
from sapl.comissoes.models import Composicao, Participacao
from sapl.materia.models import AssuntoMateria, TipoMateriaLegislativa
from sapl.norma.models import AssuntoNorma, TipoNormaJuridica
from sapl.parlamentares.models import ComposicaoMesa, Legislatura, Parlamentar
from sapl.relatorios.view_reports.mixins import RelatorioMixin
from django.views.generic import TemplateView
import markdown as md
from django.utils import timezone
from markdown.extensions.toc import slugify_unicode
from markdown.extensions.toc import TocExtension as makeTocExtension

from sapl.sessao.models import TipoSessaoPlenaria

class View(RelatorioMixin, TemplateView):

    def get(self, request, *args, **kwargs):
        self.ano = self.kwargs.get('ano', None)
        self.site_url = settings.SITE_URL
        try:
            self.ano = int(self.ano)
        except ValueError:
            self.ano = timezone.now().year
        if self.ano < 1900 or self.ano > 2100:
            self.ano = timezone.now().year
        return super(View, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(View, self).get_context_data(**kwargs)
        context['html_capa'] = self.get_html(
            [
                self.get_capa()
            ]
        )
        context['html_body'] = self.get_html(
            [
                self.get_producao_parlamentar(),
                self.get_comissoes(),
                self.get_normas(),
                self.get_materias(),
                self.get_sessoes()
            ]
        )
        return context


    def get_html(self, markdowns):
        """
        Retorna o HTML do relatório
        """
        html = []
        for i, mt in enumerate(markdowns):
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
            row = f'<div class="row">{"".join(cols)}</div>'
            html.append(row)
        return ''.join(html)

    def md2html(self, md_text):
        """
        Converte o texto markdown para html
        """
        return md.markdown(md_text, extensions=[
            makeTocExtension(slugify=slugify_unicode), #TOC
        ])


    def get_capa(self):
        """
        Retorna a página de capa do relatório
        """

        html0 = f'''
            <div class="capa">
                Relatório Anual
                de Gestão e
                <br>
                Atividades Legislativas
                <br>
                <span class="capa-ano">
                {self.ano}
            </div>'''

        mark1 = []


        self.legislatura = Legislatura.objects.filter(
            data_inicio__year__lte=self.ano,
            data_fim__year__gte=self.ano
        ).first()
        mark1.append(f'# {self.legislatura.nome}')


        mark1.append(f'## Mesa Diretora')
        self.membros_da_mesa = ComposicaoMesa.objects.filter(
            sessao_legislativa__data_inicio__year__lte=self.ano,
            sessao_legislativa__data_fim__year__gte=self.ano,
        ).order_by(
            'cargo_id'
        )
        for m in self.membros_da_mesa:
            mark1.append(f'* {m.cargo.descricao.upper()}: **{m.parlamentar.nome_parlamentar}**')

        mark2 = []
        mark2.append(f'## Parlamentares')
        self.parlamentares = Parlamentar.objects.filter(
            id__in=self.legislatura.mandato_set.values_list('parlamentar', flat=True)
        ).order_by(
            'nome_parlamentar'
        )
        for p in self.parlamentares:
            mark2.append(f'* **{p}**')

        return (
            (html0, 'col-md-12 capa-titulo', 'html'),
            ('\n'.join(mark1), 'col-md-12 capa-mesa', 'markdown'),
            ('\n'.join(mark2), 'col-md-12 capa-parlamentares', 'markdown')
        )

    def get_comissoes(self):
        """
        Retorna a página de comissões do relatório
        """
        mark0 = [f'# 6. Comissões']

        participacoes = Participacao.objects.filter(
            composicao__periodo__data_inicio__year__lte=self.ano,
            composicao__periodo__data_fim__year__gte=self.ano,
        ).order_by(
            'composicao__comissao__nome',
            'cargo_id'
        )
        comissoes = []
        comissao = []

        comissao_atual = None
        for participacao in participacoes:
            if participacao.composicao.comissao != comissao_atual:
                comissao = []
                comissoes.append(comissao)
                comissao_atual = participacao.composicao.comissao
                comissao.append(f'#### [{comissao_atual.sigla} - {comissao_atual.nome}]({self.site_url}/comissao/{comissao_atual.pk})')

            comissao.append(f'* {participacao.cargo.nome.upper()}: **{participacao.parlamentar.nome_parlamentar}**')

        r = [('\n'.join(mark0), 'col-md-12 new-page', 'markdown'),]

        length_comissoes = len(comissoes)
        row1_from_column2 = length_comissoes // 2
        row2_from_column2 = length_comissoes - row1_from_column2

        if row1_from_column2 % 2 == 1:
            row1_from_column2 += 1
            row2_from_column2 = row1_from_column2 - 2

        row3_from_column2 = length_comissoes - row1_from_column2 - row2_from_column2

        mark1 = []
        mark2 = []
        mark3 = []
        for i, comissao in enumerate(comissoes):
            if i < row1_from_column2:
                mark1.append('')
                mark1.append('\n'.join(comissao))
            elif i < row1_from_column2 + row2_from_column2:
                mark2.append('')
                mark2.append('\n'.join(comissao))
            else:
                mark3.append('')
                mark3.append('\n'.join(comissao))

        r.append(('\n'.join(mark1), 'col-md-6 columns2', 'markdown'))
        r.append(('\n'.join(mark2), 'col-md-6 columns2', 'markdown'))

        if mark3:
            r.append(('\n'.join(mark3), 'col-md-12', 'markdown'))

        return r

    def get_normas(self):

        mark = [f'# 7. Atos Normativos/Legislativos de {self.ano}']
        tipos = TipoNormaJuridica.objects.filter(
            normajuridica_set__data__year=self.ano
        ).annotate(Count('normajuridica_set')).order_by('relevancia')
        for t in tipos:
            mark.append(f'* [{t.descricao} ({t.normajuridica_set__count})]'
                        f'(http://www.jatai.go.leg.br/pesquisar/norma?tipo_i={t.pk}&ano_i={self.ano})')

        mark2 = []
        mark2.append(f'### Assuntos tratados nos Atos Normativos/Legislativos de {self.ano}')

        assuntos = AssuntoNorma.objects.filter(
            normajuridica__data__year=self.ano
        ).annotate(Count('normajuridica')).order_by('assunto')

        mark21 = []
        for i, a in enumerate(assuntos):
            text = f'* [{a.assunto} ({a.normajuridica__count})]' \
                f'(http://www.jatai.go.leg.br/pesquisar/norma?assuntos_is={a.pk}&ano_i={self.ano})'

            mark21.append(text)
        return (
            ('\n'.join(mark), 'col-12 new-page', 'markdown'),
            ('\n'.join(mark2), 'col-12', 'markdown'),
            ('\n'.join(mark21), 'col-12 col-md-6 columns2', 'markdown'),
        )

    def get_materias(self):

        mark = [f'# 8. Matérias Legislativas no ano de {self.ano}']
        tipos =TipoMateriaLegislativa.objects.filter(
            materialegislativa__ano=self.ano,
        ).annotate(Count('materialegislativa')).order_by('sequencia_regimental')

        for t in tipos:
            mark.append(f'* [{t.descricao} ({t.materialegislativa__count})]'
                        f'(http://www.jatai.go.leg.br/pesquisar/materia?tipo_i={t.pk}&ano_i={self.ano})')

        mark2 = []

        assuntos = AssuntoMateria.objects.filter(
            materialegislativa__ano=self.ano,
            materialegislativa__tipo_id=3
        ).annotate(Count('materialegislativa')).order_by('assunto')
        for i, a in enumerate(assuntos):
            if not i:
                mark2.append('')
                mark2.append(f'### Assuntos dos Requerimentos de {self.ano}')
            mark2.append(
                f'* [{a.assunto} ({a.materialegislativa__count})]'
                f'(http://www.jatai.go.leg.br/pesquisar/materia?assuntos_is={a.pk}&ano_i={self.ano})'
            )

        return (
            ('\n'.join(mark), 'col-md-12 new-page', 'markdown'),
            ('\n'.join(mark2[:2]), 'col-md-12', 'markdown'),
            ('\n'.join(mark2[2:]), 'col-md-12 columns2', 'markdown'),
        )

    def get_producao_parlamentar(self):
        """
        Retorna a página de produção parlamentar por parlamentar
        """
        mark0 = [f'# 5. Produção Legislativa em {self.ano}']
        marks = []

        cols = []
        for p in self.parlamentares:
            autor = p.autor.first()
            if not autor:
                continue

            col = []
            col.append('')
            col.append(f'### {p.nome_parlamentar}')

            tipos_de_materia_do_parlamentar = TipoMateriaLegislativa.objects.filter(
                materialegislativa__ano=self.ano,
                materialegislativa__isnull=False,
                materialegislativa__autoria__autor=autor,
            ).annotate(Count('materialegislativa'))
            for t in tipos_de_materia_do_parlamentar:
                col.append(f'* [{t.descricao} ({t.materialegislativa__count})]'
                            f'(http://www.jatai.go.leg.br/pesquisar/materia?tipo_i={t.pk}&ano_i={self.ano}&autoria_is={autor.pk})')

            html_col = '<div class="col-md-6 inside-columns">{}</div>'.format(
                self.md2html('\n'.join(col))
            )

            cols.append(html_col)

            if len(cols) == 2:
                marks.append((''.join(cols), 'col-md-6 columns2', 'html'))
                cols = []

        marks.insert(0, ('\n'.join(mark0), 'col-md-12', 'markdown'))

        return marks


    def get_sessoes(self):
        """
        Retorna a página de sessões do relatório
        """
        tipos_de_sessao = TipoSessaoPlenaria.objects.filter(
            sessaoplenaria__data_inicio__year=self.ano,
        ).annotate(Count('sessaoplenaria'))

        mark = [f'# 9. Sessões Plenárias de {self.ano}']

        for t in tipos_de_sessao:
            mark.append(
                f'* [{t.nome} ({t.sessaoplenaria__count})]'
                f'(http://www.jatai.go.leg.br/sessao/pesquisar-sessao?tipo={t.pk}&data_inicio__year={self.ano})')

        return (
            ('\n'.join(mark), 'col-md-12', 'markdown'),
        )
    